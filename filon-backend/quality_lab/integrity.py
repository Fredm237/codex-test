"""Primitives d'integrite deterministes du FILON Quality Lab v0.5.

Ce module reste volontairement limite a la bibliotheque standard.  Il fournit
une seule definition de la serialisation canonique, des empreintes et de la
politique de split afin que la preparation, l'annotation et l'audit des jeux
de donnees ne puissent pas diverger silencieusement.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import unicodedata
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any


LAB_VERSION = "0.5.0"
RECORD_VERSION = "0.5.0"
PACK_VERSION = "0.5.0"
SPLIT_POLICY_VERSION = "sha256-prefix32-mod100-70-15-15-v1"
SPLIT_SALT = "filon-quality-v1"

DATASETS: tuple[str, ...] = (
    "taxonomy",
    "entity_resolution",
    "variant_resolution",
    "offer_attachment",
    "offer_truth",
    "retrieval",
    "decision",
)
"""Roster ferme des datasets couverts par le Quality Lab v0.5."""

SCENARIO_TYPES: tuple[str, ...] = (
    "exact_product",
    "generic_product",
    "use_case",
    "constraint_heavy",
    "accessory",
    "replacement_part",
    "variant_sensitive",
    "multi_product",
    "ambiguous",
    "no_match",
)
LANGUAGES: tuple[str, ...] = ("fr", "nl", "en")
VERTICALS: tuple[str, ...] = (
    "smartphones",
    "laptops",
    "tv",
    "headphones_audio",
    "appliances",
)

SCHEMA_FILES: dict[str, str] = {
    "taxonomy": "taxonomy.schema.json",
    "entity_resolution": "entity-resolution.schema.json",
    "variant_resolution": "variant-resolution.schema.json",
    "offer_attachment": "offer-attachment.schema.json",
    "offer_truth": "offer-truth.schema.json",
    "retrieval": "retrieval.schema.json",
    "decision": "decision.schema.json",
}

INPUT_FIELDS: dict[str, tuple[str, ...]] = {
    "taxonomy": ("strata", "observation"),
    "entity_resolution": ("strata", "left", "right"),
    "variant_resolution": ("strata", "observation"),
    "offer_attachment": ("strata", "offer"),
    "offer_truth": ("strata", "offer"),
    "retrieval": ("strata", "locale", "query", "hard_constraints"),
    "decision": ("strata", "request", "candidate_ids", "evidence"),
}
"""Allowlist des seuls champs visibles par les annotateurs, par dataset."""

SPLITS: tuple[str, ...] = ("train", "dev", "test")
SPLIT_THRESHOLDS: tuple[int, ...] = (70, 85, 100)

FINGERPRINT_PATTERN = re.compile(r"\Asha256:[0-9a-f]{64}\Z", re.ASCII)
"""Forme unique des empreintes exposees par ce module."""

_SCHEMA_DOMAIN = f"filon.quality.schema.v{LAB_VERSION.removesuffix('.0')}"
_INPUT_DOMAIN = f"filon.quality.input.v{RECORD_VERSION.removesuffix('.0')}"
_PACK_DOMAIN = f"filon.quality.pack.v{PACK_VERSION.removesuffix('.0')}"
_COMPLETED_PACK_DOMAIN = (
    f"filon.quality.completed-pack.v{PACK_VERSION.removesuffix('.0')}"
)
_CASE_DOMAIN = f"filon.quality.case.v{RECORD_VERSION.removesuffix('.0')}"
_DISAGREEMENT_DOMAIN = (
    f"filon.quality.disagreement.v{RECORD_VERSION.removesuffix('.0')}"
)
_MANIFEST_DOMAIN = f"filon.quality.manifest.v{LAB_VERSION.removesuffix('.0')}"

_EXACT_RESERVED_FIELDS = frozenset(
    {
        "actual",
        "truth",
        "ground_truth",
        "prediction",
        "predictions",
        "predicted",
        "model_output",
        "expected_answer",
        "gold",
        "annotation",
        "annotations",
        "label",
        "labels",
        # Golds propres aux schemas. Leur presence imbriquee serait une
        # fuite meme si la projection top-level reste correctement allowlistee.
        "product_relation",
        "variant_relation",
        "expected_variant",
        "expected_variant_id",
        "eligibility",
        "relevant_product_ids",
        "constraint_violating_product_ids",
        "acceptable_outcomes",
        "forbidden_claims",
        "claim_evidence",
        "expected_category",
        "expected_subcategory",
        "expected_product_role",
        "expected_price",
        "expected_stock",
        "expected_shipping",
        "expected_affiliate_link",
    }
)
_RESERVED_TOKENS = frozenset(
    {
        "actual",
        "truth",
        "prediction",
        "predictions",
        "predicted",
        "gold",
    }
)
_ENGINE_DOMAIN_FIELDS = frozenset(
    {
        "engine_capacity",
        "engine_code",
        "engine_displacement",
        "engine_fuel_type",
        "engine_manufacturer",
        "engine_power",
        "engine_type",
    }
)
_OUTPUT_TOKENS = frozenset(
    {
        "answer",
        "classification",
        "confidence",
        "decision",
        "label",
        "output",
        "prediction",
        "result",
        "score",
    }
)
_CAMEL_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")
_MANIFEST_SELF_FIELDS = frozenset(
    {"manifest_fingerprint", "manifest_digest", "manifest_sha256"}
)


class _DuplicateKeyError(Exception):
    """Erreur interne preservee jusqu'a la frontiere publique."""

    def __init__(self, key: str) -> None:
        self.key = key


