"""
SmartWave Quant Lab — FastAPI Backend (v4 — Import MT5 + Moteur Réel)
=====================================================================
Ajout des endpoints :
  - POST /api/v1/data/upload   : upload CSV/HST MT5
  - GET  /api/v1/data/datasets : lister les datasets importés
  - DELETE /api/v1/data/datasets/{id} : supprimer un dataset
  - GET  /api/v1/data/preview/{id}    : aperçu d'un dataset
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import sys
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Imports FastAPI au niveau MODULE (obligatoire pour l'injection BackgroundTasks)
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ajouter le répertoire parent au path Python
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartwave.api")

# Dossier de stockage des datasets uploadés
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ══════════════════════════════════════════════════════════════

class TimeframeEnum(str, Enum):
    M1 = "M1"; M5 = "M5"; M15 = "M15"; M30 = "M30"
    H1 = "H1"; H4 = "H4"; D1 = "D1"


class ExecutionModelSchema(BaseModel):
    spread_model: str = Field("dynamic")
    avg_spread_points: float = Field(25.0, ge=0)
    slippage_model: str = Field("probabilistic")
    max_slippage_points: float = Field(5.0, ge=0)
    latency_ms: float = Field(50.0, ge=0)
    commission_per_lot: float = Field(7.0, ge=0)


class RiskParamsSchema(BaseModel):
    max_risk_per_trade_pct: float = Field(1.0, ge=0.1, le=10)
    max_daily_dd_pct: float = Field(5.0, ge=1, le=20)
    max_total_dd_pct: float = Field(10.0, ge=2, le=50)
    max_concurrent_trades: int = Field(3, ge=1, le=20)


class BacktestRequest(BaseModel):
    strategy_name: str
    symbol: str = "XAUUSD"
    timeframe: TimeframeEnum = TimeframeEnum.M5
    start_date: str = "2024-01-01"
    end_date: str = "2025-12-31"
    initial_capital: float = Field(100_000, ge=100)
    leverage: int = Field(100, ge=1, le=500)
    execution: ExecutionModelSchema = Field(default_factory=ExecutionModelSchema)
    risk: RiskParamsSchema = Field(default_factory=RiskParamsSchema)
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    dataset_id: Optional[str] = Field(None, description="ID du dataset MT5 importé (optionnel)")


class OptimizationRequest(BaseModel):
    strategy_name: str
    symbol: str = "XAUUSD"
    timeframe: TimeframeEnum = TimeframeEnum.M5
    start_date: str = "2024-01-01"
    end_date: str = "2025-12-31"
    initial_capital: float = 100_000
    n_trials: int = Field(50, ge=10, le=5000)
    mode: str = "single"
    parameter_space: list[dict[str, Any]] = Field(default_factory=list)
    execution: ExecutionModelSchema = Field(default_factory=ExecutionModelSchema)
    risk: RiskParamsSchema = Field(default_factory=RiskParamsSchema)
    dataset_id: Optional[str] = Field(None)


class MonteCarloRequest(BaseModel):
    backtest_id: str
    n_simulations: int = Field(500, ge=50, le=10000)
    method: str = "trade_permutation"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    message: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None
    result: Optional[dict[str, Any]] = None


class StrategyInfo(BaseModel):
    name: str
    description: str = ""
    type: str = ""
    parameters: list[dict[str, Any]] = []
    default_params: dict[str, Any] = {}


class HealthResponse(BaseModel):
    status: str = "healthy"
    engine_status: str = "online"
    data_status: str = "synced"
    optimizer_status: str = "ready"
    queue_depth: int = 0
    uptime_seconds: float = 0.0
    version: str = "4.0.0"


class DatasetInfo(BaseModel):
    id: str
    filename: str
    symbol: str
    timeframe: str
    format: str  # "mt5_bars", "mt5_ticks", "generic_csv"
    rows: int
    size_kb: float
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    uploaded_at: str


# ══════════════════════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════════════════════

app = FastAPI(
    title="SmartWave Quant Lab API",
    version="4.0.0",
    description="Institutional-grade backtesting — Moteur event-driven + Import MT5",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job store en mémoire
jobs: dict[str, dict] = {}
# Dataset registry en mémoire (persisté sur disque via JSON)
datasets: dict[str, dict] = {}
_start_time = datetime.utcnow()

STRATEGIES = {
    "ICTUnicornPro": StrategyInfo(
        name="ICTUnicornPro",
        description="ICT Unicorn Model — FVG + OB confluence",
        type="ICT/SMC",
        parameters=[
            {"name": "atr_period", "type": "int", "default": 14, "min": 5, "max": 50},
            {"name": "atr_min", "type": "float", "default": 2.0, "min": 0.5, "max": 10.0},
            {"name": "rr_ratio", "type": "float", "default": 2.0, "min": 1.0, "max": 5.0},
            {"name": "fvg_min_size", "type": "float", "default": 1.0, "min": 0.1, "max": 5.0},
            {"name": "ema_fast", "type": "int", "default": 21, "min": 5, "max": 50},
            {"name": "ema_slow", "type": "int", "default": 50, "min": 20, "max": 200},
        ],
        default_params={"atr_period": 14, "rr_ratio": 2.0, "ema_fast": 21, "ema_slow": 50},
    ),
    "MACrossover": StrategyInfo(
        name="MACrossover",
        description="Simple MA Crossover — benchmark strategy",
        type="Trend Following",
        parameters=[
            {"name": "fast_period", "type": "int", "default": 10, "min": 3, "max": 50},
            {"name": "slow_period", "type": "int", "default": 30, "min": 10, "max": 200},
            {"name": "lot_size", "type": "float", "default": 0.1, "min": 0.01, "max": 1.0},
            {"name": "atr_sl_mult", "type": "float", "default": 1.5, "min": 0.5, "max": 5.0},
            {"name": "rr_ratio", "type": "float", "default": 2.0, "min": 1.0, "max": 5.0},
        ],
        default_params={"fast_period": 10, "slow_period": 30, "rr_ratio": 2.0},
    ),
}


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _safe_float(v):
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0.0
    if isinstance(v, float):
        return round(v, 4)
    return v


def _load_dataset_registry():
    """Charger le registre des datasets depuis le disque."""
    import json
    registry_path = UPLOADS_DIR / "registry.json"
    if registry_path.exists():
        try:
            with open(registry_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_dataset_registry(registry: dict):
    """Sauvegarder le registre des datasets sur le disque."""
    import json
    registry_path = UPLOADS_DIR / "registry.json"
    try:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save registry: {e}")


def _detect_csv_format(filepath: Path) -> dict:
    """
    Détecter le format du CSV MT5 et extraire les métadonnées.
    Retourne: {format, rows, date_start, date_end, is_tick_data}
    """
    import csv as csv_module

    result = {
        "format": "generic_csv",
        "rows": 0,
        "date_start": None,
        "date_end": None,
        "is_tick_data": False,
    }

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            f.seek(0)

            # Détecter séparateur
            sep = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")

            # Détecter si c'est des ticks ou des barres
            lower = first_line.lower()
            if "bid" in lower or "ask" in lower:
                result["format"] = "mt5_ticks"
                result["is_tick_data"] = True
            elif "open" in lower or "high" in lower or "close" in lower:
                result["format"] = "mt5_bars"
            else:
                # Pas de header — détecter par le contenu de la première colonne
                parts = first_line.split(sep)
                first_col = parts[0].strip() if parts else ""
                # Format compact YYYYMMDD (ex: 20210412) ou avec séparateur (2024.01.02)
                has_date = (
                    ("." in first_col and ":" in first_line) or  # 2024.01.02 + HH:MM
                    ("-" in first_col) or                        # 2024-01-02
                    (len(first_col) == 8 and first_col.isdigit())  # 20210412
                )
                if has_date and len(parts) >= 5:
                    result["format"] = "mt5_bars"

            reader = csv_module.reader(f, delimiter=sep)
            rows = list(reader)

            # Ignorer le header
            data_rows = rows[1:] if rows and any(
                h in rows[0][0].lower() for h in ["date", "time", "open", "bid"]
            ) else rows

            result["rows"] = len(data_rows)

            # Extraire les dates de début et fin
            if data_rows:
                try:
                    first_row = [c.strip() for c in data_rows[0] if c.strip()]
                    last_row = [c.strip() for c in data_rows[-1] if c.strip()]
                    def _normalize_date(raw: str) -> str:
                        """Convertit YYYYMMDD en YYYY-MM-DD, sinon retourne les 10 premiers chars."""
                        raw = raw.strip()
                        if len(raw) == 8 and raw.isdigit():
                            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                        return raw[:10]
                    if first_row:
                        result["date_start"] = _normalize_date(first_row[0])
                    if last_row:
                        result["date_end"] = _normalize_date(last_row[0])
                except Exception:
                    pass

    except Exception as e:
        logger.warning(f"Format detection error: {e}")

    return result


def _get_ticks_from_dataset(dataset_id: str, start_date: str, end_date: str):
    """
    Charger les ticks depuis un dataset importé.
    Convertit les barres MT5 en ticks via BarToTickSynthesizer.
    """
    from data.connectors import MT5CSVImporter, BarToTickSynthesizer
    from core.models import Timeframe

    if dataset_id not in datasets:
        raise ValueError(f"Dataset '{dataset_id}' not found")

    ds = datasets[dataset_id]
    filepath = Path(ds["filepath"])

    if not filepath.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}")

    logger.info(f"Loading dataset '{dataset_id}' ({ds['filename']}) for backtest")

    importer = MT5CSVImporter(symbol=ds["symbol"])

    if ds["format"] == "mt5_ticks":
        # Import direct des ticks
        ticks = importer.import_ticks(
            filepath=filepath,
            start_date=start_date,
            end_date=end_date,
            max_rows=500_000,  # Limite pour la performance
        )
        logger.info(f"Loaded {len(ticks)} ticks from dataset")
        return ticks
    else:
        # Import des barres puis conversion en ticks
        tf_map = {
            "M1": Timeframe.M1, "M5": Timeframe.M5, "M15": Timeframe.M15,
            "M30": Timeframe.M30, "H1": Timeframe.H1, "H4": Timeframe.H4,
            "D1": Timeframe.D1,
        }
        tf = tf_map.get(ds.get("timeframe", "M5"), Timeframe.M5)

        bars = importer.import_bars(
            filepath=filepath,
            timeframe=tf,
            start_date=start_date,
            end_date=end_date,
            max_rows=200_000,
        )

        if not bars:
            raise ValueError(f"No bars loaded from dataset '{dataset_id}'")

        logger.info(f"Loaded {len(bars)} bars, converting to ticks...")

        synthesizer = BarToTickSynthesizer(
            ticks_per_bar=30,  # 30 ticks par barre = bon compromis vitesse/précision
            base_spread_points=25.0,
            method="random_walk",
        )
        ticks = synthesizer.synthesize(bars)
        logger.info(f"Synthesized {len(ticks)} ticks from {len(bars)} bars")
        return ticks


# ══════════════════════════════════════════════════════════════
# MOTEUR DE CALCUL
# ══════════════════════════════════════════════════════════════

def _run_backtest_sync(req: BacktestRequest) -> dict[str, Any]:
    """Exécute le vrai backtest dans un thread séparé."""
    from core.models import BacktestConfig, Timeframe
    from core.engine import BacktestEngine
    from data.datastore import SyntheticTickGenerator
    from strategies.strategies import ICTUnicornPro, MACrossover

    tf_map = {
        "M1": Timeframe.M1, "M5": Timeframe.M5, "M15": Timeframe.M15,
        "M30": Timeframe.M30, "H1": Timeframe.H1, "H4": Timeframe.H4,
        "D1": Timeframe.D1,
    }
    timeframe = tf_map.get(req.timeframe.value, Timeframe.M5)

    # Choisir la source de données
    if req.dataset_id and req.dataset_id in datasets:
        logger.info(f"Using real MT5 dataset: {req.dataset_id}")
        ticks = _get_ticks_from_dataset(req.dataset_id, req.start_date, req.end_date)
        data_source = f"MT5 dataset: {datasets[req.dataset_id]['filename']}"
    else:
        # Données synthétiques (fallback)
        gen = SyntheticTickGenerator(
            symbol=req.symbol,
            base_price=2700.0 if req.symbol == "XAUUSD" else 40000.0,
            ticks_per_day=2000,
        )
        ticks = gen.generate(start_date=req.start_date, end_date=req.end_date)
        data_source = "synthetic"
        logger.info(f"Generated {len(ticks)} synthetic ticks for {req.symbol}")

    logger.info(f"Running backtest with {len(ticks)} ticks (source: {data_source})")

    config = BacktestConfig(
        strategy_name=req.strategy_name,
        symbol=req.symbol,
        timeframe=timeframe,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        leverage=req.leverage,
        spread_model=req.execution.spread_model,
        avg_spread_points=req.execution.avg_spread_points,
        slippage_model=req.execution.slippage_model,
        max_slippage_points=req.execution.max_slippage_points,
        latency_ms=req.execution.latency_ms,
        commission_per_lot=req.execution.commission_per_lot,
        max_risk_per_trade_pct=req.risk.max_risk_per_trade_pct,
        max_daily_dd_pct=req.risk.max_daily_dd_pct,
        max_total_dd_pct=req.risk.max_total_dd_pct,
        max_concurrent_trades=req.risk.max_concurrent_trades,
        strategy_params=req.strategy_params,
    )

    strategy_map = {"ICTUnicornPro": ICTUnicornPro, "MACrossover": MACrossover}
    StrategyClass = strategy_map.get(req.strategy_name)
    if not StrategyClass:
        raise ValueError(f"Unknown strategy: {req.strategy_name}")

    strategy = StrategyClass(params=req.strategy_params)
    engine = BacktestEngine(config=config, strategy=strategy)
    result = engine.run(ticks)

    pf = result.profit_factor
    if pf == float('inf') or (isinstance(pf, float) and math.isinf(pf)):
        pf = 999.0

    return {
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": _safe_float(result.win_rate),
        "total_pnl": _safe_float(result.total_pnl),
        "total_return_pct": _safe_float(result.total_return_pct),
        "profit_factor": _safe_float(pf),
        "expectancy": _safe_float(result.expectancy),
        "sharpe_ratio": _safe_float(result.sharpe_ratio),
        "sortino_ratio": _safe_float(result.sortino_ratio),
        "calmar_ratio": _safe_float(result.calmar_ratio),
        "max_drawdown_pct": _safe_float(result.max_drawdown_pct),
        "max_drawdown_abs": _safe_float(result.max_drawdown_abs),
        "recovery_factor": _safe_float(result.recovery_factor),
        "avg_win": _safe_float(result.avg_win),
        "avg_loss": _safe_float(result.avg_loss),
        "largest_win": _safe_float(result.largest_win),
        "largest_loss": _safe_float(result.largest_loss),
        "max_consecutive_wins": result.max_consecutive_wins,
        "max_consecutive_losses": result.max_consecutive_losses,
        "avg_trade_duration_hours": _safe_float(result.avg_trade_duration_hours),
        "total_commission": _safe_float(result.total_commission),
        "duration_seconds": _safe_float(result.duration_seconds),
        "equity_curve": result.equity_curve or [],
        "trade_log": result.trade_log[:500] if result.trade_log else [],
        "daily_returns": [round(float(r), 6) for r in (result.daily_returns or [])],
        "data_source": data_source,
        "ticks_processed": len(ticks),
    }


# ══════════════════════════════════════════════════════════════
# BACKGROUND TASKS
# ══════════════════════════════════════════════════════════════

async def run_backtest_job(job_id: str, req: BacktestRequest):
    jobs[job_id]["status"] = "running"
    jobs[job_id]["progress"] = 5.0
    logger.info(f"[Job {job_id}] Backtest start: {req.strategy_name} {req.symbol}")
    try:
        result = await asyncio.to_thread(_run_backtest_sync, req)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100.0
        jobs[job_id]["result"] = result
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[Job {job_id}] Done: {result.get('total_trades')} trades, PnL={result.get('total_pnl')}")
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = {"error": str(e)}
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()


# ══════════════════════════════════════════════════════════════
# STARTUP — Charger le registre des datasets
# ══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    global datasets
    datasets = _load_dataset_registry()
    logger.info(f"Loaded {len(datasets)} datasets from registry")


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — HEALTH & STRATEGIES
# ══════════════════════════════════════════════════════════════

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    uptime = (datetime.utcnow() - _start_time).total_seconds()
    running = sum(1 for j in jobs.values() if j["status"] == "running")
    return HealthResponse(queue_depth=running, uptime_seconds=uptime)


@app.get("/api/v1/strategies", response_model=list[StrategyInfo])
async def list_strategies():
    return list(STRATEGIES.values())


@app.get("/api/v1/strategies/{name}", response_model=StrategyInfo)
async def get_strategy(name: str):
    if name not in STRATEGIES:
        raise HTTPException(404, f"Strategy '{name}' not found")
    return STRATEGIES[name]


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — DATA MANAGEMENT (MT5 IMPORT)
# ══════════════════════════════════════════════════════════════

@app.post("/api/v1/data/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    symbol: str = Form("XAUUSD"),
    timeframe: str = Form("M5"),
):
    """
    Upload un fichier CSV MT5 (barres OHLCV ou ticks).
    Supporte les fichiers de toute taille via streaming par chunks (pas de limite).
    
    Formats acceptés :
    - MT5 History Center export (CSV avec colonnes Date, Time, Open, High, Low, Close, Volume)
    - MT5 Tick export (CSV avec colonnes Date, Time, Bid, Ask)
    - CSV générique (timestamp,open,high,low,close,volume)
    """
    import time as _time
    t_start = _time.monotonic()

    # ── Validation du fichier ──────────────────────────────────
    if not file.filename:
        raise HTTPException(400, detail={"code": "MISSING_FILENAME", "message": "Nom de fichier manquant"})

    ext = Path(file.filename).suffix.lower()
    if ext not in [".csv", ".txt", ".tsv"]:
        raise HTTPException(400, detail={
            "code": "UNSUPPORTED_FORMAT",
            "message": f"Extension '{ext}' non supportée. Utilisez .csv, .txt ou .tsv",
            "hint": "Exportez depuis MetaTrader 5 → History Center → CSV"
        })

    # ── Générer un ID unique ───────────────────────────────────
    dataset_id = str(uuid.uuid4())[:8]
    safe_filename = f"{dataset_id}_{file.filename}"
    filepath = UPLOADS_DIR / safe_filename

    # ── Écriture en streaming par chunks de 8 MB ──────────────
    # Aucune limite de taille : supporte les fichiers MT5 de plusieurs Go
    CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB par chunk
    size_bytes = 0
    chunk_count = 0
    try:
        with open(filepath, "wb") as out_f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                out_f.write(chunk)
                size_bytes += len(chunk)
                chunk_count += 1
                # Log de progression pour les gros fichiers (tous les 128 MB)
                if chunk_count % 16 == 0:
                    elapsed = _time.monotonic() - t_start
                    speed_mbs = (size_bytes / 1024 / 1024) / max(elapsed, 0.001)
                    logger.info(f"[Upload] {file.filename} — {size_bytes/1024/1024:.1f} MB reçus @ {speed_mbs:.1f} MB/s")
    except OSError as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(500, detail={
            "code": "WRITE_ERROR",
            "message": f"Erreur d'écriture disque : {e}",
            "hint": "Vérifiez l'espace disque disponible"
        })
    except Exception as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(500, detail={
            "code": "UPLOAD_ERROR",
            "message": f"Erreur lors de la réception du fichier : {e}"
        })

    t_write = _time.monotonic()
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    write_duration = t_write - t_start
    write_speed_mbs = size_mb / max(write_duration, 0.001)

    if size_kb < 0.1:
        filepath.unlink(missing_ok=True)
        raise HTTPException(400, detail={
            "code": "EMPTY_FILE",
            "message": "Fichier vide ou trop petit (< 100 octets)"
        })

    # ── Analyser le format CSV ─────────────────────────────────
    try:
        meta = _detect_csv_format(filepath)
    except UnicodeDecodeError:
        filepath.unlink(missing_ok=True)
        raise HTTPException(400, detail={
            "code": "ENCODING_ERROR",
            "message": "Encodage non supporté. Sauvegardez le fichier en UTF-8 ou ANSI depuis Excel/MT5",
            "hint": "Dans Excel : Enregistrer sous → CSV UTF-8 (délimité par des virgules)"
        })
    except Exception as e:
        logger.warning(f"Format detection failed: {e}")
        meta = {"format": "generic_csv", "rows": 0, "date_start": None, "date_end": None}

    if meta["rows"] == 0:
        filepath.unlink(missing_ok=True)
        raise HTTPException(400, detail={
            "code": "NO_DATA",
            "message": "Aucune ligne de données valide trouvée dans le fichier",
            "hint": "Vérifiez que le fichier contient des colonnes Date, Time, Open, High, Low, Close"
        })

    t_parse = _time.monotonic()
    parse_duration = t_parse - t_write
    total_duration = t_parse - t_start

    # ── Enregistrer dans le registre ──────────────────────────
    dataset_info = {
        "id": dataset_id,
        "filename": file.filename,
        "filepath": str(filepath),
        "symbol": symbol.upper(),
        "timeframe": timeframe.upper(),
        "format": meta["format"],
        "rows": meta["rows"],
        "size_kb": round(size_kb, 1),
        "date_start": meta.get("date_start"),
        "date_end": meta.get("date_end"),
        "uploaded_at": datetime.utcnow().isoformat(),
    }

    datasets[dataset_id] = dataset_info
    _save_dataset_registry(datasets)

    logger.info(
        f"Dataset uploaded: {file.filename} | {meta['rows']:,} rows | "
        f"{meta['format']} | {size_mb:.1f} MB | "
        f"write: {write_duration:.1f}s @ {write_speed_mbs:.1f} MB/s | "
        f"parse: {parse_duration:.1f}s | total: {total_duration:.1f}s | ID: {dataset_id}"
    )

    return {
        "success": True,
        "dataset_id": dataset_id,
        "filename": file.filename,
        "format": meta["format"],
        "rows": meta["rows"],
        "size_kb": round(size_kb, 1),
        "size_mb": round(size_mb, 2),
        "date_start": meta.get("date_start"),
        "date_end": meta.get("date_end"),
        "symbol": symbol.upper(),
        "timeframe": timeframe.upper(),
        "upload_stats": {
            "write_duration_s": round(write_duration, 2),
            "parse_duration_s": round(parse_duration, 2),
            "total_duration_s": round(total_duration, 2),
            "write_speed_mbs": round(write_speed_mbs, 1),
            "chunk_count": chunk_count,
        },
        "message": f"Dataset importé en {total_duration:.1f}s : {meta['rows']:,} barres ({meta['format']}, {size_mb:.1f} MB @ {write_speed_mbs:.1f} MB/s)",
    }


@app.get("/api/v1/data/datasets", response_model=list[DatasetInfo])
async def list_datasets():
    """Lister tous les datasets importés."""
    result = []
    for ds in datasets.values():
        # Vérifier que le fichier existe encore
        if Path(ds["filepath"]).exists():
            result.append(DatasetInfo(**ds))
    return sorted(result, key=lambda x: x.uploaded_at, reverse=True)


@app.get("/api/v1/data/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Obtenir les informations d'un dataset."""
    if dataset_id not in datasets:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")
    ds = datasets[dataset_id]
    if not Path(ds["filepath"]).exists():
        raise HTTPException(404, "Fichier dataset introuvable sur le disque")
    return ds


