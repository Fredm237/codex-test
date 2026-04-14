"""
SmartWave Quant Lab — Event-Driven Backtester Engine
=====================================================
Tick-by-tick simulation with full order lifecycle management.

Architecture:
  DataFeed → [Tick] → Engine → Strategy.on_tick() → Orders → ExecutionEngine → Fills → Positions

The engine maintains:
  - Account state (balance, equity, margin)
  - Order book (pending orders)
  - Position book (open positions)
  - Equity curve snapshots
  - Full trade log with MAE/MFE
"""

from __future__ import annotations

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Protocol

import numpy as np

from core.models import (
    AccountState,
    BacktestConfig,
    BacktestResult,
    Bar,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    PositionStatus,
    Tick,
    Timeframe,
)
from core.execution import ExecutionEngine

logger = logging.getLogger("smartwave.engine")


# ══════════════════════════════════════════════════════════════
# STRATEGY PROTOCOL (interface)
# ══════════════════════════════════════════════════════════════

class StrategyProtocol(Protocol):
    """Any strategy must implement this interface."""

    def on_init(self, engine: "BacktestEngine") -> None: ...
    def on_tick(self, tick: Tick) -> None: ...
    def on_bar(self, bar: Bar) -> None: ...
    def on_order_filled(self, order: Order) -> None: ...
    def on_position_closed(self, position: Position) -> None: ...


# ══════════════════════════════════════════════════════════════
# BAR BUILDER (aggregates ticks into bars)
# ══════════════════════════════════════════════════════════════

