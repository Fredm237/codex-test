"""
SmartWave Quant Lab — Robustness Engine
=========================================
Monte Carlo simulation + Walk-Forward optimization + Stress testing.

Monte Carlo Methods:
  1. Trade Permutation: shuffle trade order to assess path dependency
  2. Parameter Perturbation: add noise to optimal params
  3. Data Perturbation: modify tick data slightly (noise injection)

Walk-Forward:
  Rolling IS/OOS windows to validate out-of-sample stability.

Stress Testing:
  Simulate extreme market conditions (flash crash, gap, liquidity drought).
"""

from __future__ import annotations

import logging
import copy
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from core.models import BacktestConfig, BacktestResult, Tick
from core.engine import BacktestEngine
from strategies.strategies import BaseStrategy

logger = logging.getLogger("smartwave.robustness")


# ══════════════════════════════════════════════════════════════
# MONTE CARLO SIMULATION
# ══════════════════════════════════════════════════════════════

@dataclass
class MonteCarloConfig:
    n_simulations: int = 500
    method: str = "trade_permutation"  # "trade_permutation" | "param_perturbation" | "data_noise"
    param_noise_pct: float = 10.0     # % perturbation for param method
    data_noise_std: float = 0.001     # std for data noise injection
    confidence_levels: list[float] = field(default_factory=lambda: [0.05, 0.25, 0.50, 0.75, 0.95])
    seed: int = 42


@dataclass
class MonteCarloResult:
    """Aggregate statistics from Monte Carlo runs."""
    n_simulations: int = 0
    method: str = ""
    # Distribution of final equity
    median_equity: float = 0.0
    mean_equity: float = 0.0
    std_equity: float = 0.0
    percentiles: dict[str, float] = field(default_factory=dict)
    # Risk metrics
    prob_profit: float = 0.0           # P(final equity > initial)
    prob_ruin: float = 0.0             # P(equity < 50% of initial at any point)
    worst_case_equity: float = 0.0
    best_case_equity: float = 0.0
    # Distribution of max drawdown
    median_max_dd: float = 0.0
    p95_max_dd: float = 0.0
    # Sharpe distribution
    median_sharpe: float = 0.0
    p5_sharpe: float = 0.0
    # Full paths for visualization (downsampled)
    equity_paths: list[list[float]] = field(default_factory=list)
    final_equities: list[float] = field(default_factory=list)
    max_drawdowns: list[float] = field(default_factory=list)


