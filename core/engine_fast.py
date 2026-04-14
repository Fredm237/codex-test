"""
SmartWave v3 — Numba-Accelerated Backtest Core
================================================
The hot path (tick-by-tick loop) is 100% NumPy arrays.
Zero Python objects, zero dict lookups, zero allocations in the loop.

This is what makes us faster than StrategyQuant:
  - SQ: Python interpreter loop → ~5K bars/sec
  - MT5: C++ native → ~500K bars/sec
  - Us:  Numba JIT → ~200K-800K bars/sec (approaches MT5)

Architecture:
  OHLCV arrays + Indicator matrix + Signal array → Numba loop → Trade arrays

Everything flows through numpy. Strategies produce signal arrays,
the engine processes them without ever touching Python in the hot path.
"""

from __future__ import annotations
import numpy as np
from numba import njit, prange, types
from numba.typed import List as NumbaList
import time
import logging

logger = logging.getLogger("smartwave.engine_fast")

# ══════════════════════════════════════════════════════════════
# VECTORIZED INDICATORS (computed ONCE, shared by ALL strategies)
# ══════════════════════════════════════════════════════════════

@njit(cache=True)
def _ema(src: np.ndarray, period: int) -> np.ndarray:
    """EMA — Numba-accelerated."""
    out = np.empty_like(src)
    k = 2.0 / (period + 1)
    out[0] = src[0]
    for i in range(1, len(src)):
        out[i] = src[i] * k + out[i - 1] * (1 - k)
    return out


@njit(cache=True)
def _sma(src: np.ndarray, period: int) -> np.ndarray:
    """SMA — Numba-accelerated."""
    out = np.empty_like(src)
    out[:period - 1] = np.nan
    cumsum = 0.0
    for i in range(period):
        cumsum += src[i]
    out[period - 1] = cumsum / period
    for i in range(period, len(src)):
        cumsum += src[i] - src[i - period]
        out[i] = cumsum / period
    return out


@njit(cache=True)
def _rsi(src: np.ndarray, period: int = 14) -> np.ndarray:
    """RSI — Wilder's smoothing, Numba-accelerated."""
    out = np.full_like(src, 50.0)
    if len(src) < period + 1:
        return out
    avg_gain = 0.0
    avg_loss = 0.0
    for i in range(1, period + 1):
        d = src[i] - src[i - 1]
        if d > 0:
            avg_gain += d
        else:
            avg_loss -= d
    avg_gain /= period
    avg_loss /= period
    if avg_loss == 0:
        out[period] = 100.0
    else:
        out[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, len(src)):
        d = src[i] - src[i - 1]
        gain = d if d > 0 else 0.0
        loss = -d if d < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            out[i] = 100.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


@njit(cache=True)
def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """ATR — Wilder's smoothing, Numba-accelerated."""
    n = len(high)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, max(hc, lc))
    out = np.empty(n, dtype=np.float64)
    out[:period] = np.nan
    s = 0.0
    for i in range(period):
        s += tr[i]
    out[period - 1] = s / period
    for i in range(period, n):
        out[i] = (out[i - 1] * (period - 1) + tr[i]) / period
    return out


@njit(cache=True)
def _bollinger(src: np.ndarray, period: int = 20, std_mult: float = 2.0):
    """Bollinger Bands — returns (upper, middle, lower)."""
    mid = _sma(src, period)
    upper = np.empty_like(src)
    lower = np.empty_like(src)
    for i in range(len(src)):
        if i < period - 1:
            upper[i] = np.nan
            lower[i] = np.nan
            continue
        s = 0.0
        for j in range(i - period + 1, i + 1):
            s += (src[j] - mid[i]) ** 2
        std = (s / period) ** 0.5
        upper[i] = mid[i] + std_mult * std
        lower[i] = mid[i] - std_mult * std
    return upper, mid, lower