@app.get("/api/v1/data/preview/{dataset_id}")
async def preview_dataset(dataset_id: str, rows: int = 10):
    """Aperçu des premières lignes d'un dataset."""
    if dataset_id not in datasets:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")

    ds = datasets[dataset_id]
    filepath = Path(ds["filepath"])

    if not filepath.exists():
        raise HTTPException(404, "Fichier dataset introuvable")

    try:
        import csv as csv_module
        with open(filepath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            f.seek(0)
            sep = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
            reader = csv_module.reader(f, delimiter=sep)
            preview_rows = []
            for i, row in enumerate(reader):
                if i >= rows + 1:
                    break
                preview_rows.append(row)

        return {
            "dataset_id": dataset_id,
            "filename": ds["filename"],
            "preview": preview_rows[:rows + 1],  # Include header
            "total_rows": ds["rows"],
        }
    except Exception as e:
        raise HTTPException(500, f"Erreur de lecture : {e}")


@app.delete("/api/v1/data/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Supprimer un dataset."""
    if dataset_id not in datasets:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")

    ds = datasets[dataset_id]
    filepath = Path(ds["filepath"])

    # Supprimer le fichier
    try:
        filepath.unlink(missing_ok=True)
    except Exception as e:
        logger.warning(f"Could not delete file: {e}")

    # Supprimer du registre
    del datasets[dataset_id]
    _save_dataset_registry(datasets)

    return {"success": True, "message": f"Dataset '{dataset_id}' supprimé"}


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — DATASET STATS
# ══════════════════════════════════════════════════════════════

@app.get("/api/v1/data/stats/{dataset_id}")
async def get_dataset_stats(dataset_id: str):
    """
    Calcule des statistiques descriptives sur un dataset MT5 :
    - Volatilité moyenne (ATR moyen)
    - Range moyen par bougie
    - Heure de plus forte activité (volume)
    - Nombre de gaps détectés
    - Distribution des ranges (min, max, median, p95)
    """
    if dataset_id not in datasets:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found")
    ds = datasets[dataset_id]
    filepath = Path(ds["filepath"])
    if not filepath.exists():
        raise HTTPException(404, "Fichier dataset introuvable")

    try:
        import csv as csv_module
        import statistics
        from collections import defaultdict

        rows_data = []
        with open(filepath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            f.seek(0)
            sep = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
            reader = csv_module.reader(f, delimiter=sep)
            header = None
            for row in reader:
                if not row or not row[0].strip():
                    continue
                # Détecter l'en-tête
                if header is None:
                    first_val = row[0].strip().lower().replace('<', '').replace('>', '')
                    if first_val in ('date', 'time', 'datetime', 'timestamp'):
                        header = [c.strip().lower().replace('<', '').replace('>', '') for c in row]
                        continue
                    else:
                        header = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
                rows_data.append(row)

        if not rows_data:
            return {"dataset_id": dataset_id, "error": "Aucune donnée"}

        # Parser les colonnes OHLCV
        col_idx = {}
        if header:
            for i, h in enumerate(header):
                col_idx[h] = i

        opens, highs, lows, closes, volumes = [], [], [], [], []
        hours_volume = defaultdict(float)
        gaps = 0
        prev_close = None

        for row in rows_data:
            try:
                hi_idx = col_idx.get('high', 3)
                lo_idx = col_idx.get('low', 4)
                cl_idx = col_idx.get('close', 5)
                op_idx = col_idx.get('open', 2)
                vol_idx = col_idx.get('tickvol', col_idx.get('vol', 6))
                time_idx = col_idx.get('time', 1)

                if len(row) <= max(hi_idx, lo_idx, cl_idx, op_idx):
                    continue

                o = float(row[op_idx].strip())
                h = float(row[hi_idx].strip())
                l = float(row[lo_idx].strip())
                c = float(row[cl_idx].strip())

                opens.append(o)
                highs.append(h)
                lows.append(l)
                closes.append(c)

                # Volume par heure
                if len(row) > vol_idx:
                    try:
                        vol = float(row[vol_idx].strip())
                        volumes.append(vol)
                        if len(row) > time_idx:
                            time_str = row[time_idx].strip()
                            hour = int(time_str.split(':')[0]) if ':' in time_str else 0
                            hours_volume[hour] += vol
                    except (ValueError, IndexError):
                        pass

                # Gap : |open - prev_close| > 2 * avg_range
                if prev_close is not None:
                    gap_size = abs(o - prev_close)
                    avg_range_so_far = statistics.mean([h2 - l2 for h2, l2 in zip(highs[-20:], lows[-20:])]) if len(highs) >= 5 else 1.0
                    if gap_size > 2 * avg_range_so_far and avg_range_so_far > 0:
                        gaps += 1
                prev_close = c

            except (ValueError, IndexError):
                continue

        if not highs:
            return {"dataset_id": dataset_id, "error": "Impossible de parser les données"}

        ranges = [h - l for h, l in zip(highs, lows)]
        sorted_ranges = sorted(ranges)
        n = len(sorted_ranges)

        # ATR simple (moyenne des ranges)
        avg_range = statistics.mean(ranges)
        avg_range_pips = round(avg_range * 10, 1)  # Approximation pips pour XAUUSD

        # Heure la plus active
        peak_hour = max(hours_volume, key=hours_volume.get) if hours_volume else None
        peak_hour_volume = hours_volume.get(peak_hour, 0) if peak_hour is not None else 0

        # Distribution des ranges
        p25_idx = max(0, int(n * 0.25) - 1)
        p50_idx = max(0, int(n * 0.50) - 1)
        p75_idx = max(0, int(n * 0.75) - 1)
        p95_idx = max(0, int(n * 0.95) - 1)

        # Volatilité des closes (std dev)
        close_returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes)) if closes[i-1] != 0]
        volatility_pct = round(statistics.stdev(close_returns), 4) if len(close_returns) > 1 else 0.0

        # Top 5 heures actives
        top_hours = sorted(hours_volume.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "dataset_id": dataset_id,
            "filename": ds["filename"],
            "symbol": ds["symbol"],
            "timeframe": ds["timeframe"],
            "total_bars": len(ranges),
            "avg_range": round(avg_range, 5),
            "avg_range_pips": avg_range_pips,
            "min_range": round(sorted_ranges[0], 5),
            "max_range": round(sorted_ranges[-1], 5),
            "median_range": round(sorted_ranges[p50_idx], 5),
            "p25_range": round(sorted_ranges[p25_idx], 5),
            "p75_range": round(sorted_ranges[p75_idx], 5),
            "p95_range": round(sorted_ranges[p95_idx], 5),
            "volatility_pct": volatility_pct,
            "gaps_detected": gaps,
            "peak_hour": peak_hour,
            "peak_hour_volume": round(peak_hour_volume, 0),
            "top_active_hours": [{"hour": h, "volume": round(v, 0)} for h, v in top_hours],
            "avg_volume": round(statistics.mean(volumes), 1) if volumes else 0,
            "total_volume": round(sum(volumes), 0) if volumes else 0,
            "range_distribution": _compute_range_distribution(ranges),
            "quality_score": _compute_quality_score(ranges, gaps, volumes, closes),
        }
    except Exception as e:
        logger.error(f"Stats error for {dataset_id}: {e}")
        raise HTTPException(500, f"Erreur de calcul des statistiques : {e}")