class BarBuilder:
    """Aggregates tick data into OHLCV bars of the specified timeframe."""

    def __init__(self, timeframe: Timeframe) -> None:
        self.tf = timeframe
        self._current_bar: Optional[dict] = None
        self._bar_end: Optional[datetime] = None

    def _get_bar_boundary(self, dt: datetime) -> datetime:
        secs = self.tf.seconds
        ts = dt.timestamp()
        bar_start = int(ts // secs) * secs
        return datetime.fromtimestamp(bar_start + secs)

    def feed_tick(self, tick: Tick) -> Optional[Bar]:
        """Feed a tick, returns a completed Bar if boundary crossed."""
        if self._current_bar is None:
            self._bar_end = self._get_bar_boundary(tick.timestamp)
            self._current_bar = {
                "open": tick.mid, "high": tick.mid, "low": tick.mid,
                "close": tick.mid, "volume": tick.bid_volume + tick.ask_volume,
                "tick_volume": 1, "spread": tick.spread,
                "timestamp": tick.timestamp,
            }
            return None

        if tick.timestamp >= self._bar_end:
            # Complete the bar
            completed = Bar(
                timestamp=self._current_bar["timestamp"],
                open=self._current_bar["open"],
                high=self._current_bar["high"],
                low=self._current_bar["low"],
                close=self._current_bar["close"],
                volume=self._current_bar["volume"],
                tick_volume=self._current_bar["tick_volume"],
                spread=self._current_bar["spread"] / max(1, self._current_bar["tick_volume"]),
                timeframe=self.tf,
            )
            # Start new bar
            self._bar_end = self._get_bar_boundary(tick.timestamp)
            self._current_bar = {
                "open": tick.mid, "high": tick.mid, "low": tick.mid,
                "close": tick.mid, "volume": tick.bid_volume + tick.ask_volume,
                "tick_volume": 1, "spread": tick.spread,
                "timestamp": tick.timestamp,
            }
            return completed

        # Update current bar
        b = self._current_bar
        b["high"] = max(b["high"], tick.mid)
        b["low"] = min(b["low"], tick.mid)
        b["close"] = tick.mid
        b["volume"] += tick.bid_volume + tick.ask_volume
        b["tick_volume"] += 1
        b["spread"] += tick.spread
        return None


# ══════════════════════════════════════════════════════════════
# BACKTEST ENGINE (core orchestrator)
# ══════════════════════════════════════════════════════════════

class BacktestEngine:
    """
    Event-driven backtest engine.
    
    Processes ticks sequentially, managing:
    - Pending order activation (limit/stop triggers)
    - SL/TP checking on every tick
    - Position P&L tracking with MAE/MFE
    - Risk limit enforcement
    - Equity curve snapshots
    """

    def __init__(self, config: BacktestConfig, strategy: StrategyProtocol) -> None:
        self.config = config
        self.strategy = strategy
        self.execution = ExecutionEngine(config)
        self.bar_builder = BarBuilder(config.timeframe)

        # State
        self.account = AccountState(
            balance=config.initial_capital,
            equity=config.initial_capital,
            peak_equity=config.initial_capital,
            leverage=config.leverage,
        )
        self.pending_orders: list[Order] = []
        self.open_positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.order_history: list[Order] = []

        # Tracking
        self._equity_curve: list[dict] = []
        self._daily_equity: dict[str, float] = {}
        self._tick_count: int = 0
        self._current_tick: Optional[Tick] = None
        self._daily_start_equity: float = config.initial_capital
        self._current_day: str = ""
        self._bars: list[Bar] = []  # History for strategy lookback

    # ── PUBLIC API (called by strategy) ────────────────────────

    def submit_order(
        self,
        side: OrderSide,
        lots: float,
        order_type: OrderType = OrderType.MARKET,
        price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        magic: int = 0,
        comment: str = "",
    ) -> Optional[Order]:
        """Submit an order. Returns the order object or None if rejected."""
        # Risk check: max concurrent trades
        if len(self.open_positions) >= self.config.max_concurrent_trades:
            logger.debug("Order rejected: max concurrent trades reached")
            return None

        # Risk check: max risk per trade
        if self._current_tick and stop_loss > 0:
            risk_per_unit = abs(self._current_tick.mid - stop_loss)
            risk_pct = (risk_per_unit * lots * 100) / self.account.equity * 100
            if risk_pct > self.config.max_risk_per_trade_pct:
                logger.debug(f"Order rejected: risk {risk_pct:.1f}% > limit {self.config.max_risk_per_trade_pct}%")
                return None

        order = Order(
            symbol=self.config.symbol,
            side=side,
            order_type=order_type,
            lots=lots,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            submitted_at=self._current_tick.timestamp if self._current_tick else None,
            magic_number=magic,
            comment=comment,
        )

        if order_type == OrderType.MARKET:
            self._process_market_order(order)
        else:
            self.pending_orders.append(order)
            logger.debug(f"Pending order placed: {order.id} {side.value} {lots} @ {price}")

        self.order_history.append(order)
        return order

    def close_position(self, position: Position, comment: str = "") -> bool:
        """Close a specific position at market."""
        if position.status != PositionStatus.OPEN or self._current_tick is None:
            return False
        close_price = self._current_tick.bid if position.side == OrderSide.BUY else self._current_tick.ask
        self._close_position(position, close_price, comment or "Manual close")
        return True

    def close_all(self, comment: str = "Close all") -> int:
        """Close all open positions."""
        closed = 0
        for pos in list(self.open_positions):
            if self.close_position(pos, comment):
                closed += 1
        return closed

    def modify_position(self, position: Position, sl: float = 0, tp: float = 0) -> bool:
        """Modify SL/TP of an open position."""
        if position.status != PositionStatus.OPEN:
            return False
        if sl > 0: position.stop_loss = sl
        if tp > 0: position.take_profit = tp
        return True

    def cancel_order(self, order: Order) -> bool:
        """Cancel a pending order."""
        if order in self.pending_orders:
            order.status = OrderStatus.CANCELLED
            self.pending_orders.remove(order)
            return True
        return False

    def get_bars(self, count: int = 100) -> list[Bar]:
        """Get the last N completed bars for strategy lookback."""
        return self._bars[-count:]

    @property
    def positions_count(self) -> int:
        return len(self.open_positions)

    @property
    def current_price(self) -> float:
        return self._current_tick.mid if self._current_tick else 0.0

    # ── INTERNAL PROCESSING ────────────────────────────────────

    def _process_market_order(self, order: Order) -> None:
        """Execute a market order immediately."""
        if self._current_tick is None:
            order.status = OrderStatus.REJECTED
            return

        result = self.execution.execute_order(order, self._current_tick, self.account.equity)

        if not result.success:
            order.status = OrderStatus.REJECTED
            logger.debug(f"Order rejected: {result.rejection_reason}")
            return

        order.status = OrderStatus.FILLED
        order.fill_price = result.fill_price
        order.slippage = result.slippage_points
        order.commission = result.commission
        order.filled_at = self._current_tick.timestamp

        # Create position
        pos = Position(
            symbol=order.symbol,
            side=order.side,
            lots=order.lots,
            entry_price=result.fill_price,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            commission=result.commission,
            opened_at=self._current_tick.timestamp,
            order_id=order.id,
            magic_number=order.magic_number,
            comment=order.comment,
        )

        # Margin reservation
        margin = (pos.lots * 100 * result.fill_price) / self.config.leverage
        self.account.margin_used += margin

        self.open_positions.append(pos)
        self.strategy.on_order_filled(order)
        logger.debug(f"Filled: {order.side.value} {order.lots} @ {result.fill_price} (slip={result.slippage_points}pts)")

    def _close_position(self, pos: Position, price: float, reason: str = "") -> None:
        """Close a position at the given price."""
        pos.exit_price = price
        pos.profit = pos.calculate_profit(price) - pos.commission - pos.swap
        pos.status = PositionStatus.CLOSED
        pos.closed_at = self._current_tick.timestamp if self._current_tick else None
        pos.comment = reason if reason else pos.comment

        # Update account
        self.account.balance += pos.profit
        self.account.realized_pnl += pos.profit
        margin = (pos.lots * 100 * pos.entry_price) / self.config.leverage
        self.account.margin_used = max(0, self.account.margin_used - margin)

        self.open_positions.remove(pos)
        self.closed_positions.append(pos)
        self.strategy.on_position_closed(pos)
        logger.debug(f"Closed: {pos.side.value} {pos.lots} P&L=${pos.profit:.2f} ({reason})")

    def _check_pending_orders(self, tick: Tick) -> None:
        """Check if any pending orders should be triggered."""
        for order in list(self.pending_orders):
            triggered = False

            if order.order_type == OrderType.LIMIT:
                if order.is_buy and tick.ask <= order.price:
                    triggered = True
                elif not order.is_buy and tick.bid >= order.price:
                    triggered = True

            elif order.order_type == OrderType.STOP:
                if order.is_buy and tick.ask >= order.price:
                    triggered = True
                elif not order.is_buy and tick.bid <= order.price:
                    triggered = True

            if triggered:
                self.pending_orders.remove(order)
                self._process_market_order(order)

    def _check_sl_tp(self, tick: Tick) -> None:
        """Check SL/TP on all open positions."""
        for pos in list(self.open_positions):
            trigger = self.execution.check_sl_tp(pos, tick)
            if trigger == "SL":
                close_price = pos.stop_loss  # Fill at SL level (with potential slippage)
                self._close_position(pos, close_price, "Stop Loss")
            elif trigger == "TP":
                close_price = pos.take_profit
                self._close_position(pos, close_price, "Take Profit")

    def _update_positions_pnl(self, tick: Tick) -> None:
        """Update unrealized P&L and MAE/MFE for all open positions."""
        total_unrealized = 0.0
        for pos in self.open_positions:
            if pos.side == OrderSide.BUY:
                unrealized = (tick.bid - pos.entry_price) * pos.lots * 100
            else:
                unrealized = (pos.entry_price - tick.ask) * pos.lots * 100
            unrealized -= pos.commission
            total_unrealized += unrealized
            pos.update_excursion(tick.mid)

        self.account.update_equity(total_unrealized)

    def _check_risk_limits(self, tick: Tick) -> None:
        """Enforce daily and total drawdown limits (prop firm compliance)."""
        # Daily drawdown check
        daily_dd = ((self._daily_start_equity - self.account.equity) / self._daily_start_equity) * 100
        if daily_dd >= self.config.max_daily_dd_pct:
            logger.warning(f"Daily DD limit hit: {daily_dd:.1f}% — closing all")
            self.close_all("Daily DD limit")

        # Total drawdown check
        if self.account.max_drawdown_pct >= self.config.max_total_dd_pct:
            logger.warning(f"Total DD limit hit: {self.account.max_drawdown_pct:.1f}% — closing all")
            self.close_all("Total DD limit")

    def _snapshot_equity(self, tick: Tick) -> None:
        """Take equity curve snapshot (once per bar, not per tick)."""
        day = tick.timestamp.strftime("%Y-%m-%d")
        self._daily_equity[day] = self.account.equity

        # Track daily reset
        if day != self._current_day:
            self._current_day = day
            self._daily_start_equity = self.account.balance

    # ── MAIN LOOP ──────────────────────────────────────────────

    def process_tick(self, tick: Tick) -> None:
        """Process a single tick through the full pipeline."""
        self._current_tick = tick
        self._tick_count += 1

        # Feed spread model
        self.execution.spread.feed_price(tick.mid)

        # 1. Check pending orders
        self._check_pending_orders(tick)

        # 2. Check SL/TP
        self._check_sl_tp(tick)

        # 3. Update P&L
        self._update_positions_pnl(tick)

        # 4. Risk limits
        self._check_risk_limits(tick)

        # 5. Build bar
        bar = self.bar_builder.feed_tick(tick)
        if bar:
            self._bars.append(bar)
            if len(self._bars) > 5000:
                self._bars = self._bars[-3000:]
            self.strategy.on_bar(bar)

        # 6. Strategy tick callback
        self.strategy.on_tick(tick)

        # 7. Equity snapshot
        self._snapshot_equity(tick)

    def run(self, ticks: list[Tick] | np.ndarray) -> BacktestResult:
        """Run the full backtest on a tick dataset."""
        start_time = time.perf_counter()
        logger.info(f"Starting backtest: {self.config.strategy_name} | {len(ticks)} ticks")

        # Initialize strategy
        self.strategy.on_init(self)

        # Main loop
        for tick in ticks:
            self.process_tick(tick)

        # Close remaining positions
        if self.open_positions and self._current_tick:
            self.close_all("End of backtest")

        elapsed = time.perf_counter() - start_time
        logger.info(f"Backtest complete in {elapsed:.2f}s | {self._tick_count} ticks | {len(self.closed_positions)} trades")

        return self._compute_results(elapsed)

    # ── RESULTS COMPUTATION ────────────────────────────────────

    def _compute_results(self, elapsed: float) -> BacktestResult:
        """Compute all performance metrics from trade history."""
        result = BacktestResult(config=self.config)

        trades = self.closed_positions
        result.total_trades = len(trades)

        if not trades:
            result.duration_seconds = elapsed
            return result

        # Basic P&L
        pnls = [t.profit for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        result.total_pnl = sum(pnls)
        result.total_return_pct = (result.total_pnl / self.config.initial_capital) * 100
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = (len(wins) / len(pnls)) * 100 if pnls else 0

        result.avg_win = np.mean(wins) if wins else 0.0
        result.avg_loss = np.mean(losses) if losses else 0.0
        result.largest_win = max(wins) if wins else 0.0
        result.largest_loss = min(losses) if losses else 0.0

        # Profit Factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Expectancy
        result.expectancy = np.mean(pnls) if pnls else 0.0

        # Daily returns for ratio calculations
        equity_values = list(self._daily_equity.values())
        if len(equity_values) > 1:
            daily_returns = []
            for i in range(1, len(equity_values)):
                dr = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                daily_returns.append(dr)
            result.daily_returns = daily_returns

            # Sharpe Ratio (annualized, risk-free = 0)
            if len(daily_returns) > 5:
                mean_r = np.mean(daily_returns)
                std_r = np.std(daily_returns)
                if std_r > 0:
                    result.sharpe_ratio = round((mean_r / std_r) * np.sqrt(252), 2)

                # Sortino (downside deviation only)
                downside = [r for r in daily_returns if r < 0]
                if downside:
                    down_std = np.std(downside)
                    if down_std > 0:
                        result.sortino_ratio = round((mean_r / down_std) * np.sqrt(252), 2)

        # Drawdown
        result.max_drawdown_abs = self.account.max_drawdown
        result.max_drawdown_pct = round(self.account.max_drawdown_pct, 2)

        # Calmar Ratio
        if result.max_drawdown_pct > 0:
            annual_return = result.total_return_pct  # simplified
            result.calmar_ratio = round(annual_return / result.max_drawdown_pct, 2)

        # Recovery Factor
        if result.max_drawdown_abs > 0:
            result.recovery_factor = round(result.total_pnl / result.max_drawdown_abs, 2)

        # Consecutive wins/losses
        result.max_consecutive_wins = self._max_consecutive(pnls, positive=True)
        result.max_consecutive_losses = self._max_consecutive(pnls, positive=False)

        # Trade durations
        durations = []
        for t in trades:
            if t.opened_at and t.closed_at:
                dur = (t.closed_at - t.opened_at).total_seconds() / 3600
                durations.append(dur)
        result.avg_trade_duration_hours = round(np.mean(durations), 1) if durations else 0

        # Execution quality
        slippages = [o.slippage for o in self.order_history if o.status == OrderStatus.FILLED]
        result.avg_slippage = round(np.mean(slippages), 1) if slippages else 0
        result.total_commission = sum(t.commission for t in trades)

        # Equity curve for charting
        result.equity_curve = [
            {"date": date, "equity": eq} for date, eq in self._daily_equity.items()
        ]

        # Trade log
        result.trade_log = [
            {
                "id": t.id, "side": t.side.value, "lots": t.lots,
                "entry": t.entry_price, "exit": t.exit_price,
                "pnl": round(t.profit, 2), "mae": round(t.mae, 2), "mfe": round(t.mfe, 2),
                "opened": t.opened_at.isoformat() if t.opened_at else "",
                "closed": t.closed_at.isoformat() if t.closed_at else "",
                "comment": t.comment,
            }
            for t in trades
        ]

        result.duration_seconds = elapsed
        result.started_at = trades[0].opened_at if trades else None
        result.completed_at = trades[-1].closed_at if trades else None

        return result

    @staticmethod
    def _max_consecutive(pnls: list[float], positive: bool) -> int:
        max_streak = 0
        current = 0
        for p in pnls:
            if (positive and p > 0) or (not positive and p <= 0):
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        return max_streak
