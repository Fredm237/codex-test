"""
SmartWave v3 — Statistical Validation Engine
==============================================
What separates us from StrategyQuant:
  1. Deflated Sharpe Ratio (corrects for multiple testing)
  2. Monte Carlo with trade permutation
  3. Walk-Forward with integrated optimization
  4. Regime detection (trend vs range)
  5. Equity curve analysis (linearity, stability)
"""

from __future__ import annotations
import numpy as np
from numba import njit
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("smartwave.validation")


# ══════════════════════════════════════════════════════════════
# METRICS COMPUTATION (from raw backtest output)
# ══════════════════════════════════════════════════════════════

@dataclass
class Metrics:
    """Complete performance metrics from a single backtest."""
    total_pnl: float = 0.0
    total_return_pct: float = 0.0
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0
    max_dd_pct: float = 0.0
    max_dd_abs: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    expectancy: float = 0.0
    recovery_factor: float = 0.0
    total_trades: int = 0
    winning: int = 0
    losing: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    max_consec_wins: int = 0
    max_consec_losses: int = 0
    total_commission: float = 0.0
    sqn: float = 0.0                    # System Quality Number
    kelly: float = 0.0                  # Kelly Criterion
    tail_ratio: float = 0.0
    equity_r2: float = 0.0             # Linearity of equity curve
    deflated_sharpe: float = 0.0       # Multiple-testing corrected
    # Monte Carlo
    mc_prob_profit: float = 0.0
    mc_p95_dd: float = 0.0
    mc_median_equity: float = 0.0
    # Composite
    composite_score: float = 0.0