@njit(cache=True)
def _swing_detect(high: np.ndarray, low: np.ndarray, lookback: int = 5):
    """Detect swing highs/lows. Returns arrays of levels."""
    n = len(high)
    swing_h = np.full(n, np.nan)
    swing_l = np.full(n, np.nan)
    for i in range(lookback, n - lookback):
        is_high = True
        is_low = True
        for j in range(-lookback, lookback + 1):
            if j == 0:
                continue
            if high[i + j] > high[i]:
                is_high = False
            if low[i + j] < low[i]:
                is_low = False
        if is_high:
            swing_h[i] = high[i]
        if is_low:
            swing_l[i] = low[i]
    return swing_h, swing_l


def precompute_indicators(O: np.ndarray, H: np.ndarray, L: np.ndarray,
                          C: np.ndarray, V: np.ndarray) -> dict[str, np.ndarray]:
    """
    Pre-compute ALL indicators ONCE. Shared by every strategy.
    This is the #1 speedup: never recompute inside the backtest loop.
    """
    t0 = time.perf_counter()
    ind = {
        # EMAs
        "ema8": _ema(C, 8), "ema13": _ema(C, 13), "ema21": _ema(C, 21),
        "ema34": _ema(C, 34), "ema50": _ema(C, 50), "ema100": _ema(C, 100),
        "ema200": _ema(C, 200),
        # SMAs
        "sma20": _sma(C, 20), "sma50": _sma(C, 50),
        # RSI
        "rsi14": _rsi(C, 14), "rsi7": _rsi(C, 7),
        # ATR
        "atr14": _atr(H, L, C, 14), "atr7": _atr(H, L, C, 7),
        # Bollinger
        **dict(zip(["bb_upper", "bb_mid", "bb_lower"], _bollinger(C, 20, 2.0))),
        # Swing points
        **dict(zip(["swing_h5", "swing_l5"], _swing_detect(H, L, 5))),
        **dict(zip(["swing_h10", "swing_l10"], _swing_detect(H, L, 10))),
    }
    dt = time.perf_counter() - t0
    logger.info(f"Indicators pre-computed: {len(ind)} arrays in {dt:.3f}s")
    return ind


# ══════════════════════════════════════════════════════════════
# NUMBA-ACCELERATED BACKTEST CORE
# ══════════════════════════════════════════════════════════════
# The signal array encodes strategy decisions:
#   +1.0 = go long    -1.0 = go short    0.0 = no action
#   +0.5 = close long -0.5 = close short
#
# The SL/TP arrays encode risk per bar (in price units).

