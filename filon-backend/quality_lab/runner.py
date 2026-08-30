"""Runner aveugle et reproductible du FILON Quality Lab.

Le runner ne remet jamais un enregistrement annote a un moteur.  Chaque
adaptateur recoit uniquement l'entree allowlistee du cas, privee des strates
d'evaluation.  Les labels, annotations, identifiants de cas et empreintes ne
franchissent donc pas la frontiere moteur.

Les adaptateurs fournis ici correspondent uniquement aux moteurs qui existent
effectivement dans l'application : taxonomie/role produit, regroupement EAN,
resolution conservative de variantes, attachement exact d'offres, projection
des faits Awin, recherche catalogue et decision generale. Le Graph reste
shadow et non calibre : sa presence ne rend aucun dataset humain eligible.
"""

from __future__ import annotations

import argparse
import asyncio
import ctypes
import errno
import json
import math
import os
import shutil
import sys
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import resolve_intent
from app.observations.awin import project_awin_row
from app.product_graph.resolution import (
    ProductGraphResolutionError,
    RESOLVER_VERSION,
    attach_offer_to_candidates,
    resolve_entity_pair,
    resolve_variant_observation,
)
from app.services import product_role, taxonomy
from app.services.catalog_grouping import normalize_ean
from app.services.catalog_search import search_internal_products

from .integrity import (
    DATASETS,
    FINGERPRINT_PATTERN,
    LAB_VERSION,
    RECORD_VERSION,
    atomic_write_text,
    canonical_json,
    case_fingerprint,
    project_blind_input,
    read_json,
    read_jsonl,
    require_identifier,
    sha256_file,
    strict_loads,
)
from .readiness import build_readiness_report
from .run_identity import RUN_SCHEMA_VERSION, quality_run_id


MAX_RETRIEVAL_RESULTS = 50


class QualityRunnerError(ValueError):
    """Erreur fail-closed avec un libelle stable et exploitable en CLI."""


@dataclass(frozen=True)
class AdapterPrediction:
    """Sortie minimale d'un moteur, avant ajout de la provenance du run."""

    prediction: Mapping[str, Any]
    # Zero signifie explicitement "non calibre".  Les adaptateurs ne
    # transforment jamais une heuristique interne en probabilite artificielle.
    confidence: float = 0.0


class QualityAdapter(ABC):
    """Frontiere explicite entre un dataset et un moteur applicatif reel."""

    dataset: str
    engine_id: str
    engine_version: str

    @abstractmethod
    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        """Execute le moteur sur une copie aveugle, sans metadata d'evaluation."""


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise QualityRunnerError(f"{field_name} must be an object")
    return value


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise QualityRunnerError(f"{field_name} must be a string or null")
    return value


_ROLE_MAP = {
    product_role.MAIN_PRODUCT: "primary_product",
    product_role.ACCESSORY: "accessory",
    product_role.PROTECTIVE_CASE: "accessory",
    product_role.SCREEN_PROTECTOR: "accessory",
    product_role.CHARGER: "accessory",
    product_role.CABLE: "accessory",
    product_role.BATTERY: "accessory",
    product_role.ADAPTER: "accessory",
    product_role.STAND: "accessory",
    product_role.MOUNT: "accessory",
    product_role.HOLDER: "accessory",
    product_role.BAG: "accessory",
    product_role.REPLACEMENT_PART: "replacement_part",
    product_role.CONSUMABLE: "consumable",
    product_role.BUNDLE: "bundle",
    product_role.SERVICE: "service",
    product_role.SUBSCRIPTION: "service",
    product_role.SOFTWARE: "digital_content",
    product_role.UNKNOWN: "unknown",
}


class TaxonomyProductRoleAdapter(QualityAdapter):
    """Branche le dataset taxonomy sur les classifieurs publics du Core."""

    dataset = "taxonomy"
    engine_id = "app.services.taxonomy+app.services.product_role"
    engine_version = f"taxonomy-current+{product_role.VERSION}"

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        observation = _require_mapping(
            engine_input.get("observation"), "taxonomy observation"
        )
        name = _optional_text(observation.get("name"), "observation.name")
        merchant_category = _optional_text(
            observation.get("merchant_category"),
            "observation.merchant_category",
        )
        brand = _optional_text(observation.get("brand"), "observation.brand")
        merchant_name = _optional_text(
            observation.get("merchant_name"), "observation.merchant_name"
        )

        offer_kind = taxonomy.classify_offer_kind(
            merchant_category,
            name,
            brand,
            merchant_name,
        )
        category = taxonomy.classify(
            merchant_category,
            name,
            brand,
            merchant_name,
        )
        subcategory = taxonomy.classify_subcategory(
            category,
            name,
            merchant_category,
            merchant_name,
        )
        understanding = product_role.understand_offer(
            name=name,
            merchant_category=merchant_category,
            brand=brand,
            offer_kind=offer_kind,
        )
        if offer_kind == taxonomy.ACCOMMODATION:
            quality_role = "accommodation"
        elif offer_kind == taxonomy.SERVICE:
            quality_role = "service"
        elif offer_kind == taxonomy.DIGITAL_CONTENT:
            quality_role = "digital_content"
        else:
            quality_role = _ROLE_MAP.get(
                understanding.get("product_role"), "unknown"
            )
            if (
                quality_role == "unknown"
                and offer_kind == taxonomy.TECH_ACCESSORY
            ):
                quality_role = "accessory"

        return AdapterPrediction(
            prediction={
                "category": category or "unknown",
                "subcategory": subcategory or "unknown",
                "product_role": quality_role,
            }
        )


