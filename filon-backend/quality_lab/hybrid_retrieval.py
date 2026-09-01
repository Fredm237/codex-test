"""Benchmark autonome Phase 5 Hybrid Retrieval.

Le corpus est entièrement synthétique, déterministe, multilingue et séparé du
code des futurs adaptateurs. L'oracle ratifie les attentes ; l'adaptateur
``legacy_offer_first`` démontre que le benchmark détecte les anti-patterns que
Phase 5 doit éliminer. Aucun résultat oracle n'est éligible à une promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .integrity import atomic_write_text, canonical_json


SCHEMA_VERSION = "hybrid-retrieval-benchmark/v1"
MANIFEST_VERSION = "hybrid-retrieval-benchmark-manifest/v1"
GENERATOR_VERSION = "filon-hybrid-retrieval-holdout/v1"
LIMITATION = "NO_EXTERNAL_HUMAN_GROUND_TRUTH"
ORACLE_VERSION = "hybrid-retrieval-contract-oracle/v1"
LEGACY_VERSION = "legacy-offer-first-simulator/v1"
VERTICALS = (
    "smartphones",
    "laptops",
    "audio",
    "fashion",
    "appliances_hvac",
    "tyres",
)
LOCALES = ("fr", "nl", "en")
SCENARIOS = (
    "exact_product",
    "multilingual_alias",
    "no_match",
    "ambiguous",
    "accessory_trap",
    "constraint_conflict",
    "duplicate_offers",
    "semantic_only_unresolved",
)


class HybridRetrievalBenchmarkError(ValueError):
    """Manifest, regressions ou corpus hors contrat."""


@dataclass(frozen=True)
class Candidate:
    entity_ref: str | None
    product_role: str
    product_type: str
    model: str
    attributes: Mapping[str, str]
    offer_ids: tuple[int, ...]
    source_types: tuple[str, ...]
    violates_constraint: bool = False


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    vertical: str
    locale: str
    scenario: str
    query: str
    expected_outcome: str
    expected_entity_refs: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    truth_basis: str


@dataclass(frozen=True)
class PredictedCandidate:
    entity_ref: str | None
    offer_ids: tuple[int, ...]
    source_types: tuple[str, ...]
    violates_constraint: bool


@dataclass(frozen=True)
class Prediction:
    outcome: str
    candidates: tuple[PredictedCandidate, ...]


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    vertical: str
    locale: str
    scenario: str
    expected_outcome: str
    actual_outcome: str
    expected_entity_refs: tuple[str, ...]
    actual_entity_refs: tuple[str | None, ...]
    recall_hits: int
    recall_total: int
    ndcg_at_10: float
    top3_relevant: bool | None
    constraint_violations: int
    false_product_groupings: int
    provenance_candidates: int
    provenance_complete_candidates: int
    semantic_only_false_resolutions: int
    passed: bool
    truth_basis: str


def _wilson(successes: int, total: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        raise HybridRetrievalBenchmarkError("metric denominator must be positive")
    probability = successes / total
    denominator = 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        probability * (1 - probability) / total + z * z / (4 * total * total)
    ) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _metric(successes: int, total: int) -> dict[str, Any]:
    lower, upper = _wilson(successes, total)
    return {
        "cases": total,
        "successes": successes,
        "rate": round(successes / total, 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def _event_metric(events: int, total: int, event_name: str) -> dict[str, Any]:
    lower, upper = _wilson(events, total)
    return {
        "cases": total,
        event_name: events,
        "rate": round(events / total, 8),
        "ci95_lower": round(lower, 8),
        "ci95_upper": round(upper, 8),
    }


def _load_json(path: Path, error: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HybridRetrievalBenchmarkError(error) from exc
    if not isinstance(value, Mapping):
        raise HybridRetrievalBenchmarkError(error)
    return value


def _load_manifest(path: Path) -> Mapping[str, Any]:
    manifest = _load_json(path, "hybrid retrieval manifest is unreadable")
    if manifest.get("schema_version") != MANIFEST_VERSION:
        raise HybridRetrievalBenchmarkError("unsupported hybrid retrieval manifest")
    if manifest.get("limitation") != LIMITATION:
        raise HybridRetrievalBenchmarkError("human-ground-truth limitation is missing")
    if manifest.get("retrieval_policy") != "product_first_expand_only_fail_closed":
        raise HybridRetrievalBenchmarkError("retrieval policy is invalid")
    if manifest.get("verticals") != list(VERTICALS):
        raise HybridRetrievalBenchmarkError("vertical roster is invalid")
    if manifest.get("locales") != list(LOCALES):
        raise HybridRetrievalBenchmarkError("locale roster is invalid")
    if manifest.get("scenarios") != list(SCENARIOS):
        raise HybridRetrievalBenchmarkError("scenario roster is invalid")

    generator = manifest.get("generator")
    if not isinstance(generator, Mapping):
        raise HybridRetrievalBenchmarkError("generator configuration is missing")
    seeds = generator.get("seeds")
    samples = generator.get("samples_per_vertical_seed")
    if (
        generator.get("version") != GENERATOR_VERSION
        or generator.get("development_engine_input") is not False
        or not isinstance(seeds, list)
        or not seeds
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or isinstance(samples, bool)
        or not isinstance(samples, int)
        or not 32 <= samples <= 512
    ):
        raise HybridRetrievalBenchmarkError("generator configuration is invalid")

    expected_support = {
        "positive_cases": 4000,
        "no_match_cases": 2000,
        "ambiguous_cases": 2000,
        "constraint_cases": 1000,
        "grouping_cases": 1000,
        "semantic_only_cases": 1000,
    }
    if manifest.get("minimum_statistical_support") != expected_support:
        raise HybridRetrievalBenchmarkError("minimum statistical support is invalid")

    gates = manifest.get("gates")
    required_gates = {
        "recall_at_50_min",
        "ndcg_at_10_min",
        "top3_relevance_ci95_lower_min",
        "no_match_accuracy_ci95_lower_min",
        "ambiguous_accuracy_ci95_lower_min",
        "constraint_violations_max",
        "false_product_groupings_max",
        "provenance_completeness_min",
        "semantic_only_false_resolutions_max",
        "blocking_failures_max",
    }
    if not isinstance(gates, Mapping) or set(gates) != required_gates:
        raise HybridRetrievalBenchmarkError("benchmark gates are invalid")
    exact_thresholds = {
        "recall_at_50_min": 0.95,
        "ndcg_at_10_min": 0.85,
        "top3_relevance_ci95_lower_min": 0.90,
        "no_match_accuracy_ci95_lower_min": 0.99,
        "ambiguous_accuracy_ci95_lower_min": 0.95,
        "constraint_violations_max": 0,
        "false_product_groupings_max": 0,
        "provenance_completeness_min": 1.0,
        "semantic_only_false_resolutions_max": 0,
        "blocking_failures_max": 0,
    }
    if gates != exact_thresholds:
        raise HybridRetrievalBenchmarkError("benchmark thresholds are not ratified gates")
    regression = manifest.get("regression_ground_truth")
    if not isinstance(regression, str) or Path(regression).name != regression:
        raise HybridRetrievalBenchmarkError("regression path is invalid")
    return manifest


def _surface(vertical: str, index: int) -> dict[str, str]:
    return {
        "smartphones": {"type": "smartphone", "brand": "Example Mobile", "model": f"Phone Pro {index}", "attribute": "storage", "a": "128GB", "b": "256GB", "accessory": "protective case"},
        "laptops": {"type": "laptop", "brand": "Example Compute", "model": f"Notebook Air {index}", "attribute": "memory", "a": "16GB", "b": "32GB", "accessory": "power adapter"},
        "audio": {"type": "headphones", "brand": "Example Audio", "model": f"Sound Max {index}", "attribute": "color", "a": "black", "b": "white", "accessory": "carrying case"},
        "fashion": {"type": "jacket", "brand": "Example Wear", "model": f"Urban Shell {index}", "attribute": "size", "a": "M", "b": "XL", "accessory": "garment bag"},
        "appliances_hvac": {"type": "air conditioner", "brand": "Example Home", "model": f"Climate Pro {index}", "attribute": "capacity", "a": "9000BTU", "b": "12000BTU", "accessory": "replacement filter"},
        "tyres": {"type": "tyre", "brand": "Example Tyres", "model": f"Road Grip {index}", "attribute": "size", "a": "205/55R16", "b": "225/45R17", "accessory": "wheel cover"},
    }[vertical]


def _query(locale: str, scenario: str, surface: Mapping[str, str]) -> str:
    type_alias = {
        "fr": {"smartphone": "téléphone", "laptop": "ordinateur portable", "headphones": "casque", "jacket": "veste", "air conditioner": "climatiseur", "tyre": "pneu"},
        "nl": {"smartphone": "telefoon", "laptop": "laptop", "headphones": "koptelefoon", "jacket": "jas", "air conditioner": "airco", "tyre": "band"},
        "en": {"smartphone": "phone", "laptop": "laptop", "headphones": "headphones", "jacket": "jacket", "air conditioner": "air conditioner", "tyre": "tyre"},
    }[locale][surface["type"]]
    if scenario == "no_match":
        return f"Synthetic Missing {type_alias} ZXQ"
    if scenario == "ambiguous":
        return type_alias
    if scenario == "accessory_trap":
        return f"{surface['brand']} {surface['model']} {type_alias}"
    if scenario == "constraint_conflict":
        return f"{surface['model']} {surface['attribute']} {surface['a']}"
    if scenario == "semantic_only_unresolved":
        return f"quiet comfortable {type_alias}"
    return f"{surface['brand']} {surface['model']} {type_alias}"


def _candidate(
    ref: str | None,
    surface: Mapping[str, str],
    *,
    role: str = "PRIMARY_PRODUCT",
    model: str | None = None,
    attribute: str | None = None,
    offers: tuple[int, ...],
    sources: tuple[str, ...],
    violates: bool = False,
) -> Candidate:
    return Candidate(
        entity_ref=ref,
        product_role=role,
        product_type=surface["type"],
        model=(model or surface["model"]) if role == "PRIMARY_PRODUCT" else surface["accessory"],
        attributes={surface["attribute"]: attribute or surface["a"]},
        offer_ids=offers,
        source_types=sources,
        violates_constraint=violates,
    )


def _build_case(*, case_id: str, vertical: str, locale: str, scenario: str, index: int, truth_basis: str) -> BenchmarkCase:
    surface = _surface(vertical, index)
    base = abs(int(hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:10], 16))
    main_ref = f"variant:{base}"
    sibling_ref = f"variant:{base + 1}"
    accessory_ref = f"variant:{base + 2}"
    main = _candidate(main_ref, surface, offers=(base + 10,), sources=("LEXICAL", "STRUCTURED"))
    sibling = _candidate(
        sibling_ref,
        surface,
        model=f"Alternative {index}",
        attribute=surface["b"],
        offers=(base + 20,),
        sources=("LEXICAL", "SEMANTIC"),
    )
    accessory = _candidate(accessory_ref, surface, role="ACCESSORY", offers=(base + 30,), sources=("LEXICAL",))
    outcome = "CANDIDATES"
    expected: tuple[str, ...] = (main_ref,)
    candidates: tuple[Candidate, ...]
    if scenario in {"exact_product", "multilingual_alias"}:
        candidates = (main, sibling, accessory)
    elif scenario == "no_match":
        outcome, expected, candidates = "NO_MATCH", (), (sibling, accessory)
    elif scenario == "ambiguous":
        outcome, expected, candidates = "AMBIGUOUS", (), (main, sibling)
    elif scenario == "accessory_trap":
        candidates = (accessory, main, sibling)
    elif scenario == "constraint_conflict":
        conflict = _candidate(
            sibling_ref,
            surface,
            model=surface["model"],
            attribute=surface["b"],
            offers=(base + 20,),
            sources=("LEXICAL", "STRUCTURED"),
            violates=True,
        )
        accessory_conflict = _candidate(accessory_ref, surface, role="ACCESSORY", offers=(base + 30,), sources=("LEXICAL",), violates=True)
        outcome, expected, candidates = "NO_MATCH", (), (conflict, accessory_conflict)
    elif scenario == "duplicate_offers":
        duplicate_a = _candidate(main_ref, surface, offers=(base + 10,), sources=("LEXICAL",))
        duplicate_b = _candidate(main_ref, surface, offers=(base + 11, base + 12), sources=("STRUCTURED", "SEMANTIC"))
        candidates = (duplicate_a, duplicate_b, sibling)
    elif scenario == "semantic_only_unresolved":
        unresolved = _candidate(None, surface, offers=(), sources=("SEMANTIC",))
        outcome, expected, candidates = "AMBIGUOUS", (), (unresolved,)
    else:  # pragma: no cover - roster validated before generation
        raise HybridRetrievalBenchmarkError("unknown benchmark scenario")
    return BenchmarkCase(
        case_id=case_id,
        vertical=vertical,
        locale=locale,
        scenario=scenario,
        query=_query(locale, scenario, surface),
        expected_outcome=outcome,
        expected_entity_refs=expected,
        candidates=candidates,
        truth_basis=truth_basis,
    )


def _generated_cases(*, seed: int, samples: int) -> list[BenchmarkCase]:
    rng = random.Random(seed)
    cases: list[BenchmarkCase] = []
    for vertical_index, vertical in enumerate(VERTICALS):
        for index in range(samples):
            locale = LOCALES[(index + vertical_index + rng.randrange(len(LOCALES))) % len(LOCALES)]
            for scenario in SCENARIOS:
                case_id = f"holdout:{seed}:{vertical}:{index}:{scenario}"
                cases.append(
                    _build_case(
                        case_id=case_id,
                        vertical=vertical,
                        locale=locale,
                        scenario=scenario,
                        index=index,
                        truth_basis="DETERMINISTIC_SYNTHETIC_ORACLE",
                    )
                )
    return cases


def _regression_cases(path: Path, manifest: Mapping[str, Any]) -> tuple[list[BenchmarkCase], Mapping[str, Any]]:
    payload = _load_json(path.parent / str(manifest["regression_ground_truth"]), "hybrid retrieval regressions are unreadable")
    if (
        payload.get("schema_version") != "hybrid-retrieval-regressions/v1"
        or payload.get("truth_basis") != "REGRESSION_GROUND_TRUTH"
        or payload.get("limitation") != LIMITATION
        or not isinstance(payload.get("cases"), list)
    ):
        raise HybridRetrievalBenchmarkError("hybrid retrieval regressions are invalid")
    cases: list[BenchmarkCase] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(payload["cases"]):
        if not isinstance(raw, Mapping):
            raise HybridRetrievalBenchmarkError("regression case is invalid")
        case_id = raw.get("case_id")
        vertical = raw.get("vertical")
        locale = raw.get("locale")
        scenario = raw.get("scenario")
        truth_basis = raw.get("truth_basis")
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in identifiers
            or vertical not in VERTICALS
            or locale not in LOCALES
            or scenario not in SCENARIOS
            or not isinstance(truth_basis, str)
            or not truth_basis
        ):
            raise HybridRetrievalBenchmarkError("regression case is invalid")
        identifiers.add(case_id)
        cases.append(_build_case(case_id=f"regression:{case_id}", vertical=str(vertical), locale=str(locale), scenario=str(scenario), index=index + 9000, truth_basis=str(truth_basis)))
    if {case.vertical for case in cases} != set(VERTICALS):
        raise HybridRetrievalBenchmarkError("regressions must cover every vertical")
    if {case.locale for case in cases} != set(LOCALES):
        raise HybridRetrievalBenchmarkError("regressions must cover every locale")
    if {case.scenario for case in cases} != set(SCENARIOS):
        raise HybridRetrievalBenchmarkError("regressions must cover every scenario")
    return cases, payload


def _oracle_prediction(case: BenchmarkCase) -> Prediction:
    if case.expected_outcome == "NO_MATCH":
        return Prediction("NO_MATCH", ())
    if case.expected_outcome == "AMBIGUOUS":
        quarantined = tuple(
            PredictedCandidate(None, (), candidate.source_types, False)
            for candidate in case.candidates
        )
        return Prediction("AMBIGUOUS", quarantined)
    grouped: list[PredictedCandidate] = []
    for ref in case.expected_entity_refs:
        matches = [candidate for candidate in case.candidates if candidate.entity_ref == ref]
        offers = tuple(sorted({offer for candidate in matches for offer in candidate.offer_ids}))
        sources = tuple(sorted({source for candidate in matches for source in candidate.source_types}))
        grouped.append(PredictedCandidate(ref, offers, sources, False))
    return Prediction("CANDIDATES", tuple(grouped))


def _legacy_prediction(case: BenchmarkCase) -> Prediction:
    if not case.candidates:
        return Prediction("NO_MATCH", ())
    predicted = tuple(
        PredictedCandidate(
            candidate.entity_ref or f"legacy-unresolved:{index}",
            candidate.offer_ids,
            candidate.source_types,
            candidate.violates_constraint,
        )
        for index, candidate in enumerate(case.candidates)
    )
    return Prediction("CANDIDATES", predicted)


def _lexical_prediction(case: BenchmarkCase) -> Prediction:
    from app.hybrid_retrieval.lexical import LexicalDocument, retrieve_lexical

    documents = tuple(
        LexicalDocument(
            document_ref=f"{case.case_id}:{index}",
            entity_ref=candidate.entity_ref,
            brand=_surface(case.vertical, 0)["brand"],
            model=candidate.model,
            product_type=candidate.product_type,
            product_role=candidate.product_role,
            attributes=candidate.attributes,
            offer_ids=candidate.offer_ids,
        )
        for index, candidate in enumerate(case.candidates)
        if "LEXICAL" in candidate.source_types
    )
    result = retrieve_lexical(case.query, documents)
    return Prediction(
        result.outcome,
        tuple(
            PredictedCandidate(hit.entity_ref, hit.offer_ids, ("LEXICAL",), False)
            for hit in result.hits
        ),
    )


def _expanded_prediction(case: BenchmarkCase) -> Prediction:
    from app.hybrid_retrieval.expand_only import combine_expand_only
    from app.hybrid_retrieval.lexical import LexicalDocument, retrieve_lexical
    from app.hybrid_retrieval.semantic import SemanticDocument, retrieve_semantic
    from app.hybrid_retrieval.structured import (
        StructuredDocument,
        intent_from_query,
        retrieve_structured,
    )
    brand = _surface(case.vertical, 0)["brand"]
    lexical_documents = tuple(
        LexicalDocument(
            document_ref=f"{case.case_id}:lexical:{index}",
            entity_ref=candidate.entity_ref,
            brand=brand,
            model=candidate.model,
            product_type=candidate.product_type,
            product_role=candidate.product_role,
            attributes=candidate.attributes,
            offer_ids=candidate.offer_ids,
        )
        for index, candidate in enumerate(case.candidates)
        if "LEXICAL" in candidate.source_types
    )
    structured_documents = tuple(
        StructuredDocument(
            document_ref=f"{case.case_id}:structured:{index}",
            entity_ref=candidate.entity_ref,
            product_type=(
                "airconditioner"
                if candidate.product_type == "air conditioner"
                else candidate.product_type
            ),
            product_role=candidate.product_role,
            attributes=candidate.attributes,
            offer_ids=candidate.offer_ids,
        )
        for index, candidate in enumerate(case.candidates)
        if "STRUCTURED" in candidate.source_types
    )
    semantic_documents = tuple(
        SemanticDocument(
            document_ref=f"{case.case_id}:semantic:{index}",
            entity_ref=candidate.entity_ref,
            product_type=candidate.product_type,
            offer_ids=candidate.offer_ids,
        )
        for index, candidate in enumerate(case.candidates)
        if "SEMANTIC" in candidate.source_types
    )
    result = combine_expand_only(
        retrieve_lexical(case.query, lexical_documents),
        retrieve_structured(intent_from_query(case.query), structured_documents),
        retrieve_semantic(case.query, semantic_documents),
    )
    return Prediction(
        result.outcome,
        tuple(
            PredictedCandidate(
                candidate.entity_ref,
                candidate.offer_ids,
                candidate.source_types,
                False,
            )
            for candidate in result.candidates
        ),
    )


def _fused_prediction(case: BenchmarkCase) -> Prediction:
    from app.hybrid_retrieval.fusion import FusionSourceHit, reciprocal_rank_fusion
    from app.hybrid_retrieval.lexical import LexicalDocument, retrieve_lexical
    from app.hybrid_retrieval.semantic import SemanticDocument, retrieve_semantic
    from app.hybrid_retrieval.structured import StructuredDocument, intent_from_query, retrieve_structured

    brand = _surface(case.vertical, 0)["brand"]
    lexical = retrieve_lexical(
        case.query,
        tuple(
            LexicalDocument(
                f"{case.case_id}:lexical:{index}", candidate.entity_ref, brand,
                candidate.model, candidate.product_type, candidate.product_role,
                candidate.attributes, candidate.offer_ids,
            )
            for index, candidate in enumerate(case.candidates)
            if "LEXICAL" in candidate.source_types
        ),
    )
    structured = retrieve_structured(
        intent_from_query(case.query),
        tuple(
            StructuredDocument(
                f"{case.case_id}:structured:{index}", candidate.entity_ref,
                "airconditioner" if candidate.product_type == "air conditioner" else candidate.product_type,
                candidate.product_role, candidate.attributes, candidate.offer_ids,
            )
            for index, candidate in enumerate(case.candidates)
            if "STRUCTURED" in candidate.source_types
        ),
    )
    semantic = retrieve_semantic(
        case.query,
        tuple(
            SemanticDocument(
                f"{case.case_id}:semantic:{index}", candidate.entity_ref,
                candidate.product_type, candidate.offer_ids,
            )
            for index, candidate in enumerate(case.candidates)
            if "SEMANTIC" in candidate.source_types
        ),
    )
    hits = [
        FusionSourceHit("LEXICAL", hit.source_rank, hit.entity_ref, hit.offer_ids, f"{case.case_id}:lexical:{hit.source_rank}")
        for hit in lexical.hits
    ]
    hits.extend(
        FusionSourceHit("STRUCTURED", hit.source_rank, hit.entity_ref, hit.offer_ids, f"{case.case_id}:structured:{hit.source_rank}")
        for hit in structured.hits
    )
    hits.extend(
        FusionSourceHit("SEMANTIC", hit.source_rank, hit.entity_ref, hit.offer_ids, f"{case.case_id}:semantic:{hit.source_rank}")
        for hit in semantic.hits
    )
    query_digest = "sha256:" + hashlib.sha256(case.query.encode("utf-8")).hexdigest()
    result = reciprocal_rank_fusion(
        hits,
        query_digest=query_digest,
        snapshot_ref=case.case_id,
        index_versions={"LEXICAL": "synthetic-lexical/v1", "STRUCTURED": "synthetic-structured/v1", "SEMANTIC": "synthetic-semantic/v1"},
        ambiguity_guard=lexical.outcome == "AMBIGUOUS" or structured.outcome == "AMBIGUOUS",
    )
    return Prediction(
        result.outcome,
        tuple(
            PredictedCandidate(
                candidate.entity_ref,
                candidate.offer_ids,
                tuple(evidence.source_type for evidence in candidate.source_evidence),
                False,
            )
            for candidate in result.candidates
        ),
    )



def _ndcg(actual: tuple[str | None, ...], expected: tuple[str, ...], *, limit: int = 10) -> float:
    if not expected:
        return 1.0
    seen: set[str] = set()
    dcg = 0.0
    for index, entity_ref in enumerate(actual[:limit]):
        relevant = entity_ref in expected and entity_ref not in seen
        if entity_ref is not None:
            seen.add(entity_ref)
        if relevant:
            dcg += 3.0 / math.log2(index + 2)
    ideal = sum(3.0 / math.log2(index + 2) for index in range(min(len(expected), limit)))
    return dcg / ideal


def _evaluate(case: BenchmarkCase, *, adapter: str) -> CaseResult:
    if adapter == "oracle":
        prediction = _oracle_prediction(case)
    elif adapter == "legacy_offer_first":
        prediction = _legacy_prediction(case)
    elif adapter == "lexical":
        prediction = _lexical_prediction(case)
    elif adapter == "expanded":
        prediction = _expanded_prediction(case)
    elif adapter == "fused":
        prediction = _fused_prediction(case)
    else:
        raise HybridRetrievalBenchmarkError("benchmark adapter is invalid")
    actual_refs = tuple(candidate.entity_ref for candidate in prediction.candidates)
    unique_actual = {ref for ref in actual_refs[:50] if ref is not None}
    recall_hits = sum(ref in unique_actual for ref in case.expected_entity_refs)
    top3 = None if not case.expected_entity_refs else any(ref in case.expected_entity_refs for ref in actual_refs[:3])
    counts: dict[str, int] = {}
    for ref in actual_refs:
        if ref is not None:
            counts[ref] = counts.get(ref, 0) + 1
    false_groupings = sum(count - 1 for count in counts.values() if count > 1)
    provenance_candidates = len(prediction.candidates)
    provenance_complete = sum(bool(candidate.source_types) for candidate in prediction.candidates)
    constraint_violations = sum(candidate.violates_constraint for candidate in prediction.candidates[:10])
    semantic_false = 0
    if case.scenario == "semantic_only_unresolved":
        semantic_false = sum(candidate.entity_ref is not None for candidate in prediction.candidates)
    passed = (
        prediction.outcome == case.expected_outcome
        and recall_hits == len(case.expected_entity_refs)
        and constraint_violations == 0
        and false_groupings == 0
        and provenance_complete == provenance_candidates
        and semantic_false == 0
    )
    return CaseResult(
        case_id=case.case_id,
        vertical=case.vertical,
        locale=case.locale,
        scenario=case.scenario,
        expected_outcome=case.expected_outcome,
        actual_outcome=prediction.outcome,
        expected_entity_refs=case.expected_entity_refs,
        actual_entity_refs=actual_refs,
        recall_hits=recall_hits,
        recall_total=len(case.expected_entity_refs),
        ndcg_at_10=round(_ndcg(actual_refs, case.expected_entity_refs), 8),
        top3_relevant=top3,
        constraint_violations=constraint_violations,
        false_product_groupings=false_groupings,
        provenance_candidates=provenance_candidates,
        provenance_complete_candidates=provenance_complete,
        semantic_only_false_resolutions=semantic_false,
        passed=passed,
        truth_basis=case.truth_basis,
    )


def build_report(manifest_path: str | Path, *, adapter: str = "oracle") -> dict[str, Any]:
    path = Path(manifest_path).resolve()
    manifest = _load_manifest(path)
    cases, regressions = _regression_cases(path, manifest)
    generator = manifest["generator"]
    for seed in generator["seeds"]:
        cases.extend(_generated_cases(seed=seed, samples=generator["samples_per_vertical_seed"]))
    results = [_evaluate(case, adapter=adapter) for case in cases]

    positives = [result for result in results if result.recall_total]
    no_match = [result for result in results if result.expected_outcome == "NO_MATCH"]
    ambiguous = [result for result in results if result.expected_outcome == "AMBIGUOUS"]
    constraints = [result for result in results if result.scenario == "constraint_conflict"]
    grouping = [result for result in results if result.scenario == "duplicate_offers"]
    semantic_only = [result for result in results if result.scenario == "semantic_only_unresolved"]
    recall_hits = sum(result.recall_hits for result in positives)
    recall_total = sum(result.recall_total for result in positives)
    top3_successes = sum(result.top3_relevant is True for result in positives)
    no_match_successes = sum(result.actual_outcome == "NO_MATCH" and not result.actual_entity_refs for result in no_match)
    ambiguous_successes = sum(result.actual_outcome == "AMBIGUOUS" for result in ambiguous)
    constraint_violations = sum(result.constraint_violations for result in constraints)
    constraint_violating_cases = sum(result.constraint_violations > 0 for result in constraints)
    false_groupings = sum(result.false_product_groupings for result in grouping)
    provenance_candidates = sum(result.provenance_candidates for result in results)
    provenance_complete = sum(result.provenance_complete_candidates for result in results)
    semantic_false = sum(result.semantic_only_false_resolutions for result in semantic_only)
    ndcg = round(sum(result.ndcg_at_10 for result in positives) / len(positives), 8)

    metrics = {
        "recall_at_50": _metric(recall_hits, recall_total),
        "ndcg_at_10": {"cases": len(positives), "mean": ndcg},
        "top3_relevance": _metric(top3_successes, len(positives)),
        "no_match_accuracy": _metric(no_match_successes, len(no_match)),
        "ambiguous_accuracy": _metric(ambiguous_successes, len(ambiguous)),
        "constraint_violation_rate_top10": {
            **_event_metric(constraint_violating_cases, len(constraints), "violating_cases"),
            "violations": constraint_violations,
        },
        "false_product_grouping_rate": _event_metric(false_groupings, len(grouping), "false_groupings"),
        "provenance_completeness": _metric(provenance_complete, provenance_candidates),
        "semantic_only_false_resolution_rate": _event_metric(semantic_false, len(semantic_only), "false_resolutions"),
    }
    gates = manifest["gates"]
    gate_results = {
        "recall_at_50_min": metrics["recall_at_50"]["rate"] >= gates["recall_at_50_min"],
        "ndcg_at_10_min": metrics["ndcg_at_10"]["mean"] >= gates["ndcg_at_10_min"],
        "top3_relevance_ci95_lower_min": metrics["top3_relevance"]["ci95_lower"] >= gates["top3_relevance_ci95_lower_min"],
        "no_match_accuracy_ci95_lower_min": metrics["no_match_accuracy"]["ci95_lower"] >= gates["no_match_accuracy_ci95_lower_min"],
        "ambiguous_accuracy_ci95_lower_min": metrics["ambiguous_accuracy"]["ci95_lower"] >= gates["ambiguous_accuracy_ci95_lower_min"],
        "constraint_violations_max": constraint_violations <= gates["constraint_violations_max"],
        "false_product_groupings_max": false_groupings <= gates["false_product_groupings_max"],
        "provenance_completeness_min": metrics["provenance_completeness"]["rate"] >= gates["provenance_completeness_min"],
        "semantic_only_false_resolutions_max": semantic_false <= gates["semantic_only_false_resolutions_max"],
    }
    blocking_failures = constraint_violations + false_groupings + semantic_false
    gate_results["blocking_failures_max"] = blocking_failures <= gates["blocking_failures_max"]
    support = manifest["minimum_statistical_support"]
    support_results = {
        "positive_cases": len(positives) >= support["positive_cases"],
        "no_match_cases": len(no_match) >= support["no_match_cases"],
        "ambiguous_cases": len(ambiguous) >= support["ambiguous_cases"],
        "constraint_cases": len(constraints) >= support["constraint_cases"],
        "grouping_cases": len(grouping) >= support["grouping_cases"],
        "semantic_only_cases": len(semantic_only) >= support["semantic_only_cases"],
    }
    qualified = all(gate_results.values()) and all(support_results.values())
    safety_qualified = (
        constraint_violations == 0
        and false_groupings == 0
        and semantic_false == 0
        and metrics["provenance_completeness"]["rate"] == 1.0
        and metrics["no_match_accuracy"]["ci95_lower"] >= gates["no_match_accuracy_ci95_lower_min"]
    )
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_version": manifest["benchmark_version"],
        "limitation": LIMITATION,
        "quality_status": "DETERMINISTIC_ORACLE_WITHOUT_EXTERNAL_HUMAN_GROUND_TRUTH",
        "adapter_version": (
            ORACLE_VERSION
            if adapter == "oracle"
            else (
                LEGACY_VERSION
                if adapter == "legacy_offer_first"
                else (
                    "hybrid-lexical-pgtrgm/v1"
                    if adapter == "lexical"
                    else (
                        "hybrid-expand-only/v1"
                        if adapter == "expanded"
                        else "hybrid-rrf-product-first/v1"
                    )
                )
            )
        ),
        "generator": generator,
        "verticals": list(VERTICALS),
        "locales": list(LOCALES),
        "scenarios": list(SCENARIOS),
        "summary": {
            "benchmark_status": "RATIFIED" if all(support_results.values()) else "INVALID_SUPPORT",
            "adapter_status": (
                "QUALIFIED"
                if qualified
                else ("SAFE_INCOMPLETE" if safety_qualified else "UNSAFE")
            ),
            "promotion_eligible": adapter != "oracle" and qualified,
            "cases": len(results),
            "mismatches": sum(not result.passed for result in results),
            "blocking_failures": blocking_failures,
            "gate_results": gate_results,
            "support_results": support_results,
        },
        "metrics": metrics,
        "by_vertical": {vertical: {"cases": sum(result.vertical == vertical for result in results), "mismatches": sum(result.vertical == vertical and not result.passed for result in results)} for vertical in VERTICALS},
        "by_locale": {locale: {"cases": sum(result.locale == locale for result in results), "mismatches": sum(result.locale == locale and not result.passed for result in results)} for locale in LOCALES},
        "by_scenario": {scenario: {"cases": sum(result.scenario == scenario for result in results), "mismatches": sum(result.scenario == scenario and not result.passed for result in results)} for scenario in SCENARIOS},
        "regressions": {
            "cases": sum(result.case_id.startswith("regression:") for result in results),
            "mismatches": [result.case_id for result in results if result.case_id.startswith("regression:") and not result.passed],
        },
        "mismatch_samples": json.loads(json.dumps(
            [asdict(result) for result in results if not result.passed][:25],
            ensure_ascii=False,
        )),
    }
    # ``asdict`` conserve les tuples. Le JSON standard les accepte, mais le
    # validateur canonique exige volontairement les seuls types JSON natifs.
    corpus = json.loads(json.dumps([asdict(case) for case in cases], ensure_ascii=False))
    report["corpus_sha256"] = "sha256:" + hashlib.sha256(canonical_json(corpus).encode("utf-8")).hexdigest()
    report["regressions_sha256"] = "sha256:" + hashlib.sha256(canonical_json(regressions).encode("utf-8")).hexdigest()
    report["evaluation_id"] = "sha256:" + hashlib.sha256(canonical_json({"manifest": manifest, "report": report}).encode("utf-8")).hexdigest()
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark Hybrid Retrieval FILON")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    parser.add_argument(
        "--adapter",
        choices=("oracle", "legacy_offer_first", "lexical", "expanded", "fused"),
        default="oracle",
    )
    parser.add_argument("--require-promotion", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = build_report(args.manifest, adapter=args.adapter)
    except HybridRetrievalBenchmarkError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}))
        return 2
    payload = canonical_json(report) + "\n"
    if args.output:
        atomic_write_text(args.output, payload)
        print(canonical_json({"evaluation_id": report["evaluation_id"], "summary": report["summary"], "metrics": report["metrics"]}))
    else:
        print(payload, end="")
    return int(args.require_promotion and not report["summary"]["promotion_eligible"])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
