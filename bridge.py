"""
SmartWave Quant Lab — Integration Bridge
==========================================
Connects EXISTING modules to the NEW Numba engine:
  - MT5 CSV/HST data → NumPy arrays for fast_backtest
  - Strategy DNA → MQL5 code generation
  - Prop firm compliance checking
  - Report generation

This is the GLUE that makes everything work together.
"""

from __future__ import annotations

import logging
import time
import os
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from core.models import Tick, Bar, Timeframe, BacktestConfig
from core.engine_fast import (
    precompute_indicators, fast_backtest,
    signal_ema_cross, signal_fvg_ob, signal_breakout,
    signal_mean_reversion, signal_asian_breakout,
)
from core.validation import (
    compute_metrics, deflated_sharpe, monte_carlo_permutation,
    walk_forward, composite_score, detect_regime, Metrics,
)

logger = logging.getLogger("smartwave.bridge")


# ══════════════════════════════════════════════════════════════
# DATA BRIDGE: MT5 CSV/Bars → NumPy arrays for Numba engine
# ══════════════════════════════════════════════════════════════

class DataBridge:
    """
    Converts data from ANY existing connector into NumPy arrays
    compatible with the Numba fast_backtest engine.
    
    Input sources (from data/connectors.py and data/mt5_bridge.py):
      - MT5 CSV bars (import_bars)
      - MT5 tick export (import_ticks)  
      - MT5 HST binary files
      - Dukascopy ticks
      - Synthetic generator
      
    Output: dict of aligned NumPy float64 arrays
    """

    @staticmethod
    def bars_to_arrays(bars: list[Bar]) -> dict[str, np.ndarray]:
        """Convert list of Bar objects → NumPy arrays."""
        n = len(bars)
        O = np.empty(n, dtype=np.float64)
        H = np.empty(n, dtype=np.float64)
        L = np.empty(n, dtype=np.float64)
        C = np.empty(n, dtype=np.float64)
        V = np.empty(n, dtype=np.float64)
        SP = np.empty(n, dtype=np.float64)
        HOUR = np.empty(n, dtype=np.float64)

        for i, bar in enumerate(bars):
            O[i] = bar.open
            H[i] = bar.high
            L[i] = bar.low
            C[i] = bar.close
            V[i] = bar.volume
            SP[i] = bar.spread if bar.spread > 0 else 0.25  # default spread
            HOUR[i] = bar.timestamp.hour

        logger.info(f"Converted {n:,} bars → NumPy arrays | "
                     f"Price: {C.min():.2f}-{C.max():.2f}")
        return {"O": O, "H": H, "L": L, "C": C, "V": V,
                "spread": SP, "hour": HOUR}

    @staticmethod
    def ticks_to_bar_arrays(ticks: list[Tick], timeframe: Timeframe = Timeframe.M5
                            ) -> dict[str, np.ndarray]:
        """Convert list of Tick objects → aggregated bar arrays."""
        if not ticks:
            raise ValueError("No ticks provided")

        tf_seconds = timeframe.seconds
        bars_O, bars_H, bars_L, bars_C = [], [], [], []
        bars_V, bars_SP, bars_HOUR = [], [], []

        # Aggregate ticks into bars
        current_bar_start = None
        cur_o = cur_h = cur_l = cur_c = 0.0
        cur_v = 0.0
        cur_sp_sum = 0.0
        cur_count = 0

        for tick in ticks:
            ts = tick.timestamp
            bar_start_ts = int(ts.timestamp()) // tf_seconds * tf_seconds
            bar_start = datetime.fromtimestamp(bar_start_ts)

            if current_bar_start is None or bar_start != current_bar_start:
                # Save previous bar
                if current_bar_start is not None and cur_count > 0:
                    bars_O.append(cur_o)
                    bars_H.append(cur_h)
                    bars_L.append(cur_l)
                    bars_C.append(cur_c)
                    bars_V.append(cur_v)
                    bars_SP.append(cur_sp_sum / cur_count)
                    bars_HOUR.append(current_bar_start.hour)

                # Start new bar
                current_bar_start = bar_start
                cur_o = tick.mid
                cur_h = tick.mid
                cur_l = tick.mid
                cur_c = tick.mid
                cur_v = tick.bid_volume + tick.ask_volume
                cur_sp_sum = tick.spread
                cur_count = 1
            else:
                cur_h = max(cur_h, tick.mid)
                cur_l = min(cur_l, tick.mid)
                cur_c = tick.mid
                cur_v += tick.bid_volume + tick.ask_volume
                cur_sp_sum += tick.spread
                cur_count += 1

        # Last bar
        if cur_count > 0:
            bars_O.append(cur_o)
            bars_H.append(cur_h)
            bars_L.append(cur_l)
            bars_C.append(cur_c)
            bars_V.append(cur_v)
            bars_SP.append(cur_sp_sum / cur_count)
            bars_HOUR.append(current_bar_start.hour if current_bar_start else 0)

        result = {
            "O": np.array(bars_O, dtype=np.float64),
            "H": np.array(bars_H, dtype=np.float64),
            "L": np.array(bars_L, dtype=np.float64),
            "C": np.array(bars_C, dtype=np.float64),
            "V": np.array(bars_V, dtype=np.float64),
            "spread": np.array(bars_SP, dtype=np.float64),
            "hour": np.array(bars_HOUR, dtype=np.float64),
        }

        logger.info(f"Aggregated {len(ticks):,} ticks → {len(bars_O):,} {timeframe.value} bars")
        return result

    @staticmethod
    def from_mt5_csv(filepath: str, timeframe: str = "M5",
                     start_date: str = None, end_date: str = None
                     ) -> dict[str, np.ndarray]:
        """
        Full pipeline: MT5 CSV file → NumPy arrays.
        
        Usage:
            data = DataBridge.from_mt5_csv("XAUUSD_M5.csv", "M5")
            indicators = precompute_indicators(data["O"], data["H"], ...)
        """
        from data.connectors import MT5CSVImporter
        importer = MT5CSVImporter()
        bars = importer.import_bars(filepath, Timeframe(timeframe),
                                    start_date, end_date)
        if not bars:
            raise ValueError(f"No bars imported from {filepath}")
        return DataBridge.bars_to_arrays(bars)

    @staticmethod
    def from_mt5_report(filepath: str) -> tuple[np.ndarray, float]:
        """
        Import MT5 report trades → trade PnL array for Monte Carlo.
        Returns: (trade_pnls_array, initial_capital)
        """
        from data.mt5_bridge import MT5ReportParser, MT5ResultConverter
        parser = MT5ReportParser()

        if filepath.endswith('.htm') or filepath.endswith('.html'):
            report = parser.parse_html_report(filepath)
        else:
            report = parser.parse_csv_trades(filepath)

        pnls = np.array([t.profit for t in report.trades], dtype=np.float64)
        capital = report.initial_deposit or 100000.0
        logger.info(f"Imported {len(pnls)} trades from MT5 report | Net P&L: ${pnls.sum():.2f}")
        return pnls, capital


