"""
SmartWave Quant Lab — Strategy Framework
==========================================
Abstract base strategy + ICT Unicorn Pro example implementation.

Every strategy inherits from BaseStrategy which provides:
- Access to the engine (orders, positions, account)
- Parameter management
- Indicator helpers
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from core.models import (
    Bar,
    Order,
    OrderSide,
    OrderType,
    Position,
    Tick,
    Timeframe,
)

logger = logging.getLogger("smartwave.strategy")


# ══════════════════════════════════════════════════════════════
# BASE STRATEGY
# ══════════════════════════════════════════════════════════════

class BaseStrategy(ABC):
    """
    Abstract base strategy. Subclass this to create trading strategies.
    
    Lifecycle:
        on_init()          → called once at start, setup indicators
        on_tick(tick)       → called on every tick (use sparingly)
        on_bar(bar)         → called when a new bar completes (main logic)
        on_order_filled()   → notification
        on_position_closed() → notification
    """

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params: dict[str, Any] = params or {}
        self.engine: Any = None  # Set in on_init
        self._name: str = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    def on_init(self, engine: Any) -> None:
        """Called once before the backtest starts."""
        self.engine = engine
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        """Setup indicators, parameters, etc."""
        ...

    def on_tick(self, tick: Tick) -> None:
        """Called on every tick. Override only if needed."""
        pass

    @abstractmethod
    def on_bar(self, bar: Bar) -> None:
        """Called when a new bar completes. Main strategy logic here."""
        ...

    def on_order_filled(self, order: Order) -> None:
        """Called when an order is filled."""
        pass

    def on_position_closed(self, position: Position) -> None:
        """Called when a position is closed."""
        pass

    # ── HELPER METHODS ─────────────────────────────────────────

    def buy(
        self,
        lots: float,
        sl: float = 0,
        tp: float = 0,
        order_type: OrderType = OrderType.MARKET,
        price: float = 0,
        comment: str = "",
    ) -> Optional[Order]:
        return self.engine.submit_order(
            side=OrderSide.BUY, lots=lots, order_type=order_type,
            price=price, stop_loss=sl, take_profit=tp, comment=comment,
        )

    def sell(
        self,
        lots: float,
        sl: float = 0,
        tp: float = 0,
        order_type: OrderType = OrderType.MARKET,
        price: float = 0,
        comment: str = "",
    ) -> Optional[Order]:
        return self.engine.submit_order(
            side=OrderSide.SELL, lots=lots, order_type=order_type,
            price=price, stop_loss=sl, take_profit=tp, comment=comment,
        )

    def close_all(self, comment: str = "") -> int:
        return self.engine.close_all(comment)


# ══════════════════════════════════════════════════════════════
# INDICATOR HELPERS
# ══════════════════════════════════════════════════════════════

def sma(data: list[float], period: int) -> float:
    """Simple Moving Average of last N values."""
    if len(data) < period:
        return 0.0
    return float(np.mean(data[-period:]))


def ema(data: list[float], period: int) -> float:
    """Exponential Moving Average (recursive approximation using last 3*period values)."""
    if len(data) < period:
        return 0.0
    subset = data[-(period * 3):]
    weights = np.exp(np.linspace(-1, 0, len(subset)))
    weights /= weights.sum()
    return float(np.dot(subset, weights))


def atr(bars: list[Bar], period: int = 14) -> float:
    """Average True Range from bar data."""
    if len(bars) < period + 1:
        return 0.0
    trs = []
    for i in range(-period, 0):
        bar = bars[i]
        prev = bars[i - 1]
        tr = max(
            bar.high - bar.low,
            abs(bar.high - prev.close),
            abs(bar.low - prev.close),
        )
        trs.append(tr)
    return float(np.mean(trs))


def rsi(closes: list[float], period: int = 14) -> float:
    """Relative Strength Index."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = float(np.mean(gains))
    avg_loss = float(np.mean(losses))
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def detect_fvg(bars: list[Bar], min_size: float = 0.5) -> list[dict]:
    """
    Detect Fair Value Gaps (ICT concept).
    A bullish FVG: bar[i-2].high < bar[i].low (gap between)
    A bearish FVG: bar[i-2].low > bar[i].high
    """
    fvgs = []
    if len(bars) < 3:
        return fvgs
    for i in range(2, len(bars)):
        # Bullish FVG
        if bars[i].low > bars[i-2].high:
            gap = bars[i].low - bars[i-2].high
            if gap >= min_size:
                fvgs.append({
                    "type": "bullish",
                    "top": bars[i].low,
                    "bottom": bars[i-2].high,
                    "size": gap,
                    "timestamp": bars[i].timestamp,
                })
        # Bearish FVG
        if bars[i].high < bars[i-2].low:
            gap = bars[i-2].low - bars[i].high
            if gap >= min_size:
                fvgs.append({
                    "type": "bearish",
                    "top": bars[i-2].low,
                    "bottom": bars[i].high,
                    "size": gap,
                    "timestamp": bars[i].timestamp,
                })
    return fvgs