class EanEntityResolutionAdapter(QualityAdapter):
    """Expose l'identite Graph conservative : meme variante ou abstention."""

    dataset = "entity_resolution"
    engine_id = "app.product_graph.resolution.resolve_entity_pair"
    engine_version = RESOLVER_VERSION

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        left = _require_mapping(engine_input.get("left"), "entity left observation")
        right = _require_mapping(
            engine_input.get("right"), "entity right observation"
        )
        try:
            relation = resolve_entity_pair(left, right)
        except ProductGraphResolutionError as exc:
            raise QualityRunnerError(str(exc)) from None
        return AdapterPrediction(prediction=relation.prediction())


class ExactGtinVariantResolutionAdapter(QualityAdapter):
    """Expose le resolver Graph v1, sans similarite textuelle ni confiance."""

    dataset = "variant_resolution"
    engine_id = "app.product_graph.resolution.resolve_variant_observation"
    engine_version = RESOLVER_VERSION

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        observation = _require_mapping(
            engine_input.get("observation"),
            "variant observation",
        )
        try:
            resolution = resolve_variant_observation(observation)
        except ProductGraphResolutionError as exc:
            raise QualityRunnerError(str(exc)) from None
        return AdapterPrediction(prediction=resolution.prediction())


class ExactGtinOfferAttachmentAdapter(QualityAdapter):
    """Attache une offre uniquement a un candidat portant le meme GTIN."""

    dataset = "offer_attachment"
    engine_id = "app.product_graph.resolution.attach_offer_to_candidates"
    engine_version = RESOLVER_VERSION

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        offer = _require_mapping(
            engine_input.get("offer"),
            "offer attachment input",
        )
        try:
            attachment = attach_offer_to_candidates(offer)
        except ProductGraphResolutionError as exc:
            raise QualityRunnerError(str(exc)) from None
        return AdapterPrediction(prediction=attachment.prediction())


def _parse_observed_at(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise QualityRunnerError("offer.observed_at must be an ISO datetime or null")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError):
        raise QualityRunnerError(
            "offer.observed_at must be an ISO datetime or null"
        ) from None