def _compute_range_distribution(ranges: list) -> list:
    """Calcule la distribution des ranges (H-L) en 10 buckets."""
    if not ranges:
        return []
    min_r = min(ranges)
    max_r = max(ranges)
    if max_r == min_r:
        return [{"range": f"{min_r:.4f}", "count": len(ranges), "pct": 100.0}]
    bucket_size = (max_r - min_r) / 10
    buckets = [0] * 10
    for r in ranges:
        idx = min(int((r - min_r) / bucket_size), 9)
        buckets[idx] += 1
    total = len(ranges)
    result = []
    for i, count in enumerate(buckets):
        lo = min_r + i * bucket_size
        hi = lo + bucket_size
        result.append({
            "range": f"{lo:.4f}-{hi:.4f}",
            "range_short": f"{lo:.3f}",
            "count": count,
            "pct": round(count / total * 100, 1),
        })
    return result


def _compute_quality_score(ranges: list, gaps: int, volumes: list, closes: list) -> dict:
    """Calcule un score de qualité global (0-100) avec détail par critère."""
    n = len(ranges)
    if n == 0:
        return {"score": 0, "label": "unknown", "color": "gray", "details": {}}

    # Critère 1 : Densité de données (40 pts) — plus de barres = mieux
    density_score = min(40, int(n / 50))  # 40 pts pour 2000+ barres

    # Critère 2 : Absence de gaps (35 pts)
    gap_rate = gaps / n if n > 0 else 0
    gap_score = max(0, 35 - int(gap_rate * 500))  # -5 pts par 1% de gaps

    # Critère 3 : Régularité des ranges (15 pts) — faible CV = données propres
    if len(ranges) > 1:
        import statistics as _stats
        mean_r = _stats.mean(ranges)
        std_r = _stats.stdev(ranges)
        cv = std_r / mean_r if mean_r > 0 else 999
        regularity_score = max(0, 15 - int(cv * 10))
    else:
        regularity_score = 0

    # Critère 4 : Présence de volume (10 pts)
    volume_score = 10 if volumes and sum(volumes) > 0 else 0

    total = density_score + gap_score + regularity_score + volume_score
    total = min(100, max(0, total))

    if total >= 75:
        label, color = "excellent", "green"
    elif total >= 50:
        label, color = "bon", "orange"
    else:
        label, color = "faible", "red"

    return {
        "score": total,
        "label": label,
        "color": color,
        "details": {
            "density": density_score,
            "gaps": gap_score,
            "regularity": regularity_score,
            "volume": volume_score,
        }
    }