def detect_order_block(bars: list[Bar], lookback: int = 20) -> list[dict]:
    """
    Detect Order Blocks (ICT concept).
    Bullish OB: last bearish candle before a strong bullish move.
    Bearish OB: last bullish candle before a strong bearish move.
    """
    obs = []
    if len(bars) < lookback:
        return obs
    recent = bars[-lookback:]
    for i in range(1, len(recent) - 1):
        # Bullish OB: bearish candle followed by strong bullish
        if recent[i].close < recent[i].open:  # bearish
            if recent[i+1].close > recent[i+1].open:  # bullish
                move = (recent[i+1].close - recent[i+1].open) / recent[i+1].open
                if move > 0.001:  # significant move
                    obs.append({
                        "type": "bullish",
                        "high": recent[i].high,
                        "low": recent[i].low,
                        "timestamp": recent[i].timestamp,
                    })
        # Bearish OB
        if recent[i].close > recent[i].open:  # bullish
            if recent[i+1].close < recent[i+1].open:  # bearish
                move = (recent[i+1].open - recent[i+1].close) / recent[i+1].open
                if move > 0.001:
                    obs.append({
                        "type": "bearish",
                        "high": recent[i].high,
                        "low": recent[i].low,
                        "timestamp": recent[i].timestamp,
                    })
    return obs


# ══════════════════════════════════════════════════════════════
# ICT UNICORN PRO — EXAMPLE STRATEGY
# ══════════════════════════════════════════════════════════════

class ICTUnicornPro(BaseStrategy):
    """
    ICT Unicorn Model implementation.
    
    Logic:
    1. Identify market structure (CHoCH/BOS) via swing highs/lows
    2. Wait for FVG formation in the direction of structure break
    3. Look for Order Block confluence near FVG
    4. Enter on FVG retracement with OB confluence
    5. SL below/above OB, TP at opposing liquidity level
    
    Session filter: London + NY only (07:00-20:00 UTC)
    ATR filter: only trade when ATR > threshold (avoid ranging)
    """

    def initialize(self) -> None:
        # Parameters (optimizable)
        self.p = {
            "atr_period": self.params.get("atr_period", 14),
            "atr_min": self.params.get("atr_min", 2.0),
            "rr_ratio": self.params.get("rr_ratio", 2.0),
            "risk_pct": self.params.get("risk_pct", 1.0),
            "fvg_min_size": self.params.get("fvg_min_size", 1.0),
            "session_start": self.params.get("session_start", 7),
            "session_end": self.params.get("session_end", 20),
            "ema_fast": self.params.get("ema_fast", 21),
            "ema_slow": self.params.get("ema_slow", 50),
            "max_spread_pts": self.params.get("max_spread_pts", 40),
        }
        self._closes: list[float] = []
        self._last_signal_bar: int = 0

    def _in_session(self, bar: Bar) -> bool:
        """London + NY session filter."""
        return self.p["session_start"] <= bar.timestamp.hour < self.p["session_end"]

    def _calculate_lot_size(self, sl_distance: float) -> float:
        """Position sizing based on risk percentage."""
        risk_amount = self.engine.account.equity * (self.p["risk_pct"] / 100)
        lot_size = risk_amount / (sl_distance * 100)  # 100 = lot multiplier for gold
        return round(max(0.01, min(lot_size, 1.0)), 2)

    def on_bar(self, bar: Bar) -> None:
        self._closes.append(bar.close)
        bars = self.engine.get_bars(200)

        if len(bars) < 60 or self.engine.positions_count > 0:
            return

        # Session filter
        if not self._in_session(bar):
            return

        # Cooldown: at least 5 bars between trades
        bar_idx = len(bars)
        if bar_idx - self._last_signal_bar < 5:
            return

        # Spread filter
        if bar.spread * 100 > self.p["max_spread_pts"]:  # spread in price → points
            return

        # ATR filter
        current_atr = atr(bars, self.p["atr_period"])
        if current_atr < self.p["atr_min"]:
            return

        # Trend via EMA cross
        fast = ema(self._closes, self.p["ema_fast"])
        slow = ema(self._closes, self.p["ema_slow"])
        if fast == 0 or slow == 0:
            return
        bullish_trend = fast > slow
        bearish_trend = fast < slow

        # Detect FVGs
        fvgs = detect_fvg(bars[-10:], self.p["fvg_min_size"])

        # Detect Order Blocks for confluence
        obs = detect_order_block(bars, lookback=20)

        # ── BULLISH SETUP ──
        if bullish_trend:
            bull_fvgs = [f for f in fvgs if f["type"] == "bullish"]
            bull_obs = [o for o in obs if o["type"] == "bullish"]

            if bull_fvgs:
                fvg = bull_fvgs[-1]  # most recent

                # Check if price is retracing into FVG zone
                if fvg["bottom"] <= bar.close <= fvg["top"]:
                    # OB confluence check
                    has_ob = any(
                        o["low"] <= fvg["bottom"] <= o["high"]
                        for o in bull_obs
                    )

                    sl = fvg["bottom"] - current_atr * 0.5
                    sl_dist = bar.close - sl
                    tp = bar.close + sl_dist * self.p["rr_ratio"]
                    lots = self._calculate_lot_size(sl_dist)

                    comment = "ICT Unicorn BUY" + (" +OB" if has_ob else "")
                    self.buy(lots=lots, sl=round(sl, 2), tp=round(tp, 2), comment=comment)
                    self._last_signal_bar = bar_idx

        # ── BEARISH SETUP ──
        elif bearish_trend:
            bear_fvgs = [f for f in fvgs if f["type"] == "bearish"]
            bear_obs = [o for o in obs if o["type"] == "bearish"]

            if bear_fvgs:
                fvg = bear_fvgs[-1]

                if fvg["bottom"] <= bar.close <= fvg["top"]:
                    has_ob = any(
                        o["low"] <= fvg["top"] <= o["high"]
                        for o in bear_obs
                    )

                    sl = fvg["top"] + current_atr * 0.5
                    sl_dist = sl - bar.close
                    tp = bar.close - sl_dist * self.p["rr_ratio"]
                    lots = self._calculate_lot_size(sl_dist)

                    comment = "ICT Unicorn SELL" + (" +OB" if has_ob else "")
                    self.sell(lots=lots, sl=round(sl, 2), tp=round(tp, 2), comment=comment)
                    self._last_signal_bar = bar_idx