class MonteCarloEngine:
    """
    Monte Carlo simulation engine.
    
    Trade Permutation method:
    - Takes the trade P&L sequence from a completed backtest
    - Randomly shuffles the order of trades
    - Reconstructs equity curves
    - This reveals: path dependency, drawdown risk, ruin probability
    
    Parameter Perturbation method:
    - Takes optimal parameters
    - Adds Gaussian noise (% of value)
    - Re-runs full backtest with noisy params
    - This reveals: parameter sensitivity, overfitting risk
    """

    def __init__(
        self,
        config: MonteCarloConfig,
    ) -> None:
        self.config = config
        self._rng = np.random.default_rng(config.seed)

    def run_trade_permutation(
        self,
        backtest_result: BacktestResult,
        initial_capital: float = 100_000.0,
    ) -> MonteCarloResult:
        """
        Shuffle trade P&L order and reconstruct equity curves.
        Fast method — doesn't re-run backtests.
        """
        logger.info(f"Running Monte Carlo trade permutation: {self.config.n_simulations} sims")

        pnls = [t["pnl"] for t in backtest_result.trade_log]
        if not pnls:
            return MonteCarloResult()

        result = MonteCarloResult(
            n_simulations=self.config.n_simulations,
            method="trade_permutation",
        )

        paths: list[list[float]] = []
        finals: list[float] = []
        max_dds: list[float] = []

        for sim in range(self.config.n_simulations):
            # Shuffle trade order
            shuffled = self._rng.permutation(pnls).tolist()

            # Reconstruct equity curve
            equity = initial_capital
            peak = equity
            max_dd = 0.0
            path = [equity]

            for pnl in shuffled:
                equity += pnl
                peak = max(peak, equity)
                dd = (peak - equity) / peak * 100 if peak > 0 else 0
                max_dd = max(max_dd, dd)
                path.append(equity)

            paths.append(path)
            finals.append(equity)
            max_dds.append(max_dd)

        # Compute statistics
        finals_arr = np.array(finals)
        dd_arr = np.array(max_dds)

        result.mean_equity = float(np.mean(finals_arr))
        result.median_equity = float(np.median(finals_arr))
        result.std_equity = float(np.std(finals_arr))
        result.worst_case_equity = float(np.min(finals_arr))
        result.best_case_equity = float(np.max(finals_arr))
        result.prob_profit = float(np.mean(finals_arr > initial_capital))
        result.prob_ruin = float(np.mean(finals_arr < initial_capital * 0.5))

        for cl in self.config.confidence_levels:
            pct = float(np.percentile(finals_arr, cl * 100))
            result.percentiles[f"p{int(cl*100)}"] = round(pct, 0)

        result.median_max_dd = float(np.median(dd_arr))
        result.p95_max_dd = float(np.percentile(dd_arr, 95))

        # Downsample paths for visualization (max 100 paths, max 100 points each)
        sample_count = min(100, len(paths))
        sample_indices = self._rng.choice(len(paths), sample_count, replace=False)
        for idx in sample_indices:
            path = paths[idx]
            if len(path) > 100:
                step = len(path) // 100
                path = path[::step]
            result.equity_paths.append(path)

        result.final_equities = finals
        result.max_drawdowns = max_dds

        logger.info(
            f"MC complete: median={result.median_equity:.0f} "
            f"P(profit)={result.prob_profit:.1%} "
            f"P95 DD={result.p95_max_dd:.1f}%"
        )

        return result

    def run_parameter_perturbation(
        self,
        strategy_class: type[BaseStrategy],
        base_config: BacktestConfig,
        optimal_params: dict[str, Any],
        tick_data: list[Tick],
    ) -> MonteCarloResult:
        """
        Perturb optimal parameters and re-run backtests.
        Expensive but reveals overfitting risk.
        """
        logger.info(f"Running MC parameter perturbation: {self.config.n_simulations} sims")

        result = MonteCarloResult(
            n_simulations=self.config.n_simulations,
            method="param_perturbation",
        )

        finals: list[float] = []
        max_dds: list[float] = []
        sharpes: list[float] = []

        for sim in range(self.config.n_simulations):
            # Perturb parameters
            noisy_params = {}
            for key, value in optimal_params.items():
                if isinstance(value, (int, float)):
                    noise = self._rng.normal(0, abs(value) * self.config.param_noise_pct / 100)
                    noisy_value = value + noise
                    noisy_params[key] = type(value)(max(0, noisy_value)) if isinstance(value, int) else noisy_value
                else:
                    noisy_params[key] = value

            # Run backtest with noisy params
            strategy = strategy_class(params=noisy_params)
            config = BacktestConfig(
                strategy_name=f"MC_sim_{sim}",
                symbol=base_config.symbol,
                timeframe=base_config.timeframe,
                start_date=base_config.start_date,
                end_date=base_config.end_date,
                initial_capital=base_config.initial_capital,
                leverage=base_config.leverage,
                spread_model=base_config.spread_model,
                avg_spread_points=base_config.avg_spread_points,
                slippage_model=base_config.slippage_model,
                max_slippage_points=base_config.max_slippage_points,
                latency_ms=base_config.latency_ms,
                commission_per_lot=base_config.commission_per_lot,
                max_risk_per_trade_pct=base_config.max_risk_per_trade_pct,
                max_daily_dd_pct=base_config.max_daily_dd_pct,
                max_total_dd_pct=base_config.max_total_dd_pct,
                max_concurrent_trades=base_config.max_concurrent_trades,
                strategy_params=noisy_params,
            )

            engine = BacktestEngine(config, strategy)
            bt_result = engine.run(tick_data)

            final_eq = base_config.initial_capital + bt_result.total_pnl
            finals.append(final_eq)
            max_dds.append(bt_result.max_drawdown_pct)
            sharpes.append(bt_result.sharpe_ratio)

            if sim % 50 == 0:
                logger.info(f"MC param perturbation: {sim}/{self.config.n_simulations}")

        # Statistics
        finals_arr = np.array(finals)
        result.mean_equity = float(np.mean(finals_arr))
        result.median_equity = float(np.median(finals_arr))
        result.std_equity = float(np.std(finals_arr))
        result.prob_profit = float(np.mean(finals_arr > base_config.initial_capital))
        result.worst_case_equity = float(np.min(finals_arr))
        result.best_case_equity = float(np.max(finals_arr))
        result.median_max_dd = float(np.median(max_dds))
        result.p95_max_dd = float(np.percentile(max_dds, 95))
        result.median_sharpe = float(np.median(sharpes))
        result.p5_sharpe = float(np.percentile(sharpes, 5))
        result.final_equities = finals
        result.max_drawdowns = max_dds

        for cl in self.config.confidence_levels:
            result.percentiles[f"p{int(cl*100)}"] = round(float(np.percentile(finals_arr, cl * 100)), 0)

        return result


