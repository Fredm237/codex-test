"""
SmartWave v3 — Full Pipeline
==============================
The complete system: generate → test → validate → rank.

This is the PRODUCTION pipeline that runs end-to-end:
  1. Generate market data (or load real data)
  2. Pre-compute indicators ONCE
  3. Generate strategy variations (parameter space exploration)
  4. Fast backtest ALL strategies (Numba-accelerated)
  5. Filter: minimum criteria
  6. Deep validation: Monte Carlo + Deflated Sharpe
  7. Rank by composite score
  8. Walk-Forward on top candidates
  9. Export results

Architecture:
  Data → Indicators (once) → [Strategy DNA → Signal Array → fast_backtest()] × N → Validate → Rank
"""

from __future__ import annotations

import logging
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Any
from concurrent.futures import ProcessPoolExecutor, as_completed

from core.engine_fast import (
    precompute_indicators, fast_backtest,
    signal_ema_cross, signal_fvg_ob, signal_breakout,
    signal_mean_reversion, signal_asian_breakout,
)
from core.validation import (
    compute_metrics, deflated_sharpe, monte_carlo_permutation,
    walk_forward, composite_score, detect_regime, Metrics,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("smartwave.pipeline")


# ══════════════════════════════════════════════════════════════
# MARKET DATA GENERATOR
# ══════════════════════════════════════════════════════════════

def generate_market_data(symbol: str = "XAUUSD", days: int = 180,
                         seed: int = 42) -> dict[str, np.ndarray]:
    """
    Generate realistic M5 OHLCV data.
    In production: replace with real data loader (MT5 CSV, Dukascopy, etc.)
    """
    rng = np.random.default_rng(seed)
    cfg = {
        "XAUUSD": {"price": 2650.0, "vol": 0.18, "spread_pts": 25},
        "EURUSD": {"price": 1.085, "vol": 0.09, "spread_pts": 12},
        "BTCUSD": {"price": 85000.0, "vol": 0.45, "spread_pts": 800},
    }
    c = cfg.get(symbol, cfg["XAUUSD"])
    bars_per_day = 288  # M5
    price = c["price"]

    # Pre-allocate arrays
    max_bars = days * bars_per_day
    O = np.empty(max_bars, dtype=np.float64)
    H = np.empty(max_bars, dtype=np.float64)
    L = np.empty(max_bars, dtype=np.float64)
    C = np.empty(max_bars, dtype=np.float64)
    V = np.empty(max_bars, dtype=np.float64)
    SP = np.empty(max_bars, dtype=np.float64)
    HOUR = np.empty(max_bars, dtype=np.float64)

    idx = 0
    from datetime import datetime, timedelta
    dt = datetime(2025, 1, 2)

    for d in range(days):
        day = dt + timedelta(days=d)
        if day.weekday() >= 5:  # Skip weekends
            continue
        for b in range(bars_per_day):
            hour = b * 5 // 60
            vol_mult = 1.3 if 7 <= hour < 16 else (1.0 if 16 <= hour < 20 else 0.6)
            ret = (rng.standard_normal() * c["vol"] / np.sqrt(252 * bars_per_day)
                   * vol_mult * 1.5)

            o = price
            price *= (1 + ret)
            noise = rng.standard_normal(2) * abs(ret) * o * 0.5
            h = max(o, price) + abs(noise[0])
            l = min(o, price) - abs(noise[1])

            sp_mult = 1.4 if hour < 7 else (0.7 if 12 <= hour < 16 else (1.8 if hour >= 20 else 1.0))
            sp = c["spread_pts"] * sp_mult * (0.7 + rng.random() * 0.6) * 0.01

            O[idx] = o
            H[idx] = h
            L[idx] = l
            C[idx] = price
            V[idx] = rng.exponential(300) * vol_mult
            SP[idx] = sp
            HOUR[idx] = hour
            idx += 1

    # Trim to actual size
    O, H, L, C, V, SP, HOUR = O[:idx], H[:idx], L[:idx], C[:idx], V[:idx], SP[:idx], HOUR[:idx]

    logger.info(f"Market data: {symbol} | {idx:,} bars ({idx // bars_per_day} days) | "
                f"Price range: {C.min():.2f} - {C.max():.2f}")

    return {"O": O, "H": H, "L": L, "C": C, "V": V, "spread": SP, "hour": HOUR}


# ══════════════════════════════════════════════════════════════
# STRATEGY DNA — Defines what to test
# ══════════════════════════════════════════════════════════════

@dataclass
class StrategyDNA:
    id: str = ""
    name: str = ""
    signal_type: str = ""     # "ema_cross", "fvg_ob", "breakout", "mean_rev", "asian"
    params: dict[str, Any] = field(default_factory=dict)
    category: str = ""
    complexity: str = ""
    metrics: Metrics = field(default_factory=Metrics)


# ══════════════════════════════════════════════════════════════
# STRATEGY FACTORY — Generate signal arrays from DNA
# ══════════════════════════════════════════════════════════════

def generate_signals(dna: StrategyDNA, data: dict, indicators: dict,
                     capital: float = 100000) -> tuple:
    """Convert a StrategyDNA into signal/SL/TP/lot arrays."""
    p = dna.params
    C = data["C"]
    H = data["H"]
    L = data["L"]
    O = data["O"]
    hours = data["hour"]
    atr = indicators.get(f"atr{p.get('atr_period', 14)}", indicators["atr14"])
    ss, se = p.get("session_start", 7), p.get("session_end", 20)

    if dna.signal_type == "ema_cross":
        ema_f = indicators.get(f"ema{p.get('ema_fast', 8)}", indicators["ema8"])
        ema_s = indicators.get(f"ema{p.get('ema_slow', 34)}", indicators["ema34"])
        return signal_ema_cross(C, ema_f, ema_s, atr, p.get("rr", 2.0),
                                hours, ss, se, p.get("risk_pct", 1.0), capital)

    elif dna.signal_type == "fvg_ob":
        ema_f = indicators.get(f"ema{p.get('ema_fast', 21)}", indicators["ema21"])
        ema_s = indicators.get(f"ema{p.get('ema_slow', 50)}", indicators["ema50"])
        return signal_fvg_ob(C, H, L, O, ema_f, ema_s, atr, hours,
                             p.get("rr", 2.5), p.get("fvg_min", 0.5),
                             ss, se, p.get("risk_pct", 1.0), capital,
                             p.get("cooldown", 5))

    elif dna.signal_type == "breakout":
        ema_t = indicators.get(f"ema{p.get('ema_trend', 50)}", indicators["ema50"])
        return signal_breakout(C, H, L, atr, ema_t, hours,
                               p.get("period", 20), p.get("atr_mult", 1.5),
                               p.get("rr", 2.0), ss, se, p.get("risk_pct", 1.0),
                               capital, p.get("cooldown", 10))

    elif dna.signal_type == "mean_rev":
        return signal_mean_reversion(C, indicators["bb_upper"], indicators["bb_lower"],
                                     indicators["bb_mid"], indicators["rsi14"], atr,
                                     hours, p.get("rsi_ob", 70), p.get("rsi_os", 30),
                                     ss, se, p.get("risk_pct", 1.0), capital,
                                     p.get("cooldown", 10))

    elif dna.signal_type == "asian":
        ema_t = indicators.get(f"ema{p.get('ema_trend', 50)}", indicators["ema50"])
        return signal_asian_breakout(C, H, L, ema_t, atr, hours,
                                     p.get("rr", 2.0), p.get("risk_pct", 1.0),
                                     capital, p.get("cooldown", 5))

    else:
        n = len(C)
        return (np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n))


