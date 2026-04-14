"""
SmartWave Quant Lab — Execution Model
=======================================
Realistic market microstructure simulation:
- Dynamic spread (session + volatility driven)
- Probabilistic slippage (skewed adverse distribution)
- Latency simulation (log-normal)
- Commission & swap calculation
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from core.models import (
    BacktestConfig,
    Order,
    OrderSide,
    OrderType,
    Tick,
    Position,
)


class SpreadModel:
    """Dynamic spread: session-aware + volatility-sensitive."""

    SESSION_MULT = {
        "asian": 1.4, "london_early": 0.9, "london_ny": 0.7,
        "ny_afternoon": 1.0, "rollover": 2.0,
    }

    def __init__(self, base_pts: float = 25.0, model: str = "dynamic",
                 vol_sens: float = 0.3, rng_seed: int | None = None) -> None:
        self.base = base_pts
        self.model = model
        self.vol_sens = vol_sens
        self._rng = np.random.default_rng(rng_seed)
        self._returns: list[float] = []
        self._last_price: float = 0.0

    def _session(self, dt: datetime) -> str:
        h = dt.hour
        if h < 7: return "asian"
        if h < 12: return "london_early"
        if h < 16: return "london_ny"
        if h < 20: return "ny_afternoon"
        return "rollover"

    def feed_price(self, price: float) -> None:
        if self._last_price > 0:
            self._returns.append((price - self._last_price) / self._last_price)
            if len(self._returns) > 100:
                self._returns = self._returns[-50:]
        self._last_price = price

    def _vol_mult(self) -> float:
        if len(self._returns) < 5:
            return 1.0
        std = float(np.std(self._returns[-20:]))
        return max(0.5, min(3.0, std / 0.001))

    def get_spread(self, timestamp: datetime) -> float:
        """Returns spread in price units (points * 0.01 for gold)."""
        if self.model == "fixed":
            return self.base * 0.01
        s_mult = self.SESSION_MULT[self._session(timestamp)]
        v_mult = 1.0 + (self._vol_mult() - 1.0) * self.vol_sens
        noise = float(self._rng.lognormal(0, 0.15))
        pts = max(5.0, min(200.0, self.base * s_mult * v_mult * noise))
        return pts * 0.01


class SlippageModel:
    """
    Probabilistic slippage: skewed adverse distribution.
    60% zero, 25% small adverse, 10% large adverse, 5% favorable.
    """

    def __init__(self, max_pts: float = 5.0, model: str = "probabilistic",
                 rng_seed: int | None = None) -> None:
        self.max = max_pts
        self.model = model
        self._rng = np.random.default_rng(rng_seed)

    def get_slippage(self, order: Order, vol_factor: float = 1.0) -> float:
        """Positive = adverse. Returns points."""
        if self.model == "none": return 0.0
        if self.model == "fixed": return self.max * 0.5
        if order.order_type == OrderType.LIMIT:
            return 0.0 if self._rng.random() < 0.9 else -float(self._rng.uniform(0, 1))
        r = float(self._rng.random())
        mx = self.max * vol_factor
        if r < 0.60: return 0.0
        if r < 0.85: return float(self._rng.uniform(0.5, min(3.0, mx)))
        if r < 0.95: return float(self._rng.uniform(3.0, mx))
        return -float(self._rng.uniform(0.5, 2.0))


class LatencyModel:
    """Log-normal latency simulation."""

    def __init__(self, base_ms: float = 50.0, rng_seed: int | None = None) -> None:
        self.base = base_ms
        self._rng = np.random.default_rng(rng_seed)

    def get_latency_ms(self) -> float:
        mu = math.log(self.base) - 0.5 * 0.3**2
        return float(self._rng.lognormal(mu, 0.3))


class CommissionCalculator:
    def __init__(self, per_lot: float = 7.0) -> None:
        self.per_lot = per_lot

    def calculate(self, lots: float, price: float = 0.0) -> float:
        return round(lots * self.per_lot, 2)


@dataclass
class ExecutionResult:
    success: bool
    fill_price: float = 0.0
    slippage_points: float = 0.0
    commission: float = 0.0
    latency_ms: float = 0.0
    rejection_reason: str = ""


class ExecutionEngine:
    """
    Full execution pipeline:
    Order → Latency → Spread → Slippage → Fill → Commission
    """

    def __init__(self, config: BacktestConfig, rng_seed: int = 42) -> None:
        self.config = config
        self.spread = SpreadModel(config.avg_spread_points, config.spread_model, rng_seed=rng_seed)
        self.slippage = SlippageModel(config.max_slippage_points, config.slippage_model, rng_seed=rng_seed+1)
        self.latency = LatencyModel(config.latency_ms, rng_seed=rng_seed+2)
        self.commission = CommissionCalculator(config.commission_per_lot)

    def execute_order(self, order: Order, tick: Tick, equity: float) -> ExecutionResult:
        lat = self.latency.get_latency_ms()
        base = tick.ask if order.is_buy else tick.bid
        slip = self.slippage.get_slippage(order)
        slip_price = slip * 0.01
        fill = base + slip_price if order.is_buy else base - slip_price
        margin_req = (order.lots * 100 * fill) / self.config.leverage
        if margin_req > equity * 0.9:
            return ExecutionResult(False, rejection_reason="Insufficient margin")
        comm = self.commission.calculate(order.lots, fill)
        return ExecutionResult(True, round(fill, 2), round(slip, 1), comm, round(lat, 1))

    def check_sl_tp(self, pos: Position, tick: Tick) -> str | None:
        if pos.stop_loss > 0:
            if pos.side == OrderSide.BUY and tick.bid <= pos.stop_loss: return "SL"
            if pos.side == OrderSide.SELL and tick.ask >= pos.stop_loss: return "SL"
        if pos.take_profit > 0:
            if pos.side == OrderSide.BUY and tick.bid >= pos.take_profit: return "TP"
            if pos.side == OrderSide.SELL and tick.ask <= pos.take_profit: return "TP"
        return None