# ════════════════════════════════════════════════════════════
# ENDPOINTS — BACKTEST
# ════════════════════════════════════════════════════════════

@app.post("/api/v1/backtest", response_model=JobResponse)
async def submit_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    """Lance un vrai backtest event-driven en arrière-plan."""
    job_id = str(uuid.uuid4())[:8]

    # Valider le dataset si fourni
    if req.dataset_id and req.dataset_id not in datasets:
        raise HTTPException(400, f"Dataset '{req.dataset_id}' introuvable. Importez d'abord vos données MT5.")

    data_info = ""
    if req.dataset_id:
        ds = datasets[req.dataset_id]
        data_info = f" | Dataset: {ds['filename']} ({ds['rows']} barres)"

    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "request": req.model_dump(),
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "message": "",
    }
    background_tasks.add_task(run_backtest_job, job_id, req)
    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message=f"Backtest lancé : {req.strategy_name} {req.symbol} {req.timeframe.value}{data_info}",
        created_at=jobs[job_id]["created_at"],
    )


@app.get("/api/v1/backtest/{job_id}", response_model=JobResponse)
async def get_backtest(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, f"Job '{job_id}' not found")
    j = jobs[job_id]
    return JobResponse(
        job_id=job_id,
        status=j["status"],
        progress=j["progress"],
        message=j.get("message", ""),
        result=j.get("result"),
        created_at=j["created_at"],
        completed_at=j.get("completed_at"),
    )


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — OPTIMIZATION
# ══════════════════════════════════════════════════════════════

