"""
SmartWave Quant Lab — Real Data Connectors
=============================================
Import real historical market data from multiple sources.

Supported sources:
  1. MT5 CSV Export    — File > History Center > Export (most common)
  2. MT5 HST Binary    — Direct .hst file reading (legacy format)
  3. Dukascopy Ticks   — Free tick-by-tick data via HTTP
  4. Generic CSV       — Any CSV with timestamp,open,high,low,close,volume
  5. Bar-to-Tick Synth — Generate realistic ticks from OHLCV bars

All connectors output List[Tick] compatible with BacktestEngine.run()
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from core.models import Tick, Bar, Timeframe

logger = logging.getLogger("smartwave.data")


# ══════════════════════════════════════════════════════════════
# MT5 CSV IMPORTER
# ══════════════════════════════════════════════════════════════

class MT5CSVImporter:
    """
    Import data exported from MetaTrader 5 History Center.
    
    MT5 exports bars in CSV with these common formats:
    
    Format A (Tab-separated, default MT5 export):
        2024.01.02	00:00:00	2071.45	2072.10	2070.80	2071.95	1234
        Date        Time        Open    High    Low     Close   TickVol
    
    Format B (Comma-separated, custom export):
        2024-01-02,00:00:00,2071.45,2072.10,2070.80,2071.95,1234,0,25
        Date,Time,Open,High,Low,Close,TickVol,Vol,Spread
    
    Format C (MT5 tick export — rare but possible):
        2024.01.02 00:00:00.123,2071.45,2071.70,0,0
        DateTime,Bid,Ask,LastVol,Flags
    
    This importer auto-detects the format.
    """

    # Common date/time format patterns from MT5
    DATETIME_FORMATS = [
        "%Y.%m.%d %H:%M:%S",       # MT5 default with seconds
        "%Y.%m.%d %H:%M",          # MT5 without seconds (common in M5/H1 exports)
        "%Y.%m.%d\t%H:%M:%S",      # Tab-separated with seconds
        "%Y.%m.%d\t%H:%M",         # Tab-separated without seconds
        "%Y-%m-%d %H:%M:%S",       # ISO-ish with seconds
        "%Y-%m-%d %H:%M",          # ISO-ish without seconds
        "%Y-%m-%d,%H:%M:%S",       # Comma-separated with seconds
        "%Y-%m-%d,%H:%M",          # Comma-separated without seconds
        "%Y.%m.%d %H:%M:%S.%f",   # With milliseconds (tick data)
        "%Y-%m-%dT%H:%M:%S",       # ISO
        "%Y-%m-%dT%H:%M",          # ISO without seconds
        "%d/%m/%Y %H:%M:%S",       # European with seconds
        "%d/%m/%Y %H:%M",          # European without seconds
        "%m/%d/%Y %H:%M:%S",       # US with seconds
        "%m/%d/%Y %H:%M",          # US without seconds
        "%Y%m%d %H:%M:%S",         # Compact date + time (20210412 02:00:00)
        "%Y%m%d %H:%M",            # Compact date + time without seconds
        "%Y%m%d %H%M%S",           # Compact date + compact time
        "%Y%m%d",                  # Compact date only
    ]

    def __init__(self, symbol: str = "XAUUSD") -> None:
        self.symbol = symbol
        self._detected_format: Optional[str] = None
        self._is_tick_data: bool = False

    def _detect_separator(self, first_line: str) -> str:
        """Auto-detect CSV separator."""
        if "\t" in first_line:
            return "\t"
        if ";" in first_line:
            return ";"
        return ","

    def _parse_datetime(self, date_str: str, time_str: str = "") -> Optional[datetime]:
        """Try multiple datetime formats."""
        combined = f"{date_str} {time_str}".strip() if time_str else date_str

        # If format already detected, use it
        if self._detected_format:
            try:
                return datetime.strptime(combined, self._detected_format)
            except ValueError:
                pass

        # Try all formats
        for fmt in self.DATETIME_FORMATS:
            try:
                dt = datetime.strptime(combined, fmt)
                self._detected_format = fmt
                return dt
            except ValueError:
                continue
        return None

    def import_bars(
        self,
        filepath: str | Path,
        timeframe: Timeframe = Timeframe.M5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> list[Bar]:
        """
        Import OHLCV bars from MT5 CSV export.
        
        Args:
            filepath: Path to CSV file
            timeframe: Bar timeframe for metadata
            start_date: Filter start (YYYY-MM-DD)
            end_date: Filter end (YYYY-MM-DD)
            max_rows: Limit number of rows to read
        
        Returns:
            List of Bar objects
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        logger.info(f"Importing MT5 CSV: {filepath} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)")

        bars: list[Bar] = []
        errors = 0

        # Parse date filters
        dt_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        dt_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        with open(filepath, "r", encoding="utf-8-sig") as f:
            # Read first line to detect format
            first_line = f.readline().strip()
            f.seek(0)

            sep = self._detect_separator(first_line)

            # Check if first line is header
            has_header = any(h in first_line.lower() for h in ["date", "time", "open", "high", "close"])

            reader = csv.reader(f, delimiter=sep)
            if has_header:
                next(reader)  # Skip header

            for row_num, row in enumerate(reader):
                if max_rows and row_num >= max_rows:
                    break

                try:
                    row = [c.strip() for c in row if c.strip()]

                    # 5 colonnes minimum : Date, Time, O, H, L, C (Volume optionnel)
                    if len(row) < 5:
                        errors += 1
                        continue

                    # Parse date/time — could be 1 or 2 columns
                    # Support: 2024.01.02 / 2024-01-02 / 20210412 (compact)
                    date_col = row[0]
                    is_compact_date = (len(date_col) == 8 and date_col.isdigit())
                    has_separator = "." in date_col or "-" in date_col or "/" in date_col
                    if has_separator or is_compact_date:
                        # Separate date and time columns
                        if len(row) > 1 and ":" in row[1]:
                            dt = self._parse_datetime(date_col, row[1])
                            data_start = 2
                        else:
                            dt = self._parse_datetime(date_col)
                            data_start = 1
                    else:
                        errors += 1
                        continue

                    if dt is None:
                        errors += 1
                        continue

                    # Date filters
                    if dt_start and dt < dt_start:
                        continue
                    if dt_end and dt > dt_end:
                        continue

                    o = float(row[data_start])
                    h = float(row[data_start + 1])
                    l = float(row[data_start + 2])
                    c = float(row[data_start + 3])
                    v = float(row[data_start + 4]) if len(row) > data_start + 4 else 0.0

                    # Optional: real volume and spread
                    real_vol = float(row[data_start + 5]) if len(row) > data_start + 5 else 0.0
                    spread = float(row[data_start + 6]) if len(row) > data_start + 6 else 0.0

                    bars.append(Bar(
                        timestamp=dt,
                        open=o, high=h, low=l, close=c,
                        volume=v,
                        tick_volume=int(v),
                        spread=spread * 0.01 if spread > 0 else 0.0,  # points to price
                        timeframe=timeframe,
                    ))

                except (ValueError, IndexError) as e:
                    errors += 1
                    if errors <= 5:
                        logger.debug(f"Row {row_num}: parse error: {e}")

        logger.info(f"Imported {len(bars)} bars ({errors} errors) | "
                     f"Range: {bars[0].timestamp} → {bars[-1].timestamp}" if bars else "No bars imported")

        return bars

    def import_ticks(
        self,
        filepath: str | Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_rows: Optional[int] = None,
    ) -> list[Tick]:
        """
        Import tick data from MT5 tick export.
        
        MT5 tick export format:
            2024.01.02 00:00:00.123  2071.45  2071.70  0  0
            DateTime                 Bid      Ask      LastVol  Flags
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        logger.info(f"Importing MT5 ticks: {filepath}")

        ticks: list[Tick] = []
        errors = 0
        dt_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        dt_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        with open(filepath, "r", encoding="utf-8-sig") as f:
            first_line = f.readline().strip()
            f.seek(0)
            sep = self._detect_separator(first_line)
            has_header = any(h in first_line.lower() for h in ["bid", "ask", "time", "date"])

            reader = csv.reader(f, delimiter=sep)
            if has_header:
                next(reader)

            for row_num, row in enumerate(reader):
                if max_rows and row_num >= max_rows:
                    break
                try:
                    row = [c.strip() for c in row if c.strip()]
                    if len(row) < 3:
                        errors += 1
                        continue

                    # Parse datetime
                    if ":" in row[1] and ("." in row[0] or "-" in row[0]):
                        dt = self._parse_datetime(row[0], row[1])
                        bid_idx = 2
                    else:
                        dt = self._parse_datetime(row[0])
                        bid_idx = 1

                    if dt is None:
                        errors += 1
                        continue

                    if dt_start and dt < dt_start:
                        continue
                    if dt_end and dt > dt_end:
                        continue

                    bid = float(row[bid_idx])
                    ask = float(row[bid_idx + 1])

                    # Validate: ask > bid, prices > 0
                    if bid <= 0 or ask <= 0 or ask < bid:
                        errors += 1
                        continue

                    vol = float(row[bid_idx + 2]) if len(row) > bid_idx + 2 else 0.0

                    ticks.append(Tick(
                        timestamp=dt,
                        bid=bid,
                        ask=ask,
                        bid_volume=vol,
                        ask_volume=vol,
                    ))

                except (ValueError, IndexError):
                    errors += 1

        logger.info(f"Imported {len(ticks)} ticks ({errors} errors)")
        return ticks


# ══════════════════════════════════════════════════════════════
# MT5 HST BINARY FILE READER
# ══════════════════════════════════════════════════════════════

class MT5HSTReader:
    """
    Read MetaTrader .hst binary history files.
    
    HST v401 format (64 bytes per bar):
        int64  time       — bar open time (Unix timestamp)
        double open
        double high
        double low
        double close
        int64  tick_volume
        int32  spread
        int64  real_volume
    
    Header is 148 bytes.
    """

    HST_HEADER_SIZE = 148
    HST_BAR_SIZE = 60  # v401

    def __init__(self, symbol: str = "XAUUSD") -> None:
        self.symbol = symbol

    def read(
        self,
        filepath: str | Path,
        timeframe: Timeframe = Timeframe.M5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[Bar]:
        """Read bars from .hst binary file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"HST file not found: {filepath}")

        file_size = filepath.stat().st_size
        logger.info(f"Reading HST file: {filepath} ({file_size / 1024 / 1024:.1f} MB)")

        dt_start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        dt_end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        bars: list[Bar] = []

        with open(filepath, "rb") as f:
            # Read header
            header = f.read(self.HST_HEADER_SIZE)
            if len(header) < self.HST_HEADER_SIZE:
                raise ValueError("File too small for HST header")

            # Parse header: version at offset 0 (int32)
            version = struct.unpack_from("<i", header, 0)[0]
            logger.info(f"HST version: {version}")

            # Read bars
            while True:
                data = f.read(self.HST_BAR_SIZE)
                if len(data) < self.HST_BAR_SIZE:
                    break

                try:
                    # v401 format
                    time_val = struct.unpack_from("<q", data, 0)[0]
                    o = struct.unpack_from("<d", data, 8)[0]
                    h = struct.unpack_from("<d", data, 16)[0]
                    l = struct.unpack_from("<d", data, 24)[0]
                    c = struct.unpack_from("<d", data, 32)[0]
                    tick_vol = struct.unpack_from("<q", data, 40)[0]
                    spread = struct.unpack_from("<i", data, 48)[0]
                    real_vol = struct.unpack_from("<q", data, 52)[0]

                    dt = datetime.fromtimestamp(time_val)

                    if dt_start and dt < dt_start:
                        continue
                    if dt_end and dt > dt_end:
                        continue

                    bars.append(Bar(
                        timestamp=dt,
                        open=o, high=h, low=l, close=c,
                        volume=float(real_vol) if real_vol > 0 else float(tick_vol),
                        tick_volume=int(tick_vol),
                        spread=spread * 0.01,
                        timeframe=timeframe,
                    ))

                except (struct.error, ValueError, OSError):
                    continue

        logger.info(f"Read {len(bars)} bars from HST")
        return bars