def _money_from_projection(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    amount = value.get("amount")
    currency = value.get("currency")
    if not isinstance(amount, str) or not isinstance(currency, str):
        return None
    try:
        minor = Decimal(amount) * 100
    except InvalidOperation:
        return None
    if minor != minor.to_integral_value() or minor < 0:
        return None
    return {"amount_minor": int(minor), "currency": currency}


def _https_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    return value


class AwinOfferTruthAdapter(QualityAdapter):
    """Projette un payload Awin avec le pipeline shadow append-only reel."""

    dataset = "offer_truth"
    engine_id = "app.observations.awin.project_awin_row"
    engine_version = "awin-offer-observation-v1"

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        offer = _require_mapping(engine_input.get("offer"), "offer truth input")
        source_type = offer.get("source_type")
        if source_type != "awin_feed":
            raise QualityRunnerError(
                "offer truth adapter only supports source_type 'awin_feed'"
            )
        row = _require_mapping(offer.get("row"), "offer.row")
        feed_id = require_identifier(offer.get("feed_id"), "offer.feed_id")
        merchant_id = offer.get("merchant_id")
        if (
            isinstance(merchant_id, bool)
            or not isinstance(merchant_id, int)
            or merchant_id <= 0
        ):
            raise QualityRunnerError("offer.merchant_id must be a positive integer")
        merchant_name = _optional_text(
            offer.get("merchant_name"), "offer.merchant_name"
        )
        projection = project_awin_row(
            row,
            feed_id=feed_id,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            observed_at=_parse_observed_at(offer.get("observed_at")),
        )
        observations = {
            item.field: item
            for item in projection.observations
            if item.status == "verified"
        }
        price_observation = observations.get("price")
        stock_observation = observations.get("availability")
        link_observation = observations.get("deep_link")
        stock = (
            stock_observation.value
            if stock_observation is not None
            and stock_observation.value in {"in_stock", "out_of_stock"}
            else "unknown"
        )
        return AdapterPrediction(
            prediction={
                "price": _money_from_projection(
                    price_observation.value if price_observation else None
                ),
                "stock": stock,
                # AwinProjection ne collecte actuellement aucun fait de port.
                "shipping": None,
                "affiliate_link": _https_url(
                    link_observation.value if link_observation else None
                ),
            }
        )


async def _application_catalog_search(
    query: str,
    budget: float | None,
    *,
    country: str | None,
) -> list[dict[str, Any]]:
    return await search_internal_products(
        query,
        budget,
        limit=MAX_RETRIEVAL_RESULTS,
        country=country,
    )


def _retrieval_identity(row: Mapping[str, Any]) -> str:
    raw_ean = row.get("product_ean")
    normalized_ean = normalize_ean(str(raw_ean)) if raw_ean is not None else None
    if normalized_ean is not None:
        return f"ean:{normalized_ean}"
    offer_id = row.get("offer_id")
    if (
        isinstance(offer_id, bool)
        or not isinstance(offer_id, int)
        or offer_id <= 0
    ):
        raise QualityRunnerError(
            "catalog retrieval result has neither a valid product EAN nor offer_id"
        )
    return f"offer:{offer_id}"


@dataclass
class CatalogRetrievalAdapter(QualityAdapter):
    """Branche retrieval sur la recherche catalogue fail-closed de l'Assistant.

    L'espace d'identifiants est explicite : ``ean:<GTIN normalise>`` lorsque le
    produit est comparable, sinon ``offer:<id>``.  Les contraintes que le moteur
    ne sait pas appliquer font echouer le cas ; elles ne sont jamais ignorees.
    """

    dataset: str = field(default="retrieval", init=False)
    engine_id: str = field(
        default="app.services.catalog_search.search_internal_products",
        init=False,
    )
    engine_version: str = field(
        default="catalog-search-current-evidence-v1", init=False
    )
    search: Callable[..., Awaitable[list[dict[str, Any]]]] = field(
        default=_application_catalog_search,
        repr=False,
    )

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        query = require_identifier(engine_input.get("query"), "retrieval query")
        locale = engine_input.get("locale")
        if locale not in {"fr", "nl", "en"}:
            raise QualityRunnerError("retrieval locale is unsupported")
        constraints = _require_mapping(
            engine_input.get("hard_constraints"), "retrieval hard_constraints"
        )
        unknown_constraints = sorted(
            set(constraints) - {"budget_eur", "country"}
        )
        if unknown_constraints:
            raise QualityRunnerError(
                "catalog retrieval cannot enforce constraints: "
                + ", ".join(unknown_constraints)
            )
        budget = constraints.get("budget_eur")
        if budget is not None and (
            isinstance(budget, bool)
            or not isinstance(budget, (int, float))
            or not math.isfinite(float(budget))
            or float(budget) < 0
        ):
            raise QualityRunnerError(
                "retrieval hard_constraints.budget_eur must be finite and non-negative"
            )
        country = constraints.get("country")
        if country is not None:
            country = require_identifier(country, "retrieval hard_constraints.country")

        rows = await self.search(
            query,
            float(budget) if budget is not None else None,
            country=country,
        )
        if not isinstance(rows, list):
            raise QualityRunnerError("catalog retrieval engine must return a list")
        identities: list[str] = []
        for raw_row in rows:
            row = _require_mapping(raw_row, "catalog retrieval result")
            identity = _retrieval_identity(row)
            if identity not in identities:
                identities.append(identity)
            if len(identities) == MAX_RETRIEVAL_RESULTS:
                break
        return AdapterPrediction(
            prediction={
                "resolution": "matched" if identities else "no_match",
                "retrieved_product_ids": identities,
            }
        )


def _decision_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise QualityRunnerError(f"{field_name} must be an offset-aware ISO datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise QualityRunnerError(
            f"{field_name} must be an offset-aware ISO datetime"
        ) from None
    if parsed.utcoffset() is None:
        raise QualityRunnerError(f"{field_name} must be an offset-aware ISO datetime")
    return parsed.astimezone(UTC)


def _optional_decision_datetime(value: Any, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _decision_datetime(value, field_name)


def _optional_positive_integer(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise QualityRunnerError(f"{field_name} must be a positive integer or null")
    return value


def _required_positive_integer(value: Any, field_name: str) -> int:
    checked = _optional_positive_integer(value, field_name)
    if checked is None:
        raise QualityRunnerError(f"{field_name} is required")
    return checked


def _decision_identifier_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise QualityRunnerError(f"{field_name} must be an array")
    identifiers = [require_identifier(item, f"{field_name} item") for item in value]
    if len(identifiers) != len(set(identifiers)):
        raise QualityRunnerError(f"{field_name} values must be unique")
    return identifiers


def _decision_offer(
    raw_offer: Any,
    *,
    index: int,
) -> tuple[str, CoreOfferSnapshot, list[str]]:
    offer = _require_mapping(raw_offer, f"decision request offer {index}")
    candidate_id = require_identifier(
        offer.get("candidate_id"), f"decision offer {index} candidate_id"
    )
    offer_id = _required_positive_integer(
        offer.get("offer_id"), f"decision offer {index} offer_id"
    )
    price = offer.get("price")
    if price is not None and (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(float(price))
    ):
        raise QualityRunnerError(f"decision offer {index} price must be finite or null")
    availability = offer.get("availability")
    if availability not in {"in_stock", "out_of_stock", "unknown"}:
        raise QualityRunnerError(f"decision offer {index} availability is invalid")
    evidence_refs = _decision_identifier_list(
        offer.get("evidence_refs"),
        f"decision offer {index} evidence_refs",
    )
    if not evidence_refs:
        raise QualityRunnerError(
            f"decision offer {index} evidence_refs must not be empty"
        )

    snapshot = CoreOfferSnapshot(
        offer_id=offer_id,
        catalog_product_id=_optional_positive_integer(
            offer.get("catalog_product_id"),
            f"decision offer {index} catalog_product_id",
        ),
        name=require_identifier(
            offer.get("name"), f"decision offer {index} name"
        ),
        brand=_optional_text(offer.get("brand"), f"decision offer {index} brand"),
        filon_category=_optional_text(
            offer.get("filon_category"),
            f"decision offer {index} filon_category",
        ),
        filon_subcategory=_optional_text(
            offer.get("filon_subcategory"),
            f"decision offer {index} filon_subcategory",
        ),
        offer_kind=_optional_text(
            offer.get("offer_kind"),
            f"decision offer {index} offer_kind",
        ),
        price=float(price) if price is not None else None,
        currency=_optional_text(
            offer.get("currency"), f"decision offer {index} currency"
        ),
        availability=availability,
        image_url=None,
        deep_link=None,
        merchant_id=_required_positive_integer(
            offer.get("merchant_id"),
            f"decision offer {index} merchant_id",
        ),
        merchant_name=require_identifier(
            offer.get("merchant_name"),
            f"decision offer {index} merchant_name",
        ),
        merchant_region=_optional_text(
            offer.get("merchant_region"),
            f"decision offer {index} merchant_region",
        ),
        observed_at=_optional_decision_datetime(
            offer.get("observed_at"),
            f"decision offer {index} observed_at",
        ),
    )
    return candidate_id, snapshot, evidence_refs


class GeneralDecisionAdapter(QualityAdapter):
    """Mesure le planificateur général déterministe sur une entrée sourcée."""

    dataset = "decision"
    engine_id = (
        "app.intelligence.intent_resolution.resolve_intent+"
        "app.intelligence.general_decision.compose_general_plan"
    )
    engine_version = "general-decision-current-evidence-v1"

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        request = _require_mapping(engine_input.get("request"), "decision request")
        query = require_identifier(request.get("query"), "decision request query")
        locale = request.get("locale")
        if locale not in {"fr", "nl", "en"}:
            raise QualityRunnerError("decision request locale is unsupported")
        reference = _decision_datetime(
            request.get("reference_time"), "decision request reference_time"
        )
        raw_offers = request.get("offers")
        if not isinstance(raw_offers, list) or len(raw_offers) > 50:
            raise QualityRunnerError("decision request offers must contain at most 50 rows")

        candidate_ids = _decision_identifier_list(
            engine_input.get("candidate_ids"), "decision candidate_ids"
        )
        inventory = engine_input.get("evidence")
        if not isinstance(inventory, list):
            raise QualityRunnerError("decision evidence must be an array")
        inventory_refs: list[str] = []
        for index, raw_evidence in enumerate(inventory):
            evidence = _require_mapping(raw_evidence, f"decision evidence {index}")
            inventory_refs.append(
                require_identifier(
                    evidence.get("evidence_ref"),
                    f"decision evidence {index} evidence_ref",
                )
            )
            require_identifier(
                evidence.get("source_ref"),
                f"decision evidence {index} source_ref",
            )
        if len(inventory_refs) != len(set(inventory_refs)):
            raise QualityRunnerError("decision evidence_ref values must be unique")
        available_evidence = set(inventory_refs)

        offers: list[CoreOfferSnapshot] = []
        candidate_by_offer_id: dict[int, tuple[str, list[str]]] = {}
        observed_candidate_ids: list[str] = []
        for index, raw_offer in enumerate(raw_offers):
            candidate_id, offer, evidence_refs = _decision_offer(
                raw_offer,
                index=index,
            )
            if offer.offer_id in candidate_by_offer_id:
                raise QualityRunnerError("decision offer_id values must be unique")
            unknown_refs = set(evidence_refs) - available_evidence
            if unknown_refs:
                raise QualityRunnerError(
                    "decision offer evidence_refs are absent from inventory: "
                    + ", ".join(sorted(unknown_refs))
                )
            observed_candidate_ids.append(candidate_id)
            candidate_by_offer_id[offer.offer_id] = (candidate_id, evidence_refs)
            offers.append(offer)
        if candidate_ids != observed_candidate_ids:
            raise QualityRunnerError(
                "decision candidate_ids must match request offers in canonical order"
            )

        intent = resolve_intent(query, locale)
        plan = compose_general_plan(intent, offers, now=reference)
        decision = plan.get("decision")
        if decision == "abstain":
            return AdapterPrediction(
                prediction={"outcome": "abstain", "claims": []}
            )
        if decision != "recommend":
            raise QualityRunnerError(
                "general decision returned an unsupported outcome"
            )

        selected = plan.get("items")
        if not isinstance(selected, list) or not selected:
            raise QualityRunnerError(
                "general decision returned recommend without selected items"
            )
        claims: list[dict[str, Any]] = []
        for raw_item in selected:
            item = _require_mapping(raw_item, "general decision selected item")
            offer_id = item.get("offer_id")
            if (
                isinstance(offer_id, bool)
                or not isinstance(offer_id, int)
                or offer_id not in candidate_by_offer_id
            ):
                raise QualityRunnerError(
                    "general decision selected an unknown candidate"
                )
            candidate_id, evidence_refs = candidate_by_offer_id[offer_id]
            claims.append(
                {
                    "claim": f"selected_candidate:{candidate_id}",
                    "evidence_refs": sorted(evidence_refs),
                }
            )
        return AdapterPrediction(
            prediction={"outcome": "recommend", "claims": claims}
        )


def builtin_adapters() -> dict[str, QualityAdapter]:
    """Retourne les sept branchements applicatifs reels et non calibres."""

    adapters: tuple[QualityAdapter, ...] = (
        TaxonomyProductRoleAdapter(),
        EanEntityResolutionAdapter(),
        ExactGtinVariantResolutionAdapter(),
        ExactGtinOfferAttachmentAdapter(),
        AwinOfferTruthAdapter(),
        CatalogRetrievalAdapter(),
        GeneralDecisionAdapter(),
    )
    return {adapter.dataset: adapter for adapter in adapters}


@dataclass(frozen=True)
class RunArtifacts:
    run_id: str
    manifest_path: Path
    manifest_sha256: str
    dataset_paths: Mapping[str, Path]


def _checked_adapters(
    adapters: Mapping[str, QualityAdapter],
) -> dict[str, QualityAdapter]:
    checked: dict[str, QualityAdapter] = {}
    for dataset, adapter in adapters.items():
        if dataset not in DATASETS:
            raise QualityRunnerError(f"unknown adapter dataset {dataset!r}")
        if not isinstance(adapter, QualityAdapter):
            raise QualityRunnerError(
                f"adapter for {dataset} must implement QualityAdapter"
            )
        if adapter.dataset != dataset:
            raise QualityRunnerError(
                f"adapter key {dataset!r} does not match {adapter.dataset!r}"
            )
        require_identifier(adapter.engine_id, f"{dataset} engine_id")
        require_identifier(adapter.engine_version, f"{dataset} engine_version")
        checked[dataset] = adapter
    return checked


def _json_validator(path: Path, label: str) -> Draft202012Validator:
    schema = read_json(path)
    if not isinstance(schema, dict):
        raise QualityRunnerError(f"{label} schema root must be an object")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise QualityRunnerError(
            f"{label} schema is invalid: {exc.message}"
        ) from None
    return Draft202012Validator(schema)


def _schema_errors(
    validator: Draft202012Validator, value: Mapping[str, Any]
) -> list[str]:
    return [
        violation.message
        for violation in sorted(
            validator.iter_errors(value),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                error.message,
            ),
        )
    ]


def _cleanup_staging(staging: Path, *, parent: Path, prefix: str) -> None:
    """Supprime uniquement le repertoire temporaire cree pour ce run."""

    try:
        resolved = staging.resolve()
        resolved_parent = parent.resolve()
    except OSError:
        return
    if resolved.parent != resolved_parent or not resolved.name.startswith(prefix):
        # Une corruption de chemin ne doit jamais elargir la cible de nettoyage.
        return
    shutil.rmtree(resolved, ignore_errors=True)


def _release_output_lock(descriptor: int, lock_path: Path) -> None:
    try:
        os.close(descriptor)
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            # Le run publie reste complet. Un verrou residuel est fail-closed
            # pour toute tentative ulterieure sur le meme nom de destination.
            pass


def _rename_directory_noreplace(source: Path, destination: Path) -> None:
    """Publie ``source`` atomiquement sans remplacer ``destination``.

    ``os.rename`` peut remplacer un repertoire destination vide sur POSIX. Le
    verrou de publication ne protege que les producteurs cooperatifs ; les
    primitives natives ci-dessous ajoutent la garantie atomique NOREPLACE. Si
    la plateforme ne l'expose pas, le runner echoue ferme.
    """

    if os.name == "nt":
        # Windows refuse deja le remplacement d'une destination existante.
        os.rename(source, destination)
        return

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    result: int
    if sys.platform == "darwin":
        renamex = getattr(libc, "renamex_np", None)
        if renamex is None:
            raise OSError(
                errno.ENOTSUP,
                "atomic no-replace rename is unavailable",
                str(destination),
            )
        renamex.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        renamex.restype = ctypes.c_int
        # macOS <stdio.h>: RENAME_EXCL = 0x00000004.
        result = renamex(source_bytes, destination_bytes, 0x00000004)
    elif sys.platform.startswith("linux"):
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise OSError(
                errno.ENOTSUP,
                "atomic no-replace rename is unavailable",
                str(destination),
            )
        renameat2.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        renameat2.restype = ctypes.c_int
        # Linux: AT_FDCWD = -100 et RENAME_NOREPLACE = 1.
        result = renameat2(-100, source_bytes, -100, destination_bytes, 1)
    else:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-replace rename is unavailable",
            str(destination),
        )

    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            os.strerror(error_number),
            str(destination),
        )


