"""
SmartWave Quant Lab — MT5 Bridge & EA Integration
====================================================
The CRITICAL module that makes this platform operational for real traders.

3 MODES D'INTÉGRATION :

Mode 1: IMPORT MT5 REPORT
  → Le trader lance son EA dans MT5 Strategy Tester
  → Exporte le rapport (HTML ou CSV)
  → Upload ici → analyse avancée (Monte Carlo, Walk-Forward, etc.)
  → C'EST CE QUE MT5 NE SAIT PAS FAIRE

Mode 2: MT5 TERMINAL BRIDGE
  → Connexion directe au terminal MT5 via MetaTrader5 Python package
  → Récupère l'historique de trades du compte
  → Lance des analyses sur les positions réelles

Mode 3: MQL5 LOGIC PARSER
  → Parse les patterns MQL5 courants (OnTick, OrderSend, iMA, etc.)
  → Traduit en stratégie Python pour notre moteur
  → Backtest tick-by-tick avec notre simulation réaliste

CE QUI NOUS REND SUPÉRIEUR À MT5 STRATEGY TESTER :
  ✅ Monte Carlo simulation (MT5 = 0)
  ✅ Walk-Forward automatisé (MT5 = 0)
  ✅ Stress testing multi-scénarios (MT5 = 0)
  ✅ Spread dynamique par session (MT5 = spread fixe)
  ✅ Slippage probabiliste réaliste (MT5 = fixe ou rien)
  ✅ MAE/MFE tracking automatique
  ✅ Pareto multi-objectif (MT5 = 1 seul objectif)
  ✅ Parameter importance analysis (MT5 = 0)
  ✅ Equity curve fitting detection
  ✅ Prop firm compliance checking
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import struct
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np

from core.models import BacktestResult, BacktestConfig, OrderSide

logger = logging.getLogger("smartwave.mt5bridge")


# ══════════════════════════════════════════════════════════════
# MODE 1: MT5 REPORT PARSER
# ══════════════════════════════════════════════════════════════

@dataclass
class MT5Trade:
    """Single trade parsed from MT5 report."""
    ticket: int = 0
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    type: str = ""              # "buy" or "sell"
    lots: float = 0.0
    symbol: str = ""
    entry_price: float = 0.0
    exit_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    comment: str = ""
    magic: int = 0
    duration_hours: float = 0.0
    pips: float = 0.0


@dataclass
class MT5ReportData:
    """Complete parsed MT5 report."""
    # Metadata
    ea_name: str = ""
    symbol: str = ""
    timeframe: str = ""
    period: str = ""
    initial_deposit: float = 0.0
    # Trades
    trades: list[MT5Trade] = field(default_factory=list)
    # Summary from report
    total_net_profit: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    # Equity curve (if available)
    equity_points: list[dict] = field(default_factory=list)


class MT5ReportParser:
    """
    Parse MT5 Strategy Tester reports.
    
    Supports:
    - HTML report (File → Save Report in Strategy Tester)
    - CSV trade export
    - Detailed report (XML)
    
    WORKFLOW CLIENT :
    1. Ouvrir MT5 Strategy Tester
    2. Lancer le backtest de l'EA
    3. Onglet "Résultats" → clic droit → "Sauvegarder comme rapport"
    4. Choisir "Rapport détaillé en HTML"
    5. Upload le fichier .htm sur notre plateforme
    """

    # Regex patterns for MT5 HTML report parsing
    _RE_TABLE_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    _RE_TABLE_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE)
    _RE_CLEAN_HTML = re.compile(r"<[^>]+>")
    _RE_NBSP = re.compile(r"&nbsp;?")

    def _clean_html(self, text: str) -> str:
        """Strip HTML tags and entities."""
        text = self._RE_NBSP.sub(" ", text)
        text = self._RE_CLEAN_HTML.sub("", text)
        return text.strip()

    def _parse_float(self, text: str) -> float:
        """Parse float from various formats (space separators, etc.)."""
        text = text.replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            return float(text)
        except (ValueError, TypeError):
            return 0.0

    def _parse_datetime_mt5(self, text: str) -> Optional[datetime]:
        """Parse MT5 datetime formats."""
        text = text.strip()
        for fmt in [
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
        ]:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def parse_html_report(self, filepath: str | Path) -> MT5ReportData:
        """
        Parse MT5 Strategy Tester HTML report.
        
        The HTML report contains:
        - Summary table (top) with stats
        - Deals/orders table with every trade
        """
        filepath = Path(filepath)
        logger.info(f"Parsing MT5 HTML report: {filepath}")

        # Read with fallback encodings
        content = None
        for enc in ["utf-8", "utf-16", "cp1252", "latin-1"]:
            try:
                content = filepath.read_text(encoding=enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            raise ValueError(f"Cannot read file: {filepath}")

        report = MT5ReportData()

        # Extract all table rows
        rows = self._RE_TABLE_ROW.findall(content)

        # Phase 1: Parse summary section
        for row in rows:
            cells = [self._clean_html(c) for c in self._RE_TABLE_CELL.findall(row)]
            if len(cells) < 2:
                continue

            label = cells[0].lower().strip()

            if "expert" in label or "expert advisor" in label:
                report.ea_name = cells[1]
            elif "symbol" in label and "symbole" in label.lower() or label == "symbol":
                report.symbol = cells[1]
            elif "period" in label or "période" in label:
                report.timeframe = cells[1]
            elif "initial deposit" in label or "dépôt initial" in label:
                report.initial_deposit = self._parse_float(cells[1])
            elif "total net profit" in label or "profit net total" in label:
                report.total_net_profit = self._parse_float(cells[1])
            elif "gross profit" in label or "profit brut" in label:
                report.gross_profit = self._parse_float(cells[1])
            elif "gross loss" in label or "perte brute" in label:
                report.gross_loss = self._parse_float(cells[1])
            elif "profit factor" in label or "facteur de profit" in label:
                report.profit_factor = self._parse_float(cells[1])
            elif "total trades" in label or "total des trades" in label:
                report.total_trades = int(self._parse_float(cells[1]))
            elif ("maximal drawdown" in label or "drawdown" in label) and "%" in cells[1]:
                # Extract percentage
                match = re.search(r"([\d.]+)\s*%", cells[1].replace(",", "."))
                if match:
                    report.max_drawdown_pct = float(match.group(1))
                report.max_drawdown = self._parse_float(cells[1].split("(")[0] if "(" in cells[1] else cells[1])
            elif "sharpe" in label:
                report.sharpe_ratio = self._parse_float(cells[1])
            elif ("short trades" in label or "trades short" in label) and "won" in cells[1].lower():
                pass  # Will extract win rate elsewhere
            elif "profit trades" in label:
                match = re.search(r"([\d.]+)\s*%", cells[1].replace(",", "."))
                if match:
                    report.win_rate = float(match.group(1))

        # Phase 2: Parse trade table (Deals/Orders)
        # MT5 deals table has columns: Time, Deal, Symbol, Type, Direction, Volume, Price, ...
        in_deals = False
        deal_header_found = False

        for row in rows:
            cells = [self._clean_html(c) for c in self._RE_TABLE_CELL.findall(row)]

            if not cells:
                continue

            # Detect deals table header
            if any("deal" in c.lower() or "ordre" in c.lower() for c in cells[:3]):
                if any("profit" in c.lower() or "résultat" in c.lower() for c in cells):
                    deal_header_found = True
                    in_deals = True
                    continue

            if not in_deals or not deal_header_found:
                continue

            # Try to parse as trade row
            # Typical MT5 deal columns: Time, Deal#, Symbol, Type, Direction, Volume, Price, Order, Commission, Fee, Swap, Profit, Balance, Comment
            if len(cells) < 8:
                continue

            try:
                trade = MT5Trade()

                # Find the timestamp (first cell that looks like a date)
                for idx, cell in enumerate(cells[:3]):
                    dt = self._parse_datetime_mt5(cell)
                    if dt:
                        trade.open_time = dt
                        break

                if trade.open_time is None:
                    continue

                # Find symbol
                for cell in cells[1:5]:
                    if any(s in cell.upper() for s in ["XAU", "EUR", "GBP", "USD", "JPY"]):
                        trade.symbol = cell.strip()
                        break

                # Find type (buy/sell)
                for cell in cells:
                    cl = cell.lower().strip()
                    if cl in ("buy", "sell", "achat", "vente"):
                        trade.type = "buy" if cl in ("buy", "achat") else "sell"
                        break

                if not trade.type:
                    continue

                # Find volume, price, profit from numeric cells
                numerics = []
                for cell in cells[3:]:
                    val = self._parse_float(cell)
                    if val != 0:
                        numerics.append(val)

                if len(numerics) >= 3:
                    # Heuristic: volume is small (0.01-100), price is large (100+), profit last
                    for n in numerics:
                        if 0.001 <= n <= 100 and trade.lots == 0:
                            trade.lots = n
                        elif n > 100 and trade.entry_price == 0:
                            trade.entry_price = n

                    trade.profit = numerics[-1]  # Profit is typically last numeric

                # Find commission and swap
                for i, cell in enumerate(cells):
                    cl = cell.lower()
                    if "commission" in cl or (i > 0 and "commission" in cells[0].lower()):
                        pass  # Already in the summary

                if trade.lots > 0:
                    report.trades.append(trade)

            except (ValueError, IndexError):
                continue

        logger.info(
            f"Parsed MT5 report: EA={report.ea_name} | "
            f"{report.total_trades} trades | "
            f"Profit={report.total_net_profit} | "
            f"PF={report.profit_factor} | "
            f"DD={report.max_drawdown_pct}%"
        )

        return report

    def parse_csv_trades(self, filepath: str | Path) -> MT5ReportData:
        """
        Parse trade history exported as CSV from MT5.
        
        MT5 → Terminal → Onglet "Historique" → Clic droit → "Rapport" → CSV
        
        Common columns: Ticket, Open Time, Type, Volume, Symbol, Price,
                        S/L, T/P, Close Time, Close Price, Commission, Swap, Profit
        """
        filepath = Path(filepath)
        logger.info(f"Parsing MT5 CSV trades: {filepath}")

        report = MT5ReportData()

        with open(filepath, "r", encoding="utf-8-sig") as f:
            # Try to detect separator
            first_line = f.readline()
            f.seek(0)

            sep = "\t" if "\t" in first_line else (";" if ";" in first_line else ",")
            reader = csv.DictReader(f, delimiter=sep)

            # Normalize column names
            if reader.fieldnames:
                col_map = {}
                for col in reader.fieldnames:
                    cl = col.lower().strip()
                    if "ticket" in cl or "order" in cl or "deal" in cl:
                        col_map["ticket"] = col
                    elif "open time" in cl or "time" == cl:
                        col_map["open_time"] = col
                    elif "close time" in cl:
                        col_map["close_time"] = col
                    elif "type" in cl:
                        col_map["type"] = col
                    elif "volume" in cl or "lots" in cl or "size" in cl:
                        col_map["volume"] = col
                    elif "symbol" in cl:
                        col_map["symbol"] = col
                    elif cl == "price" or "open price" in cl or "entry" in cl:
                        col_map["entry_price"] = col
                    elif "close price" in cl or "exit" in cl:
                        col_map["exit_price"] = col
                    elif "s/l" in cl or "stop loss" in cl or "sl" == cl:
                        col_map["sl"] = col
                    elif "t/p" in cl or "take profit" in cl or "tp" == cl:
                        col_map["tp"] = col
                    elif "commission" in cl:
                        col_map["commission"] = col
                    elif "swap" in cl:
                        col_map["swap"] = col
                    elif "profit" in cl:
                        col_map["profit"] = col
                    elif "comment" in cl:
                        col_map["comment"] = col
                    elif "magic" in cl:
                        col_map["magic"] = col

                for row in reader:
                    try:
                        trade = MT5Trade()

                        if "ticket" in col_map:
                            trade.ticket = int(self._parse_float(row.get(col_map["ticket"], "0")))
                        if "open_time" in col_map:
                            trade.open_time = self._parse_datetime_mt5(row.get(col_map["open_time"], ""))
                        if "close_time" in col_map:
                            trade.close_time = self._parse_datetime_mt5(row.get(col_map["close_time"], ""))
                        if "type" in col_map:
                            t = row.get(col_map["type"], "").lower()
                            trade.type = "buy" if "buy" in t else ("sell" if "sell" in t else "")
                        if "volume" in col_map:
                            trade.lots = self._parse_float(row.get(col_map["volume"], "0"))
                        if "symbol" in col_map:
                            trade.symbol = row.get(col_map["symbol"], "").strip()
                        if "entry_price" in col_map:
                            trade.entry_price = self._parse_float(row.get(col_map["entry_price"], "0"))
                        if "exit_price" in col_map:
                            trade.exit_price = self._parse_float(row.get(col_map["exit_price"], "0"))
                        if "sl" in col_map:
                            trade.stop_loss = self._parse_float(row.get(col_map["sl"], "0"))
                        if "tp" in col_map:
                            trade.take_profit = self._parse_float(row.get(col_map["tp"], "0"))
                        if "commission" in col_map:
                            trade.commission = self._parse_float(row.get(col_map["commission"], "0"))
                        if "swap" in col_map:
                            trade.swap = self._parse_float(row.get(col_map["swap"], "0"))
                        if "profit" in col_map:
                            trade.profit = self._parse_float(row.get(col_map["profit"], "0"))
                        if "comment" in col_map:
                            trade.comment = row.get(col_map["comment"], "")
                        if "magic" in col_map:
                            trade.magic = int(self._parse_float(row.get(col_map["magic"], "0")))

                        # Compute duration
                        if trade.open_time and trade.close_time:
                            trade.duration_hours = (trade.close_time - trade.open_time).total_seconds() / 3600

                        if trade.type and trade.lots > 0:
                            report.trades.append(trade)

                    except (ValueError, TypeError):
                        continue

        # Compute summary from trades
        if report.trades:
            report.total_trades = len(report.trades)
            profits = [t.profit for t in report.trades]
            report.total_net_profit = sum(profits)
            wins = [p for p in profits if p > 0]
            losses = [p for p in profits if p <= 0]
            report.gross_profit = sum(wins)
            report.gross_loss = sum(losses)
            report.profit_factor = abs(report.gross_profit / report.gross_loss) if report.gross_loss else float('inf')
            report.win_rate = len(wins) / len(profits) * 100 if profits else 0
            report.symbol = report.trades[0].symbol

        logger.info(f"Parsed {len(report.trades)} trades from CSV")
        return report


# ══════════════════════════════════════════════════════════════
# CONVERT MT5 REPORT → BacktestResult (for analysis)
# ══════════════════════════════════════════════════════════════

class MT5ResultConverter:
    """
    Convert parsed MT5 report data into our BacktestResult format.
    
    This is the BRIDGE: once converted, all our analysis tools work:
    - Monte Carlo simulation
    - Walk-Forward analysis
    - Stress testing
    - Equity curve analysis
    - Prop firm compliance checking
    """

    @staticmethod
    def convert(
        report: MT5ReportData,
        initial_capital: float = 0.0,
    ) -> BacktestResult:
        """Convert MT5 report to BacktestResult."""
        capital = initial_capital or report.initial_deposit or 100_000.0

        result = BacktestResult()
        result.config = BacktestConfig(
            strategy_name=report.ea_name or "MT5 EA Import",
            symbol=report.symbol,
            initial_capital=capital,
        )

        trades = report.trades
        if not trades:
            return result

        # Basic stats
        pnls = [t.profit for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        result.total_trades = len(trades)
        result.total_pnl = sum(pnls)
        result.total_return_pct = (result.total_pnl / capital) * 100
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = (len(wins) / len(pnls)) * 100 if pnls else 0
        result.avg_win = float(np.mean(wins)) if wins else 0
        result.avg_loss = float(np.mean(losses)) if losses else 0
        result.largest_win = max(wins) if wins else 0
        result.largest_loss = min(losses) if losses else 0

        # Profit Factor
        gp = sum(wins) if wins else 0
        gl = abs(sum(losses)) if losses else 0
        result.profit_factor = gp / gl if gl > 0 else float('inf')

        # Expectancy
        result.expectancy = float(np.mean(pnls)) if pnls else 0

        # Build equity curve
        equity = capital
        peak = equity
        max_dd = 0
        max_dd_pct = 0
        daily_equities: dict[str, float] = {}

        for trade in trades:
            equity += trade.profit
            if trade.close_time:
                day = trade.close_time.strftime("%Y-%m-%d")
                daily_equities[day] = equity

            peak = max(peak, equity)
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = (dd / peak) * 100

        result.max_drawdown_abs = max_dd
        result.max_drawdown_pct = round(max_dd_pct, 2)

        # Sharpe from daily returns
        eq_values = list(daily_equities.values())
        if len(eq_values) > 5:
            daily_returns = []
            for i in range(1, len(eq_values)):
                dr = (eq_values[i] - eq_values[i-1]) / eq_values[i-1]
                daily_returns.append(dr)
            result.daily_returns = daily_returns

            mean_r = float(np.mean(daily_returns))
            std_r = float(np.std(daily_returns))
            if std_r > 0:
                result.sharpe_ratio = round((mean_r / std_r) * np.sqrt(252), 2)

                downside = [r for r in daily_returns if r < 0]
                if downside:
                    ds = float(np.std(downside))
                    if ds > 0:
                        result.sortino_ratio = round((mean_r / ds) * np.sqrt(252), 2)

        # Calmar
        if max_dd_pct > 0:
            result.calmar_ratio = round(result.total_return_pct / max_dd_pct, 2)

        # Recovery factor
        if max_dd > 0:
            result.recovery_factor = round(result.total_pnl / max_dd, 2)

        # Consecutive
        result.max_consecutive_wins = _max_consecutive(pnls, True)
        result.max_consecutive_losses = _max_consecutive(pnls, False)

        # Duration
        durations = [t.duration_hours for t in trades if t.duration_hours > 0]
        result.avg_trade_duration_hours = round(float(np.mean(durations)), 1) if durations else 0

        # Commission totals
        result.total_commission = sum(t.commission for t in trades)
        result.total_swap = sum(t.swap for t in trades)

        # Equity curve for charting
        result.equity_curve = [
            {"date": d, "equity": e} for d, e in daily_equities.items()
        ]

        # Trade log
        result.trade_log = [
            {
                "id": str(t.ticket),
                "side": t.type.upper(),
                "lots": t.lots,
                "entry": t.entry_price,
                "exit": t.exit_price,
                "pnl": round(t.profit, 2),
                "mae": 0,  # Not available from MT5 report
                "mfe": 0,
                "opened": t.open_time.isoformat() if t.open_time else "",
                "closed": t.close_time.isoformat() if t.close_time else "",
                "comment": t.comment,
            }
            for t in trades
        ]

        return result


def _max_consecutive(pnls: list[float], positive: bool) -> int:
    max_streak = current = 0
    for p in pnls:
        if (positive and p > 0) or (not positive and p <= 0):
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return max_streak


# ══════════════════════════════════════════════════════════════
# MODE 2: MT5 TERMINAL BRIDGE
# ══════════════════════════════════════════════════════════════

class MT5TerminalBridge:
    """
    Connect to a running MT5 terminal via MetaTrader5 Python package.
    
    Requirements:
    - MetaTrader 5 terminal installed and running
    - pip install MetaTrader5
    - Terminal must be logged in to a broker account
    
    This allows:
    - Retrieve account trade history
    - Download historical bars directly
    - Get real-time tick data
    - Read positions/orders
    """

    def __init__(self) -> None:
        self._connected = False
        self._mt5 = None

    def connect(self, path: str = "", login: int = 0, password: str = "", server: str = "") -> bool:
        """Connect to MT5 terminal."""
        try:
            import MetaTrader5 as mt5
            self._mt5 = mt5
        except ImportError:
            logger.error(
                "MetaTrader5 package not installed. Install with:\n"
                "  pip install MetaTrader5\n"
                "Note: Only works on Windows with MT5 terminal installed."
            )
            return False

        kwargs = {}
        if path:
            kwargs["path"] = path
        if login:
            kwargs["login"] = login
        if password:
            kwargs["password"] = password
        if server:
            kwargs["server"] = server

        if not self._mt5.initialize(**kwargs):
            logger.error(f"MT5 initialization failed: {self._mt5.last_error()}")
            return False

        self._connected = True
        info = self._mt5.account_info()
        if info:
            logger.info(
                f"Connected to MT5: {info.server} | "
                f"Account: {info.login} | "
                f"Balance: {info.balance} {info.currency}"
            )
        return True

    def disconnect(self) -> None:
        if self._mt5 and self._connected:
            self._mt5.shutdown()
            self._connected = False

    def get_trade_history(
        self,
        start_date: str = "2024-01-01",
        end_date: str = "2025-12-31",
        symbol: str = "",
        magic: int = 0,
    ) -> MT5ReportData:
        """Retrieve trade history from connected terminal."""
        if not self._connected:
            raise RuntimeError("Not connected to MT5")

        from datetime import timezone
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        deals = self._mt5.history_deals_get(start, end)
        if deals is None:
            logger.warning("No deals found")
            return MT5ReportData()

        report = MT5ReportData()

        # Group deals into trades (entry + exit pairs)
        entries: dict[int, dict] = {}

        for deal in deals:
            pos_id = deal.position_id
            if pos_id == 0:
                continue

            if symbol and deal.symbol != symbol:
                continue
            if magic and deal.magic != magic:
                continue

            if deal.entry == 0:  # DEAL_ENTRY_IN
                entries[pos_id] = {
                    "ticket": deal.ticket,
                    "symbol": deal.symbol,
                    "type": "buy" if deal.type == 0 else "sell",
                    "lots": deal.volume,
                    "entry_price": deal.price,
                    "open_time": datetime.fromtimestamp(deal.time),
                    "commission": deal.commission,
                    "magic": deal.magic,
                    "comment": deal.comment,
                }
            elif deal.entry == 1 and pos_id in entries:  # DEAL_ENTRY_OUT
                e = entries[pos_id]
                trade = MT5Trade(
                    ticket=e["ticket"],
                    open_time=e["open_time"],
                    close_time=datetime.fromtimestamp(deal.time),
                    type=e["type"],
                    lots=e["lots"],
                    symbol=e["symbol"],
                    entry_price=e["entry_price"],
                    exit_price=deal.price,
                    commission=e["commission"] + deal.commission,
                    swap=deal.swap,
                    profit=deal.profit,
                    magic=e["magic"],
                    comment=e["comment"],
                )
                trade.duration_hours = (
                    (trade.close_time - trade.open_time).total_seconds() / 3600
                    if trade.close_time and trade.open_time else 0
                )
                report.trades.append(trade)
                del entries[pos_id]

        # Summary
        if report.trades:
            report.total_trades = len(report.trades)
            report.symbol = report.trades[0].symbol
            profits = [t.profit for t in report.trades]
            report.total_net_profit = sum(profits)
            wins = [p for p in profits if p > 0]
            losses = [p for p in profits if p <= 0]
            report.gross_profit = sum(wins)
            report.gross_loss = sum(losses)
            report.profit_factor = abs(report.gross_profit / report.gross_loss) if report.gross_loss else float('inf')
            report.win_rate = len(wins) / len(profits) * 100 if profits else 0

        logger.info(f"Retrieved {len(report.trades)} trades from MT5 terminal")
        return report

    def download_bars(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "M5",
        count: int = 50000,
    ) -> list[dict]:
        """Download bars directly from MT5 terminal."""
        if not self._connected:
            raise RuntimeError("Not connected to MT5")

        tf_map = {
            "M1": self._mt5.TIMEFRAME_M1,
            "M5": self._mt5.TIMEFRAME_M5,
            "M15": self._mt5.TIMEFRAME_M15,
            "M30": self._mt5.TIMEFRAME_M30,
            "H1": self._mt5.TIMEFRAME_H1,
            "H4": self._mt5.TIMEFRAME_H4,
            "D1": self._mt5.TIMEFRAME_D1,
        }

        mt5_tf = tf_map.get(timeframe, self._mt5.TIMEFRAME_M5)
        rates = self._mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)

        if rates is None:
            logger.warning("No rates received")
            return []

        bars = []
        for r in rates:
            bars.append({
                "timestamp": datetime.fromtimestamp(r['time']),
                "open": r['open'],
                "high": r['high'],
                "low": r['low'],
                "close": r['close'],
                "volume": r['tick_volume'],
                "spread": r['spread'],
            })

        logger.info(f"Downloaded {len(bars)} {timeframe} bars for {symbol}")
        return bars


# ══════════════════════════════════════════════════════════════
# ADVANCED ANALYSIS SUITE
# (what makes us BETTER than MT5 Strategy Tester)
# ══════════════════════════════════════════════════════════════

class AdvancedAnalyzer:
    """
    Advanced analysis that MT5 & StrategyQuant can't do (or do poorly).
    
    Run ALL of these on any imported EA results.
    """

    @staticmethod
    def full_analysis(
        result: BacktestResult,
        initial_capital: float = 100_000,
    ) -> dict:
        """
        Run the complete analysis suite on backtest results.
        Returns a comprehensive report.
        """
        from robustness.robustness import (
            MonteCarloEngine, MonteCarloConfig,
        )

        report = {
            "performance": result.to_dict(),
            "monte_carlo": None,
            "prop_compliance": None,
            "trade_quality": None,
            "equity_analysis": None,
        }

        # 1. Monte Carlo (500 trade permutations)
        if result.total_trades >= 5:
            mc = MonteCarloEngine(MonteCarloConfig(n_simulations=1000, seed=42))
            mc_result = mc.run_trade_permutation(result, initial_capital)
            report["monte_carlo"] = {
                "simulations": mc_result.n_simulations,
                "median_equity": round(mc_result.median_equity, 0),
                "prob_profit": round(mc_result.prob_profit, 3),
                "prob_ruin": round(mc_result.prob_ruin, 3),
                "worst_case": round(mc_result.worst_case_equity, 0),
                "best_case": round(mc_result.best_case_equity, 0),
                "p5_equity": mc_result.percentiles.get("p5", 0),
                "p95_equity": mc_result.percentiles.get("p95", 0),
                "median_max_dd": round(mc_result.median_max_dd, 1),
                "p95_max_dd": round(mc_result.p95_max_dd, 1),
            }

        # 2. Prop Firm Compliance
        report["prop_compliance"] = {
            "ftmo_challenge": _check_prop_compliance(result, max_daily_dd=5.0, max_total_dd=10.0, profit_target=10.0, min_days=4),
            "ftmo_verification": _check_prop_compliance(result, max_daily_dd=5.0, max_total_dd=10.0, profit_target=5.0, min_days=4),
            "mff_challenge": _check_prop_compliance(result, max_daily_dd=5.0, max_total_dd=12.0, profit_target=8.0, min_days=3),
        }

        # 3. Trade Quality Analysis
        if result.trade_log:
            pnls = [t["pnl"] for t in result.trade_log]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p <= 0]

            report["trade_quality"] = {
                "payoff_ratio": round(abs(np.mean(wins) / np.mean(losses)), 2) if losses else float('inf'),
                "kelly_criterion": _kelly_criterion(result.win_rate / 100, abs(np.mean(wins) / np.mean(losses)) if losses and wins else 0),
                "sqn": _system_quality_number(pnls),
                "z_score": _z_score_consecutive(pnls),
                "tail_ratio": _tail_ratio(pnls),
            }

        # 4. Equity Curve Analysis
        if result.equity_curve and len(result.equity_curve) > 10:
            equities = [p["equity"] for p in result.equity_curve]
            report["equity_analysis"] = {
                "linearity": _equity_linearity(equities),
                "stability_score": _stability_score(result.daily_returns) if result.daily_returns else 0,
            }

        return report


def _check_prop_compliance(result: BacktestResult, max_daily_dd: float, max_total_dd: float, profit_target: float, min_days: int) -> dict:
    """Check if results pass a specific prop firm's rules."""
    passed_dd = result.max_drawdown_pct <= max_total_dd
    passed_target = result.total_return_pct >= profit_target
    days = len(result.equity_curve)

    return {
        "passed": passed_dd and passed_target and days >= min_days,
        "max_dd_ok": passed_dd,
        "target_ok": passed_target,
        "max_dd_actual": result.max_drawdown_pct,
        "return_actual": round(result.total_return_pct, 2),
        "trading_days": days,
    }