class _NonFiniteNumberError(Exception):
    """Erreur interne preservee jusqu'a la frontiere publique."""

    def __init__(self, token: str) -> None:
        self.token = token


def _object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise _NonFiniteNumberError(token)


def _finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise _NonFiniteNumberError(token)
    return value


def strict_loads(text: str | bytes, source: str = "<json>") -> Any:
    """Parse un document JSON strict.

    Les cles dupliquees, ``NaN``, ``Infinity``, ``-Infinity`` et les nombres
    dont l'exposant deborde vers l'infini sont refuses. Les erreurs publiques
    sont des :class:`ValueError` au libelle stable.
    """

    source_label = str(source)
    if isinstance(text, bytes):
        try:
            decoded = text.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise ValueError(f"{source_label}: invalid UTF-8 JSON") from None
    elif isinstance(text, str):
        decoded = text
    else:
        raise ValueError(f"{source_label}: JSON text must be str or bytes")

    try:
        return json.loads(
            decoded,
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
        )
    except _DuplicateKeyError as exc:
        raise ValueError(
            f"{source_label}: duplicate JSON key {exc.key!r}"
        ) from None
    except _NonFiniteNumberError as exc:
        raise ValueError(
            f"{source_label}: non-finite JSON number {exc.token!r}"
        ) from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{source_label}: invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from None
    except RecursionError:
        raise ValueError(f"{source_label}: JSON nesting is too deep") from None


def _path(value: str | Path) -> Path:
    try:
        return Path(value)
    except TypeError:
        raise ValueError("path must be path-like") from None


def read_json(path: str | Path) -> Any:
    """Lit un fichier JSON UTF-8 avec les garanties de :func:`strict_loads`."""

    file_path = _path(path)
    try:
        payload = file_path.read_bytes()
    except OSError:
        raise ValueError(f"{file_path}: unable to read JSON file") from None
    return strict_loads(payload, source=str(file_path))


def read_jsonl(
    path: str | Path,
    missing_ok: bool = False,
) -> list[dict[str, Any]]:
    """Lit un JSONL strict et exige un objet JSON sur chaque ligne non vide.

    Une ligne vide est ignoree et une fin de fichier sans saut de ligne est
    acceptee. Si ``missing_ok`` vaut vrai, un fichier absent produit ``[]``.
    """

    file_path = _path(path)
    try:
        payload = file_path.read_bytes()
    except FileNotFoundError:
        if missing_ok:
            return []
        raise ValueError(f"{file_path}: JSONL file does not exist") from None
    except OSError:
        raise ValueError(f"{file_path}: unable to read JSONL file") from None

    return strict_load_jsonl(payload, source=str(file_path))


