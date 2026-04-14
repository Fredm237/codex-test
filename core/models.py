"""
SmartWave Quant Lab — Core Domain Models
=========================================
Canonical type definitions for the entire system.
All modules import from here. Immutable where possible.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════

class OrderSide(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PositionStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class Timeframe(enum.Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    @property
    def seconds(self) -> int:
        return {
            "M1": 60, "M5": 300, "M15": 900, "M30": 1800,
            "H1": 3600, "H4": 14400, "D1": 86400,
            "W1": 604800, "MN1": 2592000,
        }[self.value]


# ══════════════════════════════════════════════════════════════
# MARKET DATA
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class Tick:
    """Atomic market data unit."""
    timestamp: datetime
    bid: float
    ask: float
    bid_volume: float = 0.0
    ask_volume: float = 0.0

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    @property
    def spread_points(self) -> float:
        return round(self.spread / 0.01)


@dataclass(frozen=True, slots=True)
class Bar:
    """OHLCV bar aggregated from ticks."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    tick_volume: int = 0
    spread: float = 0.0
    timeframe: Timeframe = Timeframe.M5


# ══════════════════════════════════════════════════════════════
# ORDERS & POSITIONS
# ══════════════════════════════════════════════════════════════

@dataclass(slots=True)
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    symbol: str = "XAUUSD"
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    lots: float = 0.01
    price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    fill_price: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    magic_number: int = 0
    comment: str = ""

    @property
    def is_buy(self) -> bool:
        return self.side == OrderSide.BUY

    @property
    def is_pending(self) -> bool:
        return self.order_type in (OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT)


@dataclass(slots=True)
class Position:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    symbol: str = "XAUUSD"
    side: OrderSide = OrderSide.BUY
    lots: float = 0.01
    entry_price: float = 0.0
    exit_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    order_id: str = ""
    magic_number: int = 0
    comment: str = ""
    mae: float = 0.0
    mfe: float = 0.0
    _max_favorable: float = field(default=0.0, repr=False)
    _max_adverse: float = field(default=0.0, repr=False)

    def update_excursion(self, current_price: float) -> None:
        if self.side == OrderSide.BUY:
            unrealized = (current_price - self.entry_price) * self.lots * 100
        else:
            unrealized = (self.entry_price - current_price) * self.lots * 100
        if unrealized > self._max_favorable:
            self._max_favorable = unrealized
            self.mfe = unrealized
        if unrealized < self._max_adverse:
            self._max_adverse = unrealized
            self.mae = unrealized

    def calculate_profit(self, exit_price: float) -> float:
        if self.side == OrderSide.BUY:
            return (exit_price - self.entry_price) * self.lots * 100
        else:
            return (self.entry_price - exit_price) * self.lots * 100


# ══════════════════════════════════════════════════════════════
# ACCOUNT STATE
# ══════════════════════════════════════════════════════════════

@dataclass(slots=True)
class AccountState:
    balance: float = 100_000.0
    equity: float = 100_000.0
    margin_used: float = 0.0
    margin_free: float = 100_000.0
    margin_level: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    daily_pnl: float = 0.0
    peak_equity: float = 100_000.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    leverage: int = 100
    currency: str = "USD"

    def update_equity(self, unrealized: float) -> None:
        self.unrealized_pnl = unrealized
        self.equity = self.balance + unrealized
        self.margin_free = self.equity - self.margin_used
        if self.margin_used > 0:
            self.margin_level = (self.equity / self.margin_used) * 100
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity
        dd = self.peak_equity - self.equity
        if dd > self.max_drawdown:
            self.max_drawdown = dd
            self.max_drawdown_pct = (dd / self.peak_equity) * 100


# ══════════════════════════════════════════════════════════════
# BACKTEST CONFIG & RESULT
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class BacktestConfig:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    strategy_name: str = ""
    symbol: str = "XAUUSD"
    timeframe: Timeframe = Timeframe.M5
    start_date: str = "2024-01-01"
    end_date: str = "2025-12-31"
    initial_capital: float = 100_000.0
    leverage: int = 100
    spread_model: str = "dynamic"
    avg_spread_points: float = 25.0
    slippage_model: str = "probabilistic"
    max_slippage_points: float = 5.0
    latency_ms: float = 50.0
    commission_per_lot: float = 7.0
    max_risk_per_trade_pct: float = 1.0
    max_daily_dd_pct: float = 5.0
    max_total_dd_pct: float = 10.0
    max_concurrent_trades: int = 3
    strategy_params: dict = field(default_factory=dict)


@dataclass(slots=True)
class BacktestResult:
    config: BacktestConfig = field(default_factory=BacktestConfig)
    total_return_pct: float = 0.0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_abs: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    expectancy: float = 0.0
    recovery_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    avg_trade_duration_hours: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    equity_curve: list[dict] = field(default_factory=list)
    trade_log: list[dict] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)
    avg_slippage: float = 0.0
    total_commission: float = 0.0
    total_swap: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        from dataclasses import fields
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if not f.name.startswith("_") and f.name != "config"
        }
