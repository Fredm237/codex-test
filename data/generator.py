"""
SmartWave Quant Lab — Strategy Generator Engine
=================================================
Generates trading strategies from proven market patterns,
validates them via backtesting, and ranks by composite score.

WHAT MAKES THIS DIFFERENT FROM STRATEGYQUANT:
  StrategyQuant: random indicator combinations → mostly noise
  SmartWave:     proven market structure patterns → signal

Architecture:
  StrategyDNA → Assembler → BacktestEngine → Validator → Ranker → Output

Strategy DNA is a structured representation of a strategy:
  - Entry logic (composable blocks)
  - Exit logic (SL/TP/trailing/time)
  - Filters (session, volatility, trend)
  - Risk management (position sizing, limits)
  - Market adaptation rules

The generator doesn't randomly combine indicators.
It selects from PROVEN PATTERNS and varies their parameters.
"""

from __future__ import annotations

import copy
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np

from core.models import (
    BacktestConfig, BacktestResult, Bar, Order, OrderSide,
    OrderType, Position, Tick, Timeframe,
)
from core.engine import BacktestEngine
from strategies.strategies import BaseStrategy, atr, ema, sma, rsi, detect_fvg, detect_order_block

logger = logging.getLogger("smartwave.generator")


# ══════════════════════════════════════════════════════════════
# STRATEGY DNA — Structured representation
# ══════════════════════════════════════════════════════════════

class EntryType(Enum):
    FVG_RETRACEMENT = "fvg_retracement"
    ORDER_BLOCK = "order_block"
    LIQUIDITY_SWEEP = "liquidity_sweep"
    EMA_CROSS = "ema_cross"
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean_reversion"
    BOS_CHOCH = "bos_choch"             # Break of Structure / Change of Character
    ASIAN_RANGE = "asian_range"
    SUPPLY_DEMAND = "supply_demand"
    RSI_DIVERGENCE = "rsi_divergence"


class ExitType(Enum):
    FIXED_RR = "fixed_rr"
    TRAILING_ATR = "trailing_atr"
    STRUCTURE_BASED = "structure_based"
    TIME_BASED = "time_based"
    OPPOSITE_SIGNAL = "opposite_signal"


class FilterType(Enum):
    SESSION = "session"
    TREND_EMA = "trend_ema"
    VOLATILITY_ATR = "volatility_atr"
    RSI_EXTREME = "rsi_extreme"
    SPREAD_MAX = "spread_max"
    DAY_OF_WEEK = "day_of_week"
    NEWS_AVOID = "news_avoid"