# ══════════════════════════════════════════════════════════════
# SIMPLE MA CROSSOVER (testing/benchmark strategy)
# ══════════════════════════════════════════════════════════════

class MACrossover(BaseStrategy):
    """Simple MA crossover for benchmarking and testing."""

    def initialize(self) -> None:
        self.fast_period = self.params.get("fast_period", 10)
        self.slow_period = self.params.get("slow_period", 30)
        self.lot_size = self.params.get("lot_size", 0.1)
        self.atr_sl_mult = self.params.get("atr_sl_mult", 1.5)
        self.rr_ratio = self.params.get("rr_ratio", 2.0)
        self._closes: list[float] = []
        self._prev_fast: float = 0
        self._prev_slow: float = 0

    def on_bar(self, bar: Bar) -> None:
        self._closes.append(bar.close)

        if len(self._closes) < self.slow_period + 5:
            return

        fast = sma(self._closes, self.fast_period)
        slow = sma(self._closes, self.slow_period)

        # Detect crossover
        if self._prev_fast > 0 and self._prev_slow > 0:
            # Bullish cross
            if self._prev_fast <= self._prev_slow and fast > slow:
                if self.engine.positions_count == 0:
                    bars = self.engine.get_bars(20)
                    current_atr = atr(bars) if len(bars) > 15 else 5.0
                    sl = bar.close - current_atr * self.atr_sl_mult
                    tp = bar.close + current_atr * self.atr_sl_mult * self.rr_ratio
                    self.buy(self.lot_size, sl=round(sl, 2), tp=round(tp, 2), comment="MA Cross BUY")

            # Bearish cross
            elif self._prev_fast >= self._prev_slow and fast < slow:
                if self.engine.positions_count == 0:
                    bars = self.engine.get_bars(20)
                    current_atr = atr(bars) if len(bars) > 15 else 5.0
                    sl = bar.close + current_atr * self.atr_sl_mult
                    tp = bar.close - current_atr * self.atr_sl_mult * self.rr_ratio
                    self.sell(self.lot_size, sl=round(sl, 2), tp=round(tp, 2), comment="MA Cross SELL")

        self._prev_fast = fast
        self._prev_slow = slow
