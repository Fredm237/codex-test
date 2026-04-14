"""
SmartWave Quant Lab — Guide Pratique Données Réelles
=====================================================

CE FICHIER EST UN SCRIPT EXÉCUTABLE.
Lance-le directement pour tester tes propres données.

3 MÉTHODES POUR IMPORTER TES DONNÉES :

═══════════════════════════════════════════════════════════════
MÉTHODE 1 : Export CSV depuis MT5 (LE PLUS SIMPLE)
═══════════════════════════════════════════════════════════════

Dans MetaTrader 5 :
  1. Ouvrir le terminal MT5 (Vantage Markets)
  2. Menu : Affichage → Symboles (ou Ctrl+U)
  3. Sélectionner XAUUSD
  4. Onglet "Barres" → choisir la période (M1 ou M5)
  5. Cliquer "Exporter les barres"
  6. Sauvegarder en CSV (par ex. XAUUSD_M5_2024.csv)

Le fichier aura ce format :
  2024.01.02  00:00:00  2071.45  2072.10  2070.80  2071.95  1234  0  25

═══════════════════════════════════════════════════════════════
MÉTHODE 2 : Export tick data depuis MT5
═══════════════════════════════════════════════════════════════

  1. Menu : Affichage → Symboles
  2. Sélectionner XAUUSD
  3. Onglet "Ticks"
  4. Choisir la plage de dates
  5. Exporter → CSV

Format :
  2024.01.02 00:00:00.123  2071.45  2071.70  0  0

═══════════════════════════════════════════════════════════════
MÉTHODE 3 : Dukascopy (données tick gratuites depuis 2003)
═══════════════════════════════════════════════════════════════

  Le module DukascopyDownloader télécharge automatiquement.
  Note : nécessite accès réseau à datafeed.dukascopy.com

═══════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import sys
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("smartwave.guide")


def example_mt5_bars():
    """
    ╔══════════════════════════════════════════════════════╗
    ║  MÉTHODE 1 : MT5 CSV Bars → Backtest complet       ║
    ╚══════════════════════════════════════════════════════╝
    
    Change le chemin ci-dessous vers ton fichier exporté.
    """
    from data.connectors import DataPipeline
    from core.models import BacktestConfig, Timeframe
    from core.engine import BacktestEngine
    from strategies.strategies import ICTUnicornPro, MACrossover

    # ──────────────────────────────────────────────────
    # ⬇️  CHANGE CE CHEMIN VERS TON FICHIER MT5  ⬇️
    # ──────────────────────────────────────────────────
    CSV_FILE = "./data/XAUUSD_M5.csv"
    # ──────────────────────────────────────────────────

    if not os.path.exists(CSV_FILE):
        print(f"\n❌ Fichier non trouvé : {CSV_FILE}")
        print("   Place ton export MT5 CSV à cet emplacement.")
        print("   Ou change la variable CSV_FILE dans ce script.")
        print()
        print("   Format attendu (tab-separated, depuis MT5) :")
        print("   2024.01.02\\t00:00:00\\t2071.45\\t2072.10\\t2070.80\\t2071.95\\t1234\\t0\\t25")
        return

    # 1. Charger et convertir
    pipeline = DataPipeline("XAUUSD")
    ticks = pipeline.from_mt5_csv(
        filepath=CSV_FILE,
        timeframe="M5",          # Timeframe de tes barres
        ticks_per_bar=30,        # 30 ticks synthétisés par barre M5
        spread_points=25.0,      # Spread de base Vantage XAUUSD
        # start_date="2024-06-01",  # Optionnel : filtrer
        # end_date="2024-12-31",
    )

    print(f"\n✅ {len(ticks):,} ticks prêts pour le backtest")

    # 2. Backtest ICT Unicorn Pro
    config = BacktestConfig(
        strategy_name="ICT Unicorn Pro — Real Data",
        symbol="XAUUSD",
        timeframe=Timeframe.M5,
        initial_capital=100_000,
        leverage=100,
        spread_model="dynamic",
        avg_spread_points=25,
        slippage_model="probabilistic",
        max_slippage_points=5,
        commission_per_lot=7.0,
        max_risk_per_trade_pct=1.0,
        max_daily_dd_pct=5.0,
        max_total_dd_pct=10.0,
        max_concurrent_trades=3,
        strategy_params={
            "atr_period": 14,
            "atr_min": 1.5,
            "rr_ratio": 2.5,
            "fvg_min_size": 0.5,
            "ema_fast": 21,
            "ema_slow": 50,
            "risk_pct": 1.0,
            "max_spread_pts": 50,
        },
    )

    strategy = ICTUnicornPro(params=config.strategy_params)
    engine = BacktestEngine(config, strategy)
    result = engine.run(ticks)

    _print_full_results(result)

    # 3. Monte Carlo sur les résultats
    if result.total_trades >= 5:
        from robustness.robustness import MonteCarloEngine, MonteCarloConfig

        mc = MonteCarloEngine(MonteCarloConfig(n_simulations=500, seed=42))
        mc_result = mc.run_trade_permutation(result, 100_000)

        print("\n" + "═" * 60)
        print("MONTE CARLO — 500 simulations")
        print("═" * 60)
        print(f"Median Final:     ${mc_result.median_equity:,.0f}")
        print(f"P(Profit):        {mc_result.prob_profit:.1%}")
        print(f"95th %ile DD:     {mc_result.p95_max_dd:.1f}%")
        print(f"Worst Case:       ${mc_result.worst_case_equity:,.0f}")
        print(f"Best Case:        ${mc_result.best_case_equity:,.0f}")

    return result


def example_mt5_ticks():
    """
    ╔══════════════════════════════════════════════════════╗
    ║  MÉTHODE 2 : MT5 Tick Export → Backtest direct      ║
    ╚══════════════════════════════════════════════════════╝
    
    Si tu as exporté les ticks (bid/ask) depuis MT5.
    C'est le plus réaliste — pas de synthèse nécessaire.
    """
    from data.connectors import MT5CSVImporter
    from core.models import BacktestConfig, Timeframe
    from core.engine import BacktestEngine
    from strategies.strategies import ICTUnicornPro

    # ⬇️  CHANGE CE CHEMIN  ⬇️
    TICK_FILE = "./data/XAUUSD_ticks.csv"

    if not os.path.exists(TICK_FILE):
        print(f"\n❌ Fichier non trouvé : {TICK_FILE}")
        print("   Format attendu (depuis MT5 tick export) :")
        print("   2024.01.02 00:00:00.123\\t2071.45\\t2071.70\\t0\\t0")
        return

    importer = MT5CSVImporter("XAUUSD")
    ticks = importer.import_ticks(TICK_FILE)

    if not ticks:
        print("❌ Aucun tick importé")
        return

    print(f"\n✅ {len(ticks):,} ticks réels importés")

    # Backtest direct — pas de synthèse, données réelles
    config = BacktestConfig(
        strategy_name="ICT Unicorn Pro — Real Ticks",
        symbol="XAUUSD",
        timeframe=Timeframe.M5,
        initial_capital=100_000,
        spread_model="dynamic",
        avg_spread_points=25,
        slippage_model="probabilistic",
        max_slippage_points=5,
        commission_per_lot=7.0,
        strategy_params={
            "atr_period": 14, "rr_ratio": 2.5, "fvg_min_size": 0.5,
            "ema_fast": 21, "ema_slow": 50, "risk_pct": 1.0,
        },
    )

    strategy = ICTUnicornPro(params=config.strategy_params)
    engine = BacktestEngine(config, strategy)
    result = engine.run(ticks)
    _print_full_results(result)
    return result


def example_optimization_real():
    """
    ╔══════════════════════════════════════════════════════╗
    ║  OPTIMISATION sur données réelles                    ║
    ╚══════════════════════════════════════════════════════╝
    """
    from data.connectors import DataPipeline
    from core.models import BacktestConfig, Timeframe
    from strategies.strategies import ICTUnicornPro
    from optimization.optimizer import (
        StrategyOptimizer, OptimizationConfig, ParameterSpace,
    )

    CSV_FILE = "./data/XAUUSD_M5.csv"

    if not os.path.exists(CSV_FILE):
        print(f"\n❌ Fichier non trouvé : {CSV_FILE}")
        return

    # Charger données
    pipeline = DataPipeline("XAUUSD")
    ticks = pipeline.from_mt5_csv(CSV_FILE, timeframe="M5", ticks_per_bar=20)

    # Config de base
    base_config = BacktestConfig(
        symbol="XAUUSD",
        timeframe=Timeframe.M5,
        initial_capital=100_000,
        avg_spread_points=25,
        max_risk_per_trade_pct=1.0,
        max_daily_dd_pct=5.0,
        max_total_dd_pct=10.0,
    )

    # Espace de paramètres ICT Unicorn
    param_space = [
        ParameterSpace("atr_period", "int", 7, 30, 1),
        ParameterSpace("atr_min", "float", 0.5, 5.0, 0.5),
        ParameterSpace("rr_ratio", "float", 1.5, 4.0, 0.1),
        ParameterSpace("fvg_min_size", "float", 0.3, 3.0, 0.1),
        ParameterSpace("ema_fast", "int", 10, 30, 1),
        ParameterSpace("ema_slow", "int", 30, 100, 5),
        ParameterSpace("risk_pct", "float", 0.5, 2.0, 0.1),
    ]

    optim_config = OptimizationConfig(
        n_trials=100,       # 100 trials bayésiens
        param_space=param_space,
        mode="single",
        min_trades=10,
        max_drawdown_limit=10.0,
        seed=42,
    )

    optimizer = StrategyOptimizer(
        strategy_class=ICTUnicornPro,
        base_config=base_config,
        tick_data=ticks,
        optim_config=optim_config,
    )

    results = optimizer.run()

    print("\n" + "═" * 60)
    print("TOP 10 PARAMETER SETS (sur données réelles)")
    print("═" * 60)
    for i, r in enumerate(results[:10]):
        m = r.metrics
        print(
            f"#{i+1:2d} Score={r.score:.4f} | "
            f"Sharpe={m['sharpe_ratio']:5.2f} | "
            f"DD={m['max_drawdown_pct']:5.1f}% | "
            f"PF={m['profit_factor']:5.2f} | "
            f"WR={m['win_rate']:5.1f}% | "
            f"Trades={m['total_trades']:3.0f}"
        )

    if optimizer.best:
        print(f"\n🏆 Best params: {optimizer.best.params}")

    importance = optimizer.parameter_importance()
    if importance:
        print("\nParameter Importance:")
        for p, s in sorted(importance.items(), key=lambda x: -x[1]):
            bar = "█" * int(s * 40)
            print(f"  {p:18s} {s:.3f} {bar}")


def _print_full_results(result) -> None:
    print("\n" + "═" * 60)
    print(f"RÉSULTATS : {result.config.strategy_name}")
    print("═" * 60)
    print(f"Total P&L:        ${result.total_pnl:,.2f}")
    print(f"Total Return:     {result.total_return_pct:.2f}%")
    print(f"Sharpe Ratio:     {result.sharpe_ratio}")
    print(f"Sortino Ratio:    {result.sortino_ratio}")
    print(f"Calmar Ratio:     {result.calmar_ratio}")
    print(f"Max Drawdown:     {result.max_drawdown_pct}%")
    print(f"Profit Factor:    {result.profit_factor:.2f}")
    print(f"Win Rate:         {result.win_rate:.1f}%")
    print(f"Expectancy:       ${result.expectancy:.2f}")
    print(f"Recovery Factor:  {result.recovery_factor}")
    print(f"─" * 40)
    print(f"Total Trades:     {result.total_trades}")
    print(f"Winning:          {result.winning_trades}")
    print(f"Losing:           {result.losing_trades}")
    print(f"Avg Win:          ${result.avg_win:.2f}")
    print(f"Avg Loss:         ${result.avg_loss:.2f}")
    print(f"Largest Win:      ${result.largest_win:.2f}")
    print(f"Largest Loss:     ${result.largest_loss:.2f}")
    print(f"Avg Duration:     {result.avg_trade_duration_hours:.1f}h")
    print(f"─" * 40)
    print(f"Avg Slippage:     {result.avg_slippage} pts")
    print(f"Total Commission: ${result.total_commission:.2f}")
    print(f"Duration:         {result.duration_seconds:.2f}s")

    if result.trade_log:
        print(f"\nTrades (first 10):")
        for t in result.trade_log[:10]:
            emoji = "🟢" if t["pnl"] > 0 else "🔴"
            print(
                f"  {emoji} {t['side']:4s} {t['lots']} @ {t['entry']} → {t['exit']} | "
                f"P&L=${t['pnl']:>8} | MAE=${t['mae']:>7} | MFE=${t['mfe']:>7} | {t['comment']}"
            )


# ══════════════════════════════════════════════════════════════
# MAIN — Lance le script directement
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   SMARTWAVE FX — QUANT LAB                              ║")
    print("║   Guide Pratique Données Réelles                        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "bars":
            example_mt5_bars()
        elif cmd == "ticks":
            example_mt5_ticks()
        elif cmd == "optimize":
            example_optimization_real()
        else:
            print(f"Commande inconnue: {cmd}")
    else:
        print("Usage:")
        print("  python guide_real_data.py bars      → Backtest depuis MT5 CSV bars")
        print("  python guide_real_data.py ticks     → Backtest depuis MT5 tick export")
        print("  python guide_real_data.py optimize  → Optimisation sur données réelles")
        print()
        print("ÉTAPE 1 : Exporter tes données depuis MT5 :")
        print("  MT5 → Affichage → Symboles → XAUUSD → Barres → Exporter")
        print("  Sauver dans : ./data/XAUUSD_M5.csv")
        print()
        print("ÉTAPE 2 : Lancer le backtest :")
        print("  python guide_real_data.py bars")
