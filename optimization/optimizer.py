"""
SmartWave Quant Lab — Optimization Engine
===========================================
Bayesian multi-objective parameter optimization using Optuna.

Supports:
- Single-objective (maximize Sharpe)
- Multi-objective Pareto (Sharpe vs DD vs PF)
- Custom composite scoring
- Parallel execution via Optuna's distributed storage
- Parameter importance analysis

Architecture:
  OptimizerConfig → Optuna Study → [Trial] → BacktestEngine → Metrics → Pruning/Selection
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import numpy as np

try:
    import optuna
    from optuna.samplers import TPESampler, NSGAIISampler
    from optuna.pruners import MedianPruner, HyperbandPruner
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

from core.models import BacktestConfig, BacktestResult, Tick
from core.engine import BacktestEngine
from strategies.strategies import BaseStrategy

logger = logging.getLogger("smartwave.optimization")


# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

@dataclass
class ParameterSpace:
    """Defines the search space for a single parameter."""
    name: str
    param_type: str  # "int" | "float" | "categorical"
    low: float = 0.0
    high: float = 100.0
    step: float = 1.0
    choices: list[Any] = field(default_factory=list)
    log_scale: bool = False


@dataclass
class OptimizationConfig:
    """Full optimization configuration."""
    # Search
    n_trials: int = 200
    timeout_seconds: int = 3600
    param_space: list[ParameterSpace] = field(default_factory=list)
    # Objectives
    mode: str = "single"  # "single" | "multi"
    primary_metric: str = "sharpe_ratio"
    secondary_metrics: list[str] = field(default_factory=lambda: ["max_drawdown_pct", "profit_factor"])
    direction: str = "maximize"  # for primary metric
    # Composite score weights (for single-objective mode)
    score_weights: dict[str, float] = field(default_factory=lambda: {
        "sharpe_ratio": 0.35,
        "profit_factor": 0.20,
        "max_drawdown_pct": 0.25,  # inverted: lower = better
        "win_rate": 0.10,
        "recovery_factor": 0.10,
    })
    # Filtering
    min_trades: int = 30
    max_drawdown_limit: float = 20.0
    min_profit_factor: float = 1.0
    # Execution
    n_jobs: int = 1
    sampler: str = "tpe"  # "tpe" | "nsga2" | "random"
    pruner: str = "median"  # "median" | "hyperband" | "none"
    seed: int = 42


# ══════════════════════════════════════════════════════════════
# TRIAL RESULT
# ══════════════════════════════════════════════════════════════

@dataclass
class TrialResult:
    trial_number: int
    params: dict[str, Any]
    metrics: dict[str, float]
    score: float = 0.0
    backtest_result: Optional[BacktestResult] = None
    is_feasible: bool = True
    rejection_reason: str = ""


# ══════════════════════════════════════════════════════════════
# OPTIMIZER
# ══════════════════════════════════════════════════════════════

class StrategyOptimizer:
    """
    Bayesian optimization wrapper around Optuna.
    
    Usage:
        optimizer = StrategyOptimizer(
            strategy_class=ICTUnicornPro,
            base_config=BacktestConfig(...),
            tick_data=ticks,
            optim_config=OptimizationConfig(
                param_space=[
                    ParameterSpace("atr_period", "int", 5, 50, 1),
                    ParameterSpace("rr_ratio", "float", 1.0, 5.0, 0.1),
                ],
                n_trials=200,
            ),
        )
        results = optimizer.run()
    """

    def __init__(
        self,
        strategy_class: type[BaseStrategy],
        base_config: BacktestConfig,
        tick_data: list[Tick],
        optim_config: OptimizationConfig,
    ) -> None:
        if not HAS_OPTUNA:
            raise ImportError("Optuna is required: pip install optuna")

        self.strategy_class = strategy_class
        self.base_config = base_config
        self.tick_data = tick_data
        self.config = optim_config
        self.results: list[TrialResult] = []
        self._study: Optional[optuna.Study] = None
        self._best_result: Optional[TrialResult] = None

    def _build_sampler(self) -> Any:
        if self.config.sampler == "tpe":
            return TPESampler(seed=self.config.seed, multivariate=True)
        elif self.config.sampler == "nsga2":
            return NSGAIISampler(seed=self.config.seed)
        else:
            return optuna.samplers.RandomSampler(seed=self.config.seed)

    def _build_pruner(self) -> Any:
        if self.config.pruner == "median":
            return MedianPruner(n_startup_trials=10, n_warmup_steps=5)
        elif self.config.pruner == "hyperband":
            return HyperbandPruner()
        return optuna.pruners.NopPruner()

    def _suggest_params(self, trial: optuna.Trial) -> dict[str, Any]:
        """Map parameter space to Optuna trial suggestions."""
        params = {}
        for p in self.config.param_space:
            if p.param_type == "int":
                params[p.name] = trial.suggest_int(p.name, int(p.low), int(p.high), step=int(p.step))
            elif p.param_type == "float":
                params[p.name] = trial.suggest_float(
                    p.name, p.low, p.high,
                    step=p.step if p.step > 0 else None,
                    log=p.log_scale,
                )
            elif p.param_type == "categorical":
                params[p.name] = trial.suggest_categorical(p.name, p.choices)
        return params

    def _compute_composite_score(self, metrics: dict[str, float]) -> float:
        """
        Weighted composite score combining multiple metrics.
        Normalizes each metric to [0, 1] range before weighting.
        """
        score = 0.0
        w = self.config.score_weights

        # Sharpe: typical range [-1, 4] → normalize to [0, 1]
        if "sharpe_ratio" in w:
            norm = max(0, min(1, (metrics.get("sharpe_ratio", 0) + 1) / 5))
            score += w["sharpe_ratio"] * norm

        # Profit Factor: [0, 5] → [0, 1]
        if "profit_factor" in w:
            pf = metrics.get("profit_factor", 0)
            norm = max(0, min(1, pf / 5))
            score += w["profit_factor"] * norm

        # Max DD: inverted (lower = better), [0, 50] → [0, 1]
        if "max_drawdown_pct" in w:
            dd = metrics.get("max_drawdown_pct", 50)
            norm = max(0, min(1, 1 - dd / 50))
            score += w["max_drawdown_pct"] * norm

        # Win Rate: [30, 80] → [0, 1]
        if "win_rate" in w:
            norm = max(0, min(1, (metrics.get("win_rate", 30) - 30) / 50))
            score += w["win_rate"] * norm

        # Recovery Factor: [0, 10] → [0, 1]
        if "recovery_factor" in w:
            norm = max(0, min(1, metrics.get("recovery_factor", 0) / 10))
            score += w["recovery_factor"] * norm

        return round(score, 4)

    def _objective(self, trial: optuna.Trial) -> float | tuple[float, ...]:
        """Single trial objective function."""
        params = self._suggest_params(trial)

        # Build strategy with suggested params
        strategy = self.strategy_class(params=params)

        # Build backtest config with strategy params
        config = BacktestConfig(
            strategy_name=f"{self.strategy_class.__name__}_trial_{trial.number}",
            symbol=self.base_config.symbol,
            timeframe=self.base_config.timeframe,
            start_date=self.base_config.start_date,
            end_date=self.base_config.end_date,
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

        # Run backtest
        engine = BacktestEngine(config, strategy)
        result = engine.run(self.tick_data)

        # Extract metrics
        metrics = {
            "sharpe_ratio": result.sharpe_ratio,
            "profit_factor": result.profit_factor,
            "max_drawdown_pct": result.max_drawdown_pct,
            "win_rate": result.win_rate,
            "total_return_pct": result.total_return_pct,
            "total_trades": result.total_trades,
            "expectancy": result.expectancy,
            "recovery_factor": result.recovery_factor,
            "calmar_ratio": result.calmar_ratio,
            "sortino_ratio": result.sortino_ratio,
        }

        # Feasibility checks
        is_feasible = True
        reason = ""
        if result.total_trades < self.config.min_trades:
            is_feasible = False
            reason = f"Too few trades: {result.total_trades}"
        elif result.max_drawdown_pct > self.config.max_drawdown_limit:
            is_feasible = False
            reason = f"DD too high: {result.max_drawdown_pct:.1f}%"
        elif result.profit_factor < self.config.min_profit_factor:
            is_feasible = False
            reason = f"PF too low: {result.profit_factor:.2f}"

        # Compute score
        score = self._compute_composite_score(metrics) if is_feasible else 0.0

        # Store result
        trial_result = TrialResult(
            trial_number=trial.number,
            params=params,
            metrics=metrics,
            score=score,
            backtest_result=result,
            is_feasible=is_feasible,
            rejection_reason=reason,
        )
        self.results.append(trial_result)

        # Log progress
        if trial.number % 10 == 0:
            logger.info(
                f"Trial {trial.number}: score={score:.4f} sharpe={metrics['sharpe_ratio']:.2f} "
                f"dd={metrics['max_drawdown_pct']:.1f}% pf={metrics['profit_factor']:.2f} "
                f"trades={metrics['total_trades']}"
            )

        # Return value based on mode
        if self.config.mode == "multi":
            return (
                metrics["sharpe_ratio"],
                -metrics["max_drawdown_pct"],  # negate: lower DD is better
                metrics["profit_factor"],
            )

        return score

    def run(self) -> list[TrialResult]:
        """Execute the optimization."""
        logger.info(
            f"Starting optimization: {self.config.n_trials} trials | "
            f"mode={self.config.mode} | sampler={self.config.sampler}"
        )
        start = time.perf_counter()

        if self.config.mode == "multi":
            self._study = optuna.create_study(
                directions=["maximize", "maximize", "maximize"],
                sampler=NSGAIISampler(seed=self.config.seed),
            )
        else:
            self._study = optuna.create_study(
                direction="maximize",
                sampler=self._build_sampler(),
                pruner=self._build_pruner(),
            )

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        self._study.optimize(
            self._objective,
            n_trials=self.config.n_trials,
            timeout=self.config.timeout_seconds,
            n_jobs=self.config.n_jobs,
            show_progress_bar=True,
        )

        elapsed = time.perf_counter() - start
        logger.info(f"Optimization complete in {elapsed:.1f}s | {len(self.results)} trials evaluated")

        # Sort by score
        self.results.sort(key=lambda r: r.score, reverse=True)
        self._best_result = self.results[0] if self.results else None

        return self.results

    @property
    def best(self) -> Optional[TrialResult]:
        return self._best_result

    @property
    def pareto_front(self) -> list[TrialResult]:
        """Extract Pareto-optimal solutions (for multi-objective)."""
        if not self._study or self.config.mode != "multi":
            return self.results[:10]
        pareto_trials = self._study.best_trials
        pareto_numbers = {t.number for t in pareto_trials}
        return [r for r in self.results if r.trial_number in pareto_numbers]

    def parameter_importance(self) -> dict[str, float]:
        """Compute parameter importance scores using fANOVA."""
        if not self._study or self.config.mode == "multi":
            return {}
        try:
            importance = optuna.importance.get_param_importances(self._study)
            return dict(importance)
        except Exception as e:
            logger.warning(f"Could not compute param importance: {e}")
            return {}

    def to_dataframe(self) -> Any:
        """Export results as a pandas DataFrame."""
        import pandas as pd
        rows = []
        for r in self.results:
            row = {"trial": r.trial_number, "score": r.score, "feasible": r.is_feasible}
            row.update(r.params)
            row.update(r.metrics)
            rows.append(row)
        return pd.DataFrame(rows)
