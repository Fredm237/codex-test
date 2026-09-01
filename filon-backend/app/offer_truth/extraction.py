"""Extracteurs purs et fail-closed du contrat Offer Truth v1."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.services.currency import normalize_currency_code


EXTRACTOR_VERSION = "awin-offer-truth-extractor/v1"
FRESHNESS_POLICY_VERSION = "offer-truth-freshness-72h/v1"
OFFER_TRUTH_POLICY_VERSION = "offer-truth-policy/v1"
DEFAULT_TTL_SECONDS = 259_200

_PRICE_FIELD = "search_price"
_PRICE_CURRENCY_FIELD = "currency"
_STOCK_FIELD = "in_stock"
_SHIPPING_PAIRS = (
    ("shipping_cost", "shipping_currency"),
    ("delivery_cost", "delivery_currency"),
    ("postage", "postage_currency"),
    ("delivery_price", "delivery_price_currency"),
)
_RETURNS_ACCEPTED_FIELDS = ("returns_accepted", "return_accepted")
_RETURNS_PERIOD_FIELDS = ("return_period", "returns_period", "return_period_days")
_WARRANTY_MONTH_FIELDS = ("warranty_months", "warranty_period_months")
_WARRANTY_DESCRIPTION_FIELDS = ("warranty", "warranty_description")
_TRUE_STOCK = frozenset({"1", "true", "yes", "y", "in stock", "instock", "available"})
_FALSE_STOCK = frozenset(
    {
        "0",
        "false",
        "no",
        "n",
        "out of stock",
        "out-of-stock",
        "outofstock",
        "sold out",
        "unavailable",
    }
)
_PREORDER_STOCK = frozenset({"preorder", "pre-order", "pre order"})
_TRUE_BOOL = frozenset({"1", "true", "yes", "y"})
_FALSE_BOOL = frozenset({"0", "false", "no", "n"})
_DECIMAL_TOKEN = re.compile(r"^-?[0-9]+(?:[.,][0-9]+)?$")
_MERCHANT_STATES = frozenset(
    {"INDEXED", "AFFILIATED", "DIRECT_PARTNER", "MARKETPLACE", "UNVERIFIED"}
)


class OfferTruthExtractionError(ValueError):
    """Métadonnée structurelle invalide ; aucun snapshot ne doit être écrit."""


def _utc(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise OfferTruthExtractionError(f"{field} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first(row: Mapping[str, Any], fields: Sequence[str]) -> tuple[str | None, Any]:
    for field in fields:
        if field in row and _text(row.get(field)) is not None:
            return field, row.get(field)
    return None, None


def _evidence(
    *,
    raw_source_record_id: int,
    source_type: str,
    source_ref: str,
    observed_at: datetime,
    field: str,
    transformation: str,
) -> dict[str, Any]:
    return {
        "raw_source_record_id": raw_source_record_id,
        "source_type": source_type,
        "source_ref": source_ref,
        "observed_at": _iso(observed_at),
        "field": field,
        "transformation": transformation,
        "transformation_version": EXTRACTOR_VERSION,
        "confidence_state": "derived_deterministic",
    }


def _claim(state: str, value: Any = None, evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"state": state, "value": value, "evidence": evidence or []}


def _decimal_string(value: Any, *, allow_zero: bool) -> str | None:
    if isinstance(value, bool):
        return None
    text = _text(value)
    if text is None:
        return None
    compact = text
    for whitespace in (" ", "\u00a0", "\u202f", "\u2009"):
        compact = compact.replace(whitespace, "")
    compact = re.sub(r"[^0-9,.\-]", "", compact)
    if not compact:
        return None
    if "," in compact and "." in compact:
        decimal_separator = "," if compact.rfind(",") > compact.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        compact = compact.replace(thousands_separator, "").replace(decimal_separator, ".")
    elif "," in compact or "." in compact:
        separator = "," if "," in compact else "."
        parts = compact.split(separator)
        if len(parts) > 2:
            compact = "".join(parts)
        elif len(parts) == 2:
            compact = parts[0] + "." + parts[1]
    if not _DECIMAL_TOKEN.fullmatch(compact):
        return None
    try:
        number = Decimal(compact)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        return None
    normalized = format(number, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    if "." in normalized and len(normalized.rsplit(".", 1)[1]) > 6:
        return None
    return normalized


def _money_claim(
    row: Mapping[str, Any],
    *,
    amount_field: str,
    currency_field: str,
    allow_zero: bool,
    evidence_context: Mapping[str, Any],
    transformation: str,
) -> dict[str, Any]:
    raw_amount = _text(row.get(amount_field))
    raw_currency = _text(row.get(currency_field))
    if raw_amount is None:
        return _claim("unknown")
    amount = _decimal_string(raw_amount, allow_zero=allow_zero)
    if amount is None:
        return _claim("invalid")
    if raw_currency is None:
        return _claim("unknown")
    currency = normalize_currency_code(raw_currency)
    if currency is None:
        return _claim("invalid")
    evidence = _evidence(
        **evidence_context,
        field=amount_field,
        transformation=transformation,
    )
    return _claim(
        "known",
        {"amount_decimal": amount, "currency": currency},
        [evidence],
    )


def _shipping_claim(row: Mapping[str, Any], evidence_context: Mapping[str, Any]) -> dict[str, Any]:
    for amount_field, currency_field in _SHIPPING_PAIRS:
        if _text(row.get(amount_field)) is not None:
            return _money_claim(
                row,
                amount_field=amount_field,
                currency_field=currency_field,
                allow_zero=True,
                evidence_context=evidence_context,
                transformation="normalize_explicit_shipping_money",
            )
    return _claim("unknown")


def _stock_claim(row: Mapping[str, Any], evidence_context: Mapping[str, Any]) -> dict[str, Any]:
    raw = _text(row.get(_STOCK_FIELD))
    if raw is None:
        return _claim("unknown")
    normalized = raw.lower()
    if normalized in _TRUE_STOCK:
        value = "in_stock"
    elif normalized in _FALSE_STOCK:
        value = "out_of_stock"
    elif normalized in _PREORDER_STOCK:
        value = "preorder"
    else:
        return _claim("invalid")
    return _claim(
        "known",
        value,
        [
            _evidence(
                **evidence_context,
                field=_STOCK_FIELD,
                transformation="normalize_explicit_stock_state",
            )
        ],
    )


def _strict_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _text(value)
    if text is None:
        return None
    normalized = text.lower()
    if normalized in _TRUE_BOOL:
        return True
    if normalized in _FALSE_BOOL:
        return False
    return None


def _integer(value: Any, *, minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        result = value
    else:
        text = _text(value)
        if text is None or not text.isdigit():
            return None
        result = int(text)
    return result if minimum <= result <= maximum else None


def _returns_claim(row: Mapping[str, Any], evidence_context: Mapping[str, Any]) -> dict[str, Any]:
    accepted_field, accepted_raw = _first(row, _RETURNS_ACCEPTED_FIELDS)
    period_field, period_raw = _first(row, _RETURNS_PERIOD_FIELDS)
    if accepted_field is None and period_field is None:
        return _claim("unknown")
    accepted = _strict_bool(accepted_raw)
    if accepted_field is None or accepted is None:
        return _claim("invalid")
    period = None
    if period_field is not None:
        period = _integer(period_raw, minimum=0, maximum=3650)
        if period is None:
            return _claim("invalid")
    return _claim(
        "known",
        {"accepted": accepted, "period_days": period},
        [
            _evidence(
                **evidence_context,
                field=accepted_field,
                transformation="normalize_explicit_returns_policy",
            )
        ],
    )


def _warranty_claim(row: Mapping[str, Any], evidence_context: Mapping[str, Any]) -> dict[str, Any]:
    months_field, months_raw = _first(row, _WARRANTY_MONTH_FIELDS)
    description_field, description_raw = _first(row, _WARRANTY_DESCRIPTION_FIELDS)
    if months_field is None and description_field is None:
        return _claim("unknown")
    months = None
    if months_field is not None:
        months = _integer(months_raw, minimum=0, maximum=1200)
        if months is None:
            return _claim("invalid")
    description = _text(description_raw)
    if description is not None and len(description) > 512:
        return _claim("invalid")
    if months is None and description is None:
        return _claim("invalid")
    field = months_field or description_field
    assert field is not None
    return _claim(
        "known",
        {"duration_months": months, "description": description},
        [
            _evidence(
                **evidence_context,
                field=field,
                transformation="normalize_explicit_warranty",
            )
        ],
    )


def _merchant_claim(
    *,
    merchant_id: int,
    merchant_status: str | None,
    relationship_type: str | None,
    seller_type: str,
    evidence_context: Mapping[str, Any],
) -> dict[str, Any]:
    if merchant_status is None and relationship_type is None:
        return _claim("unknown")
    if (
        isinstance(merchant_id, bool)
        or not isinstance(merchant_id, int)
        or merchant_id < 1
        or merchant_status not in _MERCHANT_STATES
        or relationship_type not in _MERCHANT_STATES
        or merchant_status != relationship_type
        or seller_type not in {"direct", "marketplace", "unknown"}
    ):
        return _claim("invalid")
    value = {
        "merchant_id": merchant_id,
        "merchant_status": merchant_status,
        "relationship_type": relationship_type,
        "seller_type": seller_type,
    }
    return _claim(
        "known",
        value,
        [
            _evidence(
                **evidence_context,
                field="merchant_id",
                transformation="join_explicit_merchant_registry",
            )
        ],
    )


def _freshness_claim(
    *,
    observed_at: datetime,
    evaluated_at: datetime,
    ttl_seconds: int,
    evidence_context: Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds < 1:
        raise OfferTruthExtractionError("ttl_seconds must be a positive integer")
    age_seconds = int((evaluated_at - observed_at).total_seconds())
    if age_seconds < 0:
        return _claim("invalid_future")
    state = "fresh" if age_seconds <= ttl_seconds else "stale"
    return _claim(
        state,
        {"age_seconds": age_seconds, "ttl_seconds": ttl_seconds},
        [
            _evidence(
                **evidence_context,
                field="observed_at",
                transformation="evaluate_versioned_freshness",
            )
        ],
    )


def _apply_time_state(claim: dict[str, Any], freshness_state: str) -> dict[str, Any]:
    if claim["state"] != "known":
        return claim
    if freshness_state == "stale":
        return {**claim, "state": "stale"}
    if freshness_state == "invalid_future":
        return {"state": "invalid", "value": None, "evidence": claim["evidence"]}
    return claim


def _reason_codes(claims: Mapping[str, Mapping[str, Any]], *, variant_id: int | None) -> list[str]:
    reasons: list[str] = []
    if variant_id is None:
        reasons.append("identity_unresolved")
    state_reasons = {
        ("price", "unknown"): "price_unknown",
        ("price", "invalid"): "price_invalid",
        ("price", "stale"): "price_stale",
        ("stock", "unknown"): "stock_unknown",
        ("stock", "invalid"): "stock_invalid",
        ("stock", "stale"): "stock_stale",
        ("shipping", "unknown"): "shipping_unknown",
        ("returns", "unknown"): "returns_unknown",
        ("warranty", "unknown"): "warranty_unknown",
        ("merchant", "unknown"): "merchant_unknown",
        ("merchant", "invalid"): "merchant_unknown",
        ("freshness", "stale"): "observation_stale",
        ("freshness", "invalid_future"): "future_observation",
    }
    for claim_name, claim in claims.items():
        reason = state_reasons.get((claim_name, str(claim["state"])))
        if reason and reason not in reasons:
            reasons.append(reason)
    core_verified = (
        variant_id is not None
        and claims["price"]["state"] == "known"
        and claims["stock"]["state"] == "known"
        and claims["merchant"]["state"] == "known"
        and claims["freshness"]["state"] == "fresh"
    )
    if core_verified:
        reasons.insert(0, "verified_core_truth")
    return reasons or ["source_conflict"]


def _offer_status(claims: Mapping[str, Mapping[str, Any]], *, variant_id: int | None) -> str:
    if variant_id is None:
        return "QUARANTINED"
    if claims["freshness"]["state"] == "stale":
        return "STALE"
    if claims["freshness"]["state"] == "invalid_future" or any(
        claims[name]["state"] == "invalid" for name in ("price", "stock", "merchant")
    ):
        return "INVALID"
    if (
        claims["price"]["state"] == "known"
        and claims["stock"]["state"] == "known"
        and claims["merchant"]["state"] == "known"
        and claims["freshness"]["state"] == "fresh"
    ):
        return "VERIFIED"
    return "PARTIAL"


def extract_awin_offer_truth(
    row: Mapping[str, Any],
    *,
    raw_source_record_id: int,
    source_ref: str,
    observed_at: datetime,
    evaluated_at: datetime,
    offer_id: int,
    variant_id: int | None,
    merchant_id: int,
    merchant_status: str | None,
    relationship_type: str | None,
    seller_type: str = "unknown",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    """Projette une ligne Awin en snapshot v1 sans inférence favorable."""

    if not isinstance(row, Mapping):
        raise OfferTruthExtractionError("awin row must be an object")
    if (
        isinstance(raw_source_record_id, bool)
        or not isinstance(raw_source_record_id, int)
        or raw_source_record_id < 1
        or isinstance(offer_id, bool)
        or not isinstance(offer_id, int)
        or offer_id < 1
        or (
            variant_id is not None
            and (isinstance(variant_id, bool) or not isinstance(variant_id, int) or variant_id < 1)
        )
    ):
        raise OfferTruthExtractionError("offer truth ids must be positive integers")
    source_ref_text = _text(source_ref)
    if source_ref_text is None or len(source_ref_text) > 255:
        raise OfferTruthExtractionError("source_ref is invalid")
    observed = _utc(observed_at, "observed_at")
    evaluated = _utc(evaluated_at, "evaluated_at")
    evidence_context = {
        "raw_source_record_id": raw_source_record_id,
        "source_type": "awin_feed",
        "source_ref": source_ref_text,
        "observed_at": observed,
    }

    freshness = _freshness_claim(
        observed_at=observed,
        evaluated_at=evaluated,
        ttl_seconds=ttl_seconds,
        evidence_context=evidence_context,
    )
    price = _money_claim(
        row,
        amount_field=_PRICE_FIELD,
        currency_field=_PRICE_CURRENCY_FIELD,
        allow_zero=False,
        evidence_context=evidence_context,
        transformation="normalize_explicit_offer_money",
    )
    claims = {
        "price": _apply_time_state(price, freshness["state"]),
        "stock": _apply_time_state(_stock_claim(row, evidence_context), freshness["state"]),
        "shipping": _apply_time_state(_shipping_claim(row, evidence_context), freshness["state"]),
        "returns": _apply_time_state(_returns_claim(row, evidence_context), freshness["state"]),
        "warranty": _apply_time_state(_warranty_claim(row, evidence_context), freshness["state"]),
        "merchant": _merchant_claim(
            merchant_id=merchant_id,
            merchant_status=merchant_status,
            relationship_type=relationship_type,
            seller_type=seller_type,
            evidence_context=evidence_context,
        ),
        "freshness": freshness,
    }
    return {
        "contract_version": "1.0.0",
        "offer_id": offer_id,
        "variant_id": variant_id,
        "merchant_id": merchant_id,
        "offer_status": _offer_status(claims, variant_id=variant_id),
        "claims": claims,
        "reason_codes": _reason_codes(claims, variant_id=variant_id),
        "projection_version": EXTRACTOR_VERSION,
        "policy_version": OFFER_TRUTH_POLICY_VERSION,
        "evaluated_at": _iso(evaluated),
    }