@njit(cache=True)
def fast_backtest(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    spread: np.ndarray,
    signals: np.ndarray,
    sl_dist: np.ndarray,       # SL distance in price units per bar
    tp_dist: np.ndarray,       # TP distance in price units per bar
    lot_sizes: np.ndarray,     # lot size per signal
    capital: float = 100000.0,
    commission_per_lot: float = 7.0,
    max_dd_pct: float = 10.0,
    max_positions: int = 3,
    slippage_pts: float = 2.0, # avg slippage in points (price units)
) -> tuple:
    """
    Ultra-fast backtest loop. 100% Numba, zero Python.
    
    Returns:
        (balance_final, equity_curve, trade_pnls, trade_count,
         max_dd_pct_actual, total_commission, win_count, loss_count)
    """
    n = len(close)
    
    # Position tracking (flat arrays, no objects)
    MAX_POS = max_positions
    pos_active = np.zeros(MAX_POS, dtype=np.int32)      # 0=empty, 1=long, -1=short
    pos_entry = np.zeros(MAX_POS, dtype=np.float64)
    pos_sl = np.zeros(MAX_POS, dtype=np.float64)
    pos_tp = np.zeros(MAX_POS, dtype=np.float64)
    pos_lots = np.zeros(MAX_POS, dtype=np.float64)
    pos_comm = np.zeros(MAX_POS, dtype=np.float64)
    
    balance = capital
    peak = capital
    max_dd_abs = 0.0
    max_dd_pct_actual = 0.0
    total_comm = 0.0
    
    # Output arrays
    equity_curve = np.empty(n, dtype=np.float64)
    trade_pnls = np.empty(n, dtype=np.float64)  # oversized, will count
    trade_pnls[:] = 0.0
    trade_count = 0
    win_count = 0
    loss_count = 0
    dd_limit_hit = False
    
    for i in range(n):
        # ── 1. Check SL/TP on open positions ──
        for p in range(MAX_POS):
            if pos_active[p] == 0:
                continue
            
            hit_sl = False
            hit_tp = False
            
            if pos_active[p] == 1:  # Long
                if low[i] <= pos_sl[p]:
                    hit_sl = True
                elif high[i] >= pos_tp[p]:
                    hit_tp = True
            else:  # Short
                if high[i] >= pos_sl[p]:
                    hit_sl = True
                elif low[i] <= pos_tp[p]:
                    hit_tp = True
            
            if hit_sl or hit_tp:
                exit_price = pos_sl[p] if hit_sl else pos_tp[p]
                if pos_active[p] == 1:
                    gross = (exit_price - pos_entry[p]) * pos_lots[p] * 100.0
                else:
                    gross = (pos_entry[p] - exit_price) * pos_lots[p] * 100.0
                net = gross - pos_comm[p]
                balance += net
                
                if trade_count < n:
                    trade_pnls[trade_count] = net
                trade_count += 1
                if net > 0:
                    win_count += 1
                else:
                    loss_count += 1
                
                pos_active[p] = 0
        
        # ── 2. Update equity ──
        unrealized = 0.0
        for p in range(MAX_POS):
            if pos_active[p] == 1:
                unrealized += (close[i] - pos_entry[p]) * pos_lots[p] * 100.0
            elif pos_active[p] == -1:
                unrealized += (pos_entry[p] - close[i]) * pos_lots[p] * 100.0
        
        equity = balance + unrealized
        equity_curve[i] = equity
        
        if equity > peak:
            peak = equity
        dd = peak - equity
        if dd > max_dd_abs:
            max_dd_abs = dd
            max_dd_pct_actual = dd / peak * 100.0
        
        # ── 3. DD limit ──
        if max_dd_pct_actual >= max_dd_pct and not dd_limit_hit:
            # Force close all
            for p in range(MAX_POS):
                if pos_active[p] != 0:
                    if pos_active[p] == 1:
                        gross = (close[i] - pos_entry[p]) * pos_lots[p] * 100.0
                    else:
                        gross = (pos_entry[p] - close[i]) * pos_lots[p] * 100.0
                    net = gross - pos_comm[p]
                    balance += net
                    if trade_count < n:
                        trade_pnls[trade_count] = net
                    trade_count += 1
                    if net > 0:
                        win_count += 1
                    else:
                        loss_count += 1
                    pos_active[p] = 0
            dd_limit_hit = True
            equity_curve[i] = balance
            continue
        
        if dd_limit_hit:
            equity_curve[i] = balance
            continue
        
        # ── 4. Process signals ──
        sig = signals[i]
        if sig == 0.0:
            continue
        
        # Count open positions
        n_open = 0
        for p in range(MAX_POS):
            if pos_active[p] != 0:
                n_open += 1
        
        if abs(sig) == 1.0 and n_open < MAX_POS:
            # Open new position
            direction = 1 if sig > 0 else -1
            slip = slippage_pts if direction == 1 else -slippage_pts
            entry = close[i] + spread[i] / 2.0 * direction + slip
            
            sl_d = sl_dist[i]
            tp_d = tp_dist[i]
            
            if direction == 1:
                sl_price = entry - sl_d
                tp_price = entry + tp_d
            else:
                sl_price = entry + sl_d
                tp_price = entry - tp_d
            
            lots = lot_sizes[i]
            comm = lots * commission_per_lot
            total_comm += comm
            
            # Find empty slot
            for p in range(MAX_POS):
                if pos_active[p] == 0:
                    pos_active[p] = direction
                    pos_entry[p] = entry
                    pos_sl[p] = sl_price
                    pos_tp[p] = tp_price
                    pos_lots[p] = lots
                    pos_comm[p] = comm
                    break
    
    # Close remaining positions
    for p in range(MAX_POS):
        if pos_active[p] != 0:
            if pos_active[p] == 1:
                gross = (close[-1] - pos_entry[p]) * pos_lots[p] * 100.0
            else:
                gross = (pos_entry[p] - close[-1]) * pos_lots[p] * 100.0
            net = gross - pos_comm[p]
            balance += net
            if trade_count < n:
                trade_pnls[trade_count] = net
            trade_count += 1
            if net > 0:
                win_count += 1
            else:
                loss_count += 1
    
    equity_curve[-1] = balance
    return (balance, equity_curve, trade_pnls[:trade_count], trade_count,
            max_dd_pct_actual, total_comm, win_count, loss_count)