# ══════════════════════════════════════════════════════════════
# WALK-FORWARD ANALYSIS
# ══════════════════════════════════════════════════════════════

@dataclass
class WalkForwardConfig:
    n_windows: int = 12
    is_ratio: float = 0.70           # In-Sample portion
    anchored: bool = False            # True = expanding window, False = rolling
    min_trades_per_window: int = 15
    optimization_trials: int = 50     # Trials per IS optimization


@dataclass
class WFWindowResult:
    window: int
    is_start_idx: int
    is_end_idx: int
    oos_start_idx: int
    oos_end_idx: int
    is_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    is_return: float = 0.0
    oos_return: float = 0.0
    is_pf: float = 0.0
    oos_pf: float = 0.0
    is_trades: int = 0
    oos_trades: int = 0
    best_params: dict = field(default_factory=dict)
    efficiency: float = 0.0   # OOS_return / IS_return
    is_robust: bool = False


@dataclass
class WalkForwardResult:
    windows: list[WFWindowResult] = field(default_factory=list)
    avg_oos_sharpe: float = 0.0
    avg_efficiency: float = 0.0
    robust_windows: int = 0
    total_windows: int = 0
    robustness_score: float = 0.0  # % of windows that are robust


class WalkForwardEngine:
    """
    Walk-Forward Analysis engine.
    
    Process:
    1. Divide data into N overlapping IS/OOS windows
    2. For each window:
       a. Optimize parameters on IS data
       b. Test optimized params on OOS data
       c. Compare IS vs OOS performance
    3. Aggregate results to assess overfitting risk
    
    A strategy is "robust" if OOS performance is a reasonable
    fraction of IS performance across most windows.
    """

    def __init__(
        self,
        strategy_class: type[BaseStrategy],
        base_config: BacktestConfig,
        tick_data: list[Tick],
        param_space: list[Any],
        config: WalkForwardConfig,
    ) -> None:
        self.strategy_class = strategy_class
        self.base_config = base_config
        self.tick_data = tick_data
        self.param_space = param_space
        self.config = config

    def _run_backtest_on_slice(
        self,
        tick_slice: list[Tick],
        params: dict[str, Any],
    ) -> BacktestResult:
        """Run a backtest on a subset of tick data."""
        strategy = self.strategy_class(params=params)
        config = BacktestConfig(
            strategy_name=f"WF_{self.strategy_class.__name__}",
            symbol=self.base_config.symbol,
            timeframe=self.base_config.timeframe,
            initial_capital=self.base_config.initial_capital,
            leverage=self.base_config.leverage,
            spread_model=self.base_config.spread_model,
            avg_spread_points=self.base_config.avg_spread_points,
            slippage_model=self.base_config.slippage_model,
            max_slippage_points=self.base_config.max_slippage_points,
            latency_ms=self.base_config.latency_ms,
            commission_per_lot=self.base_config.commission_per_lot,
            max_risk_per_trade_pct=self.base_config.max_risk_per_trade_pct,
            max_daily_dd_pct=self.base_config.max_daily_dd_pct,
            max_total_dd_pct=self.base_config.max_total_dd_pct,
            max_concurrent_trades=self.base_config.max_concurrent_trades,
            strategy_params=params,
        )
        engine = BacktestEngine(config, strategy)
        return engine.run(tick_slice)

    def _optimize_on_window(self, tick_slice: list[Tick]) -> dict[str, Any]:
        """Run a mini-optimization on an IS window."""
        from optimization.optimizer import (
            StrategyOptimizer, OptimizationConfig,
        )

        optim_config = OptimizationConfig(
            n_trials=self.config.optimization_trials,
            param_space=self.param_space,
            mode="single",
            min_trades=self.config.min_trades_per_window,
            seed=42,
        )

        optimizer = StrategyOptimizer(
            strategy_class=self.strategy_class,
            base_config=self.base_config,
            tick_data=tick_slice,
            optim_config=optim_config,
        )
        results = optimizer.run()

        if optimizer.best:
            return optimizer.best.params
        return {}

    def run(self) -> WalkForwardResult:
        """Execute walk-forward analysis."""
        n = len(self.tick_data)
        n_windows = self.config.n_windows

        # Calculate window sizes
        total_window = n // n_windows
        is_size = int(total_window * self.config.is_ratio)
        oos_size = total_window - is_size

        logger.info(
            f"Walk-Forward: {n_windows} windows | "
            f"IS={is_size} ticks | OOS={oos_size} ticks | "
            f"Total={n} ticks"
        )

        result = WalkForwardResult(total_windows=n_windows)

        for w in range(n_windows):
            logger.info(f"Processing window {w+1}/{n_windows}")

            if self.config.anchored:
                is_start = 0
            else:
                is_start = w * oos_size  # Rolling

            is_end = is_start + is_size
            oos_start = is_end
            oos_end = min(oos_start + oos_size, n)

            if oos_end > n:
                break

            is_ticks = self.tick_data[is_start:is_end]
            oos_ticks = self.tick_data[oos_start:oos_end]

            # 1. Optimize on IS
            best_params = self._optimize_on_window(is_ticks)

            if not best_params:
                logger.warning(f"Window {w+1}: optimization failed, skipping")
                continue

            # 2. Test on IS with best params (for comparison)
            is_result = self._run_backtest_on_slice(is_ticks, best_params)

            # 3. Test on OOS with same params
            oos_result = self._run_backtest_on_slice(oos_ticks, best_params)

            # 4. Compute efficiency
            efficiency = 0.0
            if is_result.total_return_pct != 0:
                efficiency = oos_result.total_return_pct / is_result.total_return_pct * 100

            is_robust = (
                oos_result.total_return_pct > 0
                and abs(efficiency) > 30  # OOS captures > 30% of IS
                and oos_result.sharpe_ratio > 0
            )

            window_result = WFWindowResult(
                window=w + 1,
                is_start_idx=is_start,
                is_end_idx=is_end,
                oos_start_idx=oos_start,
                oos_end_idx=oos_end,
                is_sharpe=is_result.sharpe_ratio,
                oos_sharpe=oos_result.sharpe_ratio,
                is_return=is_result.total_return_pct,
                oos_return=oos_result.total_return_pct,
                is_pf=is_result.profit_factor,
                oos_pf=oos_result.profit_factor,
                is_trades=is_result.total_trades,
                oos_trades=oos_result.total_trades,
                best_params=best_params,
                efficiency=round(efficiency, 1),
                is_robust=is_robust,
            )

            result.windows.append(window_result)
            if is_robust:
                result.robust_windows += 1

        # Aggregate
        if result.windows:
            result.avg_oos_sharpe = round(
                np.mean([w.oos_sharpe for w in result.windows]), 2
            )
            efficiencies = [w.efficiency for w in result.windows if w.is_return != 0]
            result.avg_efficiency = round(np.mean(efficiencies), 1) if efficiencies else 0
            result.robustness_score = round(
                result.robust_windows / len(result.windows) * 100, 1
            )

        logger.info(
            f"Walk-Forward complete: {result.robust_windows}/{len(result.windows)} robust | "
            f"Avg OOS Sharpe={result.avg_oos_sharpe} | "
            f"Robustness={result.robustness_score}%"
        )

        return result


