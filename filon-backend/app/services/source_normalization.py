"""Normalisations déterministes partagées par le legacy et le shadow."""

from __future__ import annotations

import re


_TRUE_VALUES = frozenset({"1", "true", "yes", "y", "in stock", "instock"})
_FALSE_VALUES = frozenset(
    {"0", "false", "no", "n", "out of stock", "outofstock", "sold out"}
)


def parse_price(value: str | None) -> float | None:
    """Convertit les formats prix Awin connus, sans inventer une valeur."""
    if not value:
        return None
    cleaned = value.strip()
    for whitespace in (" ", "\u00a0", "\u202f", "\u2009"):
        cleaned = cleaned.replace(whitespace, "")
    normalized = re.sub(r"[^0-9,.\-]", "", cleaned)
    if not normalized:
        return None

    if "," in normalized and "." in normalized:
        decimal_separator = (
            "," if normalized.rfind(",") > normalized.rfind(".") else "."
        )
        thousands_separator = "." if decimal_separator == "," else ","
        normalized = normalized.replace(thousands_separator, "").replace(
            decimal_separator,
            ".",
        )
    elif "," in normalized or "." in normalized:
        separator = "," if "," in normalized else "."
        parts = normalized.split(separator)
        if len(parts) > 2:
            normalized = "".join(parts)
        elif len(parts[1]) == 3 and parts[0].lstrip("-") not in ("", "0"):
            normalized = parts[0] + parts[1]
        else:
            normalized = parts[0] + "." + parts[1]

    try:
        return round(float(normalized), 2)
    except ValueError:
        return None


def parse_tristate_bool(value: str | None) -> bool | None:
    """Retourne vrai, faux ou inconnu ; une valeur non reconnue reste inconnue."""
    if value is None or value.strip() == "":
        return None
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return None