# ══════════════════════════════════════════════════════════════
# PROP FIRM COMPLIANCE CHECKER
# ══════════════════════════════════════════════════════════════

@dataclass
class PropFirmRule:
    name: str
    max_daily_dd_pct: float
    max_total_dd_pct: float
    profit_target_pct: float
    min_trading_days: int = 4
    max_trading_days: int = 999
    weekend_holding: bool = True
    news_trading: bool = True


PROP_FIRMS = {
    "ftmo_challenge": PropFirmRule("FTMO Challenge", 5.0, 10.0, 10.0, 4, 30),
    "ftmo_verification": PropFirmRule("FTMO Verification", 5.0, 10.0, 5.0, 4, 60),
    "mff_challenge": PropFirmRule("MyFundedFX Challenge", 5.0, 12.0, 8.0, 3, 30),
    "mff_rapid": PropFirmRule("MFF Rapid Challenge", 5.0, 12.0, 8.0, 0, 999),
    "topstep_50k": PropFirmRule("Topstep $50K", 4.0, 4.5, 6.0, 0, 999),
    "the5ers_100k": PropFirmRule("The5ers $100K", 4.0, 6.0, 6.0, 3, 60),
    "e8_100k": PropFirmRule("E8 Funding $100K", 5.0, 8.0, 8.0, 0, 999),
}