# ══════════════════════════════════════════════════════════════
# STRESS TESTING
# ══════════════════════════════════════════════════════════════

@dataclass
class StressScenario:
    name: str
    description: str
    spread_multiplier: float = 1.0
    slippage_multiplier: float = 1.0
    price_shock_pct: float = 0.0      # sudden move
    gap_points: float = 0.0           # weekend gap
    volatility_multiplier: float = 1.0


@dataclass
class StressResult:
    scenario: StressScenario
    pnl: float = 0.0
    max_dd_pct: float = 0.0
    trades: int = 0
    sharpe: float = 0.0
    status: str = "PASS"  # PASS | CAUTION | FAIL


# Pre-built scenarios for gold trading
STRESS_SCENARIOS = [
    StressScenario("Flash Crash", "Gold drops 5% in 30 min", spread_multiplier=5, slippage_multiplier=3, price_shock_pct=-5),
    StressScenario("High Vol Regime", "VIX>35, spreads x3", spread_multiplier=3, volatility_multiplier=2),
    StressScenario("Weekend Gap", "Monday open gap 200pts", gap_points=200),
    StressScenario("Liquidity Drought", "Spread x5, slippage x3", spread_multiplier=5, slippage_multiplier=3),
    StressScenario("NFP Spike", "Instant volatility on news", spread_multiplier=4, slippage_multiplier=2, volatility_multiplier=3),
    StressScenario("Prolonged Range", "Low volatility, whipsaws", volatility_multiplier=0.3),
]