def _records_for_split(
    records: Sequence[Mapping[str, Any]],
    *,
    dataset: str,
    selected_splits: frozenset[str],
) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    seen_case_ids: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise QualityRunnerError(f"{dataset} record must be an object")
        if record.get("dataset") != dataset:
            raise QualityRunnerError(f"{dataset} record has a mismatched dataset")
        if record.get("record_version") != RECORD_VERSION:
            raise QualityRunnerError(
                f"{dataset} record_version must be {RECORD_VERSION}"
            )
        case_id = require_identifier(record.get("case_id"), "case_id")
        if case_id in seen_case_ids:
            raise QualityRunnerError(f"duplicate {dataset} case_id {case_id!r}")
        seen_case_ids.add(case_id)
        if record.get("split") not in selected_splits:
            continue
        supplied_fingerprint = record.get("case_fingerprint")
        if not isinstance(supplied_fingerprint, str) or not FINGERPRINT_PATTERN.fullmatch(
            supplied_fingerprint
        ):
            raise QualityRunnerError(
                f"{dataset}/{case_id} has an invalid case_fingerprint"
            )
        if case_fingerprint(record) != supplied_fingerprint:
            raise QualityRunnerError(
                f"{dataset}/{case_id} case_fingerprint mismatch"
            )
        selected.append(record)
    return sorted(selected, key=lambda record: str(record["case_id"]))