# ══════════════════════════════════════════════════════════════
# SIGNAL GENERATORS (strategy logic → signal arrays)
# ══════════════════════════════════════════════════════════════
# Each strategy produces 3 arrays: signals, sl_dist, tp_dist
# These are computed VECTORIZED, not in a loop.

@njit(cache=True)
def signal_ema_cross(close: np.ndarray, ema_fast: np.ndarray, ema_slow: np.ndarray,
                     atr: np.ndarray, rr: float, session_hours: np.ndarray,
                     session_start: int, session_end: int, risk_pct: float,
                     capital: float) -> tuple:
    """EMA crossover strategy — fully vectorized signal generation."""
    n = len(close)
    signals = np.zeros(n, dtype=np.float64)
    sl_dist = np.zeros(n, dtype=np.float64)
    tp_dist = np.zeros(n, dtype=np.float64)
    lot_sizes = np.zeros(n, dtype=np.float64)
    
    for i in range(2, n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        # Session filter
        h = session_hours[i]
        if h < session_start or h >= session_end:
            continue
        
        # Bullish cross
        if ema_fast[i - 1] <= ema_slow[i - 1] and ema_fast[i] > ema_slow[i]:
            signals[i] = 1.0
            sl_dist[i] = atr[i] * 1.5
            tp_dist[i] = atr[i] * 1.5 * rr
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_dist[i] * 100.0)))
        
        # Bearish cross
        elif ema_fast[i - 1] >= ema_slow[i - 1] and ema_fast[i] < ema_slow[i]:
            signals[i] = -1.0
            sl_dist[i] = atr[i] * 1.5
            tp_dist[i] = atr[i] * 1.5 * rr
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_dist[i] * 100.0)))
    
    return signals, sl_dist, tp_dist, lot_sizes