def run_stress_tests(
    strategy_class: type[BaseStrategy],
    base_config: BacktestConfig,
    tick_data: list[Tick],
    params: dict[str, Any],
    scenarios: list[StressScenario] | None = None,
) -> list[StressResult]:
    """Run the strategy through multiple stress scenarios."""
    if scenarios is None:
        scenarios = STRESS_SCENARIOS

    results = []
    for scenario in scenarios:
        logger.info(f"Stress test: {scenario.name}")

        # Modify config for stress conditions
        stressed_config = BacktestConfig(
            strategy_name=f"STRESS_{scenario.name}",
            symbol=base_config.symbol,
            timeframe=base_config.timeframe,
            initial_capital=base_config.initial_capital,
            leverage=base_config.leverage,
            spread_model=base_config.spread_model,
            avg_spread_points=base_config.avg_spread_points * scenario.spread_multiplier,
            slippage_model=base_config.slippage_model,
            max_slippage_points=base_config.max_slippage_points * scenario.slippage_multiplier,
            latency_ms=base_config.latency_ms,
            commission_per_lot=base_config.commission_per_lot,
            max_risk_per_trade_pct=base_config.max_risk_per_trade_pct,
            max_daily_dd_pct=base_config.max_daily_dd_pct,
            max_total_dd_pct=base_config.max_total_dd_pct,
            max_concurrent_trades=base_config.max_concurrent_trades,
            strategy_params=params,
        )

        strategy = strategy_class(params=params)
        engine = BacktestEngine(stressed_config, strategy)
        bt_result = engine.run(tick_data)

        # Determine status
        status = "PASS"
        if bt_result.max_drawdown_pct > base_config.max_total_dd_pct:
            status = "FAIL"
        elif bt_result.max_drawdown_pct > base_config.max_total_dd_pct * 0.7:
            status = "CAUTION"

        results.append(StressResult(
            scenario=scenario,
            pnl=bt_result.total_pnl,
            max_dd_pct=bt_result.max_drawdown_pct,
            trades=bt_result.total_trades,
            sharpe=bt_result.sharpe_ratio,
            status=status,
        ))

    return results
