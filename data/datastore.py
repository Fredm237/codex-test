"""
SmartWave Quant Lab — Data Layer
==================================
Tick data management: loading, storage, and synthetic generation.

Supports:
- Parquet columnar storage (production)
- CSV import (legacy MT5 exports)
- Synthetic tick data generation (for testing)
- Bar aggregation from ticks
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np

from core.models import Tick, Bar, Timeframe

logger = logging.getLogger("smartwave.data")


class SyntheticTickGenerator:
    """
    Generate realistic synthetic tick data for testing.
    
    Uses a geometric Brownian motion (GBM) model with:
    - Mean-reverting volatility (Heston-like)
    - Session-dependent activity
    - Realistic bid-ask spread modeling
    - Microstructure noise
    """

    def __init__(
        self,
        symbol: str = "XAUUSD",
        base_price: float = 2700.0,
        annual_vol: float = 0.18,
        ticks_per_day: int = 50_000,
        seed: int = 42,
    ) -> None:
        self.symbol = symbol
        self.base_price = base_price
        self.annual_vol = annual_vol
        self.ticks_per_day = ticks_per_day
        self._rng = np.random.default_rng(seed)

    def generate(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2025-12-31",
        include_weekends: bool = False,
    ) -> list[Tick]:
        """Generate synthetic tick data for the date range."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days

        logger.info(f"Generating synthetic ticks: {start_date} to {end_date} ({days} days)")

        ticks: list[Tick] = []
        price = self.base_price
        vol = self.annual_vol
        dt = 1.0 / (252 * self.ticks_per_day)  # time step

        for day in range(days):
            current_date = start + timedelta(days=day)

            # Skip weekends
            if not include_weekends and current_date.weekday() >= 5:
                continue

            # Vary activity by session
            for tick_num in range(self.ticks_per_day):
                # Time within day (0-24 hours)
                hour_frac = (tick_num / self.ticks_per_day) * 24
                hour = int(hour_frac)
                minute = int((hour_frac - hour) * 60)
                second = int(((hour_frac - hour) * 60 - minute) * 60)

                timestamp = current_date.replace(
                    hour=hour, minute=minute, second=second, microsecond=0
                )

                # GBM price evolution
                dW = self._rng.standard_normal()
                drift = 0.0001 * dt  # small drift
                diffusion = vol * np.sqrt(dt) * dW
                price *= (1 + drift + diffusion)

                # Mean-reverting volatility
                vol_mean = self.annual_vol
                vol_speed = 0.5
                vol_vol = 0.1
                dW_vol = self._rng.standard_normal()
                vol += vol_speed * (vol_mean - vol) * dt + vol_vol * np.sqrt(dt) * dW_vol
                vol = max(0.05, min(0.50, vol))  # Clamp

                # Spread (session-dependent)
                base_spread_pts = 20.0
                if hour < 7:  # Asian
                    spread_mult = 1.3
                elif 12 <= hour < 16:  # London-NY overlap
                    spread_mult = 0.7
                elif hour >= 20:  # Rollover
                    spread_mult = 1.8
                else:
                    spread_mult = 1.0

                spread_pts = base_spread_pts * spread_mult * (1 + self._rng.exponential(0.2))
                spread = spread_pts * 0.01  # Convert to price

                bid = round(price - spread / 2, 2)
                ask = round(price + spread / 2, 2)

                # Volume (higher during London/NY)
                base_vol = 10.0
                if 7 <= hour < 20:
                    vol_mult = 2.0 + self._rng.exponential(0.5)
                else:
                    vol_mult = 0.5 + self._rng.exponential(0.2)

                tick = Tick(
                    timestamp=timestamp,
                    bid=bid,
                    ask=ask,
                    bid_volume=round(base_vol * vol_mult * self._rng.exponential(1.0), 1),
                    ask_volume=round(base_vol * vol_mult * self._rng.exponential(1.0), 1),
                )
                ticks.append(tick)

        logger.info(f"Generated {len(ticks)} ticks")
        return ticks

    def generate_bars(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2025-12-31",
        timeframe: Timeframe = Timeframe.M5,
    ) -> list[Bar]:
        """Generate synthetic OHLCV bars (faster than tick generation)."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        bars_per_day = 86400 // timeframe.seconds

        bars: list[Bar] = []
        price = self.base_price

        for day in range(days):
            current_date = start + timedelta(days=day)
            if current_date.weekday() >= 5:
                continue

            for bar_num in range(bars_per_day):
                seconds_offset = bar_num * timeframe.seconds
                timestamp = current_date + timedelta(seconds=seconds_offset)

                # OHLC generation
                open_price = price
                returns = self._rng.standard_normal(4) * self.annual_vol * np.sqrt(timeframe.seconds / (252 * 86400))
                intrabar = np.cumsum(returns) * open_price
                high = open_price + abs(max(intrabar))
                low = open_price - abs(min(intrabar))
                close = open_price + intrabar[-1]
                price = close

                volume = float(self._rng.exponential(100))

                bars.append(Bar(
                    timestamp=timestamp,
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    volume=round(volume, 1),
                    timeframe=timeframe,
                ))

        logger.info(f"Generated {len(bars)} {timeframe.value} bars")
        return bars


class ParquetDataStore:
    """
    Parquet-based tick data storage.
    
    Directory structure:
      data/
        XAUUSD/
          ticks/
            2024-01.parquet
            2024-02.parquet
          bars/
            M5/
              2024.parquet
    """

    def __init__(self, base_path: str = "./data") -> None:
        self.base_path = Path(base_path)

    def save_ticks(self, symbol: str, ticks: list[Tick]) -> Path:
        """Save ticks to Parquet file."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            logger.warning("pyarrow not installed, falling back to CSV")
            return self._save_ticks_csv(symbol, ticks)

        path = self.base_path / symbol / "ticks"
        path.mkdir(parents=True, exist_ok=True)

        # Build Arrow table
        table = pa.table({
            "timestamp": [t.timestamp for t in ticks],
            "bid": [t.bid for t in ticks],
            "ask": [t.ask for t in ticks],
            "bid_volume": [t.bid_volume for t in ticks],
            "ask_volume": [t.ask_volume for t in ticks],
        })

        filepath = path / f"{symbol}_ticks.parquet"
        pq.write_table(table, filepath, compression="zstd")
        logger.info(f"Saved {len(ticks)} ticks to {filepath}")
        return filepath

    def load_ticks(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[Tick]:
        """Load ticks from Parquet."""
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return self._load_ticks_csv(symbol)

        filepath = self.base_path / symbol / "ticks" / f"{symbol}_ticks.parquet"
        if not filepath.exists():
            logger.warning(f"No tick data found at {filepath}")
            return []

        table = pq.read_table(filepath)
        df = table.to_pandas()

        # Date filtering
        if start_date:
            df = df[df["timestamp"] >= start_date]
        if end_date:
            df = df[df["timestamp"] <= end_date]

        ticks = [
            Tick(
                timestamp=row["timestamp"],
                bid=row["bid"],
                ask=row["ask"],
                bid_volume=row["bid_volume"],
                ask_volume=row["ask_volume"],
            )
            for _, row in df.iterrows()
        ]

        logger.info(f"Loaded {len(ticks)} ticks from {filepath}")
        return ticks

    def _save_ticks_csv(self, symbol: str, ticks: list[Tick]) -> Path:
        """Fallback CSV storage."""
        path = self.base_path / symbol / "ticks"
        path.mkdir(parents=True, exist_ok=True)
        filepath = path / f"{symbol}_ticks.csv"

        with open(filepath, "w") as f:
            f.write("timestamp,bid,ask,bid_volume,ask_volume\n")
            for t in ticks:
                f.write(f"{t.timestamp.isoformat()},{t.bid},{t.ask},{t.bid_volume},{t.ask_volume}\n")

        return filepath

    def _load_ticks_csv(self, symbol: str) -> list[Tick]:
        """Fallback CSV loading."""
        filepath = self.base_path / symbol / "ticks" / f"{symbol}_ticks.csv"
        if not filepath.exists():
            return []

        ticks = []
        with open(filepath) as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split(",")
                ticks.append(Tick(
                    timestamp=datetime.fromisoformat(parts[0]),
                    bid=float(parts[1]),
                    ask=float(parts[2]),
                    bid_volume=float(parts[3]),
                    ask_volume=float(parts[4]),
                ))
        return ticks