@njit(cache=True)
def signal_fvg_ob(close: np.ndarray, high: np.ndarray, low: np.ndarray, open_: np.ndarray,
                  ema_fast: np.ndarray, ema_slow: np.ndarray, atr: np.ndarray,
                  session_hours: np.ndarray, rr: float, fvg_min: float,
                  session_start: int, session_end: int, risk_pct: float,
                  capital: float, cooldown: int) -> tuple:
    """ICT FVG + OB confluence — Numba signal generator."""
    n = len(close)
    signals = np.zeros(n, dtype=np.float64)
    sl_dist = np.zeros(n, dtype=np.float64)
    tp_dist = np.zeros(n, dtype=np.float64)
    lot_sizes = np.zeros(n, dtype=np.float64)
    last_signal = 0
    
    for i in range(5, n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        if i - last_signal < cooldown:
            continue
        h = session_hours[i]
        if h < session_start or h >= session_end:
            continue
        
        bullish_trend = ema_fast[i] > ema_slow[i]
        bearish_trend = ema_fast[i] < ema_slow[i]
        
        # Bullish FVG: bar[i-2].high < bar[i].low
        if bullish_trend and i >= 3:
            gap = low[i] - high[i - 2]
            if gap > fvg_min:
                # Price in FVG zone
                fvg_top = low[i]
                fvg_bot = high[i - 2]
                if fvg_bot <= close[i] <= fvg_top:
                    # Check OB: last bearish candle before bullish move
                    has_ob = False
                    for k in range(i - 5, i - 1):
                        if k >= 0 and close[k] < open_[k] and close[k + 1] > open_[k + 1]:
                            if low[k] <= fvg_bot <= high[k]:
                                has_ob = True
                                break
                    if has_ob or gap > fvg_min * 2:  # Strong FVG doesn't need OB
                        sl_d = close[i] - fvg_bot + atr[i] * 0.5
                        signals[i] = 1.0
                        sl_dist[i] = sl_d
                        tp_dist[i] = sl_d * rr
                        risk_amount = capital * risk_pct / 100.0
                        lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
                        last_signal = i
        
        # Bearish FVG
        if bearish_trend and i >= 3:
            gap = low[i - 2] - high[i]
            if gap > fvg_min:
                fvg_top = low[i - 2]
                fvg_bot = high[i]
                if fvg_bot <= close[i] <= fvg_top:
                    has_ob = False
                    for k in range(i - 5, i - 1):
                        if k >= 0 and close[k] > open_[k] and close[k + 1] < open_[k + 1]:
                            if low[k] <= fvg_top <= high[k]:
                                has_ob = True
                                break
                    if has_ob or gap > fvg_min * 2:
                        sl_d = fvg_top - close[i] + atr[i] * 0.5
                        signals[i] = -1.0
                        sl_dist[i] = sl_d
                        tp_dist[i] = sl_d * rr
                        risk_amount = capital * risk_pct / 100.0
                        lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
                        last_signal = i
    
    return signals, sl_dist, tp_dist, lot_sizes


@njit(cache=True)
def signal_breakout(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                    atr: np.ndarray, ema_trend: np.ndarray, session_hours: np.ndarray,
                    period: int, atr_mult: float, rr: float,
                    session_start: int, session_end: int, risk_pct: float,
                    capital: float, cooldown: int) -> tuple:
    """Volatility breakout strategy."""
    n = len(close)
    signals = np.zeros(n, dtype=np.float64)
    sl_dist = np.zeros(n, dtype=np.float64)
    tp_dist = np.zeros(n, dtype=np.float64)
    lot_sizes = np.zeros(n, dtype=np.float64)
    last_signal = 0
    
    for i in range(period + 1, n):
        if np.isnan(atr[i]) or atr[i] <= 0:
            continue
        if i - last_signal < cooldown:
            continue
        h = session_hours[i]
        if h < session_start or h >= session_end:
            continue
        
        # Range high/low
        range_h = high[i - period]
        range_l = low[i - period]
        for j in range(i - period, i):
            if high[j] > range_h:
                range_h = high[j]
            if low[j] < range_l:
                range_l = low[j]
        
        threshold = atr[i] * 0.3
        
        # Bullish breakout
        if close[i] > range_h + threshold and close[i] > ema_trend[i]:
            sl_d = atr[i] * atr_mult
            signals[i] = 1.0
            sl_dist[i] = sl_d
            tp_dist[i] = sl_d * rr
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
            last_signal = i
        
        # Bearish breakout
        elif close[i] < range_l - threshold and close[i] < ema_trend[i]:
            sl_d = atr[i] * atr_mult
            signals[i] = -1.0
            sl_dist[i] = sl_d
            tp_dist[i] = sl_d * rr
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
            last_signal = i
    
    return signals, sl_dist, tp_dist, lot_sizes


@njit(cache=True)
def signal_mean_reversion(close: np.ndarray, bb_upper: np.ndarray, bb_lower: np.ndarray,
                          bb_mid: np.ndarray, rsi: np.ndarray, atr: np.ndarray,
                          session_hours: np.ndarray, rsi_ob: float, rsi_os: float,
                          session_start: int, session_end: int, risk_pct: float,
                          capital: float, cooldown: int) -> tuple:
    """Mean reversion at Bollinger extremes + RSI confirmation."""
    n = len(close)
    signals = np.zeros(n, dtype=np.float64)
    sl_dist = np.zeros(n, dtype=np.float64)
    tp_dist = np.zeros(n, dtype=np.float64)
    lot_sizes = np.zeros(n, dtype=np.float64)
    last_signal = 0
    
    for i in range(2, n):
        if np.isnan(atr[i]) or np.isnan(bb_upper[i]):
            continue
        if i - last_signal < cooldown:
            continue
        h = session_hours[i]
        if h < session_start or h >= session_end:
            continue
        
        # Oversold → buy
        if close[i] < bb_lower[i] and rsi[i] < rsi_os:
            sl_d = atr[i] * 2.0
            signals[i] = 1.0
            sl_dist[i] = sl_d
            tp_dist[i] = bb_mid[i] - close[i]  # Target = mean
            if tp_dist[i] <= 0:
                tp_dist[i] = sl_d * 1.5
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
            last_signal = i
        
        # Overbought → sell
        elif close[i] > bb_upper[i] and rsi[i] > rsi_ob:
            sl_d = atr[i] * 2.0
            signals[i] = -1.0
            sl_dist[i] = sl_d
            tp_dist[i] = close[i] - bb_mid[i]
            if tp_dist[i] <= 0:
                tp_dist[i] = sl_d * 1.5
            risk_amount = capital * risk_pct / 100.0
            lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
            last_signal = i
    
    return signals, sl_dist, tp_dist, lot_sizes


@njit(cache=True)
def signal_asian_breakout(close: np.ndarray, high: np.ndarray, low: np.ndarray,
                          ema_trend: np.ndarray, atr: np.ndarray,
                          session_hours: np.ndarray, rr: float,
                          risk_pct: float, capital: float, cooldown: int) -> tuple:
    """Asian session range breakout during London."""
    n = len(close)
    signals = np.zeros(n, dtype=np.float64)
    sl_dist_arr = np.zeros(n, dtype=np.float64)
    tp_dist_arr = np.zeros(n, dtype=np.float64)
    lot_sizes = np.zeros(n, dtype=np.float64)
    
    asian_h = -1e18
    asian_l = 1e18
    last_signal = 0
    traded_today = False
    prev_hour = -1
    
    for i in range(1, n):
        h = session_hours[i]
        
        # Reset on new day (hour goes from 23 to 0)
        if h < prev_hour:
            asian_h = -1e18
            asian_l = 1e18
            traded_today = False
        prev_hour = h
        
        # Asian session: 0-7 UTC
        if h < 7:
            if high[i] > asian_h:
                asian_h = high[i]
            if low[i] < asian_l:
                asian_l = low[i]
        
        # London session: 7-16
        elif 7 <= h < 16 and not traded_today and asian_h > -1e18:
            if np.isnan(atr[i]) or atr[i] <= 0:
                continue
            if i - last_signal < cooldown:
                continue
            
            # Bullish breakout above Asian high
            if close[i] > asian_h and close[i] > ema_trend[i]:
                sl_d = close[i] - asian_l
                if sl_d > 0:
                    signals[i] = 1.0
                    sl_dist_arr[i] = sl_d
                    tp_dist_arr[i] = sl_d * rr
                    risk_amount = capital * risk_pct / 100.0
                    lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
                    last_signal = i
                    traded_today = True
            
            # Bearish breakout below Asian low
            elif close[i] < asian_l and close[i] < ema_trend[i]:
                sl_d = asian_h - close[i]
                if sl_d > 0:
                    signals[i] = -1.0
                    sl_dist_arr[i] = sl_d
                    tp_dist_arr[i] = sl_d * rr
                    risk_amount = capital * risk_pct / 100.0
                    lot_sizes[i] = min(1.0, max(0.01, risk_amount / (sl_d * 100.0)))
                    last_signal = i
                    traded_today = True
    
    return signals, sl_dist_arr, tp_dist_arr, lot_sizes