async def _engine_outputs(
    records_by_dataset: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    adapters: Mapping[str, QualityAdapter],
    selected_splits: frozenset[str],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, str]]]:
    selected: dict[str, list[Mapping[str, Any]]] = {}
    for dataset in DATASETS:
        selected[dataset] = _records_for_split(
            records_by_dataset.get(dataset, ()),
            dataset=dataset,
            selected_splits=selected_splits,
        )

    unsupported = sorted(
        dataset for dataset, records in selected.items() if records and dataset not in adapters
    )
    if unsupported:
        raise QualityRunnerError(
            "no real application adapter for non-empty datasets: "
            + ", ".join(unsupported)
        )
    if not any(selected.values()):
        raise QualityRunnerError(
            "no cases selected; an empty run cannot provide quality evidence"
        )

    outputs: dict[str, list[dict[str, Any]]] = {dataset: [] for dataset in DATASETS}
    provenance: dict[str, dict[str, str]] = {}
    for dataset in DATASETS:
        records = selected[dataset]
        if not records:
            continue
        adapter = adapters[dataset]
        provenance[dataset] = {
            "engine_id": adapter.engine_id,
            "engine_version": adapter.engine_version,
        }
        for record in records:
            case_id = str(record["case_id"])
            try:
                input_value = _require_mapping(
                    record.get("input"), f"{dataset}/{case_id} input"
                )
                blind_input = project_blind_input(dataset, input_value)
                # Les strates servent a mesurer la couverture, pas a predire.
                # Les retirer ferme notamment la fuite evidente des tags
                # `no_match` et `ambiguous` vers le retriever.
                engine_input = {
                    key: value for key, value in blind_input.items() if key != "strata"
                }
                # Second round-trip : l'adaptateur ne peut pas muter la copie
                # conservee par le runner et aucun objet Python exotique ne passe.
                isolated_input = strict_loads(
                    canonical_json(engine_input), source="<engine-input>"
                )
                result = await adapter.predict(isolated_input)
            except Exception as exc:
                raise QualityRunnerError(
                    f"{dataset}/{case_id} engine refused the blind input: {exc}"
                ) from None
            if not isinstance(result, AdapterPrediction):
                raise QualityRunnerError(
                    f"{dataset}/{case_id} adapter returned an invalid result"
                )
            if (
                isinstance(result.confidence, bool)
                or not isinstance(result.confidence, (int, float))
                or not math.isfinite(float(result.confidence))
                or not 0 <= float(result.confidence) <= 1
            ):
                raise QualityRunnerError(
                    f"{dataset}/{case_id} adapter confidence is invalid"
                )
            prediction = strict_loads(
                canonical_json(dict(result.prediction)),
                source="<engine-prediction>",
            )
            outputs[dataset].append(
                {
                    "record_version": RECORD_VERSION,
                    "dataset": dataset,
                    "case_id": case_id,
                    "case_fingerprint": record["case_fingerprint"],
                    "confidence": float(result.confidence),
                    "prediction": prediction,
                }
            )
    return outputs, provenance