# ══════════════════════════════════════════════════════════════
# STRATEGY LIBRARY — Proven patterns + variations
# ══════════════════════════════════════════════════════════════

def generate_strategy_population(seed: int = 42) -> list[StrategyDNA]:
    """
    Generate a diverse population of strategies.
    Each base pattern gets multiple parameter variations.
    
    This is NOT random indicator combination (StrategyQuant).
    These are structured patterns with systematic parameter exploration.
    """
    rng = np.random.default_rng(seed)
    population = []
    idx = 0

    def add_variations(base_name, signal_type, base_params, category, complexity, n_vars=5):
        nonlocal idx
        # Add base
        population.append(StrategyDNA(
            id=f"S{idx:04d}", name=base_name, signal_type=signal_type,
            params=dict(base_params), category=category, complexity=complexity))
        idx += 1
        # Add variations
        for v in range(n_vars):
            varied_params = {}
            for k, val in base_params.items():
                if isinstance(val, int):
                    noise = int(val * 0.2 * rng.standard_normal())
                    varied_params[k] = max(1, val + noise)
                elif isinstance(val, float):
                    noise = val * 0.2 * rng.standard_normal()
                    varied_params[k] = max(0.01, val + noise)
                else:
                    varied_params[k] = val
            population.append(StrategyDNA(
                id=f"S{idx:04d}", name=f"{base_name} v{v+1}",
                signal_type=signal_type, params=varied_params,
                category=category, complexity=complexity))
            idx += 1

    # ── ICT / Smart Money ──
    add_variations("ICT Unicorn", "fvg_ob",
        {"ema_fast": 21, "ema_slow": 50, "atr_period": 14, "rr": 2.5,
         "fvg_min": 0.5, "risk_pct": 1.0, "session_start": 7,
         "session_end": 20, "cooldown": 5},
        "ICT/SMC", "advanced", n_vars=8)

    add_variations("ICT Sniper", "fvg_ob",
        {"ema_fast": 21, "ema_slow": 50, "atr_period": 14, "rr": 3.5,
         "fvg_min": 0.3, "risk_pct": 0.5, "session_start": 8,
         "session_end": 17, "cooldown": 3},
        "ICT/SMC", "expert", n_vars=5)

    # ── EMA Strategies ──
    for fast, slow in [(8, 34), (13, 50), (21, 100), (8, 21), (13, 34)]:
        add_variations(f"EMA {fast}/{slow}", "ema_cross",
            {"ema_fast": fast, "ema_slow": slow, "atr_period": 14,
             "rr": 2.0, "risk_pct": 1.0, "session_start": 7, "session_end": 20},
            "Indicators", "simple", n_vars=4)

    # ── Breakout ──
    for period in [15, 20, 30, 50]:
        add_variations(f"Breakout {period}", "breakout",
            {"period": period, "atr_mult": 1.5, "ema_trend": 50,
             "atr_period": 14, "rr": 2.0, "risk_pct": 1.0,
             "session_start": 7, "session_end": 20, "cooldown": 10},
            "PriceAction", "intermediate", n_vars=4)

    # ── Mean Reversion ──
    add_variations("Mean Rev BB", "mean_rev",
        {"rsi_ob": 70, "rsi_os": 30, "atr_period": 14, "risk_pct": 1.0,
         "session_start": 7, "session_end": 20, "cooldown": 10},
        "Indicators", "intermediate", n_vars=6)

    add_variations("Mean Rev Extreme", "mean_rev",
        {"rsi_ob": 80, "rsi_os": 20, "atr_period": 14, "risk_pct": 0.5,
         "session_start": 0, "session_end": 24, "cooldown": 15},
        "Indicators", "advanced", n_vars=4)

    # ── Asian Range ──
    add_variations("Asian Breakout", "asian",
        {"ema_trend": 50, "atr_period": 14, "rr": 2.0,
         "risk_pct": 1.0, "cooldown": 5},
        "PriceAction", "simple", n_vars=6)

    add_variations("Asian Conservative", "asian",
        {"ema_trend": 100, "atr_period": 14, "rr": 1.5,
         "risk_pct": 0.5, "cooldown": 10},
        "PriceAction", "simple", n_vars=4)

    logger.info(f"Generated {len(population)} strategy candidates")
    return population


# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════

def run_pipeline(
    symbol: str = "XAUUSD",
    days: int = 180,
    capital: float = 100000.0,
    commission: float = 7.0,
    max_dd: float = 10.0,
    min_trades: int = 10,
    min_sharpe: float = -0.5,
    max_dd_filter: float = 20.0,
    mc_sims: int = 500,
    seed: int = 42,
) -> list[StrategyDNA]:
    """
    Run the FULL pipeline end-to-end.
    
    Returns: Ranked list of validated strategies with all metrics.
    """
    t_start = time.perf_counter()

    logger.info("=" * 70)
    logger.info("SMARTWAVE v3 — STRATEGY GENERATION PIPELINE")
    logger.info("=" * 70)

    # ── 1. Generate/load market data ──
    logger.info("Phase 1: Market data...")
    data = generate_market_data(symbol, days, seed)
    n_bars = len(data["C"])

    # ── 2. Pre-compute indicators ONCE ──
    logger.info("Phase 2: Pre-computing indicators (ONCE for all strategies)...")
    t_ind = time.perf_counter()
    indicators = precompute_indicators(data["O"], data["H"], data["L"], data["C"], data["V"])
    dt_ind = time.perf_counter() - t_ind

    # ── 3. Generate strategy population ──
    logger.info("Phase 3: Generating strategy population...")
    population = generate_strategy_population(seed)

    # ── 4. Fast backtest ALL strategies ──
    logger.info(f"Phase 4: Backtesting {len(population)} strategies...")
    t_bt = time.perf_counter()

    valid_strategies = []
    rejected = 0
    total_tested = len(population)

    for i, dna in enumerate(population):
        try:
            # Generate signals
            signals, sl_dist, tp_dist, lot_sizes = generate_signals(
                dna, data, indicators, capital)

            # Run fast backtest
            (balance, eq_curve, trade_pnls, n_trades, max_dd_pct,
             total_comm, wins, losses) = fast_backtest(
                data["O"], data["H"], data["L"], data["C"], data["spread"],
                signals, sl_dist, tp_dist, lot_sizes,
                capital=capital, commission_per_lot=commission,
                max_dd_pct=max_dd, max_positions=3)

            # ── 5. Quick filter (BEFORE expensive analysis) ──
            if n_trades < min_trades:
                rejected += 1
                continue

            # Compute metrics
            m = compute_metrics(trade_pnls, eq_curve, capital, wins, losses,
                                max_dd_pct, total_comm)

            if m.sharpe < min_sharpe or m.max_dd_pct > max_dd_filter:
                rejected += 1
                continue

            dna.metrics = m
            valid_strategies.append(dna)

        except Exception as e:
            rejected += 1
            if rejected <= 3:
                logger.warning(f"Error on {dna.name}: {e}")

        if (i + 1) % 20 == 0:
            logger.info(f"  Tested {i+1}/{total_tested} | Valid: {len(valid_strategies)} | Rejected: {rejected}")

    dt_bt = time.perf_counter() - t_bt
    logger.info(f"  Backtesting complete: {dt_bt:.2f}s | {total_tested/dt_bt:.0f} strategies/sec")
    logger.info(f"  Valid: {len(valid_strategies)} | Rejected: {rejected}")

    if not valid_strategies:
        logger.warning("No valid strategies found. Try relaxing filters.")
        return []

    # ── 6. Deep validation on valid strategies ──
    logger.info(f"Phase 5: Deep validation on {len(valid_strategies)} strategies...")
    t_val = time.perf_counter()

    for dna in valid_strategies:
        m = dna.metrics
        trade_pnls = np.array([t for t in range(m.total_trades)])  # placeholder

        # Re-run to get trade_pnls for MC
        signals, sl_dist, tp_dist, lot_sizes = generate_signals(
            dna, data, indicators, capital)
        (_, eq, pnls, nt, dd, comm, w, l) = fast_backtest(
            data["O"], data["H"], data["L"], data["C"], data["spread"],
            signals, sl_dist, tp_dist, lot_sizes,
            capital=capital, commission_per_lot=commission,
            max_dd_pct=max_dd, max_positions=3)

        # Monte Carlo
        if len(pnls) >= 5:
            _, _, prob_p, median, p5, p95, p95dd = monte_carlo_permutation(
                pnls, capital, n_sims=mc_sims, seed=seed)
            m.mc_prob_profit = round(prob_p, 3)
            m.mc_p95_dd = round(p95dd, 1)
            m.mc_median_equity = round(median, 0)

        # Deflated Sharpe
        m.deflated_sharpe = deflated_sharpe(
            m.sharpe, total_tested, n_bars // 288,
            skew=0.0, kurtosis_excess=0.0)

        # Composite score
        m.composite_score = composite_score(m, total_tested)

    dt_val = time.perf_counter() - t_val
    logger.info(f"  Validation complete: {dt_val:.2f}s")

    # ── 7. Rank ──
    valid_strategies.sort(key=lambda d: d.metrics.composite_score, reverse=True)

    # ── 8. Walk-Forward on top 5 ──
    logger.info("Phase 6: Walk-Forward on top 5...")
    for dna in valid_strategies[:5]:
        def run_slice(start, end):
            sliced_data = {k: v[start:end] for k, v in data.items()}
            sliced_ind = {k: v[start:end] for k, v in indicators.items()}
            sigs, sl, tp, lots = generate_signals(dna, sliced_data, sliced_ind, capital)
            (_, eq, pnls, nt, dd, comm, w, l) = fast_backtest(
                sliced_data["O"], sliced_data["H"], sliced_data["L"],
                sliced_data["C"], sliced_data["spread"],
                sigs, sl, tp, lots, capital=capital,
                commission_per_lot=commission, max_dd_pct=max_dd, max_positions=3)
            return compute_metrics(pnls, eq, capital, w, l, dd, comm)

        wf = walk_forward(run_slice, n_bars, n_windows=6, is_ratio=0.7)
        logger.info(f"  WF {dna.name}: {wf.n_robust}/{wf.n_total} robust | "
                     f"OOS Sharpe={wf.avg_oos_sharpe} | Robustness={wf.robustness_pct}%")

    # ── FINAL REPORT ──
    dt_total = time.perf_counter() - t_start

    logger.info("")
    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total time:       {dt_total:.2f}s")
    logger.info(f"Bars processed:   {n_bars:,}")
    logger.info(f"Strategies tested: {total_tested}")
    logger.info(f"Valid strategies:  {len(valid_strategies)}")
    logger.info(f"Indicators time:  {dt_ind:.3f}s")
    logger.info(f"Backtest time:    {dt_bt:.2f}s ({total_tested/dt_bt:.0f} strats/sec)")
    logger.info(f"Validation time:  {dt_val:.2f}s")
    logger.info("")
    logger.info("TOP 15 STRATEGIES (ranked by composite score)")
    logger.info("-" * 70)
    logger.info(f"{'#':>3} {'Name':<28} {'Score':>6} {'Sharpe':>7} {'DD%':>6} {'PF':>6} "
                f"{'WR%':>5} {'Trades':>6} {'Ret%':>7} {'DSR':>5} {'MC%':>5}")
    logger.info("-" * 70)

    for i, dna in enumerate(valid_strategies[:15]):
        m = dna.metrics
        logger.info(
            f"{i+1:3d} {dna.name:<28} {m.composite_score:6.4f} {m.sharpe:7.2f} "
            f"{m.max_dd_pct:6.1f} {m.profit_factor:6.2f} {m.win_rate:5.1f} "
            f"{m.total_trades:6d} {m.total_return_pct:7.1f} "
            f"{m.deflated_sharpe:5.3f} {m.mc_prob_profit*100:5.1f}")

    if valid_strategies:
        best = valid_strategies[0]
        logger.info("")
        logger.info(f"BEST: {best.name}")
        logger.info(f"  Params: {best.params}")
        logger.info(f"  Sharpe={best.metrics.sharpe} | DD={best.metrics.max_dd_pct}% | "
                     f"PF={best.metrics.profit_factor} | SQN={best.metrics.sqn} | "
                     f"Kelly={best.metrics.kelly*100:.1f}%")
        logger.info(f"  Deflated Sharpe: {best.metrics.deflated_sharpe} "
                     f"(corrected for {total_tested} strategies tested)")
        logger.info(f"  Monte Carlo P(Profit): {best.metrics.mc_prob_profit:.1%}")

    return valid_strategies


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    results = run_pipeline(
        symbol="XAUUSD",
        days=180,
        capital=100000,
        commission=7.0,
        max_dd=10.0,
        min_trades=8,
        min_sharpe=-1.0,
        max_dd_filter=25.0,
        mc_sims=500,
        seed=42,
    )