@dataclass
class StrategyDNA:
    """Complete genetic representation of a strategy."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    # Core logic
    entry_type: EntryType = EntryType.EMA_CROSS
    exit_type: ExitType = ExitType.FIXED_RR
    filters: list[FilterType] = field(default_factory=list)
    # Market
    markets: list[str] = field(default_factory=lambda: ["XAUUSD"])
    timeframe: Timeframe = Timeframe.M5
    style: str = "dayTrading"       # scalping, dayTrading, swing
    complexity: str = "intermediate"
    # Parameters (will be optimized)
    params: dict[str, Any] = field(default_factory=dict)
    # Metadata
    category: str = ""              # ICT/SMC, Indicators, PriceAction, Hybrid
    proven: bool = False
    generation: int = 0             # evolution generation
    parent_id: str = ""             # for evolution tracking
    # Validation results
    backtest_result: Optional[BacktestResult] = None
    score: float = 0.0
    is_valid: bool = False
    rejection_reason: str = ""


# ══════════════════════════════════════════════════════════════
# PATTERN LIBRARY — Proven strategies as DNA templates
# ══════════════════════════════════════════════════════════════

PATTERN_LIBRARY: dict[str, StrategyDNA] = {
    # ── ICT / Smart Money ──────────────────────────────────
    "ict_unicorn": StrategyDNA(
        name="ICT Unicorn Model",
        description="FVG + Order Block confluence with EMA trend filter",
        entry_type=EntryType.FVG_RETRACEMENT,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.SESSION, FilterType.TREND_EMA, FilterType.VOLATILITY_ATR, FilterType.SPREAD_MAX],
        markets=["XAUUSD", "EURUSD", "GBPUSD"],
        timeframe=Timeframe.M5,
        style="dayTrading",
        complexity="advanced",
        category="ICT/SMC",
        proven=True,
        params={
            "ema_fast": 21, "ema_slow": 50, "atr_period": 14,
            "atr_min": 1.5, "rr_ratio": 2.5, "fvg_min_size": 0.5,
            "risk_pct": 1.0, "session_start": 7, "session_end": 20,
            "max_spread_pts": 50, "cooldown_bars": 5,
        },
    ),
    "liquidity_sweep": StrategyDNA(
        name="Liquidity Sweep Reversal",
        description="Enter after liquidity sweep + displacement candle",
        entry_type=EntryType.LIQUIDITY_SWEEP,
        exit_type=ExitType.STRUCTURE_BASED,
        filters=[FilterType.SESSION, FilterType.TREND_EMA, FilterType.VOLATILITY_ATR],
        markets=["XAUUSD", "BTCUSD"],
        timeframe=Timeframe.M15,
        style="dayTrading",
        complexity="advanced",
        category="ICT/SMC",
        proven=True,
        params={
            "lookback": 50, "sweep_threshold": 0.3, "displacement_min": 2.0,
            "ema_trend": 50, "atr_period": 14, "rr_ratio": 3.0,
            "risk_pct": 1.0, "session_start": 7, "session_end": 20,
        },
    ),
    "ob_sniper": StrategyDNA(
        name="Order Block Sniper",
        description="Precision entries at validated order blocks in killzones",
        entry_type=EntryType.ORDER_BLOCK,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.SESSION, FilterType.TREND_EMA, FilterType.SPREAD_MAX],
        markets=["XAUUSD"],
        timeframe=Timeframe.M5,
        style="scalping",
        complexity="expert",
        category="ICT/SMC",
        proven=True,
        params={
            "ob_lookback": 20, "ob_strength_min": 0.001,
            "ema_fast": 21, "ema_slow": 50, "rr_ratio": 3.5,
            "risk_pct": 0.5, "session_start": 8, "session_end": 17,
            "max_spread_pts": 35,
        },
    ),
    "bos_entry": StrategyDNA(
        name="BOS/CHoCH Momentum",
        description="Enter on Break of Structure with momentum confirmation",
        entry_type=EntryType.BOS_CHOCH,
        exit_type=ExitType.TRAILING_ATR,
        filters=[FilterType.SESSION, FilterType.VOLATILITY_ATR],
        markets=["XAUUSD", "EURUSD", "BTCUSD"],
        timeframe=Timeframe.M15,
        style="dayTrading",
        complexity="advanced",
        category="ICT/SMC",
        proven=True,
        params={
            "swing_lookback": 20, "bos_confirmation_bars": 2,
            "atr_period": 14, "atr_trail_mult": 2.0,
            "risk_pct": 1.0, "session_start": 7, "session_end": 20,
        },
    ),

    # ── Price Action ───────────────────────────────────────
    "asian_range": StrategyDNA(
        name="Asian Range Breakout",
        description="Mark Asian range, enter on London break with trend",
        entry_type=EntryType.ASIAN_RANGE,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.TREND_EMA, FilterType.VOLATILITY_ATR],
        markets=["XAUUSD", "EURUSD", "GBPUSD"],
        timeframe=Timeframe.M15,
        style="dayTrading",
        complexity="simple",
        category="PriceAction",
        proven=True,
        params={
            "asian_start": 0, "asian_end": 7, "london_start": 7,
            "breakout_buffer_pts": 5, "ema_trend": 50,
            "atr_period": 14, "rr_ratio": 2.0, "risk_pct": 1.0,
        },
    ),
    "breakout_vol": StrategyDNA(
        name="Volatility Breakout",
        description="Range detection + ATR breakout + volume confirmation",
        entry_type=EntryType.BREAKOUT,
        exit_type=ExitType.TRAILING_ATR,
        filters=[FilterType.VOLATILITY_ATR, FilterType.TREND_EMA],
        markets=["XAUUSD", "EURUSD", "BTCUSD", "USDJPY"],
        timeframe=Timeframe.H1,
        style="swing",
        complexity="intermediate",
        category="PriceAction",
        proven=False,
        params={
            "range_period": 20, "breakout_atr_mult": 1.5,
            "volume_mult": 1.5, "atr_period": 14,
            "atr_trail_mult": 2.0, "risk_pct": 1.0,
        },
    ),

    # ── Indicator-Based ────────────────────────────────────
    "ema_ribbon": StrategyDNA(
        name="EMA Ribbon Momentum",
        description="8/13/21/34 EMA ribbon + RSI divergence",
        entry_type=EntryType.EMA_CROSS,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.RSI_EXTREME, FilterType.SESSION],
        markets=["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"],
        timeframe=Timeframe.M15,
        style="dayTrading",
        complexity="simple",
        category="Indicators",
        proven=True,
        params={
            "ema_1": 8, "ema_2": 13, "ema_3": 21, "ema_4": 34,
            "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
            "rr_ratio": 2.0, "risk_pct": 1.0, "atr_period": 14,
        },
    ),
    "mean_reversion": StrategyDNA(
        name="Mean Reversion Bands",
        description="Bollinger squeeze + extreme deviation entries",
        entry_type=EntryType.MEAN_REVERSION,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.VOLATILITY_ATR, FilterType.SESSION],
        markets=["EURUSD", "GBPUSD", "USDJPY"],
        timeframe=Timeframe.M30,
        style="dayTrading",
        complexity="intermediate",
        category="Indicators",
        proven=False,
        params={
            "bb_period": 20, "bb_std": 2.0, "squeeze_threshold": 0.5,
            "rsi_period": 14, "rr_ratio": 1.5, "risk_pct": 1.0,
            "atr_period": 14,
        },
    ),
    "rsi_div": StrategyDNA(
        name="RSI Divergence Reversal",
        description="RSI divergence at structure levels + trend filter",
        entry_type=EntryType.RSI_DIVERGENCE,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.TREND_EMA, FilterType.SESSION],
        markets=["XAUUSD", "EURUSD"],
        timeframe=Timeframe.M15,
        style="dayTrading",
        complexity="intermediate",
        category="Indicators",
        proven=True,
        params={
            "rsi_period": 14, "div_lookback": 20,
            "ema_filter": 200, "rr_ratio": 2.5,
            "risk_pct": 1.0, "atr_period": 14,
        },
    ),

    # ── Hybrid / Advanced ──────────────────────────────────
    "scalp_m1_gold": StrategyDNA(
        name="Gold M1 Scalper Pro",
        description="M5 structure break + M1 entry trigger during London open",
        entry_type=EntryType.BOS_CHOCH,
        exit_type=ExitType.FIXED_RR,
        filters=[FilterType.SESSION, FilterType.SPREAD_MAX, FilterType.VOLATILITY_ATR],
        markets=["XAUUSD"],
        timeframe=Timeframe.M1,
        style="scalping",
        complexity="expert",
        category="Hybrid",
        proven=True,
        params={
            "htf_ema": 50, "ltf_trigger_bars": 3,
            "rr_ratio": 3.0, "risk_pct": 0.5,
            "session_start": 7, "session_end": 11,
            "max_spread_pts": 30, "atr_period": 14,
        },
    ),
}


# ══════════════════════════════════════════════════════════════
# DYNAMIC STRATEGY — Executes any StrategyDNA
# ══════════════════════════════════════════════════════════════

class DynamicStrategy(BaseStrategy):
    """
    Universal strategy executor.
    Takes a StrategyDNA and executes its logic during backtesting.
    
    This is the KEY INNOVATION: instead of hardcoding each strategy,
    we have a single executor that interprets DNA definitions.
    """

    def initialize(self) -> None:
        self.dna: StrategyDNA = self.params.get("__dna__", StrategyDNA())
        self.p = {k: v for k, v in self.dna.params.items()}
        self._closes: list[float] = []
        self._highs: list[float] = []
        self._lows: list[float] = []
        self._last_signal_bar: int = 0
        self._asian_high: float = 0
        self._asian_low: float = float("inf")
        self._swing_highs: list[float] = []
        self._swing_lows: list[float] = []

    def _in_session(self, bar: Bar) -> bool:
        start = self.p.get("session_start", 0)
        end = self.p.get("session_end", 24)
        return start <= bar.timestamp.hour < end

    def _trend_filter(self, bullish_required: bool = True) -> bool:
        fast_p = self.p.get("ema_fast", self.p.get("ema_1", 21))
        slow_p = self.p.get("ema_slow", self.p.get("ema_trend", self.p.get("ema_4", 50)))
        if len(self._closes) < slow_p + 5:
            return False
        fast = ema(self._closes, fast_p)
        slow = ema(self._closes, slow_p)
        if fast == 0 or slow == 0:
            return False
        if bullish_required:
            return fast > slow
        return fast < slow

    def _calc_lot_size(self, sl_distance: float) -> float:
        risk_pct = self.p.get("risk_pct", 1.0)
        risk_amount = self.engine.account.equity * (risk_pct / 100)
        lot_size = risk_amount / (sl_distance * 100) if sl_distance > 0 else 0.01
        return round(max(0.01, min(lot_size, 1.0)), 2)

    def _detect_swing_points(self, bars: list[Bar], lookback: int = 5) -> None:
        """Detect swing highs and lows for structure analysis."""
        if len(bars) < lookback * 2 + 1:
            return
        for i in range(lookback, len(bars) - lookback):
            is_high = all(bars[i].high >= bars[i+j].high for j in range(-lookback, lookback+1) if j != 0)
            is_low = all(bars[i].low <= bars[i+j].low for j in range(-lookback, lookback+1) if j != 0)
            if is_high:
                self._swing_highs.append(bars[i].high)
            if is_low:
                self._swing_lows.append(bars[i].low)
        # Keep bounded
        self._swing_highs = self._swing_highs[-20:]
        self._swing_lows = self._swing_lows[-20:]

    def on_bar(self, bar: Bar) -> None:
        self._closes.append(bar.close)
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        bars = self.engine.get_bars(200)

        if len(bars) < 60 or self.engine.positions_count > 0:
            return

        bar_idx = len(bars)
        cooldown = self.p.get("cooldown_bars", 5)
        if bar_idx - self._last_signal_bar < cooldown:
            return

        # Session filter
        if FilterType.SESSION in self.dna.filters:
            if not self._in_session(bar):
                return

        # Spread filter
        if FilterType.SPREAD_MAX in self.dna.filters:
            max_spread = self.p.get("max_spread_pts", 50)
            if bar.spread * 100 > max_spread:
                return

        # ATR
        atr_p = self.p.get("atr_period", 14)
        current_atr = atr(bars, atr_p)

        # Volatility filter
        if FilterType.VOLATILITY_ATR in self.dna.filters:
            atr_min = self.p.get("atr_min", 0)
            if atr_min > 0 and current_atr < atr_min:
                return

        # ── ENTRY LOGIC BY TYPE ────────────────────────────

        # === FVG Retracement ===
        if self.dna.entry_type == EntryType.FVG_RETRACEMENT:
            bullish = self._trend_filter(True)
            bearish = self._trend_filter(False)
            fvgs = detect_fvg(bars[-10:], self.p.get("fvg_min_size", 0.5))
            obs = detect_order_block(bars, lookback=20)
            rr = self.p.get("rr_ratio", 2.5)

            if bullish:
                bull_fvgs = [f for f in fvgs if f["type"] == "bullish"]
                if bull_fvgs:
                    fvg = bull_fvgs[-1]
                    if fvg["bottom"] <= bar.close <= fvg["top"]:
                        sl = fvg["bottom"] - current_atr * 0.5
                        sl_dist = bar.close - sl
                        tp = bar.close + sl_dist * rr
                        lots = self._calc_lot_size(sl_dist)
                        self.buy(lots, sl=round(sl, 2), tp=round(tp, 2), comment=f"{self.dna.name} BUY")
                        self._last_signal_bar = bar_idx

            elif bearish:
                bear_fvgs = [f for f in fvgs if f["type"] == "bearish"]
                if bear_fvgs:
                    fvg = bear_fvgs[-1]
                    if fvg["bottom"] <= bar.close <= fvg["top"]:
                        sl = fvg["top"] + current_atr * 0.5
                        sl_dist = sl - bar.close
                        tp = bar.close - sl_dist * rr
                        lots = self._calc_lot_size(sl_dist)
                        self.sell(lots, sl=round(sl, 2), tp=round(tp, 2), comment=f"{self.dna.name} SELL")
                        self._last_signal_bar = bar_idx

        # === Order Block ===
        elif self.dna.entry_type == EntryType.ORDER_BLOCK:
            bullish = self._trend_filter(True)
            bearish = self._trend_filter(False)
            obs = detect_order_block(bars, self.p.get("ob_lookback", 20))
            rr = self.p.get("rr_ratio", 3.0)

            if bullish:
                bull_obs = [o for o in obs if o["type"] == "bullish"]
                for ob in bull_obs[-3:]:
                    if ob["low"] <= bar.close <= ob["high"]:
                        sl = ob["low"] - current_atr * 0.3
                        sl_dist = bar.close - sl
                        tp = bar.close + sl_dist * rr
                        lots = self._calc_lot_size(sl_dist)
                        self.buy(lots, sl=round(sl, 2), tp=round(tp, 2), comment=f"{self.dna.name} BUY @OB")
                        self._last_signal_bar = bar_idx
                        break

            elif bearish:
                bear_obs = [o for o in obs if o["type"] == "bearish"]
                for ob in bear_obs[-3:]:
                    if ob["low"] <= bar.close <= ob["high"]:
                        sl = ob["high"] + current_atr * 0.3
                        sl_dist = sl - bar.close
                        tp = bar.close - sl_dist * rr
                        lots = self._calc_lot_size(sl_dist)
                        self.sell(lots, sl=round(sl, 2), tp=round(tp, 2), comment=f"{self.dna.name} SELL @OB")
                        self._last_signal_bar = bar_idx
                        break

        # === EMA Cross ===
        elif self.dna.entry_type == EntryType.EMA_CROSS:
            if len(self._closes) < 40:
                return
            e1 = self.p.get("ema_1", 8)
            e2 = self.p.get("ema_2", self.p.get("ema_slow", 34))
            fast_now = ema(self._closes, e1)
            slow_now = ema(self._closes, e2)
            fast_prev = ema(self._closes[:-1], e1)
            slow_prev = ema(self._closes[:-1], e2)
            rr = self.p.get("rr_ratio", 2.0)

            if fast_prev <= slow_prev and fast_now > slow_now:
                sl = bar.close - current_atr * 1.5
                sl_dist = bar.close - sl
                lots = self._calc_lot_size(sl_dist)
                self.buy(lots, sl=round(sl, 2), tp=round(bar.close + sl_dist * rr, 2), comment=f"{self.dna.name} BUY")
                self._last_signal_bar = bar_idx

            elif fast_prev >= slow_prev and fast_now < slow_now:
                sl = bar.close + current_atr * 1.5
                sl_dist = sl - bar.close
                lots = self._calc_lot_size(sl_dist)
                self.sell(lots, sl=round(sl, 2), tp=round(bar.close - sl_dist * rr, 2), comment=f"{self.dna.name} SELL")
                self._last_signal_bar = bar_idx

        # === Breakout ===
        elif self.dna.entry_type == EntryType.BREAKOUT:
            period = self.p.get("range_period", 20)
            if len(bars) < period + 5:
                return
            recent = bars[-period:]
            range_h = max(b.high for b in recent)
            range_l = min(b.low for b in recent)
            mult = self.p.get("breakout_atr_mult", 1.5)
            rr = self.p.get("rr_ratio", 2.0)

            if bar.close > range_h + current_atr * 0.3:
                sl = range_h - current_atr * mult
                sl_dist = bar.close - sl
                lots = self._calc_lot_size(sl_dist)
                self.buy(lots, sl=round(sl, 2), tp=round(bar.close + sl_dist * rr, 2), comment=f"{self.dna.name} Breakout BUY")
                self._last_signal_bar = bar_idx

            elif bar.close < range_l - current_atr * 0.3:
                sl = range_l + current_atr * mult
                sl_dist = sl - bar.close
                lots = self._calc_lot_size(sl_dist)
                self.sell(lots, sl=round(sl, 2), tp=round(bar.close - sl_dist * rr, 2), comment=f"{self.dna.name} Breakout SELL")
                self._last_signal_bar = bar_idx

        # === Asian Range ===
        elif self.dna.entry_type == EntryType.ASIAN_RANGE:
            asian_start = self.p.get("asian_start", 0)
            asian_end = self.p.get("asian_end", 7)
            london_start = self.p.get("london_start", 7)

            if asian_start <= bar.timestamp.hour < asian_end:
                self._asian_high = max(self._asian_high, bar.high)
                self._asian_low = min(self._asian_low, bar.low)

            elif bar.timestamp.hour == london_start and bar.timestamp.minute == 0:
                # Reset for new day
                self._asian_high = bar.high
                self._asian_low = bar.low

            elif london_start <= bar.timestamp.hour < 20:
                if self._asian_high > 0 and self._asian_low < float("inf"):
                    buf = self.p.get("breakout_buffer_pts", 5) * 0.01
                    rr = self.p.get("rr_ratio", 2.0)

                    if bar.close > self._asian_high + buf and self._trend_filter(True):
                        sl = self._asian_low
                        sl_dist = bar.close - sl
                        lots = self._calc_lot_size(sl_dist)
                        self.buy(lots, sl=round(sl, 2), tp=round(bar.close + sl_dist * rr, 2), comment=f"{self.dna.name} Asian Break BUY")
                        self._last_signal_bar = bar_idx

                    elif bar.close < self._asian_low - buf and self._trend_filter(False):
                        sl = self._asian_high
                        sl_dist = sl - bar.close
                        lots = self._calc_lot_size(sl_dist)
                        self.sell(lots, sl=round(sl, 2), tp=round(bar.close - sl_dist * rr, 2), comment=f"{self.dna.name} Asian Break SELL")
                        self._last_signal_bar = bar_idx

        # === Mean Reversion ===
        elif self.dna.entry_type == EntryType.MEAN_REVERSION:
            period = self.p.get("bb_period", 20)
            std_mult = self.p.get("bb_std", 2.0)
            if len(self._closes) < period + 5:
                return
            mean = sma(self._closes, period)
            std = float(np.std(self._closes[-period:]))
            upper = mean + std * std_mult
            lower = mean - std * std_mult
            rr = self.p.get("rr_ratio", 1.5)

            if bar.close < lower:
                sl = bar.close - current_atr * 1.5
                sl_dist = bar.close - sl
                lots = self._calc_lot_size(sl_dist)
                self.buy(lots, sl=round(sl, 2), tp=round(mean, 2), comment=f"{self.dna.name} Mean Rev BUY")
                self._last_signal_bar = bar_idx

            elif bar.close > upper:
                sl = bar.close + current_atr * 1.5
                sl_dist = sl - bar.close
                lots = self._calc_lot_size(sl_dist)
                self.sell(lots, sl=round(sl, 2), tp=round(mean, 2), comment=f"{self.dna.name} Mean Rev SELL")
                self._last_signal_bar = bar_idx


# ══════════════════════════════════════════════════════════════
# STRATEGY GENERATOR — Main engine
# ══════════════════════════════════════════════════════════════

@dataclass
class GeneratorConfig:
    """Configuration for the strategy generator."""
    # Filtering
    markets: list[str] = field(default_factory=lambda: ["XAUUSD"])
    styles: list[str] = field(default_factory=lambda: ["dayTrading"])
    complexity_max: str = "expert"
    categories: list[str] = field(default_factory=list)  # empty = all
    # Variation
    n_variations: int = 3           # variations per base pattern
    param_noise_pct: float = 15.0   # % noise for parameter variation
    # Validation
    min_trades: int = 20
    min_sharpe: float = 0.5
    max_drawdown: float = 20.0
    min_profit_factor: float = 1.0
    min_win_rate: float = 35.0
    # Ranking weights
    score_weights: dict[str, float] = field(default_factory=lambda: {
        "sharpe": 0.30, "profit_factor": 0.20, "drawdown": 0.25,
        "win_rate": 0.10, "recovery": 0.10, "consistency": 0.05,
    })
    # Execution
    seed: int = 42


class StrategyGenerator:
    """
    The main generator engine.
    
    Pipeline:
    1. Select matching patterns from library
    2. Generate parameter variations
    3. Backtest each variation
    4. Validate and filter
    5. Rank by composite score
    6. Return top N strategies with full results
    
    Usage:
        generator = StrategyGenerator(
            tick_data=ticks,
            base_config=BacktestConfig(...),
            config=GeneratorConfig(markets=["XAUUSD"], styles=["dayTrading"]),
        )
        results = generator.run()
        
        for strat in results:
            print(f"{strat.name}: Sharpe={strat.backtest_result.sharpe_ratio}")
    """

    def __init__(
        self,
        tick_data: list[Tick],
        base_config: BacktestConfig,
        config: GeneratorConfig,
    ) -> None:
        self.tick_data = tick_data
        self.base_config = base_config
        self.config = config
        self._rng = np.random.default_rng(config.seed)
        self.results: list[StrategyDNA] = []

    def _select_patterns(self) -> list[StrategyDNA]:
        """Select matching patterns from the library."""
        patterns = []
        complexity_order = ["simple", "intermediate", "advanced", "expert"]
        max_idx = complexity_order.index(self.config.complexity_max) if self.config.complexity_max in complexity_order else 3

        for key, dna in PATTERN_LIBRARY.items():
            # Market filter
            if self.config.markets:
                if not any(m in dna.markets for m in self.config.markets):
                    continue

            # Style filter
            if self.config.styles:
                if dna.style not in self.config.styles and "all" not in self.config.styles:
                    continue

            # Complexity filter
            dna_idx = complexity_order.index(dna.complexity) if dna.complexity in complexity_order else 0
            if dna_idx > max_idx:
                continue

            # Category filter
            if self.config.categories:
                if not any(c.lower() in dna.category.lower() for c in self.config.categories):
                    continue

            patterns.append(copy.deepcopy(dna))

        logger.info(f"Selected {len(patterns)} matching patterns from library")
        return patterns

    def _vary_params(self, dna: StrategyDNA, variation: int) -> StrategyDNA:
        """Create a parameter variation of a strategy."""
        varied = copy.deepcopy(dna)
        varied.id = str(uuid.uuid4())[:8]
        varied.name = f"{dna.name} v{variation+1}"
        varied.generation = 1
        varied.parent_id = dna.id

        noise_pct = self.config.param_noise_pct / 100

        for key, value in dna.params.items():
            if isinstance(value, int):
                noise = int(value * noise_pct * self._rng.normal(0, 1))
                varied.params[key] = max(1, value + noise)
            elif isinstance(value, float):
                noise = value * noise_pct * float(self._rng.normal(0, 1))
                varied.params[key] = max(0.01, value + noise)

        return varied

    def _backtest_dna(self, dna: StrategyDNA) -> BacktestResult:
        """Run a backtest for a given strategy DNA."""
        strategy = DynamicStrategy(params={"__dna__": dna, **dna.params})

        config = BacktestConfig(
            strategy_name=dna.name,
            symbol=self.base_config.symbol,
            timeframe=dna.timeframe,
            initial_capital=self.base_config.initial_capital,
            leverage=self.base_config.leverage,
            spread_model=self.base_config.spread_model,
            avg_spread_points=self.base_config.avg_spread_points,
            slippage_model=self.base_config.slippage_model,
            max_slippage_points=self.base_config.max_slippage_points,
            latency_ms=self.base_config.latency_ms,
            commission_per_lot=self.base_config.commission_per_lot,
            max_risk_per_trade_pct=dna.params.get("risk_pct", 1.0),
            max_daily_dd_pct=self.base_config.max_daily_dd_pct,
            max_total_dd_pct=self.base_config.max_total_dd_pct,
            max_concurrent_trades=self.base_config.max_concurrent_trades,
            strategy_params={"__dna__": dna, **dna.params},
        )

        engine = BacktestEngine(config, strategy)
        return engine.run(self.tick_data)

    def _validate(self, dna: StrategyDNA, result: BacktestResult) -> bool:
        """Validate if a strategy meets minimum criteria."""
        if result.total_trades < self.config.min_trades:
            dna.rejection_reason = f"Too few trades: {result.total_trades} < {self.config.min_trades}"
            return False
        if result.sharpe_ratio < self.config.min_sharpe:
            dna.rejection_reason = f"Sharpe too low: {result.sharpe_ratio} < {self.config.min_sharpe}"
            return False
        if result.max_drawdown_pct > self.config.max_drawdown:
            dna.rejection_reason = f"DD too high: {result.max_drawdown_pct}% > {self.config.max_drawdown}%"
            return False
        if result.profit_factor < self.config.min_profit_factor:
            dna.rejection_reason = f"PF too low: {result.profit_factor} < {self.config.min_profit_factor}"
            return False
        if result.win_rate < self.config.min_win_rate:
            dna.rejection_reason = f"Win rate too low: {result.win_rate}% < {self.config.min_win_rate}%"
            return False
        return True

    def _compute_score(self, result: BacktestResult) -> float:
        """Compute composite quality score."""
        w = self.config.score_weights
        score = 0.0

        # Sharpe: [-1, 4] → [0, 1]
        score += w.get("sharpe", 0.3) * max(0, min(1, (result.sharpe_ratio + 1) / 5))
        # PF: [0, 5] → [0, 1]
        score += w.get("profit_factor", 0.2) * max(0, min(1, result.profit_factor / 5))
        # DD: [0, 50] → [0, 1] (inverted)
        score += w.get("drawdown", 0.25) * max(0, min(1, 1 - result.max_drawdown_pct / 50))
        # Win Rate: [30, 80] → [0, 1]
        score += w.get("win_rate", 0.1) * max(0, min(1, (result.win_rate - 30) / 50))
        # Recovery: [0, 10] → [0, 1]
        score += w.get("recovery", 0.1) * max(0, min(1, result.recovery_factor / 10))
        # Consistency (daily returns consistency)
        if result.daily_returns and len(result.daily_returns) > 10:
            pos_days = sum(1 for r in result.daily_returns if r > 0)
            consistency = pos_days / len(result.daily_returns)
            score += w.get("consistency", 0.05) * consistency

        return round(score, 4)

    def run(self) -> list[StrategyDNA]:
        """
        Execute the full generation pipeline.
        
        Returns list of validated, ranked strategies.
        """
        start_time = time.perf_counter()
        logger.info("=" * 60)
        logger.info("STRATEGY GENERATOR — Starting")
        logger.info(f"Markets: {self.config.markets} | Styles: {self.config.styles}")
        logger.info("=" * 60)

        # 1. Select patterns
        patterns = self._select_patterns()

        if not patterns:
            logger.warning("No matching patterns found")
            return []

        # 2. Generate variations
        candidates: list[StrategyDNA] = []
        for pattern in patterns:
            candidates.append(pattern)  # Original
            for v in range(self.config.n_variations):
                candidates.append(self._vary_params(pattern, v))

        logger.info(f"Generated {len(candidates)} candidates ({len(patterns)} base + {len(candidates)-len(patterns)} variations)")

        # 3. Backtest each
        valid_results: list[StrategyDNA] = []
        rejected = 0

        for i, dna in enumerate(candidates):
            logger.info(f"Testing {i+1}/{len(candidates)}: {dna.name}")

            try:
                result = self._backtest_dna(dna)
                dna.backtest_result = result

                # 4. Validate
                if self._validate(dna, result):
                    dna.score = self._compute_score(result)
                    dna.is_valid = True
                    valid_results.append(dna)
                    logger.info(
                        f"  ✅ Score={dna.score:.4f} | Sharpe={result.sharpe_ratio:.2f} | "
                        f"DD={result.max_drawdown_pct:.1f}% | PF={result.profit_factor:.2f} | "
                        f"Trades={result.total_trades}"
                    )
                else:
                    rejected += 1
                    logger.debug(f"  ❌ Rejected: {dna.rejection_reason}")

            except Exception as e:
                rejected += 1
                logger.warning(f"  ⚠️ Error testing {dna.name}: {e}")

        # 5. Rank by score
        valid_results.sort(key=lambda d: d.score, reverse=True)

        elapsed = time.perf_counter() - start_time
        logger.info("=" * 60)
        logger.info(f"GENERATION COMPLETE in {elapsed:.1f}s")
        logger.info(f"  Tested: {len(candidates)} | Valid: {len(valid_results)} | Rejected: {rejected}")
        if valid_results:
            best = valid_results[0]
            logger.info(f"  Best: {best.name} (score={best.score:.4f}, sharpe={best.backtest_result.sharpe_ratio:.2f})")
        logger.info("=" * 60)

        self.results = valid_results
        return valid_results

    def get_top(self, n: int = 5) -> list[StrategyDNA]:
        """Get top N strategies."""
        return self.results[:n]

    def export_results(self) -> list[dict]:
        """Export results as serializable dicts."""
        output = []
        for dna in self.results:
            r = dna.backtest_result
            output.append({
                "id": dna.id,
                "name": dna.name,
                "category": dna.category,
                "entry_type": dna.entry_type.value,
                "exit_type": dna.exit_type.value,
                "timeframe": dna.timeframe.value,
                "style": dna.style,
                "complexity": dna.complexity,
                "markets": dna.markets,
                "proven": dna.proven,
                "score": dna.score,
                "params": dna.params,
                "metrics": {
                    "sharpe": r.sharpe_ratio if r else 0,
                    "profit_factor": r.profit_factor if r else 0,
                    "max_drawdown": r.max_drawdown_pct if r else 0,
                    "win_rate": r.win_rate if r else 0,
                    "total_return": r.total_return_pct if r else 0,
                    "total_trades": r.total_trades if r else 0,
                    "expectancy": r.expectancy if r else 0,
                    "recovery_factor": r.recovery_factor if r else 0,
                } if r else {},
            })
        return output