def compute_metrics(trade_pnls: np.ndarray, equity_curve: np.ndarray,
                    capital: float, win_count: int, loss_count: int,
                    max_dd_pct: float, total_comm: float) -> Metrics:
    """Compute all metrics from raw backtest arrays."""
    m = Metrics()
    n = len(trade_pnls)
    m.total_trades = n
    m.winning = win_count
    m.losing = loss_count
    m.total_commission = total_comm
    m.max_dd_pct = round(max_dd_pct, 2)

    if n == 0:
        return m

    m.total_pnl = float(np.sum(trade_pnls))
    m.total_return_pct = round(m.total_pnl / capital * 100, 2)
    m.win_rate = round(win_count / n * 100, 1) if n > 0 else 0
    m.expectancy = round(float(np.mean(trade_pnls)), 2)

    wins = trade_pnls[trade_pnls > 0]
    losses = trade_pnls[trade_pnls <= 0]
    m.avg_win = round(float(np.mean(wins)), 2) if len(wins) > 0 else 0
    m.avg_loss = round(float(np.mean(losses)), 2) if len(losses) > 0 else 0
    m.max_win = round(float(np.max(wins)), 2) if len(wins) > 0 else 0
    m.max_loss = round(float(np.min(losses)), 2) if len(losses) > 0 else 0

    # Profit Factor
    gross_profit = float(np.sum(wins)) if len(wins) > 0 else 0
    gross_loss = abs(float(np.sum(losses))) if len(losses) > 0 else 0
    m.profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0

    # Max DD absolute
    peak = capital
    max_dd_abs = 0.0
    for eq in equity_curve:
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd_abs:
            max_dd_abs = dd
    m.max_dd_abs = round(max_dd_abs, 2)

    # Recovery Factor
    m.recovery_factor = round(m.total_pnl / max_dd_abs, 2) if max_dd_abs > 0 else 0

    # Calmar
    m.calmar = round(m.total_return_pct / m.max_dd_pct, 2) if m.max_dd_pct > 0 else 0

    # Daily returns for Sharpe/Sortino
    # Subsample equity curve to daily (~288 bars per day for M5)
    step = max(1, len(equity_curve) // 252)
    daily_eq = equity_curve[::step]
    if len(daily_eq) > 5:
        daily_ret = np.diff(daily_eq) / daily_eq[:-1]
        daily_ret = daily_ret[np.isfinite(daily_ret)]
        if len(daily_ret) > 3:
            mean_r = float(np.mean(daily_ret))
            std_r = float(np.std(daily_ret))
            if std_r > 0:
                m.sharpe = round(mean_r / std_r * np.sqrt(252), 2)
            down = daily_ret[daily_ret < 0]
            if len(down) > 0:
                ds = float(np.std(down))
                if ds > 0:
                    m.sortino = round(mean_r / ds * np.sqrt(252), 2)

    # Consecutive wins/losses
    m.max_consec_wins = _max_consec(trade_pnls, True)
    m.max_consec_losses = _max_consec(trade_pnls, False)

    # SQN
    if n >= 10:
        std_pnl = float(np.std(trade_pnls))
        if std_pnl > 0:
            m.sqn = round(np.sqrt(n) * float(np.mean(trade_pnls)) / std_pnl, 2)

    # Kelly Criterion
    if m.win_rate > 0 and m.avg_loss != 0 and m.avg_win > 0:
        payoff = abs(m.avg_win / m.avg_loss)
        wr = m.win_rate / 100
        m.kelly = round(max(0, wr - (1 - wr) / payoff), 3)

    # Tail Ratio
    if n >= 20:
        p95 = abs(float(np.percentile(trade_pnls, 95)))
        p5 = abs(float(np.percentile(trade_pnls, 5)))
        m.tail_ratio = round(p95 / p5, 2) if p5 > 0 else 0

    # Equity R²
    if len(equity_curve) > 10:
        x = np.arange(len(equity_curve), dtype=np.float64)
        valid = np.isfinite(equity_curve)
        if np.sum(valid) > 5:
            corr = np.corrcoef(x[valid], equity_curve[valid])[0, 1]
            m.equity_r2 = round(corr ** 2, 3) if np.isfinite(corr) else 0

    return m


def _max_consec(pnls: np.ndarray, positive: bool) -> int:
    mx = cur = 0
    for p in pnls:
        if (positive and p > 0) or (not positive and p <= 0):
            cur += 1
            mx = max(mx, cur)
        else:
            cur = 0
    return mx


# ══════════════════════════════════════════════════════════════
# DEFLATED SHARPE RATIO (Bailey & López de Prado)
# ══════════════════════════════════════════════════════════════

def deflated_sharpe(sharpe_obs: float, n_strategies_tested: int,
                    n_returns: int, skew: float = 0.0,
                    kurtosis_excess: float = 0.0) -> float:
    """
    Correct Sharpe ratio for multiple testing bias.

    When you test N strategies and pick the best, the observed Sharpe
    is biased upward. This returns the probability that the true Sharpe > 0.

    Args:
        sharpe_obs: Observed Sharpe of the best strategy
        n_strategies_tested: How many strategies were tested total
        n_returns: Number of return observations
        skew: Skewness of returns
        kurtosis_excess: Excess kurtosis of returns

    Returns:
        Deflated Sharpe Ratio (0 to 1, higher = more likely genuine)
    """
    from scipy import stats

    if n_strategies_tested <= 1 or n_returns < 10:
        return min(1.0, max(0.0, sharpe_obs / 3.0))

    # Expected max Sharpe under null (all strategies have true Sharpe = 0)
    # Approximation from Bailey & López de Prado (2014)
    euler_mascheroni = 0.5772156649
    e_max = ((1 - euler_mascheroni) * stats.norm.ppf(1 - 1 / n_strategies_tested) +
             euler_mascheroni * stats.norm.ppf(1 - 1 / (n_strategies_tested * np.e)))

    # Standard error of Sharpe
    se_sharpe = np.sqrt((1 + 0.5 * sharpe_obs ** 2 -
                         skew * sharpe_obs +
                         (kurtosis_excess / 4) * sharpe_obs ** 2) / n_returns)

    if se_sharpe <= 0:
        return 0.0

    # Test statistic
    t_stat = (sharpe_obs - e_max) / se_sharpe

    # P(true Sharpe > 0)
    dsr = float(stats.norm.cdf(t_stat))
    return round(max(0.0, min(1.0, dsr)), 3)


# ══════════════════════════════════════════════════════════════
# MONTE CARLO (Numba-accelerated trade permutation)
# ══════════════════════════════════════════════════════════════

@njit(cache=True)
def monte_carlo_permutation(trade_pnls: np.ndarray, capital: float,
                            n_sims: int = 1000, seed: int = 42):
    """
    Monte Carlo trade permutation — Numba-accelerated.
    Shuffles trade order N times, returns statistics.
    
    Returns: (final_equities, max_drawdowns, prob_profit, median_final, p95_dd)
    """
    np.random.seed(seed)
    n = len(trade_pnls)
    finals = np.empty(n_sims, dtype=np.float64)
    max_dds = np.empty(n_sims, dtype=np.float64)

    for sim in range(n_sims):
        # Fisher-Yates shuffle
        shuffled = trade_pnls.copy()
        for j in range(n - 1, 0, -1):
            k = np.random.randint(0, j + 1)
            shuffled[j], shuffled[k] = shuffled[k], shuffled[j]

        eq = capital
        peak = eq
        max_dd = 0.0
        for j in range(n):
            eq += shuffled[j]
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        finals[sim] = eq
        max_dds[sim] = max_dd

    prob_profit = 0.0
    for i in range(n_sims):
        if finals[i] > capital:
            prob_profit += 1.0
    prob_profit /= n_sims

    # Sort for percentiles
    sorted_finals = np.sort(finals)
    sorted_dds = np.sort(max_dds)
    median = sorted_finals[n_sims // 2]
    p5 = sorted_finals[int(n_sims * 0.05)]
    p95 = sorted_finals[int(n_sims * 0.95)]
    p95_dd = sorted_dds[int(n_sims * 0.95)]

    return finals, max_dds, prob_profit, median, p5, p95, p95_dd


# ══════════════════════════════════════════════════════════════
# WALK-FORWARD VALIDATION
# ══════════════════════════════════════════════════════════════

@dataclass
class WFWindow:
    window: int = 0
    is_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    is_return: float = 0.0
    oos_return: float = 0.0
    is_trades: int = 0
    oos_trades: int = 0
    efficiency: float = 0.0
    robust: bool = False


@dataclass
class WFResult:
    windows: list = field(default_factory=list)
    avg_oos_sharpe: float = 0.0
    robustness_pct: float = 0.0
    n_robust: int = 0
    n_total: int = 0


def walk_forward(run_fn, n_bars: int, n_windows: int = 8,
                 is_ratio: float = 0.7) -> WFResult:
    """
    Walk-Forward analysis.
    
    Args:
        run_fn: callable(start_idx, end_idx) -> Metrics
                Runs backtest on a data slice and returns metrics.
        n_bars: Total number of bars
        n_windows: Number of WF windows
        is_ratio: In-Sample portion (0.7 = 70%)
    
    Returns:
        WFResult with per-window and aggregate stats
    """
    window_size = n_bars // n_windows
    is_size = int(window_size * is_ratio)
    oos_size = window_size - is_size
    result = WFResult(n_total=n_windows)

    for w in range(n_windows):
        is_start = w * oos_size  # Rolling
        is_end = is_start + is_size
        oos_start = is_end
        oos_end = min(oos_start + oos_size, n_bars)

        if oos_end > n_bars:
            break

        is_metrics = run_fn(is_start, is_end)
        oos_metrics = run_fn(oos_start, oos_end)

        eff = 0.0
        if is_metrics.total_return_pct != 0:
            eff = oos_metrics.total_return_pct / is_metrics.total_return_pct * 100

        robust = (oos_metrics.total_return_pct > 0 and
                  abs(eff) > 30 and
                  oos_metrics.sharpe > 0)

        wf = WFWindow(
            window=w + 1,
            is_sharpe=is_metrics.sharpe,
            oos_sharpe=oos_metrics.sharpe,
            is_return=is_metrics.total_return_pct,
            oos_return=oos_metrics.total_return_pct,
            is_trades=is_metrics.total_trades,
            oos_trades=oos_metrics.total_trades,
            efficiency=round(eff, 1),
            robust=robust,
        )
        result.windows.append(wf)
        if robust:
            result.n_robust += 1

    if result.windows:
        result.avg_oos_sharpe = round(
            np.mean([w.oos_sharpe for w in result.windows]), 2
        )
        result.robustness_pct = round(
            result.n_robust / len(result.windows) * 100, 1
        )

    return result


# ══════════════════════════════════════════════════════════════
# REGIME DETECTION
# ══════════════════════════════════════════════════════════════

@njit(cache=True)
def detect_regime(close: np.ndarray, atr: np.ndarray, ema_slow: np.ndarray,
                  lookback: int = 50) -> np.ndarray:
    """
    Detect market regime: 1=trending up, -1=trending down, 0=ranging.
    
    Uses: price relative to EMA + ADX-like directional strength.
    """
    n = len(close)
    regime = np.zeros(n, dtype=np.int32)

    for i in range(lookback, n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue

        # Direction: price vs EMA
        diff = (close[i] - ema_slow[i]) / atr[i]

        # Strength: how directional are recent moves
        up_moves = 0.0
        down_moves = 0.0
        for j in range(i - lookback, i):
            d = close[j + 1] - close[j]
            if d > 0:
                up_moves += d
            else:
                down_moves -= d
        total = up_moves + down_moves
        if total == 0:
            continue
        directional_strength = abs(up_moves - down_moves) / total

        if directional_strength > 0.3 and diff > 1.0:
            regime[i] = 1   # Trending up
        elif directional_strength > 0.3 and diff < -1.0:
            regime[i] = -1  # Trending down
        else:
            regime[i] = 0   # Ranging

    return regime


# ══════════════════════════════════════════════════════════════
# COMPOSITE SCORING
# ══════════════════════════════════════════════════════════════

def composite_score(m: Metrics, n_strategies_tested: int = 1) -> float:
    """
    Final composite score incorporating:
    - Performance (Sharpe, PF, return)
    - Risk (DD, consistency)
    - Statistical validity (deflated Sharpe, SQN)
    - Robustness (Monte Carlo, equity linearity)
    """
    score = 0.0

    # ── Performance (40%) ──
    # Sharpe: [-1, 4] → [0, 1]
    s_sharpe = max(0, min(1, (m.sharpe + 1) / 5))
    # PF: [0, 5] → [0, 1]
    s_pf = max(0, min(1, m.profit_factor / 5))
    # Return: [-20, 60] → [0, 1]
    s_ret = max(0, min(1, (m.total_return_pct + 20) / 80))
    score += 0.15 * s_sharpe + 0.13 * s_pf + 0.12 * s_ret

    # ── Risk (25%) ──
    # DD: [0, 50] → [0, 1] (inverted)
    s_dd = max(0, min(1, 1 - m.max_dd_pct / 50))
    # Recovery: [0, 10] → [0, 1]
    s_rec = max(0, min(1, m.recovery_factor / 10))
    score += 0.15 * s_dd + 0.10 * s_rec

    # ── Statistical validity (20%) ──
    # SQN: [-2, 5] → [0, 1]
    s_sqn = max(0, min(1, (m.sqn + 2) / 7))
    # Deflated Sharpe: already [0, 1]
    s_dsr = m.deflated_sharpe
    score += 0.10 * s_sqn + 0.10 * s_dsr

    # ── Robustness (15%) ──
    # MC prob profit: [0, 1]
    s_mc = m.mc_prob_profit
    # Equity linearity: [0, 1]
    s_eq = m.equity_r2
    score += 0.08 * s_mc + 0.07 * s_eq

    return round(score, 4)