def atomic_write_text(path: str | Path, text: str) -> None:
    """Publie un texte UTF-8 par remplacement atomique dans le même dossier."""

    file_path = _path(path)
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    payload = text.encode("utf-8", errors="strict")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{file_path.name}.", suffix=".tmp", dir=file_path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, file_path)
        try:
            directory_descriptor = os.open(file_path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def strict_load_jsonl(
    payload: str | bytes,
    *,
    source: str = "<jsonl>",
) -> list[dict[str, Any]]:
    """Parse un snapshot JSONL sans confondre Unicode et séparateur LF."""

    if isinstance(payload, bytes):
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise ValueError(f"{source}: invalid UTF-8 JSONL") from None
    elif isinstance(payload, str):
        text = payload
    else:
        raise ValueError(f"{source}: JSONL payload must be str or bytes")

    records: list[dict[str, Any]] = []
    # JSONL n'a qu'un séparateur d'enregistrement : LF. ``splitlines()``
    # traiterait à tort U+0085, U+2028 et U+2029 contenus dans une chaîne JSON
    # comme des fins d'enregistrement et corromprait le round-trip Unicode.
    for line_number, raw_line in enumerate(text.split("\n"), 1):
        if not raw_line.strip():
            continue
        record_source = f"{source}:{line_number}"
        value = strict_loads(raw_line, source=record_source)
        if not isinstance(value, dict):
            raise ValueError(f"{record_source}: JSONL record must be an object")
        records.append(value)
    return records


def _validate_json_value(
    value: Any,
    *,
    path: str = "$",
    active: set[int] | None = None,
) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite number at {path}")
        return

    if active is None:
        active = set()
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            raise ValueError(f"circular JSON value at {path}")
        active.add(identity)
        try:
            for index, item in enumerate(value):
                _validate_json_value(item, path=f"{path}[{index}]", active=active)
        finally:
            active.remove(identity)
        return
    if isinstance(value, dict):
        identity = id(value)
        if identity in active:
            raise ValueError(f"circular JSON value at {path}")
        active.add(identity)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError(f"non-string JSON key at {path}")
                _validate_json_value(
                    item,
                    path=f"{path}.{key}",
                    active=active,
                )
        finally:
            active.remove(identity)
        return
    raise ValueError(f"non-JSON value at {path}")


def canonical_json(value: Any) -> str:
    """Retourne le JSON canonique UTF-8 du Quality Lab.

    Les cles sont triees, aucun espace cosmetique n'est emis, les caracteres
    Unicode restent lisibles et les nombres non finis sont interdits.
    """

    try:
        _validate_json_value(value)
        result = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        # La fonction retourne str, mais cette verification garantit que son
        # resultat est reellement serialisable en UTF-8 (pas de surrogate nu).
        result.encode("utf-8", errors="strict")
        return result
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError):
        raise ValueError("value cannot be encoded as canonical JSON") from None


def sha256_value(domain: str, value: Any) -> str:
    """Empreinte une valeur canonique avec separation de domaine.

    La formule normative est ``SHA256(domain UTF-8 || NUL || canonical JSON
    UTF-8)``. Le resultat est toujours ``sha256:`` suivi de 64 hexadecimaux.
    """

    checked_domain = require_identifier(domain, "domain")
    if "\0" in checked_domain:
        raise ValueError("domain must not contain NUL")
    payload = checked_domain.encode("utf-8") + b"\0" + canonical_json(value).encode(
        "utf-8"
    )
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def sha256_file(path: str | Path) -> str:
    """Calcule le SHA-256 des octets exacts d'un fichier, par blocs."""

    file_path = _path(path)
    digest = hashlib.sha256()
    try:
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        raise ValueError(f"{file_path}: unable to hash file") from None
    return f"sha256:{digest.hexdigest()}"


def require_identifier(value: Any, field: str) -> str:
    """Exige une chaine non vide sans espace de bord et la retourne intacte."""

    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(
            f"{field} must be a non-empty string without surrounding whitespace"
        )
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError(f"{field} must be NFC-normalized")
    return value


