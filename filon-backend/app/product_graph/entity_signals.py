"""Extraction shadow, déterministe et abstentionniste des signaux Entity Resolution."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


CONTRACT_VERSION = "1.0.0"
EXTRACTOR_VERSION = "awin-entity-signals/v1"
MAX_PAYLOAD_FIELDS = 256
MAX_TEXT_LENGTH = 512
TARGET_SIGNALS = (
    "brand",
    "mpn",
    "model",
    "storage",
    "memory",
    "capacity",
    "size",
    "color",
    "generation",
    "edition",
    "condition",
    "pack_quantity",
    "product_role",
    "title",
    "image",
    "taxonomy",
)


class EntitySignalExtractionError(ValueError):
    """Entrée d'extraction hors bornes ou provenance absente."""


@dataclass(frozen=True)
class ExtractedSignal:
    signal: str
    status: str
    source_fields: tuple[str, ...]
    normalized_values: tuple[str, ...]
    strength: str
    role: str
    reason_code: str
    transformation: str = "entity_signal_extraction"
    transformation_version: str = EXTRACTOR_VERSION

    def as_contract(self) -> dict[str, Any]:
        return {
            "signal": self.signal,
            "status": self.status,
            "source_fields": list(self.source_fields),
            "normalized_values": list(self.normalized_values),
            "strength": self.strength,
            "role": self.role,
            "reason_code": self.reason_code,
            "transformation": self.transformation,
            "transformation_version": self.transformation_version,
        }


@dataclass(frozen=True)
class EntitySignalProjection:
    raw_source_record_id: int
    source_type: str
    source_ref: str
    observed_at: datetime
    signals: tuple[ExtractedSignal, ...]

    def as_contract(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "raw_source_record_id": self.raw_source_record_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "observed_at": self.observed_at.isoformat(),
            "extractor_version": EXTRACTOR_VERSION,
            "signals": [signal.as_contract() for signal in self.signals],
        }


def _label(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _code(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).upper().split())