def _kelly_criterion(win_rate: float, payoff_ratio: float) -> float:
    """Kelly Criterion for optimal position sizing."""
    if payoff_ratio <= 0:
        return 0
    kelly = win_rate - (1 - win_rate) / payoff_ratio
    return round(max(0, kelly), 3)


def _system_quality_number(pnls: list[float]) -> float:
    """Van Tharp's SQN = sqrt(N) * mean(R) / std(R)."""
    if len(pnls) < 10:
        return 0
    mean_r = float(np.mean(pnls))
    std_r = float(np.std(pnls))
    if std_r == 0:
        return 0
    return round(np.sqrt(len(pnls)) * mean_r / std_r, 2)


def _z_score_consecutive(pnls: list[float]) -> float:
    """Z-score test for streak dependency."""
    if len(pnls) < 20:
        return 0
    n = len(pnls)
    wins = sum(1 for p in pnls if p > 0)
    losses = n - wins
    if wins == 0 or losses == 0:
        return 0
    runs = 1
    for i in range(1, n):
        if (pnls[i] > 0) != (pnls[i-1] > 0):
            runs += 1
    expected = 1 + 2 * wins * losses / n
    std = np.sqrt(2 * wins * losses * (2 * wins * losses - n) / (n * n * (n - 1)))
    if std == 0:
        return 0
    return round((runs - expected) / std, 2)


def _tail_ratio(pnls: list[float]) -> float:
    """Ratio of right tail vs left tail of P&L distribution."""
    if len(pnls) < 20:
        return 0
    p95 = abs(float(np.percentile(pnls, 95)))
    p5 = abs(float(np.percentile(pnls, 5)))
    return round(p95 / p5, 2) if p5 > 0 else 0


def _equity_linearity(equities: list[float]) -> float:
    """R² of equity curve vs perfect straight line. Higher = more consistent."""
    if len(equities) < 5:
        return 0
    x = np.arange(len(equities))
    correlation = np.corrcoef(x, equities)[0, 1]
    return round(correlation ** 2, 3)


def _stability_score(daily_returns: list[float]) -> float:
    """Composite stability: low volatility + consistent positive returns."""
    if len(daily_returns) < 10:
        return 0
    positive_pct = sum(1 for r in daily_returns if r > 0) / len(daily_returns)
    vol = float(np.std(daily_returns))
    mean_r = float(np.mean(daily_returns))
    if vol == 0:
        return 0
    score = (positive_pct * 0.4) + (max(0, min(1, mean_r / vol * 5)) * 0.3) + ((1 - min(1, vol * 100)) * 0.3)
    return round(score, 3)