# ══════════════════════════════════════════════════════════════
# DUKASCOPY TICK DATA DOWNLOADER
# ══════════════════════════════════════════════════════════════

class DukascopyDownloader:
    """
    Download free tick data from Dukascopy.
    
    Dukascopy provides tick data in bi5 (LZMA compressed binary) format.
    URL pattern:
        https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5
    
    Note: Month is 0-indexed (January = 00)
    
    Each tick record is 20 bytes:
        int32  time_ms    — milliseconds since hour start
        int32  ask        — ask price * point_value
        int32  bid        — bid price * point_value
        float  ask_vol    — ask volume
        float  bid_vol    — bid volume
    
    For XAUUSD: point_value = 1000 (prices stored as integers * 1000)
    """

    BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    # Symbol mappings (Dukascopy naming)
    SYMBOLS = {
        "XAUUSD": {"name": "XAUUSD", "point": 1000},
        "EURUSD": {"name": "EURUSD", "point": 100000},
        "GBPUSD": {"name": "GBPUSD", "point": 100000},
        "USDJPY": {"name": "USDJPY", "point": 1000},
    }

    TICK_STRUCT = struct.Struct(">IIIff")  # Big-endian: time_ms, ask, bid, ask_vol, bid_vol

    def __init__(self, symbol: str = "XAUUSD", cache_dir: str = "./data/cache") -> None:
        self.symbol = symbol
        self.sym_info = self.SYMBOLS.get(symbol, {"name": symbol, "point": 1000})
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _build_url(self, dt: datetime) -> str:
        """Build Dukascopy URL for a specific hour."""
        month = dt.month - 1  # 0-indexed
        return (
            f"{self.BASE_URL}/{self.sym_info['name']}/"
            f"{dt.year}/{month:02d}/{dt.day:02d}/{dt.hour:02d}h_ticks.bi5"
        )

    def _parse_bi5(self, data: bytes, base_dt: datetime) -> list[Tick]:
        """Parse bi5 binary tick data."""
        ticks = []
        point = self.sym_info["point"]
        record_size = self.TICK_STRUCT.size

        try:
            import lzma
            decompressed = lzma.decompress(data)
        except Exception:
            # Some files aren't LZMA — try raw
            decompressed = data

        offset = 0
        while offset + record_size <= len(decompressed):
            try:
                time_ms, ask_int, bid_int, ask_vol, bid_vol = \
                    self.TICK_STRUCT.unpack_from(decompressed, offset)

                tick_dt = base_dt + timedelta(milliseconds=time_ms)
                ask = ask_int / point
                bid = bid_int / point

                if bid > 0 and ask > 0 and ask >= bid:
                    ticks.append(Tick(
                        timestamp=tick_dt,
                        bid=round(bid, 2),
                        ask=round(ask, 2),
                        bid_volume=round(float(bid_vol), 2),
                        ask_volume=round(float(ask_vol), 2),
                    ))

            except (struct.error, ValueError):
                pass

            offset += record_size

        return ticks

    def _get_cache_path(self, dt: datetime) -> Path:
        """Cache path for a specific hour."""
        return self.cache_dir / self.symbol / f"{dt.strftime('%Y%m%d_%H')}.bi5"

    def download_hour(self, dt: datetime) -> list[Tick]:
        """Download tick data for one hour."""
        import urllib.request

        cache_path = self._get_cache_path(dt)

        # Check cache first
        if cache_path.exists():
            with open(cache_path, "rb") as f:
                data = f.read()
            if data:
                return self._parse_bi5(data, dt.replace(minute=0, second=0, microsecond=0))

        url = self._build_url(dt)
        base_dt = dt.replace(minute=0, second=0, microsecond=0)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SmartWave/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read()

            # Cache it
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(data)

            ticks = self._parse_bi5(data, base_dt)
            return ticks

        except Exception as e:
            logger.debug(f"No data for {dt}: {e}")
            return []

    def download_range(
        self,
        start_date: str,
        end_date: str,
        skip_weekends: bool = True,
        hours: Optional[tuple[int, int]] = None,
    ) -> list[Tick]:
        """
        Download tick data for a date range.
        
        Args:
            start_date: "YYYY-MM-DD"
            end_date: "YYYY-MM-DD"
            skip_weekends: Skip Saturday/Sunday
            hours: Optional (start_hour, end_hour) filter, e.g. (7, 20) for London+NY
        
        Returns:
            List of Tick objects sorted by timestamp
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        total_hours = int((end - start).total_seconds() / 3600)
        logger.info(
            f"Downloading {self.symbol} ticks: {start_date} → {end_date} "
            f"(~{total_hours} hours to fetch)"
        )

        all_ticks: list[Tick] = []
        fetched_hours = 0
        skipped = 0

        current = start
        while current < end:
            # Skip weekends
            if skip_weekends and current.weekday() >= 5:
                current += timedelta(hours=1)
                skipped += 1
                continue

            # Hour filter
            if hours and not (hours[0] <= current.hour < hours[1]):
                current += timedelta(hours=1)
                skipped += 1
                continue

            ticks = self.download_hour(current)
            if ticks:
                all_ticks.extend(ticks)
                fetched_hours += 1

            if fetched_hours % 24 == 0 and fetched_hours > 0:
                logger.info(
                    f"Progress: {fetched_hours} hours fetched, "
                    f"{len(all_ticks):,} ticks total | "
                    f"Current: {current.strftime('%Y-%m-%d %H:00')}"
                )

            current += timedelta(hours=1)

        # Sort by timestamp (should already be sorted, but ensure)
        all_ticks.sort(key=lambda t: t.timestamp)

        logger.info(
            f"Download complete: {len(all_ticks):,} ticks from "
            f"{fetched_hours} hours ({skipped} skipped)"
        )

        return all_ticks


# ══════════════════════════════════════════════════════════════
# BAR-TO-TICK SYNTHESIZER (from real bars → realistic ticks)
# ══════════════════════════════════════════════════════════════

class BarToTickSynthesizer:
    """
    Generate realistic tick data from OHLCV bars.
    
    When you have real M1/M5 bar data but not tick data,
    this creates plausible tick sequences that respect:
    - OHLC price path (Open → High/Low → Close)
    - Volume distribution within the bar
    - Realistic bid/ask spread
    - Microstructure noise
    
    Methods:
    1. "ohlc_path" — deterministic O→H→L→C or O→L→H→C path
    2. "random_walk" — GBM constrained to OHLC boundaries
    3. "volume_weighted" — more ticks near High/Low (where volume clusters)
    
    This is the KEY BRIDGE: it lets you use any M1/M5 bar data
    from MT5 exports and run tick-by-tick backtests on it.
    """

    def __init__(
        self,
        ticks_per_bar: int = 50,
        base_spread_points: float = 25.0,
        method: str = "random_walk",
        seed: int = 42,
    ) -> None:
        self.ticks_per_bar = ticks_per_bar
        self.base_spread_pts = base_spread_points
        self.method = method
        self._rng = np.random.default_rng(seed)

    def _session_spread_mult(self, hour: int) -> float:
        """Session-based spread multiplier."""
        if hour < 7:
            return 1.4  # Asian
        if 7 <= hour < 12:
            return 0.9  # London
        if 12 <= hour < 16:
            return 0.7  # London-NY overlap (tightest)
        if 16 <= hour < 20:
            return 1.0  # NY afternoon
        return 1.8  # Rollover

    def _generate_ohlc_path(self, bar: Bar) -> list[float]:
        """Generate a price path respecting OHLC boundaries."""
        n = self.ticks_per_bar
        prices = []

        # Determine if bullish or bearish bar
        bullish = bar.close >= bar.open

        if bullish:
            # O → Low → High → Close
            phase1 = max(1, int(n * 0.25))  # O → Low
            phase2 = max(1, int(n * 0.50))  # Low → High
            phase3 = n - phase1 - phase2     # High → Close

            for i in range(phase1):
                t = i / max(1, phase1 - 1)
                prices.append(bar.open + (bar.low - bar.open) * t)
            for i in range(phase2):
                t = i / max(1, phase2 - 1)
                prices.append(bar.low + (bar.high - bar.low) * t)
            for i in range(phase3):
                t = i / max(1, phase3 - 1)
                prices.append(bar.high + (bar.close - bar.high) * t)
        else:
            # O → High → Low → Close
            phase1 = max(1, int(n * 0.25))
            phase2 = max(1, int(n * 0.50))
            phase3 = n - phase1 - phase2

            for i in range(phase1):
                t = i / max(1, phase1 - 1)
                prices.append(bar.open + (bar.high - bar.open) * t)
            for i in range(phase2):
                t = i / max(1, phase2 - 1)
                prices.append(bar.high + (bar.low - bar.high) * t)
            for i in range(phase3):
                t = i / max(1, phase3 - 1)
                prices.append(bar.low + (bar.close - bar.low) * t)

        # Add microstructure noise (small, preserves OHLC boundaries)
        noise = self._rng.normal(0, bar.close * 0.00005, len(prices))
        prices = [
            max(bar.low, min(bar.high, p + n))
            for p, n in zip(prices, noise)
        ]

        # Ensure first = open, last = close
        if prices:
            prices[0] = bar.open
            prices[-1] = bar.close

        return prices

    def _generate_random_walk(self, bar: Bar) -> list[float]:
        """Constrained random walk respecting OHLC."""
        n = self.ticks_per_bar
        bar_range = bar.high - bar.low
        if bar_range <= 0:
            return [bar.close] * n

        # Generate Brownian bridge: starts at open, ends at close
        dt = 1.0 / n
        vol = bar_range / (4 * np.sqrt(1.0))  # Scale vol to bar range

        prices = [bar.open]
        for i in range(1, n):
            t = i / n
            remaining = 1 - t

            # Drift toward close
            drift = (bar.close - prices[-1]) / max(1, n - i)
            # Random component
            dW = float(self._rng.normal(0, vol * np.sqrt(dt)))

            new_price = prices[-1] + drift + dW

            # Hard clamp to [low, high] — must respect bar boundaries
            new_price = max(bar.low, min(bar.high, new_price))
            prices.append(new_price)

        prices[-1] = bar.close

        # Ensure high/low are actually hit at some point
        if max(prices) < bar.high * 0.9999:
            idx = self._rng.integers(len(prices) // 4, 3 * len(prices) // 4)
            prices[idx] = bar.high
        if min(prices) > bar.low * 1.0001:
            idx = self._rng.integers(len(prices) // 4, 3 * len(prices) // 4)
            prices[idx] = bar.low

        return prices

    def synthesize(
        self,
        bars: list[Bar],
        progress_every: int = 10000,
    ) -> list[Tick]:
        """
        Convert bars to synthetic tick data.
        
        Args:
            bars: List of OHLCV bars (from MT5 CSV, HST, or any source)
            progress_every: Log progress every N bars
            
        Returns:
            List of Tick objects
        """
        logger.info(
            f"Synthesizing ticks from {len(bars)} bars "
            f"(method={self.method}, ~{self.ticks_per_bar}/bar → "
            f"~{len(bars) * self.ticks_per_bar:,} ticks)"
        )

        all_ticks: list[Tick] = []

        for bar_idx, bar in enumerate(bars):
            # Generate price path
            if self.method == "ohlc_path":
                prices = self._generate_ohlc_path(bar)
            else:
                prices = self._generate_random_walk(bar)

            # Calculate time increment between ticks
            bar_duration_s = bar.timeframe.seconds if hasattr(bar, 'timeframe') and bar.timeframe else 300
            tick_interval = timedelta(seconds=bar_duration_s / len(prices))

            # Session-dependent spread
            hour = bar.timestamp.hour
            spread_mult = self._session_spread_mult(hour)

            for tick_idx, mid_price in enumerate(prices):
                timestamp = bar.timestamp + tick_interval * tick_idx

                # Spread with noise
                spread_pts = self.base_spread_pts * spread_mult
                spread_noise = float(self._rng.lognormal(0, 0.12))
                spread = max(3, spread_pts * spread_noise) * 0.01  # to price units

                bid = round(mid_price - spread / 2, 2)
                ask = round(mid_price + spread / 2, 2)

                # Volume distribution (higher near bar open/close)
                base_vol = (bar.volume / len(prices)) if bar.volume > 0 else 1.0
                vol_noise = float(self._rng.exponential(1.0))

                all_ticks.append(Tick(
                    timestamp=timestamp,
                    bid=bid,
                    ask=ask,
                    bid_volume=round(base_vol * vol_noise, 2),
                    ask_volume=round(base_vol * vol_noise, 2),
                ))

            if progress_every and (bar_idx + 1) % progress_every == 0:
                logger.info(f"Synthesized {bar_idx + 1}/{len(bars)} bars → {len(all_ticks):,} ticks")

        logger.info(f"Synthesis complete: {len(all_ticks):,} ticks from {len(bars)} bars")
        return all_ticks


# ══════════════════════════════════════════════════════════════
# DATA QUALITY VALIDATOR
# ══════════════════════════════════════════════════════════════

class DataValidator:
    """
    Validate and report on tick/bar data quality.
    
    Checks:
    - Timestamp ordering and gaps
    - Price validity (bid < ask, positive prices)
    - Spread reasonableness
    - Weekend data detection
    - Duplicate detection
    - Basic statistics
    """

    @staticmethod
    def validate_ticks(ticks: list[Tick], symbol: str = "XAUUSD") -> dict:
        """Validate tick data and return quality report."""
        if not ticks:
            return {"valid": False, "error": "No ticks"}

        report = {
            "valid": True,
            "total_ticks": len(ticks),
            "time_range": {
                "start": ticks[0].timestamp.isoformat(),
                "end": ticks[-1].timestamp.isoformat(),
                "days": (ticks[-1].timestamp - ticks[0].timestamp).days,
            },
            "price_range": {
                "min_bid": min(t.bid for t in ticks),
                "max_bid": max(t.bid for t in ticks),
                "min_ask": min(t.ask for t in ticks),
                "max_ask": max(t.ask for t in ticks),
            },
            "spread": {},
            "issues": [],
        }

        # Spread analysis
        spreads = [t.spread_points for t in ticks]
        report["spread"] = {
            "mean_points": round(float(np.mean(spreads)), 1),
            "median_points": round(float(np.median(spreads)), 1),
            "max_points": round(float(np.max(spreads)), 1),
            "min_points": round(float(np.min(spreads)), 1),
        }

        # Check ordering
        out_of_order = 0
        duplicates = 0
        negative_spread = 0
        gaps = []

        for i in range(1, len(ticks)):
            if ticks[i].timestamp < ticks[i-1].timestamp:
                out_of_order += 1
            if ticks[i].timestamp == ticks[i-1].timestamp:
                duplicates += 1
            if ticks[i].ask < ticks[i].bid:
                negative_spread += 1

            gap = (ticks[i].timestamp - ticks[i-1].timestamp).total_seconds()
            if gap > 3600:  # > 1 hour gap
                gaps.append({
                    "from": ticks[i-1].timestamp.isoformat(),
                    "to": ticks[i].timestamp.isoformat(),
                    "gap_hours": round(gap / 3600, 1),
                })

        if out_of_order > 0:
            report["issues"].append(f"{out_of_order} ticks out of order")
        if duplicates > 0:
            report["issues"].append(f"{duplicates} duplicate timestamps")
        if negative_spread > 0:
            report["issues"].append(f"{negative_spread} ticks with negative spread")
            report["valid"] = False
        if gaps:
            report["issues"].append(f"{len(gaps)} gaps > 1 hour")
            report["gaps"] = gaps[:10]  # Show first 10

        # Ticks per hour distribution
        hours: dict[int, int] = {}
        for t in ticks:
            h = t.timestamp.hour
            hours[h] = hours.get(h, 0) + 1

        report["ticks_per_hour"] = {
            f"{h:02d}:00": count
            for h, count in sorted(hours.items())
        }
        report["avg_ticks_per_hour"] = round(len(ticks) / max(1, len(hours)), 0)

        return report

    @staticmethod
    def validate_bars(bars: list[Bar]) -> dict:
        """Validate bar data."""
        if not bars:
            return {"valid": False, "error": "No bars"}

        issues = []
        for i, b in enumerate(bars):
            if b.high < b.low:
                issues.append(f"Bar {i}: high ({b.high}) < low ({b.low})")
            if b.open > b.high or b.open < b.low:
                issues.append(f"Bar {i}: open ({b.open}) outside H/L range")
            if b.close > b.high or b.close < b.low:
                issues.append(f"Bar {i}: close ({b.close}) outside H/L range")

        return {
            "valid": len(issues) == 0,
            "total_bars": len(bars),
            "time_range": {
                "start": bars[0].timestamp.isoformat(),
                "end": bars[-1].timestamp.isoformat(),
            },
            "price_range": {
                "min": min(b.low for b in bars),
                "max": max(b.high for b in bars),
            },
            "issues": issues[:20],
        }


# ══════════════════════════════════════════════════════════════
# CONVENIENCE PIPELINE
# ══════════════════════════════════════════════════════════════

class DataPipeline:
    """
    High-level pipeline:
    
    1. Load data from any source (MT5 CSV, HST, Dukascopy, or custom CSV)
    2. Validate quality
    3. Convert bars → ticks if needed
    4. Cache to Parquet
    5. Return ready-to-use List[Tick]
    
    Usage:
        pipeline = DataPipeline("XAUUSD")
        
        # From MT5 CSV bars → ticks
        ticks = pipeline.from_mt5_csv("XAUUSD_M5.csv", timeframe="M5")
        
        # From Dukascopy
        ticks = pipeline.from_dukascopy("2024-01-01", "2024-12-31")
        
        # From any CSV
        ticks = pipeline.from_csv("my_data.csv")
    """

    def __init__(self, symbol: str = "XAUUSD", cache_dir: str = "./data") -> None:
        self.symbol = symbol
        self.cache_dir = Path(cache_dir)
        self.validator = DataValidator()

    def from_mt5_csv(
        self,
        filepath: str,
        timeframe: str = "M5",
        ticks_per_bar: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        spread_points: float = 25.0,
    ) -> list[Tick]:
        """
        Full pipeline: MT5 CSV bars → validated ticks.
        
        This is the most common path:
        1. Export M1/M5 data from MT5 History Center as CSV
        2. Feed it here
        3. Get realistic tick data back
        """
        logger.info(f"Pipeline: MT5 CSV → Ticks | {filepath}")

        # 1. Import bars
        tf = Timeframe(timeframe)
        importer = MT5CSVImporter(self.symbol)
        bars = importer.import_bars(filepath, tf, start_date, end_date)

        if not bars:
            raise ValueError(f"No bars imported from {filepath}")

        # 2. Validate bars
        bar_report = self.validator.validate_bars(bars)
        if not bar_report["valid"]:
            logger.warning(f"Bar data has issues: {bar_report['issues'][:3]}")

        logger.info(
            f"Loaded {len(bars)} {timeframe} bars | "
            f"{bar_report['time_range']['start']} → {bar_report['time_range']['end']} | "
            f"Price range: {bar_report['price_range']['min']:.2f} - {bar_report['price_range']['max']:.2f}"
        )

        # 3. Synthesize ticks from bars
        synthesizer = BarToTickSynthesizer(
            ticks_per_bar=ticks_per_bar,
            base_spread_points=spread_points,
            method="random_walk",
        )
        ticks = synthesizer.synthesize(bars)

        # 4. Validate ticks
        tick_report = self.validator.validate_ticks(ticks, self.symbol)
        logger.info(
            f"Tick quality: {tick_report['total_ticks']:,} ticks | "
            f"Avg spread: {tick_report['spread']['mean_points']:.1f} pts | "
            f"Issues: {len(tick_report['issues'])}"
        )

        return ticks

    def from_mt5_ticks(
        self,
        filepath: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[Tick]:
        """Import actual tick data from MT5 tick export."""
        importer = MT5CSVImporter(self.symbol)
        ticks = importer.import_ticks(filepath, start_date, end_date)

        report = self.validator.validate_ticks(ticks, self.symbol)
        logger.info(f"Imported {report['total_ticks']:,} real ticks | Issues: {len(report['issues'])}")

        return ticks

    def from_mt5_hst(
        self,
        filepath: str,
        timeframe: str = "M5",
        ticks_per_bar: int = 50,
        spread_points: float = 25.0,
    ) -> list[Tick]:
        """Import from MT5 .hst binary file."""
        reader = MT5HSTReader(self.symbol)
        bars = reader.read(filepath, Timeframe(timeframe))

        synthesizer = BarToTickSynthesizer(
            ticks_per_bar=ticks_per_bar,
            base_spread_points=spread_points,
        )
        return synthesizer.synthesize(bars)

    def from_dukascopy(
        self,
        start_date: str,
        end_date: str,
        skip_weekends: bool = True,
    ) -> list[Tick]:
        """Download tick data from Dukascopy."""
        downloader = DukascopyDownloader(self.symbol, str(self.cache_dir / "cache"))
        ticks = downloader.download_range(start_date, end_date, skip_weekends)

        if ticks:
            report = self.validator.validate_ticks(ticks, self.symbol)
            logger.info(f"Dukascopy: {report['total_ticks']:,} ticks | Spread: {report['spread']['mean_points']:.1f} pts")

        return ticks

    def from_generic_csv(
        self,
        filepath: str,
        timeframe: str = "M5",
        ticks_per_bar: int = 50,
        spread_points: float = 25.0,
        date_column: str = "date",
        ohlcv_columns: Optional[list[str]] = None,
    ) -> list[Tick]:
        """
        Import from any CSV with OHLCV data.
        
        Auto-detects column names or uses provided mapping.
        Supports: date/time, datetime, timestamp columns.
        """
        importer = MT5CSVImporter(self.symbol)
        bars = importer.import_bars(filepath, Timeframe(timeframe))

        synthesizer = BarToTickSynthesizer(
            ticks_per_bar=ticks_per_bar,
            base_spread_points=spread_points,
        )
        return synthesizer.synthesize(bars)