def _attribute(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise EntitySignalExtractionError("structured signal must be scalar")
    text = str(value).strip()
    if not text:
        return None
    if len(text) > MAX_TEXT_LENGTH:
        raise EntitySignalExtractionError("structured signal is too long")
    return text


def _unknown(signal: str) -> ExtractedSignal:
    return ExtractedSignal(
        signal=signal,
        status="unknown",
        source_fields=(),
        normalized_values=(),
        strength="none",
        role="none",
        reason_code="missing_signal",
    )


def _invalid(signal: str, fields: tuple[str, ...]) -> ExtractedSignal:
    return ExtractedSignal(
        signal=signal,
        status="invalid",
        source_fields=fields,
        normalized_values=(),
        strength="none",
        role="none",
        reason_code="invalid_signal",
    )


def _structured(
    row: Mapping[str, Any],
    *,
    signal: str,
    fields: tuple[str, ...],
    normalize: Callable[[str], str],
    strength: str = "strong",
    role: str = "primary",
) -> ExtractedSignal | None:
    supplied = tuple(field for field in fields if field in row and row[field] is not None)
    if not supplied:
        return None
    values: list[str] = []
    try:
        for field in supplied:
            text = _text(row[field])
            if text is not None:
                normalized = normalize(text)
                if normalized:
                    values.append(normalized)
    except EntitySignalExtractionError:
        return _invalid(signal, supplied)
    unique = tuple(sorted(set(values)))
    if not unique:
        return None
    if len(unique) > 1:
        return ExtractedSignal(
            signal=signal,
            status="conflict",
            source_fields=supplied,
            normalized_values=unique,
            strength="none",
            role="none",
            reason_code="conflicting_structured_values",
        )
    return ExtractedSignal(
        signal=signal,
        status="observed",
        source_fields=supplied,
        normalized_values=unique,
        strength=strength,
        role=role,
        reason_code="observed_structured",
    )


_STORAGE_RE = re.compile(r"(?i)\b(\d+(?:[.,]\d+)?)\s*(GB|GO|TB|TO)\b")
_MEMORY_RE = re.compile(r"(?i)(?:\b(\d+(?:[.,]\d+)?)\s*(GB|GO)\s*(?:RAM|MEMORY|M[ÉE]MOIRE)\b|\bRAM\s*(\d+(?:[.,]\d+)?)\s*(GB|GO)\b)")
_CAPACITY_RE = re.compile(r"(?i)\b(\d+(?:[.,]\d+)?)\s*(BTU|L|LITRES?)\b")
_SIZE_RE = re.compile(r"(?i)\b(?:\d{3}/\d{2}R\d{2}|\d+(?:[.,]\d+)?\s*(?:MM|CM|POUCES?|INCH(?:ES)?|\"))\b")
_GENERATION_RE = re.compile(r"(?i)\b(?:GEN(?:ERATION)?\s*\d+|\d+(?:E|ER|ÈRE|EME|ÈME|TH|ST|ND|RD)\s*GEN(?:ERATION)?)\b")
_COLOR_WORDS = {
    "black": "black", "noir": "black", "noire": "black",
    "white": "white", "blanc": "white", "blanche": "white",
    "grey": "grey", "gray": "grey", "gris": "grey", "silver": "silver", "argent": "silver",
    "blue": "blue", "bleu": "blue", "bleue": "blue",
    "red": "red", "rouge": "red", "green": "green", "vert": "green", "verte": "green",
    "pink": "pink", "rose": "pink", "gold": "gold", "or": "gold", "doré": "gold", "dore": "gold",
    "brown": "brown", "marron": "brown", "beige": "beige", "purple": "purple", "violet": "purple",
    "yellow": "yellow", "jaune": "yellow", "orange": "orange",
}
_COLOR_RE = re.compile(r"(?i)\b(?:" + "|".join(sorted(map(re.escape, _COLOR_WORDS), key=len, reverse=True)) + r")\b")


def _unit(number: str, unit: str) -> str:
    normalized_number = number.replace(",", ".")
    normalized_unit = unit.upper()
    normalized_unit = {"GO": "GB", "TO": "TB", "LITRE": "L", "LITRES": "L"}.get(normalized_unit, normalized_unit)
    return f"{normalized_number}{normalized_unit}"


def _title_candidates(signal: str, title: str) -> tuple[str, ...]:
    if signal == "memory":
        values = []
        for match in _MEMORY_RE.finditer(title):
            number = match.group(1) or match.group(3)
            unit = match.group(2) or match.group(4)
            values.append(_unit(number, unit))
        return tuple(sorted(set(values)))
    if signal == "storage":
        values = []
        for match in _STORAGE_RE.finditer(title):
            context = title[max(0, match.start() - 8):match.end() + 12]
            if (
                re.search(r"(?i)\b(?:RAM|MEMORY|M[ÉE]MOIRE)\b", context)
                and not re.search(r"(?i)\b(?:SSD|HDD|STORAGE|STOCKAGE|DISK|DISQUE)\b", context)
            ):
                continue
            values.append(_unit(match.group(1), match.group(2)))
        return tuple(sorted(set(values)))
    if signal == "capacity":
        return tuple(sorted({_unit(match.group(1), match.group(2)) for match in _CAPACITY_RE.finditer(title)}))
    if signal == "size":
        return tuple(sorted({_code(match.group(0)).replace(" ", "") for match in _SIZE_RE.finditer(title)}))
    if signal == "generation":
        return tuple(sorted({_code(match.group(0)) for match in _GENERATION_RE.finditer(title)}))
    if signal == "color":
        return tuple(sorted({_COLOR_WORDS[match.group(0).casefold()] for match in _COLOR_RE.finditer(title)}))
    return ()


_FIELD_MAP: dict[str, tuple[tuple[str, ...], Callable[[str], str], str, str]] = {
    "brand": (("brand_name", "brand"), _label, "weak", "corroborating"),
    "mpn": (("mpn", "manufacturer_part_number", "part_number"), _code, "strong", "primary"),
    "model": (("model", "model_number", "product_model"), _label, "strong", "primary"),
    "storage": (("storage", "storage_capacity"), _attribute, "strong", "primary"),
    "memory": (("memory", "ram", "memory_capacity"), _attribute, "strong", "primary"),
    "capacity": (("capacity", "volume", "cooling_capacity"), _attribute, "strong", "primary"),
    "size": (("size", "dimensions", "tyre_size"), _attribute, "strong", "primary"),
    "color": (("color", "colour"), _label, "strong", "primary"),
    "generation": (("generation",), _label, "strong", "primary"),
    "edition": (("edition",), _label, "strong", "primary"),
    "condition": (("condition",), _label, "strong", "primary"),
    "pack_quantity": (("pack_quantity", "quantity_per_pack"), _attribute, "strong", "primary"),
    "product_role": (("product_role", "offer_kind"), _label, "strong", "primary"),
}


def project_entity_signals(
    row: Mapping[str, Any],
    *,
    raw_source_record_id: int,
    source_type: str,
    source_ref: str,
    observed_at: datetime,
) -> EntitySignalProjection:
    """Projette les champs structurés et conserve les indices lexicaux faibles.

    Aucun modèle ou MPN n'est extrait d'un titre arbitraire. Les attributs
    détectés dans le titre restent `candidate_only`; l'absence devient un
    signal `unknown` explicite.
    """

    if not isinstance(row, Mapping) or len(row) > MAX_PAYLOAD_FIELDS:
        raise EntitySignalExtractionError("row must be a bounded object")
    if isinstance(raw_source_record_id, bool) or not isinstance(raw_source_record_id, int) or raw_source_record_id <= 0:
        raise EntitySignalExtractionError("raw_source_record_id must be positive")
    if not isinstance(source_type, str) or not source_type.strip():
        raise EntitySignalExtractionError("source_type must be non-empty")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise EntitySignalExtractionError("source_ref must be non-empty")
    if not isinstance(observed_at, datetime) or observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise EntitySignalExtractionError("observed_at must include an offset")

    title_field = next((field for field in ("product_name", "title", "name") if row.get(field) not in (None, "")), None)
    title = ""
    if title_field is not None:
        try:
            title = _text(row[title_field]) or ""
        except EntitySignalExtractionError:
            title = ""

    signals: list[ExtractedSignal] = []
    lexical_signals = {"storage", "memory", "capacity", "size", "color", "generation"}
    for signal in TARGET_SIGNALS:
        if signal in _FIELD_MAP:
            fields, normalize, strength, role = _FIELD_MAP[signal]
            projection = _structured(
                row,
                signal=signal,
                fields=fields,
                normalize=normalize,
                strength=strength,
                role=role,
            )
            if projection is not None:
                signals.append(projection)
                continue
        if signal in lexical_signals and title:
            candidates = _title_candidates(signal, title)
            if candidates:
                signals.append(
                    ExtractedSignal(
                        signal=signal,
                        status="candidate_only",
                        source_fields=(title_field or "title",),
                        normalized_values=candidates,
                        strength="weak",
                        role="candidate_only",
                        reason_code="lexical_candidate",
                    )
                )
                continue
        if signal == "title" and title:
            signals.append(
                ExtractedSignal(
                    signal="title",
                    status="candidate_only",
                    source_fields=(title_field or "title",),
                    normalized_values=(_label(title),),
                    strength="weak",
                    role="candidate_only",
                    reason_code="weak_source_field",
                )
            )
            continue
        if signal == "image":
            image = _structured(
                row,
                signal="image",
                fields=("merchant_image_url", "image_url", "image"),
                normalize=lambda value: value.strip(),
                strength="weak",
                role="candidate_only",
            )
            if image is not None:
                if image.status == "observed":
                    image = ExtractedSignal(
                        signal="image",
                        status="candidate_only",
                        source_fields=image.source_fields,
                        normalized_values=image.normalized_values,
                        strength="weak",
                        role="candidate_only",
                        reason_code="weak_source_field",
                    )
                signals.append(image)
                continue
        if signal == "taxonomy":
            taxonomy = _structured(
                row,
                signal="taxonomy",
                fields=("merchant_category", "category", "filon_category", "filon_subcategory"),
                normalize=_label,
                strength="weak",
                role="candidate_only",
            )
            if taxonomy is not None:
                if taxonomy.status == "observed":
                    taxonomy = ExtractedSignal(
                        signal="taxonomy",
                        status="candidate_only",
                        source_fields=taxonomy.source_fields,
                        normalized_values=taxonomy.normalized_values,
                        strength="weak",
                        role="candidate_only",
                        reason_code="weak_source_field",
                    )
                signals.append(taxonomy)
                continue
        signals.append(_unknown(signal))

    return EntitySignalProjection(
        raw_source_record_id=raw_source_record_id,
        source_type=source_type.strip(),
        source_ref=source_ref.strip(),
        observed_at=observed_at,
        signals=tuple(signals),
    )