async def write_run(
    records_by_dataset: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    output_dir: str | Path,
    system_version: str,
    gold_manifest_sha256: str,
    prediction_schema_path: str | Path,
    adapters: Mapping[str, QualityAdapter] | None = None,
    selected_splits: frozenset[str] = frozenset({"test"}),
) -> RunArtifacts:
    """Execute les moteurs puis publie sept JSONL et un manifeste exact.

    ``selected_splits`` est injectable pour des essais synthetiques train/dev,
    tandis que la CLI de production conserve uniquement le holdout ``test``.
    Le dossier de sortie doit etre absent afin qu'un run ne puisse en ecraser un
    autre.
    """

    checked_system_version = require_identifier(system_version, "system_version")
    if not isinstance(gold_manifest_sha256, str) or not FINGERPRINT_PATTERN.fullmatch(
        gold_manifest_sha256
    ):
        raise QualityRunnerError("gold_manifest_sha256 is invalid")
    if not selected_splits or not selected_splits <= {"train", "dev", "test"}:
        raise QualityRunnerError("selected_splits must contain train, dev, or test")
    checked_adapters = _checked_adapters(
        builtin_adapters() if adapters is None else adapters
    )
    outputs, provenance = await _engine_outputs(
        records_by_dataset,
        adapters=checked_adapters,
        selected_splits=selected_splits,
    )
    run_id = quality_run_id(
        system_version=checked_system_version,
        evaluator_version=LAB_VERSION,
        gold_manifest_sha256=gold_manifest_sha256,
        outputs=outputs,
        adapters=provenance,
    )
    prediction_schema = Path(prediction_schema_path).resolve()
    prediction_validator = _json_validator(prediction_schema, "prediction")
    run_manifest_validator = _json_validator(
        prediction_schema.with_name("run-manifest.schema.json"),
        "run manifest",
    )
    completed: dict[str, list[dict[str, Any]]] = {dataset: [] for dataset in DATASETS}
    for dataset in DATASETS:
        for partial in outputs[dataset]:
            record = dict(partial)
            record["run_id"] = run_id
            errors = _schema_errors(prediction_validator, record)
            if errors:
                raise QualityRunnerError(
                    f"{dataset}/{record['case_id']} prediction schema rejected engine output: "
                    + "; ".join(errors)
                )
            completed[dataset].append(record)

    destination = Path(output_dir).resolve()
    parent = destination.parent
    if destination.exists():
        raise QualityRunnerError(f"output directory already exists: {destination}")
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise QualityRunnerError(
            f"unable to create output parent: {parent}"
        ) from None

    lock_path = parent / f".{destination.name}.publish.lock"
    try:
        lock_descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError:
        raise QualityRunnerError(
            f"another publisher owns the output lock: {lock_path}"
        ) from None
    except OSError:
        raise QualityRunnerError(
            f"unable to create output lock: {lock_path}"
        ) from None

    staging_prefix = f".{destination.name}.staging-"
    try:
        staging = Path(tempfile.mkdtemp(prefix=staging_prefix, dir=parent))
    except OSError:
        _release_output_lock(lock_descriptor, lock_path)
        raise QualityRunnerError(
            f"unable to create staging directory beside: {destination}"
        ) from None

    dataset_configs: dict[str, dict[str, str]] = {}
    try:
        prediction_dir = staging / "predictions"
        prediction_dir.mkdir(parents=False, exist_ok=False)
        for dataset in DATASETS:
            path = prediction_dir / f"{dataset}.jsonl"
            payload = "".join(
                canonical_json(record) + "\n" for record in completed[dataset]
            )
            atomic_write_text(path, payload)
            dataset_configs[dataset] = {
                "path": f"predictions/{dataset}.jsonl",
                "sha256": sha256_file(path),
            }
        manifest = {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": run_id,
            "system_version": checked_system_version,
            "evaluator_version": LAB_VERSION,
            "gold_manifest_sha256": gold_manifest_sha256,
            "adapters": provenance,
            "datasets": dataset_configs,
        }
        manifest_errors = _schema_errors(run_manifest_validator, manifest)
        if manifest_errors:
            raise QualityRunnerError(
                "run manifest schema rejected generated artifact: "
                + "; ".join(manifest_errors)
            )
        staging_manifest = staging / "run-manifest.json"
        atomic_write_text(staging_manifest, canonical_json(manifest) + "\n")
        # Le verrou serialise les producteurs cooperatifs ; la primitive native
        # NOREPLACE ferme aussi la course avec tout producteur non cooperatif.
        _rename_directory_noreplace(staging, destination)
    except (OSError, ValueError) as exc:
        _cleanup_staging(staging, parent=parent, prefix=staging_prefix)
        raise QualityRunnerError(f"unable to publish run artifacts: {exc}") from None
    finally:
        _release_output_lock(lock_descriptor, lock_path)

    manifest_path = destination / "run-manifest.json"
    dataset_paths = {
        dataset: destination / "predictions" / f"{dataset}.jsonl"
        for dataset in DATASETS
    }
    return RunArtifacts(
        run_id=run_id,
        manifest_path=manifest_path,
        manifest_sha256=sha256_file(manifest_path),
        dataset_paths=dataset_paths,
    )


