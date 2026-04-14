"""
SmartWave Quant Lab — Dynamic Strategy Executor
================================================
Traduit du code MQL4/MQL5/Python en une classe BaseStrategy exécutable
dans le moteur de backtest SmartWave via LLM (OpenAI-compatible API).
"""

from __future__ import annotations

import logging
import os
import re
import textwrap
from typing import Any

import requests

from strategies.strategies import BaseStrategy, ema, sma, rsi, atr
from core.models import Bar

logger = logging.getLogger("smartwave.dynamic")

# ── LLM CONFIG ──────────────────────────────────────────────────────────────
LLM_URL = os.environ.get("BUILT_IN_FORGE_API_URL", "")
LLM_KEY = os.environ.get("BUILT_IN_FORGE_API_KEY", "")

TRANSLATION_PROMPT = """You are an expert algorithmic trading developer specializing in converting trading strategies to Python.

Convert the following {source_lang} trading strategy code into a Python class that inherits from BaseStrategy.

STRICT REQUIREMENTS:
1. The class MUST be named `DynamicStrategy`
2. It MUST inherit from `BaseStrategy`
3. It MUST implement `initialize(self)` and `on_bar(self, bar)` methods
4. Use ONLY these available helpers: `ema(closes, period)`, `sma(closes, period)`, `rsi(closes, period)`, `atr(bars, period)`
5. Use `self.buy(lots, sl=0, tp=0)` and `self.sell(lots, sl=0, tp=0)` to place orders
6. Use `self.close_all()` to close all positions
7. Access parameters via `self.params.get('param_name', default_value)`
8. Keep a rolling history: `self.closes = []` and `self.bars_history = []` updated in `on_bar`
9. The `bar` object has: `bar.open`, `bar.high`, `bar.low`, `bar.close`, `bar.volume`, `bar.timestamp`
10. NO external imports allowed (no pandas, no ta-lib, no backtrader)
11. Keep logic simple and robust — avoid complex state machines
12. Default lot size: 0.1

SOURCE CODE ({source_lang}):
```
{source_code}
```

STRATEGY PARAMETERS (use as self.params defaults):
{parameters}

Return ONLY the Python class code, no explanations, no markdown fences, no imports.
Start directly with `class DynamicStrategy(BaseStrategy):`
"""