def _is_offset_datetime(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        return False
    return parsed.utcoffset() is not None


def _require_dataset(dataset: Any) -> str:
    checked = require_identifier(dataset, "dataset")
    if checked not in DATASETS:
        raise ValueError(f"unknown dataset {checked!r}")
    return checked


def split_bucket(group_id: str, salt: str = SPLIT_SALT) -> int:
    """Retourne le bucket canonique 0..99 d'un groupe.

    La formule normative prend les 32 premiers bits de
    ``SHA256(salt + ':' + group_id)`` en big-endian, puis applique modulo 100.
    """

    checked_group = require_identifier(group_id, "group_id")
    checked_salt = require_identifier(salt, "salt")
    digest = hashlib.sha256(f"{checked_salt}:{checked_group}".encode("utf-8"))
    return int.from_bytes(digest.digest()[:4], byteorder="big") % 100


def split_for_group(group_id: str, salt: str = SPLIT_SALT) -> str:
    """Assigne deterministiquement ``train`` (70), ``dev`` (15) ou ``test`` (15)."""

    bucket = split_bucket(group_id, salt=salt)
    if bucket < SPLIT_THRESHOLDS[0]:
        return "train"
    if bucket < SPLIT_THRESHOLDS[1]:
        return "dev"
    return "test"


def _normalized_field_tokens(key: str) -> tuple[str, ...]:
    snake_like = _CAMEL_CASE_BOUNDARY.sub("_", key).lower()
    return tuple(token for token in _NON_ALPHANUMERIC.split(snake_like) if token)


def _is_reserved_field(key: str) -> bool:
    normalized = "_".join(_normalized_field_tokens(key))
    if normalized in _EXACT_RESERVED_FIELDS:
        return True
    tokens = tuple(normalized.split("_")) if normalized else ()
    if any(token in _RESERVED_TOKENS for token in tokens):
        return True
    # ``engine_*`` est un namespace de provenance interdit par défaut. Seuls
    # quelques attributs physiques explicitement connus sont admis : ainsi un
    # nouveau champ moteur ne peut pas rendre une réponse visible par oubli.
    if tokens and tokens[0] == "engine" and normalized not in _ENGINE_DOMAIN_FIELDS:
        return True
    if "engine" in tokens and set(tokens).intersection(_OUTPUT_TOKENS):
        return True
    pairs = set(zip(tokens, tokens[1:]))
    return (
        ("model", "output") in pairs
        or ("expected", "answer") in pairs
        or bool(
            pairs
            & {
                ("engine", "output"),
                ("engine", "prediction"),
                ("engine", "result"),
            }
        )
    )


def ensure_no_reserved_fields(value: Any, path: str = "input") -> None:
    """Refuse recursivement toute cle susceptible de devoiler une reponse gold."""

    root_path = require_identifier(path, "path")

    def visit(item: Any, location: str, active: set[int]) -> None:
        if isinstance(item, dict):
            identity = id(item)
            if identity in active:
                raise ValueError(f"circular input value at {location}")
            active.add(identity)
            try:
                for key, nested in item.items():
                    if not isinstance(key, str):
                        raise ValueError(f"non-string input key at {location}")
                    child = f"{location}.{key}"
                    if _is_reserved_field(key):
                        raise ValueError(f"reserved input field {key!r} at {child}")
                    visit(nested, child, active)
            finally:
                active.remove(identity)
        elif isinstance(item, list):
            identity = id(item)
            if identity in active:
                raise ValueError(f"circular input value at {location}")
            active.add(identity)
            try:
                for index, nested in enumerate(item):
                    visit(nested, f"{location}[{index}]", active)
            finally:
                active.remove(identity)

    visit(value, root_path, set())


def project_blind_input(dataset: str, case: Mapping[str, Any]) -> dict[str, Any]:
    """Projette un cas sur l'allowlist aveugle de son dataset.

    Tous les champs allowlistes sont obligatoires. La projection est une copie
    JSON profonde et toute fuite reservee imbriquee provoque un ``ValueError``.
    """

    checked_dataset = _require_dataset(dataset)
    if not isinstance(case, Mapping):
        raise ValueError("case must be an object")
    fields = INPUT_FIELDS[checked_dataset]
    missing = [field for field in fields if field not in case]
    if missing:
        raise ValueError(
            f"case is missing input fields for {checked_dataset}: {', '.join(missing)}"
        )
    projected = {field: case[field] for field in fields}
    ensure_no_reserved_fields(projected)
    # Le round-trip produit une copie independante et exclut les objets Python
    # non representables en JSON avant qu'ils n'entrent dans une empreinte.
    return strict_loads(canonical_json(projected), source="<projected-input>")


def label_invariant_errors(
    dataset: str,
    label: Any,
    input_value: Any = None,
) -> list[str]:
    """Vérifie les invariants métier croisés absents du simple typage JSON."""

    checked_dataset = _require_dataset(dataset)
    errors: list[str] = []

    strata = input_value.get("strata") if isinstance(input_value, Mapping) else None
    scenario_type: Any = None
    language: Any = None
    if not isinstance(strata, Mapping):
        errors.append("input strata must be an object")
    else:
        scenario_type = strata.get("scenario_type")
        language = strata.get("language")
        vertical = strata.get("vertical")
        if scenario_type not in SCENARIO_TYPES:
            errors.append("input strata scenario_type is unsupported")
        if language not in LANGUAGES:
            errors.append("input strata language is unsupported")
        if vertical not in VERTICALS:
            errors.append("input strata vertical is unsupported")
        if checked_dataset == "retrieval" and input_value.get("locale") != language:
            errors.append("retrieval locale must equal strata language")

    if not isinstance(label, Mapping):
        return errors

    if checked_dataset == "entity_resolution":
        product_relation = label.get("product_relation")
        variant_relation = label.get("variant_relation")
        if product_relation == "different" and variant_relation != "not_applicable":
            errors.append(
                "different products require variant_relation not_applicable"
            )
        elif product_relation == "same" and variant_relation == "not_applicable":
            errors.append("same products forbid variant_relation not_applicable")
        elif product_relation == "ambiguous" and variant_relation != "ambiguous":
            errors.append(
                "ambiguous product relation requires ambiguous variant relation"
            )

    elif checked_dataset == "variant_resolution":
        expected = label.get("expected_variant")
        if isinstance(expected, Mapping):
            resolution = expected.get("resolution")
            variant_key = expected.get("variant_key")
            if resolution == "resolved" and variant_key is None:
                errors.append("resolved variant requires variant_key")
            elif resolution in {"ambiguous", "insufficient_evidence"} and (
                variant_key is not None
            ):
                errors.append("non-resolved variant requires null variant_key")

    elif checked_dataset == "offer_attachment":
        eligibility = label.get("eligibility")
        expected_variant_id = label.get("expected_variant_id")
        if eligibility == "eligible" and expected_variant_id is None:
            errors.append("eligible offer requires expected_variant_id")
        elif eligibility in {"quarantine", "reject"} and (
            expected_variant_id is not None
        ):
            errors.append("non-eligible offer requires null expected_variant_id")

    elif checked_dataset == "retrieval":
        resolution = label.get("resolution")
        relevant = label.get("relevant_product_ids")
        exact_products = label.get("exact_product_ids")
        violating = label.get("constraint_violating_product_ids")
        if resolution == "matched" and isinstance(relevant, list) and not relevant:
            errors.append("matched retrieval requires relevant_product_ids")
        elif (
            resolution in {"no_match", "ambiguous"}
            and isinstance(relevant, list)
            and relevant
        ):
            errors.append(
                "no_match or ambiguous retrieval forbids relevant_product_ids"
            )
        if isinstance(relevant, list) and isinstance(violating, list):
            relevant_ids = {value for value in relevant if isinstance(value, str)}
            violating_ids = {
                value for value in violating if isinstance(value, str)
            }
            if relevant_ids & violating_ids:
                errors.append(
                    "relevant_product_ids and constraint_violating_product_ids "
                    "must be disjoint"
                )
        if not isinstance(exact_products, list):
            errors.append("retrieval exact_product_ids must be an array")
        elif scenario_type == "exact_product" and resolution == "matched":
            if not exact_products:
                errors.append(
                    "matched exact_product retrieval requires exact_product_ids"
                )
            elif isinstance(relevant, list) and not set(exact_products).issubset(
                set(relevant)
            ):
                errors.append(
                    "exact_product_ids must be a subset of relevant_product_ids"
                )
        elif exact_products:
            errors.append(
                "exact_product_ids must be empty outside matched exact_product retrieval"
            )

    elif checked_dataset == "decision":
        inventory = input_value.get("evidence") if isinstance(
            input_value, Mapping
        ) else None
        inventory_refs: list[str] = []
        if not isinstance(inventory, list):
            errors.append("decision input evidence inventory must be an array")
        else:
            for item in inventory:
                if isinstance(item, Mapping) and isinstance(
                    item.get("evidence_ref"), str
                ):
                    inventory_refs.append(item["evidence_ref"])
            if len(inventory_refs) != len(inventory):
                errors.append("decision input evidence inventory is invalid")
            if len(inventory_refs) != len(set(inventory_refs)):
                errors.append("decision input evidence_ref values must be unique")

        request = input_value.get("request") if isinstance(
            input_value, Mapping
        ) else None
        candidate_ids = input_value.get("candidate_ids") if isinstance(
            input_value, Mapping
        ) else None
        offer_candidate_ids: list[str] = []
        offer_ids: list[int] = []
        offer_evidence_refs: set[str] = set()
        if not isinstance(request, Mapping):
            errors.append("decision request must be an object")
        else:
            if request.get("locale") != language:
                errors.append("decision request locale must equal strata language")
            if not _is_offset_datetime(request.get("reference_time")):
                errors.append(
                    "decision request reference_time must be an offset-aware ISO datetime"
                )
            offers = request.get("offers")
            if not isinstance(offers, list):
                errors.append("decision request offers must be an array")
            else:
                for offer in offers:
                    if not isinstance(offer, Mapping):
                        continue
                    candidate_id = offer.get("candidate_id")
                    if isinstance(candidate_id, str):
                        offer_candidate_ids.append(candidate_id)
                    offer_id = offer.get("offer_id")
                    if isinstance(offer_id, int) and not isinstance(offer_id, bool):
                        offer_ids.append(offer_id)
                    refs = offer.get("evidence_refs")
                    if isinstance(refs, list):
                        offer_evidence_refs.update(
                            ref for ref in refs if isinstance(ref, str)
                        )
                    observed_at = offer.get("observed_at")
                    if observed_at is not None and not _is_offset_datetime(observed_at):
                        errors.append(
                            "decision offer observed_at must be an offset-aware ISO datetime or null"
                        )
                if len(offer_candidate_ids) != len(offers):
                    errors.append("decision offer candidate_id values are invalid")
                if len(offer_candidate_ids) != len(set(offer_candidate_ids)):
                    errors.append("decision offer candidate_id values must be unique")
                if len(offer_ids) != len(offers) or len(offer_ids) != len(set(offer_ids)):
                    errors.append("decision offer_id values must be unique integers")

        if not isinstance(candidate_ids, list) or not all(
            isinstance(candidate_id, str) for candidate_id in candidate_ids
        ):
            errors.append("decision candidate_ids must be an array of strings")
        elif candidate_ids != offer_candidate_ids:
            errors.append(
                "decision candidate_ids must match request offers in canonical order"
            )

        unknown_offer_refs = offer_evidence_refs - set(inventory_refs)
        if unknown_offer_refs:
            errors.append(
                "decision offer evidence_refs reference unknown input evidence: "
                + ", ".join(sorted(unknown_offer_refs))
            )

        evidence_entries = label.get("claim_evidence")
        claim_names: list[str] = []
        referenced_evidence: set[str] = set()
        if isinstance(evidence_entries, list):
            for entry in evidence_entries:
                if not isinstance(entry, Mapping):
                    continue
                claim = entry.get("claim")
                if isinstance(claim, str):
                    claim_names.append(claim)
                refs = entry.get("evidence_refs")
                if isinstance(refs, list):
                    referenced_evidence.update(
                        ref for ref in refs if isinstance(ref, str)
                    )
        outcomes = label.get("acceptable_outcomes")
        if (
            isinstance(outcomes, list)
            and any(outcome in {"recommend", "wait"} for outcome in outcomes)
            and not claim_names
        ):
            errors.append(
                "non-abstain decision outcomes require non-empty claim_evidence"
            )
        if len(claim_names) != len(set(claim_names)):
            errors.append("decision claim_evidence claims must be unique")
        forbidden = label.get("forbidden_claims")
        forbidden_claims = (
            {claim for claim in forbidden if isinstance(claim, str)}
            if isinstance(forbidden, list)
            else set()
        )
        if set(claim_names) & forbidden_claims:
            errors.append(
                "decision claim_evidence claims must be disjoint from forbidden_claims"
            )
        unknown_refs = referenced_evidence - set(inventory_refs)
        if unknown_refs:
            errors.append(
                "decision claim_evidence references unknown input evidence: "
                + ", ".join(sorted(unknown_refs))
            )
    return errors


def _normalize_integral_numbers(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [_normalize_integral_numbers(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _normalize_integral_numbers(item) for key, item in value.items()
        }
    return value


def normalize_label(dataset: str, label: Mapping[str, Any]) -> dict[str, Any]:
    """Copie un label en ordonnant ses ensembles sémantiques."""

    checked_dataset = _require_dataset(dataset)
    if not isinstance(label, Mapping):
        raise ValueError("label must be an object")
    normalized = _normalize_integral_numbers(
        strict_loads(canonical_json(dict(label)), source="<label>")
    )
    if checked_dataset == "retrieval":
        for key in (
            "relevant_product_ids",
            "exact_product_ids",
            "constraint_violating_product_ids",
        ):
            values = normalized.get(key)
            if isinstance(values, list) and all(
                isinstance(value, str) for value in values
            ):
                normalized[key] = sorted(values)
    elif checked_dataset == "decision":
        for key in ("acceptable_outcomes", "forbidden_claims"):
            values = normalized.get(key)
            if isinstance(values, list) and all(
                isinstance(value, str) for value in values
            ):
                normalized[key] = sorted(values)
        entries = normalized.get("claim_evidence")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and isinstance(
                    entry.get("evidence_refs"), list
                ) and all(
                    isinstance(value, str) for value in entry["evidence_refs"]
                ):
                    entry["evidence_refs"] = sorted(entry["evidence_refs"])
            normalized["claim_evidence"] = sorted(
                entries,
                key=lambda entry: canonical_json(
                    {
                        "claim": entry.get("claim"),
                        "evidence_refs": entry.get("evidence_refs"),
                    }
                    if isinstance(entry, Mapping)
                    else entry
                ),
            )
    return normalized


def schema_fingerprint(
    dataset: str,
    quality_root: str | Path | None = None,
) -> str:
    """Empreinte le contenu JSON canonique du schema d'un dataset."""

    checked_dataset = _require_dataset(dataset)
    root = (
        Path(__file__).resolve().parents[2] / "quality"
        if quality_root is None
        else _path(quality_root)
    )
    schema = read_json(root / "schemas" / SCHEMA_FILES[checked_dataset])
    return schema_value_fingerprint(checked_dataset, schema)


def schema_value_fingerprint(dataset: str, schema: Any) -> str:
    """Empreinte un schéma déjà lu, sans second accès au fichier."""

    checked_dataset = _require_dataset(dataset)
    if not isinstance(schema, dict):
        raise ValueError(f"schema for {checked_dataset} must be an object")
    return sha256_value(
        _SCHEMA_DOMAIN,
        {"dataset": checked_dataset, "schema": schema},
    )


def _require_fingerprint(value: Any, field: str) -> str:
    checked = require_identifier(value, field)
    if FINGERPRINT_PATTERN.fullmatch(checked) is None:
        raise ValueError(f"{field} must match sha256:<64 lowercase hex>")
    return checked


def _validated_input(dataset: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("input must be an object")
    expected = set(INPUT_FIELDS[dataset])
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise ValueError(
            f"input is missing fields for {dataset}: {', '.join(missing)}"
        )
    if extra:
        raise ValueError(
            f"input contains non-allowlisted fields for {dataset}: {', '.join(extra)}"
        )
    ensure_no_reserved_fields(value)
    canonical_json(value)
    return value


def input_fingerprint(
    dataset: str,
    case_id: str,
    group_id: str,
    split: str,
    input: dict[str, Any],
) -> str:
    """Empreinte l'identite et l'entree aveugle canonique d'un cas."""

    checked_dataset = _require_dataset(dataset)
    checked_case_id = require_identifier(case_id, "case_id")
    checked_group_id = require_identifier(group_id, "group_id")
    checked_split = require_identifier(split, "split")
    if checked_split not in SPLITS:
        raise ValueError(f"unknown split {checked_split!r}")
    canonical_split = split_for_group(checked_group_id)
    if checked_split != canonical_split:
        raise ValueError(
            f"split {checked_split!r} does not match canonical split {canonical_split!r}"
        )
    checked_input = _validated_input(checked_dataset, input)
    return sha256_value(
        _INPUT_DOMAIN,
        {
            "record_version": RECORD_VERSION,
            "split_policy_version": SPLIT_POLICY_VERSION,
            "dataset": checked_dataset,
            "case_id": checked_case_id,
            "group_id": checked_group_id,
            "split": checked_split,
            "input": checked_input,
        },
    )


def pack_fingerprint(
    dataset: str,
    annotator_id: str,
    schema_fingerprint: str,
    input_fingerprints: Iterable[str],
) -> str:
    """Empreinte un pack, independamment de l'ordre de ses cas."""

    checked_dataset = _require_dataset(dataset)
    checked_annotator = require_identifier(annotator_id, "annotator_id")
    checked_schema = _require_fingerprint(
        schema_fingerprint,
        "schema_fingerprint",
    )
    if isinstance(input_fingerprints, (str, bytes)):
        raise ValueError("input_fingerprints must be an iterable of fingerprints")
    try:
        checked_inputs = [
            _require_fingerprint(value, "input_fingerprint")
            for value in input_fingerprints
        ]
    except TypeError:
        raise ValueError(
            "input_fingerprints must be an iterable of fingerprints"
        ) from None
    if not checked_inputs:
        raise ValueError("input_fingerprints must not be empty")
    if len(checked_inputs) != len(set(checked_inputs)):
        raise ValueError("input_fingerprints must not contain duplicates")
    checked_inputs.sort()
    return sha256_value(
        _PACK_DOMAIN,
        {
            "pack_version": PACK_VERSION,
            "dataset": checked_dataset,
            "annotator_id": checked_annotator,
            "schema_fingerprint": checked_schema,
            "input_fingerprints": checked_inputs,
        },
    )


def completed_pack_fingerprint(
    assignment_fingerprint: str,
    records: Iterable[Mapping[str, Any]],
) -> str:
    """Engage le contenu exact d'un pack rempli, annotations comprises."""

    checked_assignment = _require_fingerprint(
        assignment_fingerprint,
        "assignment_fingerprint",
    )
    if isinstance(records, (str, bytes)):
        raise ValueError("completed pack records must be an iterable of objects")
    try:
        supplied = list(records)
    except TypeError:
        raise ValueError(
            "completed pack records must be an iterable of objects"
        ) from None
    if not all(isinstance(record, Mapping) for record in supplied):
        raise ValueError("completed pack records must be objects")
    completed = [dict(record) for record in supplied]
    if not completed:
        raise ValueError("completed pack records must not be empty")
    if any(
        record.get("pack_fingerprint") != checked_assignment
        for record in completed
    ):
        raise ValueError("completed pack record assignment fingerprint mismatch")
    try:
        case_ids = [
            require_identifier(record.get("case_id"), "case_id")
            for record in completed
        ]
    except ValueError as exc:
        raise ValueError(f"invalid completed pack record: {exc}") from None
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("completed pack case_id values must be unique")
    completed.sort(key=canonical_json)
    return sha256_value(
        _COMPLETED_PACK_DOMAIN,
        {
            "pack_version": PACK_VERSION,
            "assignment_fingerprint": checked_assignment,
            "records": completed,
        },
    )


def _record_without(record: Mapping[str, Any], own_key: str) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("record must be an object")
    result = {key: value for key, value in record.items() if key != own_key}
    canonical_json(result)
    return result


def case_fingerprint(record: Mapping[str, Any]) -> str:
    """Empreinte un cas final en excluant son propre ``case_fingerprint``."""

    return sha256_value(
        _CASE_DOMAIN,
        {
            "record_version": RECORD_VERSION,
            "record": _record_without(record, "case_fingerprint"),
        },
    )


def disagreement_fingerprint(record: Mapping[str, Any]) -> str:
    """Empreinte un desaccord en excluant sa propre empreinte."""

    return sha256_value(
        _DISAGREEMENT_DOMAIN,
        {
            "record_version": RECORD_VERSION,
            "record": _record_without(record, "disagreement_fingerprint"),
        },
    )


def manifest_fingerprint(manifest: Mapping[str, Any]) -> str:
    """Empreinte un manifeste canonique sans ses champs d'auto-empreinte."""

    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    payload = {
        key: value
        for key, value in manifest.items()
        if key not in _MANIFEST_SELF_FIELDS
    }
    return sha256_value(_MANIFEST_DOMAIN, payload)


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    """Alias explicite de :func:`manifest_fingerprint`."""

    return manifest_fingerprint(manifest)


# Alias descriptifs utiles aux producteurs de manifestes sans multiplier les
# implementations de digest.
file_digest = sha256_file
sha256_manifest = manifest_fingerprint


__all__ = [
    "DATASETS",
    "FINGERPRINT_PATTERN",
    "INPUT_FIELDS",
    "LAB_VERSION",
    "PACK_VERSION",
    "RECORD_VERSION",
    "LANGUAGES",
    "SCHEMA_FILES",
    "SCENARIO_TYPES",
    "SPLITS",
    "SPLIT_POLICY_VERSION",
    "SPLIT_SALT",
    "SPLIT_THRESHOLDS",
    "VERTICALS",
    "canonical_json",
    "case_fingerprint",
    "completed_pack_fingerprint",
    "disagreement_fingerprint",
    "ensure_no_reserved_fields",
    "file_digest",
    "input_fingerprint",
    "label_invariant_errors",
    "manifest_digest",
    "manifest_fingerprint",
    "normalize_label",
    "pack_fingerprint",
    "project_blind_input",
    "read_json",
    "read_jsonl",
    "require_identifier",
    "schema_fingerprint",
    "schema_value_fingerprint",
    "sha256_file",
    "sha256_manifest",
    "sha256_value",
    "split_bucket",
    "split_for_group",
    "strict_loads",
    "strict_load_jsonl",
]