@app.post("/api/v1/optimize", response_model=JobResponse)
async def submit_optimization(req: OptimizationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "queued",
        "progress": 0.0,
        "result": None,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
    }

    async def run_opt(jid: str):
        jobs[jid]["status"] = "running"
        try:
            from optimization.optimizer import StrategyOptimizer
            from core.models import Timeframe
            from data.datastore import SyntheticTickGenerator
            tf_map = {"M5": Timeframe.M5, "H1": Timeframe.H1, "D1": Timeframe.D1}
            tf = tf_map.get(req.timeframe.value, Timeframe.M5)

            if req.dataset_id and req.dataset_id in datasets:
                ticks = await asyncio.to_thread(
                    _get_ticks_from_dataset, req.dataset_id, req.start_date, req.end_date
                )
            else:
                gen = SyntheticTickGenerator(symbol=req.symbol, ticks_per_day=1000)
                ticks = gen.generate(start_date=req.start_date, end_date=req.end_date)

            optimizer = StrategyOptimizer(
                strategy_name=req.strategy_name, ticks=ticks,
                symbol=req.symbol, timeframe=tf,
                initial_capital=req.initial_capital,
                n_trials=min(req.n_trials, 50),
            )
            best = optimizer.optimize(parameter_space=req.parameter_space)
            jobs[jid]["status"] = "completed"
            jobs[jid]["progress"] = 100.0
            jobs[jid]["result"] = {"best_params": best, "n_trials": req.n_trials}
            jobs[jid]["completed_at"] = datetime.utcnow().isoformat()
        except Exception as e:
            jobs[jid]["status"] = "failed"
            jobs[jid]["result"] = {"error": str(e)}
            jobs[jid]["completed_at"] = datetime.utcnow().isoformat()

    background_tasks.add_task(run_opt, job_id)
    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message=f"Optimisation : {req.n_trials} trials sur {req.strategy_name}",
        created_at=jobs[job_id]["created_at"],
    )


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — MONTE CARLO
# ══════════════════════════════════════════════════════════════