@dataclass
class PropFirmResult:
    firm_name: str
    passed: bool
    daily_dd_ok: bool
    total_dd_ok: bool
    target_ok: bool
    trading_days_ok: bool
    actual_daily_dd: float
    actual_total_dd: float
    actual_return: float
    actual_days: int
    details: str = ""


def check_prop_compliance(metrics: Metrics, equity_curve: np.ndarray,
                          capital: float, firms: list[str] = None
                          ) -> list[PropFirmResult]:
    """
    Check strategy results against multiple prop firm rules.
    Uses the ACTUAL equity curve to compute daily drawdown properly.
    """
    if firms is None:
        firms = list(PROP_FIRMS.keys())

    # Compute daily max DD from equity curve
    step = max(1, len(equity_curve) // 252)
    daily_eq = equity_curve[::step]
    max_daily_dd = 0.0
    for i in range(1, len(daily_eq)):
        daily_change = (daily_eq[i] - daily_eq[i-1]) / daily_eq[i-1] * 100
        if daily_change < -max_daily_dd:
            max_daily_dd = abs(daily_change)

    # Count trading days
    n_days = len(daily_eq)

    results = []
    for firm_id in firms:
        if firm_id not in PROP_FIRMS:
            continue
        rule = PROP_FIRMS[firm_id]

        daily_ok = max_daily_dd <= rule.max_daily_dd_pct
        total_ok = metrics.max_dd_pct <= rule.max_total_dd_pct
        target_ok = metrics.total_return_pct >= rule.profit_target_pct
        days_ok = rule.min_trading_days <= n_days <= rule.max_trading_days

        passed = daily_ok and total_ok and target_ok and days_ok

        results.append(PropFirmResult(
            firm_name=rule.name,
            passed=passed,
            daily_dd_ok=daily_ok,
            total_dd_ok=total_ok,
            target_ok=target_ok,
            trading_days_ok=days_ok,
            actual_daily_dd=round(max_daily_dd, 2),
            actual_total_dd=metrics.max_dd_pct,
            actual_return=metrics.total_return_pct,
            actual_days=n_days,
        ))

    return results


# ══════════════════════════════════════════════════════════════
# MQL5 CODE GENERATOR
# ══════════════════════════════════════════════════════════════

class MQL5Generator:
    """
    Generate MQL5 Expert Advisor code from a StrategyDNA.
    
    This is the KILLER FEATURE for traders:
    - Generate strategy in Python → validate → export to MQL5
    - Run the MQL5 EA on MT5 live or demo
    - No manual recoding needed
    """

    TEMPLATE_HEADER = '''//+------------------------------------------------------------------+
//| {name}.mq5
//| Generated by SmartWave FX Quant Lab
//| https://smartwavefx.com
//+------------------------------------------------------------------+
#property copyright "SmartWave FX"
#property version   "1.00"
#property strict

//--- Input parameters
input double RiskPercent    = {risk_pct};     // Risk per trade %
input double RR_Ratio       = {rr};          // Risk:Reward ratio
input int    ATR_Period      = {atr_period};  // ATR period
input int    SessionStart    = {session_start}; // Session start hour (UTC)
input int    SessionEnd      = {session_end};   // Session end hour (UTC)
input int    MaxPositions    = 3;             // Max concurrent positions
input double MaxDailyDD     = 5.0;           // Max daily drawdown %
input int    MagicNumber     = {magic};       // Magic number
'''

    TEMPLATE_EMA_CROSS = '''
input int    EMA_Fast        = {ema_fast};   // Fast EMA period
input int    EMA_Slow        = {ema_slow};   // Slow EMA period

//--- Global variables
int handleFast, handleSlow, handleATR;
double emaFast[], emaSlow[], atrBuf[];
datetime lastBar;

//+------------------------------------------------------------------+
int OnInit()
{{
   handleFast = iMA(_Symbol, PERIOD_M5, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   handleSlow = iMA(_Symbol, PERIOD_M5, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   handleATR  = iATR(_Symbol, PERIOD_M5, ATR_Period);
   if(handleFast==INVALID_HANDLE || handleSlow==INVALID_HANDLE || handleATR==INVALID_HANDLE)
      return INIT_FAILED;
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(atrBuf, true);
   return INIT_SUCCEEDED;
}}

void OnDeinit(const int reason) {{ IndicatorRelease(handleFast); IndicatorRelease(handleSlow); IndicatorRelease(handleATR); }}

void OnTick()
{{
   datetime currentBar = iTime(_Symbol, PERIOD_M5, 0);
   if(currentBar == lastBar) return;
   lastBar = currentBar;
   
   // Session filter
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.hour < SessionStart || dt.hour >= SessionEnd) return;
   
   // Check max positions
   if(CountPositions() >= MaxPositions) return;
   
   // Get indicator values
   CopyBuffer(handleFast, 0, 0, 3, emaFast);
   CopyBuffer(handleSlow, 0, 0, 3, emaSlow);
   CopyBuffer(handleATR, 0, 0, 2, atrBuf);
   
   double atr = atrBuf[0];
   if(atr <= 0) return;
   
   // Bullish cross
   if(emaFast[1] <= emaSlow[1] && emaFast[0] > emaSlow[0])
   {{
      double sl = atr * 1.5;
      double tp = sl * RR_Ratio;
      double lots = CalcLotSize(sl);
      OpenTrade(ORDER_TYPE_BUY, lots, sl, tp, "EMA Cross BUY");
   }}
   
   // Bearish cross
   if(emaFast[1] >= emaSlow[1] && emaFast[0] < emaSlow[0])
   {{
      double sl = atr * 1.5;
      double tp = sl * RR_Ratio;
      double lots = CalcLotSize(sl);
      OpenTrade(ORDER_TYPE_SELL, lots, sl, tp, "EMA Cross SELL");
   }}
}}
'''

    TEMPLATE_FVG_OB = '''
input int    EMA_Fast        = {ema_fast};    // Fast EMA for trend
input int    EMA_Slow        = {ema_slow};    // Slow EMA for trend
input double FVG_MinSize     = {fvg_min};     // Minimum FVG size
input int    Cooldown        = {cooldown};    // Bars between trades

int handleFast, handleSlow, handleATR;
double emaFast[], emaSlow[], atrBuf[];
datetime lastBar;
int barsSinceSignal = 0;

int OnInit()
{{
   handleFast = iMA(_Symbol, PERIOD_M5, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   handleSlow = iMA(_Symbol, PERIOD_M5, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   handleATR  = iATR(_Symbol, PERIOD_M5, ATR_Period);
   if(handleFast==INVALID_HANDLE || handleSlow==INVALID_HANDLE || handleATR==INVALID_HANDLE)
      return INIT_FAILED;
   ArraySetAsSeries(emaFast, true);
   ArraySetAsSeries(emaSlow, true);
   ArraySetAsSeries(atrBuf, true);
   return INIT_SUCCEEDED;
}}

void OnDeinit(const int reason) {{ IndicatorRelease(handleFast); IndicatorRelease(handleSlow); IndicatorRelease(handleATR); }}

void OnTick()
{{
   datetime currentBar = iTime(_Symbol, PERIOD_M5, 0);
   if(currentBar == lastBar) return;
   lastBar = currentBar;
   barsSinceSignal++;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.hour < SessionStart || dt.hour >= SessionEnd) return;
   if(CountPositions() >= MaxPositions) return;
   if(barsSinceSignal < Cooldown) return;
   
   CopyBuffer(handleFast, 0, 0, 3, emaFast);
   CopyBuffer(handleSlow, 0, 0, 3, emaSlow);
   CopyBuffer(handleATR, 0, 0, 2, atrBuf);
   
   double atr = atrBuf[0];
   if(atr <= 0) return;
   
   bool bullishTrend = emaFast[0] > emaSlow[0];
   bool bearishTrend = emaFast[0] < emaSlow[0];
   
   double close0 = iClose(_Symbol, PERIOD_M5, 0);
   double high2  = iHigh(_Symbol, PERIOD_M5, 2);
   double low0   = iLow(_Symbol, PERIOD_M5, 0);
   double low2   = iLow(_Symbol, PERIOD_M5, 2);
   double high0  = iHigh(_Symbol, PERIOD_M5, 0);
   
   // Bullish FVG: bar[2].high < bar[0].low
   if(bullishTrend)
   {{
      double gap = low0 - high2;
      if(gap > FVG_MinSize)
      {{
         double fvgBot = high2;
         double fvgTop = low0;
         if(close0 >= fvgBot && close0 <= fvgTop)
         {{
            double slDist = close0 - fvgBot + atr * 0.5;
            double tpDist = slDist * RR_Ratio;
            double lots = CalcLotSize(slDist);
            OpenTrade(ORDER_TYPE_BUY, lots, slDist, tpDist, "FVG+OB BUY");
            barsSinceSignal = 0;
         }}
      }}
   }}
   
   // Bearish FVG
   if(bearishTrend)
   {{
      double gap = low2 - high0;
      if(gap > FVG_MinSize)
      {{
         double fvgTop = low2;
         double fvgBot = high0;
         if(close0 >= fvgBot && close0 <= fvgTop)
         {{
            double slDist = fvgTop - close0 + atr * 0.5;
            double tpDist = slDist * RR_Ratio;
            double lots = CalcLotSize(slDist);
            OpenTrade(ORDER_TYPE_SELL, lots, slDist, tpDist, "FVG+OB SELL");
            barsSinceSignal = 0;
         }}
      }}
   }}
}}
'''

    TEMPLATE_UTILITY = '''
//+------------------------------------------------------------------+
//| Utility functions                                                  |
//+------------------------------------------------------------------+
int CountPositions()
{{
   int count = 0;
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {{
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         count++;
   }}
   return count;
}}

double CalcLotSize(double slDistPoints)
{{
   double riskAmount = AccountInfoDouble(ACCOUNT_EQUITY) * RiskPercent / 100.0;
   double tickValue  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickValue <= 0 || tickSize <= 0 || slDistPoints <= 0) return 0.01;
   
   double lots = riskAmount / (slDistPoints / tickSize * tickValue);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lots = MathMax(minLot, MathMin(maxLot, lots));
   lots = MathFloor(lots / stepLot) * stepLot;
   return lots;
}}

bool OpenTrade(ENUM_ORDER_TYPE type, double lots, double slDist, double tpDist, string comment)
{{
   MqlTradeRequest request = {{}};
   MqlTradeResult  result  = {{}};
   
   request.action    = TRADE_ACTION_DEAL;
   request.symbol    = _Symbol;
   request.volume    = lots;
   request.type      = type;
   request.magic     = MagicNumber;
   request.comment   = comment;
   request.deviation = 10;
   
   double price = (type == ORDER_TYPE_BUY) ?
      SymbolInfoDouble(_Symbol, SYMBOL_ASK) :
      SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   request.price = price;
   
   if(type == ORDER_TYPE_BUY)
   {{
      request.sl = price - slDist;
      request.tp = price + tpDist;
   }}
   else
   {{
      request.sl = price + slDist;
      request.tp = price - tpDist;
   }}
   
   if(!OrderSend(request, result))
   {{
      Print("OrderSend error: ", GetLastError());
      return false;
   }}
   return true;
}}
//+------------------------------------------------------------------+
'''

    @classmethod
    def generate(cls, signal_type: str, params: dict,
                 name: str = "SmartWave_EA") -> str:
        """Generate complete MQL5 EA code from strategy definition."""
        p = {
            "name": name,
            "risk_pct": params.get("risk_pct", 1.0),
            "rr": params.get("rr", 2.5),
            "atr_period": params.get("atr_period", 14),
            "session_start": params.get("session_start", 7),
            "session_end": params.get("session_end", 20),
            "magic": hash(name) % 100000 + 10000,
            "ema_fast": params.get("ema_fast", 21),
            "ema_slow": params.get("ema_slow", 50),
            "fvg_min": params.get("fvg_min", 0.5),
            "cooldown": params.get("cooldown", 5),
        }

        code = cls.TEMPLATE_HEADER.format(**p)

        if signal_type == "ema_cross":
            code += cls.TEMPLATE_EMA_CROSS.format(**p)
        elif signal_type == "fvg_ob":
            code += cls.TEMPLATE_FVG_OB.format(**p)
        else:
            # Default to EMA cross for unsupported types
            code += cls.TEMPLATE_EMA_CROSS.format(**p)

        code += cls.TEMPLATE_UTILITY.format(**p)
        return code

    @classmethod
    def save(cls, signal_type: str, params: dict,
             name: str = "SmartWave_EA", output_dir: str = "./output") -> str:
        """Generate and save MQL5 EA to file."""
        code = cls.generate(signal_type, params, name)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        filepath = os.path.join(output_dir, f"{name}.mq5")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        logger.info(f"MQL5 EA saved: {filepath} ({len(code)} chars)")
        return filepath


# ══════════════════════════════════════════════════════════════
# UNIFIED FAST ANALYSIS
# ══════════════════════════════════════════════════════════════

class FastAnalyzer:
    """
    Run the complete analysis pipeline on data from ANY source.
    
    Combines:
    - Numba-accelerated backtest
    - Pre-computed indicators
    - Monte Carlo validation
    - Deflated Sharpe
    - Prop firm compliance
    - Walk-Forward
    
    Usage:
        analyzer = FastAnalyzer(data_arrays, capital=100000)
        result = analyzer.run_strategy("ema_cross", params)
        report = analyzer.full_report(result)
    """

    def __init__(self, data: dict[str, np.ndarray], capital: float = 100000,
                 commission: float = 7.0, max_dd: float = 10.0):
        self.data = data
        self.capital = capital
        self.commission = commission
        self.max_dd = max_dd
        self.n_bars = len(data["C"])

        # Pre-compute indicators ONCE
        t0 = time.perf_counter()
        self.indicators = precompute_indicators(
            data["O"], data["H"], data["L"], data["C"], data["V"])
        self._ind_time = time.perf_counter() - t0
        logger.info(f"FastAnalyzer ready: {self.n_bars:,} bars, "
                     f"indicators in {self._ind_time:.3f}s")

    def _generate_signals(self, signal_type: str, params: dict) -> tuple:
        """Generate signal arrays from strategy parameters."""
        d = self.data
        ind = self.indicators
        p = params
        C, H, L, O = d["C"], d["H"], d["L"], d["O"]
        hours = d["hour"]
        atr = ind.get(f"atr{p.get('atr_period', 14)}", ind["atr14"])
        ss = p.get("session_start", 7)
        se = p.get("session_end", 20)

        if signal_type == "ema_cross":
            ef = ind.get(f"ema{p.get('ema_fast', 8)}", ind["ema8"])
            es = ind.get(f"ema{p.get('ema_slow', 34)}", ind["ema34"])
            return signal_ema_cross(C, ef, es, atr, p.get("rr", 2.0),
                                    hours, ss, se, p.get("risk_pct", 1.0), self.capital)
        elif signal_type == "fvg_ob":
            ef = ind.get(f"ema{p.get('ema_fast', 21)}", ind["ema21"])
            es = ind.get(f"ema{p.get('ema_slow', 50)}", ind["ema50"])
            return signal_fvg_ob(C, H, L, O, ef, es, atr, hours,
                                 p.get("rr", 2.5), p.get("fvg_min", 0.5),
                                 ss, se, p.get("risk_pct", 1.0), self.capital,
                                 p.get("cooldown", 5))
        elif signal_type == "breakout":
            et = ind.get(f"ema{p.get('ema_trend', 50)}", ind["ema50"])
            return signal_breakout(C, H, L, atr, et, hours,
                                   p.get("period", 20), p.get("atr_mult", 1.5),
                                   p.get("rr", 2.0), ss, se,
                                   p.get("risk_pct", 1.0), self.capital,
                                   p.get("cooldown", 10))
        elif signal_type == "mean_rev":
            return signal_mean_reversion(
                C, ind["bb_upper"], ind["bb_lower"], ind["bb_mid"],
                ind["rsi14"], atr, hours,
                p.get("rsi_ob", 70), p.get("rsi_os", 30),
                ss, se, p.get("risk_pct", 1.0), self.capital,
                p.get("cooldown", 10))
        elif signal_type == "asian":
            et = ind.get(f"ema{p.get('ema_trend', 50)}", ind["ema50"])
            return signal_asian_breakout(
                C, H, L, et, atr, hours,
                p.get("rr", 2.0), p.get("risk_pct", 1.0), self.capital,
                p.get("cooldown", 5))
        else:
            n = len(C)
            return np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)

    def run_strategy(self, signal_type: str, params: dict) -> dict:
        """
        Run a single strategy and return complete results.
        Returns dict with metrics, equity_curve, trade_pnls, etc.
        """
        sigs, sl, tp, lots = self._generate_signals(signal_type, params)

        t0 = time.perf_counter()
        (balance, eq, pnls, n_trades, max_dd_pct,
         total_comm, wins, losses) = fast_backtest(
            self.data["O"], self.data["H"], self.data["L"],
            self.data["C"], self.data["spread"],
            sigs, sl, tp, lots,
            capital=self.capital, commission_per_lot=self.commission,
            max_dd_pct=self.max_dd, max_positions=3)
        bt_time = time.perf_counter() - t0

        metrics = compute_metrics(pnls, eq, self.capital, wins, losses,
                                  max_dd_pct, total_comm)

        return {
            "metrics": metrics,
            "equity_curve": eq,
            "trade_pnls": pnls,
            "n_trades": n_trades,
            "backtest_time": bt_time,
            "signal_type": signal_type,
            "params": params,
        }

    def full_report(self, result: dict, n_strategies_tested: int = 1,
                    mc_sims: int = 500) -> dict:
        """
        Run FULL analysis on a strategy result:
        Monte Carlo, Deflated Sharpe, Prop Firm, Walk-Forward.
        """
        m = result["metrics"]
        pnls = result["trade_pnls"]
        eq = result["equity_curve"]

        report = {"metrics": m, "backtest_time": result["backtest_time"]}

        # Monte Carlo
        if len(pnls) >= 5:
            _, _, prob_p, median, p5, p95, p95dd = monte_carlo_permutation(
                pnls, self.capital, mc_sims, seed=42)
            m.mc_prob_profit = round(prob_p, 3)
            m.mc_p95_dd = round(p95dd, 1)
            m.mc_median_equity = round(median, 0)
            report["monte_carlo"] = {
                "prob_profit": prob_p, "p95_dd": p95dd,
                "median": median, "p5": p5, "p95": p95,
            }

        # Deflated Sharpe
        m.deflated_sharpe = deflated_sharpe(
            m.sharpe, n_strategies_tested, self.n_bars // 288)

        # Composite score
        m.composite_score = composite_score(m, n_strategies_tested)

        # Prop firm compliance
        prop_results = check_prop_compliance(m, eq, self.capital)
        report["prop_compliance"] = [
            {"firm": r.firm_name, "passed": r.passed,
             "daily_dd": r.actual_daily_dd, "total_dd": r.actual_total_dd,
             "return": r.actual_return}
            for r in prop_results
        ]

        # Walk-Forward
        def run_slice(start, end):
            sliced = {k: v[start:end] for k, v in self.data.items()}
            sliced_ind = {k: v[start:end] for k, v in self.indicators.items()}
            s, sl, tp, lots = self._generate_signals(
                result["signal_type"], result["params"])
            s, sl, tp, lots = s[start:end], sl[start:end], tp[start:end], lots[start:end]
            (_, eq2, pnls2, nt, dd, comm, w, l) = fast_backtest(
                sliced["O"], sliced["H"], sliced["L"], sliced["C"], sliced["spread"],
                s, sl, tp, lots, self.capital, self.commission, self.max_dd, 3)
            return compute_metrics(pnls2, eq2, self.capital, w, l, dd, comm)

        wf = walk_forward(run_slice, self.n_bars, n_windows=6, is_ratio=0.7)
        report["walk_forward"] = {
            "robust_windows": wf.n_robust,
            "total_windows": len(wf.windows),
            "robustness_pct": wf.robustness_pct,
            "avg_oos_sharpe": wf.avg_oos_sharpe,
        }

        # Regime analysis
        regime = detect_regime(self.data["C"], self.indicators["atr14"],
                               self.indicators["ema50"])
        n_trend = int(np.sum(np.abs(regime) == 1))
        n_range = int(np.sum(regime == 0))
        report["regime"] = {
            "trending_bars": n_trend,
            "ranging_bars": n_range,
            "trend_pct": round(n_trend / max(1, len(regime)) * 100, 1),
        }

        return report