def _call_llm(prompt: str) -> str:
    """Call the Manus LLM API to translate strategy code."""
    if not LLM_URL or not LLM_KEY:
        raise ValueError("LLM API not configured (BUILT_IN_FORGE_API_URL / BUILT_IN_FORGE_API_KEY missing)")
    
    resp = requests.post(
        f"{LLM_URL}/v1/chat/completions",
        headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2000,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def translate_to_python(source_code: str, source_lang: str, parameters: dict) -> str:
    """
    Use LLM to translate MQL4/MQL5/Python/Pine code to a BaseStrategy subclass.
    Returns the Python class code as a string.
    """
    params_str = "\n".join([f"  - {k}: min={v.get('min',0)}, max={v.get('max',100)}, default={v.get('default', v.get('min',1))}" 
                            for k, v in parameters.items()]) if parameters else "  (no parameters defined)"
    
    prompt = TRANSLATION_PROMPT.format(
        source_lang=source_lang.upper(),
        source_code=source_code[:3000],  # Limit to 3000 chars
        parameters=params_str,
    )
    
    raw = _call_llm(prompt)
    
    # Clean up: remove markdown fences if present
    raw = re.sub(r"```python\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()
    
    # Ensure it starts with the class definition
    if "class DynamicStrategy" not in raw:
        raise ValueError(f"LLM did not return a valid class. Got: {raw[:200]}")
    
    return raw


def build_strategy_class(python_code: str) -> type:
    """
    Dynamically compile and return the DynamicStrategy class from Python code.
    Runs in a sandboxed namespace with only safe imports.
    """
    # Safe namespace with only allowed modules
    namespace = {
        "BaseStrategy": BaseStrategy,
        "Bar": Bar,
        "ema": ema,
        "sma": sma,
        "rsi": rsi,
        "atr": atr,
        "Any": Any,
        "__builtins__": {
            "len": len, "range": range, "enumerate": enumerate, "zip": zip,
            "list": list, "dict": dict, "float": float, "int": int, "bool": bool,
            "str": str, "abs": abs, "max": max, "min": min, "round": round,
            "print": print, "isinstance": isinstance, "hasattr": hasattr,
            "getattr": getattr, "setattr": setattr, "None": None, "True": True, "False": False,
        },
    }
    
    try:
        exec(compile(python_code, "<dynamic_strategy>", "exec"), namespace)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in translated strategy: {e}")
    except Exception as e:
        raise ValueError(f"Error compiling strategy: {e}")
    
    if "DynamicStrategy" not in namespace:
        raise ValueError("DynamicStrategy class not found after compilation")
    
    cls = namespace["DynamicStrategy"]
    if not issubclass(cls, BaseStrategy):
        raise ValueError("DynamicStrategy must inherit from BaseStrategy")
    
    return cls


def create_dynamic_strategy(
    source_code: str,
    source_lang: str,
    parameters: dict,
    strategy_name: str = "Custom",
) -> type:
    """
    Full pipeline: translate source code → compile → return strategy class.
    
    For Python strategies that already implement BaseStrategy, try direct compilation first.
    For MQL4/MQL5/Pine, always use LLM translation.
    """
    # If it's already Python and contains BaseStrategy, try direct compilation
    if source_lang == "python" and "BaseStrategy" in source_code and "DynamicStrategy" in source_code:
        logger.info(f"[DynamicStrategy] Direct Python compilation for '{strategy_name}'")
        try:
            cls = build_strategy_class(source_code)
            logger.info(f"[DynamicStrategy] Direct compilation successful")
            return cls
        except Exception as e:
            logger.warning(f"[DynamicStrategy] Direct compilation failed: {e}, falling back to LLM")
    
    # Use LLM translation
    logger.info(f"[DynamicStrategy] LLM translation for '{strategy_name}' ({source_lang})")
    python_code = translate_to_python(source_code, source_lang, parameters)
    logger.info(f"[DynamicStrategy] LLM translation complete ({len(python_code)} chars)")
    logger.debug(f"[DynamicStrategy] Translated code:\n{python_code[:500]}")
    
    cls = build_strategy_class(python_code)
    logger.info(f"[DynamicStrategy] Compilation successful")
    return cls


# ── FALLBACK STRATEGY (when LLM is unavailable) ──────────────────────────────

class EMAFallbackStrategy(BaseStrategy):
    """
    Simple EMA crossover fallback strategy used when LLM translation fails.
    Uses parameters: fast_ema (default 9), slow_ema (default 21).
    """
    
    def initialize(self) -> None:
        self.fast_period = int(self.params.get("fast_ema", self.params.get("FastEMA", 9)))
        self.slow_period = int(self.params.get("slow_ema", self.params.get("SlowEMA", 21)))
        self.lot_size = float(self.params.get("lot_size", self.params.get("LotSize", 0.1)))
        self.sl_points = float(self.params.get("stop_loss", self.params.get("StopLoss", 50)))
        self.tp_points = float(self.params.get("take_profit", self.params.get("TakeProfit", 100)))
        self.closes: list[float] = []
        self.position_open = False
        logger.info(f"[EMAFallback] fast={self.fast_period}, slow={self.slow_period}")
    
    def on_bar(self, bar: Bar) -> None:
        self.closes.append(bar.close)
        if len(self.closes) < self.slow_period + 2:
            return
        
        fast_now = ema(self.closes, self.fast_period)
        slow_now = ema(self.closes, self.slow_period)
        fast_prev = ema(self.closes[:-1], self.fast_period)
        slow_prev = ema(self.closes[:-1], self.slow_period)
        
        point = 0.01  # XAUUSD point value
        sl = self.sl_points * point
        tp = self.tp_points * point
        
        # Bullish crossover
        if fast_prev <= slow_prev and fast_now > slow_now:
            self.close_all()
            self.buy(self.lot_size, sl=bar.close - sl, tp=bar.close + tp)
        # Bearish crossover
        elif fast_prev >= slow_prev and fast_now < slow_now:
            self.close_all()
            self.sell(self.lot_size, sl=bar.close + sl, tp=bar.close - tp)