@app.post("/api/v1/montecarlo", response_model=JobResponse)
async def submit_montecarlo(req: MonteCarloRequest, background_tasks: BackgroundTasks):
    if req.backtest_id not in jobs or jobs[req.backtest_id].get("status") != "completed":
        raise HTTPException(400, f"Backtest '{req.backtest_id}' not completed")
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "queued", "progress": 0.0, "created_at": datetime.utcnow().isoformat()}

    async def run_mc(jid: str):
        jobs[jid]["status"] = "running"
        try:
            bt_result = jobs[req.backtest_id]["result"]
            trade_pnls = [t.get("pnl", 0) for t in bt_result.get("trade_log", [])]
            if not trade_pnls:
                raise ValueError("No trades in backtest result")
            from robustness.robustness import MonteCarloAnalyzer
            mc = MonteCarloAnalyzer(n_simulations=req.n_simulations)
            mc_result = await asyncio.to_thread(mc.analyze, trade_pnls)
            jobs[jid]["status"] = "completed"
            jobs[jid]["progress"] = 100.0
            jobs[jid]["result"] = mc_result if isinstance(mc_result, dict) else {"simulations": req.n_simulations}
            jobs[jid]["completed_at"] = datetime.utcnow().isoformat()
        except Exception as e:
            jobs[jid]["status"] = "failed"
            jobs[jid]["result"] = {"error": str(e)}

    background_tasks.add_task(run_mc, job_id)
    return JobResponse(
        job_id=job_id, status=JobStatus.QUEUED,
        message=f"Monte Carlo : {req.n_simulations} simulations",
        created_at=jobs[job_id]["created_at"],
    )