def _safe_dataset_path(root: Path, relative: Any, dataset: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise QualityRunnerError(f"{dataset} dataset path is invalid")
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise QualityRunnerError(f"{dataset} dataset path escapes quality root")
    return candidate


async def run_from_manifest(
    manifest_path: str | Path,
    *,
    output_dir: str | Path,
    system_version: str,
    adapters: Mapping[str, QualityAdapter] | None = None,
) -> RunArtifacts:
    """Charge le roster ferme du manifeste et execute uniquement le holdout."""

    manifest_file = Path(manifest_path).resolve()
    manifest = read_json(manifest_file)
    if not isinstance(manifest, Mapping):
        raise QualityRunnerError("quality manifest root must be an object")
    configs = manifest.get("datasets")
    if not isinstance(configs, Mapping) or set(configs) != set(DATASETS):
        raise QualityRunnerError("quality manifest must contain exactly seven datasets")
    readiness = build_readiness_report(manifest_file)
    if not readiness.get("integrity_valid", False):
        raise QualityRunnerError(
            "quality manifest or datasets failed the integrity audit"
        )
    quality_root = manifest_file.parent
    records_by_dataset: dict[str, list[dict[str, Any]]] = {}
    for dataset in DATASETS:
        config = _require_mapping(configs[dataset], f"{dataset} manifest config")
        path = _safe_dataset_path(quality_root, config.get("path"), dataset)
        records_by_dataset[dataset] = read_jsonl(path)
    return await write_run(
        records_by_dataset,
        output_dir=output_dir,
        system_version=system_version,
        gold_manifest_sha256=sha256_file(manifest_file),
        prediction_schema_path=quality_root / "schemas" / "prediction.schema.json",
        adapters=adapters,
        selected_splits=frozenset({"test"}),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute les moteurs FILON sur les entrees aveugles du Quality Lab"
    )
    parser.add_argument("--manifest", default="../quality/manifest.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--system-version",
        required=True,
        help="version immuable du systeme evalue (par exemple un SHA Git)",
    )
    args = parser.parse_args()
    try:
        artifacts = asyncio.run(
            run_from_manifest(
                args.manifest,
                output_dir=args.output_dir,
                system_version=args.system_version,
            )
        )
    except (QualityRunnerError, ValueError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "run_manifest": os.fspath(artifacts.manifest_path),
                "run_manifest_sha256": artifacts.manifest_sha256,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