# ══════════════════════════════════════════════════════════════
# ENDPOINTS — JOBS
# ══════════════════════════════════════════════════════════════

@app.get("/api/v1/jobs", response_model=list[JobResponse])
async def list_jobs(status: Optional[str] = None, limit: int = 50):
    results = []
    for jid, j in list(jobs.items())[-limit:]:
        if status and j["status"] != status:
            continue
        results.append(JobResponse(
            job_id=jid, status=j["status"], progress=j["progress"],
            created_at=j["created_at"], completed_at=j.get("completed_at"),
        ))
    return results


@app.delete("/api/v1/jobs/{job_id}")
async def cancel_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, f"Job '{job_id}' not found")
    jobs[job_id]["status"] = "cancelled"
    return {"message": f"Job {job_id} cancelled"}



# ══════════════════════════════════════════════════════════════
# ENDPOINTS — EXPORT BACKTEST CSV
# ══════════════════════════════════════════════════════════════

@app.get("/api/v1/backtest/{job_id}/export")
async def export_backtest_csv(job_id: str):
    """
    Exporte le journal des trades d'un backtest terminé au format CSV.
    Colonnes : #, Côté, Lots, Entrée, Sortie, P&L, MAE, MFE, Ouvert, Fermé, Durée(h), Commentaire
    """
    from fastapi.responses import StreamingResponse
    import csv as csv_module
    import io

    if job_id not in jobs:
        raise HTTPException(404, f"Job '{job_id}' not found")
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Backtest '{job_id}' non terminé (status: {job['status']})")

    result = job.get("result", {})
    trade_log = result.get("trade_log", [])
    if not trade_log:
        raise HTTPException(404, "Aucun trade à exporter")

    output = io.StringIO()
    writer = csv_module.writer(output)

    # Métadonnées
    writer.writerow(["# SmartWave FX — Quant Lab — Export Backtest"])
    writer.writerow([
        "# Stratégie:", result.get("strategy_name", ""),
        "Symbole:", result.get("symbol", ""),
        "TF:", result.get("timeframe", ""),
        "Capital:", result.get("initial_capital", ""),
        "Win Rate:", f"{result.get('win_rate', 0):.1f}%",
        "P&L Total:", f"${result.get('total_pnl', 0):.2f}",
        "Trades:", len(trade_log),
    ])
    writer.writerow([])

    # En-tête
    writer.writerow([
        "#", "Côté", "Lots",
        "Entrée ($)", "Sortie ($)",
        "P&L ($)", "MAE ($)", "MFE ($)",
        "Ouvert (UTC)", "Fermé (UTC)",
        "Durée (h)", "Commentaire"
    ])

    for i, t in enumerate(trade_log, 1):
        duration_h = ""
        try:
            from datetime import datetime as dt
            opened = dt.fromisoformat(t.get("opened", "").replace("Z", "+00:00"))
            closed = dt.fromisoformat(t.get("closed", "").replace("Z", "+00:00"))
            duration_h = round((closed - opened).total_seconds() / 3600, 2)
        except Exception:
            pass

        writer.writerow([
            i,
            t.get("side", "").upper(),
            t.get("lots", ""),
            t.get("entry", ""),
            t.get("exit", ""),
            t.get("pnl", ""),
            t.get("mae", ""),
            t.get("mfe", ""),
            t.get("opened", ""),
            t.get("closed", ""),
            duration_h,
            t.get("comment", ""),
        ])

    output.seek(0)
    symbol = result.get("symbol", "XAUUSD")
    tf = result.get("timeframe", "M5")
    filename = f"backtest_{job_id}_{symbol}_{tf}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



# ══════════════════════════════════════════════════════════════
# ENDPOINTS — CHUNKED UPLOAD (pour les gros fichiers > 5 MB)
# ══════════════════════════════════════════════════════════════
import tempfile
import shutil

# Stockage temporaire des sessions d'upload en cours
_upload_sessions: dict = {}

@app.post("/api/v1/data/upload-chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    symbol: str = Form("XAUUSD"),
    timeframe: str = Form("M5"),
    filename: str = Form("data.csv"),
    file: UploadFile = File(...),
):
    """Reçoit un chunk d'un fichier CSV MT5 volumineux."""
    # Créer le répertoire temporaire pour cette session
    session_dir = Path(UPLOADS_DIR) / f"session_{upload_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le chunk
    chunk_path = session_dir / f"chunk_{chunk_index:06d}.bin"
    content = await file.read()
    chunk_path.write_bytes(content)

    # Enregistrer les métadonnées de la session
    _upload_sessions[upload_id] = {
        "symbol": symbol,
        "timeframe": timeframe,
        "filename": filename,
        "total_chunks": total_chunks,
        "received_chunks": len(list(session_dir.glob("chunk_*.bin"))),
        "session_dir": str(session_dir),
    }

    return {
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "received": _upload_sessions[upload_id]["received_chunks"],
        "total": total_chunks,
        "status": "chunk_received",
    }


@app.post("/api/v1/data/finalize-upload")
async def finalize_upload(upload_id: str = Form(...)):
    """Réassemble tous les chunks et crée le dataset."""
    if upload_id not in _upload_sessions:
        raise HTTPException(400, f"Session d'upload inconnue: {upload_id}")

    session = _upload_sessions[upload_id]
    session_dir = Path(session["session_dir"])

    # Vérifier que tous les chunks sont présents
    chunks = sorted(session_dir.glob("chunk_*.bin"))
    if len(chunks) != session["total_chunks"]:
        raise HTTPException(400, f"Chunks manquants: {len(chunks)}/{session['total_chunks']}")

    # Réassembler les chunks dans un fichier final
    dataset_id = str(uuid.uuid4())[:8]
    final_path = Path(UPLOADS_DIR) / f"{dataset_id}.csv"

    try:
        with open(final_path, "wb") as out:
            for chunk_path in chunks:
                out.write(chunk_path.read_bytes())

        # Nettoyer les chunks temporaires
        shutil.rmtree(session_dir, ignore_errors=True)
        del _upload_sessions[upload_id]

        # Détecter le format et extraire les métadonnées (utilise _detect_csv_format qui retourne un dict)
        file_size = final_path.stat().st_size
        meta = _detect_csv_format(str(final_path))
        fmt_str = meta.get("format", "generic_csv")
        row_count = meta.get("rows", 0)
        date_start = meta.get("date_start")
        date_end = meta.get("date_end")

        # Enregistrer dans le registre (utilise la variable globale 'datasets')
        size_kb = round(file_size / 1024, 1)
        entry = {
            "id": dataset_id,
            "filename": session["filename"],
            "filepath": str(final_path),
            "symbol": session["symbol"].upper(),
            "timeframe": session["timeframe"].upper(),
            "format": fmt_str,
            "rows": row_count,
            "size_kb": size_kb,
            "date_start": date_start,
            "date_end": date_end,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        datasets[dataset_id] = entry
        _save_dataset_registry(datasets)

        return {
            "dataset_id": dataset_id,
            "filename": session["filename"],
            "symbol": session["symbol"].upper(),
            "timeframe": session["timeframe"].upper(),
            "format": fmt_str,
            "rows": row_count,
            "size_kb": size_kb,
            "date_start": date_start,
            "date_end": date_end,
            "status": "ready",
            "message": f"Dataset assemblé depuis {session['total_chunks']} chunks ({row_count:,} lignes)",
        }

    except Exception as e:
        # Nettoyer en cas d'erreur
        final_path.unlink(missing_ok=True)
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(500, f"Erreur lors de l'assemblage: {str(e)}")


# ── ENTRY POINT ────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
        timeout_keep_alive=600,   # 10 min pour les gros uploads
        h11_max_incomplete_event_size=0,  # Pas de limite sur la taille des requêtes
    )