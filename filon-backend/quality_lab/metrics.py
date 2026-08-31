"""Métriques pures du Quality Lab, sans accès aux données de production."""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from numbers import Number
from typing import Any

from .integrity import LANGUAGES, SCENARIO_TYPES, VERTICALS


_MISSING = object()
_CI95_ALPHA = 0.05
_ECE_BOOTSTRAP_RESAMPLES = 2_000


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _wilson(successes: int, total: int, z: float = 1.96) -> list[float] | None:
    """Intervalle de Wilson à 95 %, plus stable qu'un intervalle normal."""
    if total == 0:
        return None
    p = successes / total
    z2 = z * z
    denominator = 1 + z2 / total
    centre = (p + z2 / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def _bounded_mean_ci95(values: Sequence[float]) -> list[float] | None:
    """Borne empirique de Bernstein pour une moyenne de scores dans [0, 1].

    Recall et NDCG sont des scores par requête, pas des Bernoulli : Wilson ne
    s'applique donc pas. Cette borne bidirectionnelle reste déterministe,
    indépendante de l'ordre des cas et plus prudente que l'erreur standard
    normale lorsque l'échantillon est petit. Un cas unique ne prouve rien.
    """

    if not values:
        return None
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("bounded mean confidence interval requires values in [0, 1]")
    if len(values) == 1:
        return [0.0, 1.0]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    # Union des deux queues à 2,5 % chacune.
    log_term = math.log(4.0 / _CI95_ALPHA)
    radius = math.sqrt(2.0 * variance * log_term / len(values)) + (
        7.0 * log_term / (3.0 * (len(values) - 1))
    )
    return [max(0.0, mean - radius), min(1.0, mean + radius)]


def _percentile(sorted_values: Sequence[float], quantile: float) -> float:
    position = (len(sorted_values) - 1) * quantile
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    fraction = position - lower_index
    return (
        sorted_values[lower_index] * (1.0 - fraction)
        + sorted_values[upper_index] * fraction
    )


def _ece(rows: Sequence[tuple[float, int]], bins: int) -> float:
    counts = [0] * bins
    confidence_sums = [0.0] * bins
    correct_sums = [0] * bins
    for confidence, correct in rows:
        bucket = min(int(confidence * bins), bins - 1)
        counts[bucket] += 1
        confidence_sums[bucket] += confidence
        correct_sums[bucket] += correct
    total = len(rows)
    value = sum(
        count
        / total
        * abs(correct_sums[index] / count - confidence_sums[index] / count)
        for index, count in enumerate(counts)
        if count
    )
    return 0.0 if abs(value) <= 1e-15 else min(1.0, max(0.0, value))


def _ece_bootstrap_ci95(
    rows: Sequence[tuple[float, int]], bins: int
) -> list[float] | None:
    """Bootstrap percentile déterministe du fonctionnel ECE à bins fixes.

    Le tri canonique rend l'intervalle invariant à l'ordre du JSONL. Le seed
    fixe rend un même run strictement rejouable ; il ne change ni le gold ni les
    prédictions et ne sert qu'au rééchantillonnage statistique.
    """

    if not rows:
        return None
    ordered = sorted(rows)
    point = _ece(ordered, bins)
    if len(ordered) == 1:
        return [0.0, 1.0]
    generator = random.Random(0xF110)
    estimates = sorted(
        _ece(generator.choices(ordered, k=len(ordered)), bins)
        for _ in range(_ECE_BOOTSTRAP_RESAMPLES)
    )
    lower = min(point, _percentile(estimates, _CI95_ALPHA / 2.0))
    upper = max(point, _percentile(estimates, 1.0 - _CI95_ALPHA / 2.0))
    return [max(0.0, lower), min(1.0, upper)]


def _iter_cases(
    cases: Iterable[Mapping[str, Any]], metric: str
) -> Iterable[tuple[int, Mapping[str, Any]]]:
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise TypeError(f"{metric}: case {index} must be a mapping")
        yield index, case


def _required(case: Mapping[str, Any], field: str, *, metric: str, index: int) -> Any:
    if field not in case:
        raise ValueError(f"{metric}: case {index} is missing required field {field!r}")
    return case[field]


def _positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value <= 0:
        raise ValueError(f"{field} must be greater than zero")
    return value


def _non_negative_int(value: Any, *, field: str, index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"decision: case {index} field {field!r} must be an integer")
    if value < 0:
        raise ValueError(f"decision: case {index} field {field!r} must be non-negative")
    return value


def _product_ids(value: Any, *, field: str, index: int) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(
            f"retrieval: case {index} field {field!r} must be a sequence of strings"
        )
    ids = list(value)
    if any(not isinstance(item, str) for item in ids):
        raise TypeError(
            f"retrieval: case {index} field {field!r} must contain only strings"
        )
    if len(ids) != len(set(ids)):
        raise ValueError(
            f"retrieval: case {index} field {field!r} must not contain duplicates"
        )
    return ids


def _exact_value(expected: Any, predicted: Any) -> bool:
    """Compare récursivement des valeurs JSON sans assimiler ``True`` à ``1``."""
    if isinstance(expected, Mapping) or isinstance(predicted, Mapping):
        if not isinstance(expected, Mapping) or not isinstance(predicted, Mapping):
            return False
        expected_keys = set(expected)
        predicted_keys = set(predicted)
        if (
            any(not isinstance(key, str) for key in expected_keys | predicted_keys)
            or expected_keys != predicted_keys
        ):
            return False
        return all(_exact_value(expected[key], predicted[key]) for key in expected_keys)
    if isinstance(expected, list) or isinstance(predicted, list):
        if not isinstance(expected, list) or not isinstance(predicted, list):
            return False
        return len(expected) == len(predicted) and all(
            _exact_value(expected_item, predicted_item)
            for expected_item, predicted_item in zip(expected, predicted, strict=True)
        )
    if (
        isinstance(expected, Number)
        and isinstance(predicted, Number)
        and not isinstance(expected, bool)
        and not isinstance(predicted, bool)
    ):
        return expected == predicted
    return type(expected) is type(predicted) and expected == predicted


def exact_json_value(expected: Any, predicted: Any) -> bool:
    """Égalité JSON structurée, avec nombres unifiés mais booléens distincts."""

    return _exact_value(expected, predicted)


def taxonomy_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Mesure séparément catégorie, sous-catégorie et rôle produit."""

    fields = ("category", "subcategory", "product_role")
    correct = {field: 0 for field in fields}
    total = 0
    for index, case in _iter_cases(cases, "taxonomy"):
        expected = _required(case, "expected", metric="taxonomy", index=index)
        predicted = _required(case, "predicted", metric="taxonomy", index=index)
        if not isinstance(expected, Mapping) or not isinstance(predicted, Mapping):
            raise TypeError(
                f"taxonomy: case {index} expected and predicted must be mappings"
            )
        for field in fields:
            expected_value = _required(
                expected, field, metric="taxonomy expected", index=index
            )
            predicted_value = _required(
                predicted, field, metric="taxonomy predicted", index=index
            )
            if not isinstance(expected_value, str) or not expected_value:
                raise TypeError(
                    f"taxonomy: case {index} expected {field} must be a non-empty string"
                )
            if not isinstance(predicted_value, str) or not predicted_value:
                raise TypeError(
                    f"taxonomy: case {index} predicted {field} must be a non-empty string"
                )
            correct[field] += int(expected_value == predicted_value)
        total += 1
    return {
        "evaluated": total,
        **{
            f"{field}_correct": correct[field]
            for field in fields
        },
        **{
            f"{field}_accuracy": _ratio(correct[field], total)
            for field in fields
        },
        **{
            f"{field}_accuracy_ci95": _wilson(correct[field], total)
            for field in fields
        },
    }


def offer_truth_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Mesure l'égalité exacte des quatre vérités locales d'une offre.

    Les montants sont comparés comme objets ``amount_minor/currency`` afin de
    ne jamais introduire de tolérance flottante implicite. ``null`` représente
    explicitement une valeur inconnue et reste donc mesurable fail-closed.
    """

    fields = ("price", "stock", "shipping", "affiliate_link")
    correct = {field: 0 for field in fields}
    total = 0
    for index, case in _iter_cases(cases, "offer truth"):
        expected = _required(case, "expected", metric="offer truth", index=index)
        predicted = _required(case, "predicted", metric="offer truth", index=index)
        if not isinstance(expected, Mapping) or not isinstance(predicted, Mapping):
            raise TypeError(
                f"offer truth: case {index} expected and predicted must be mappings"
            )
        for field in fields:
            expected_value = _required(
                expected, field, metric="offer truth expected", index=index
            )
            predicted_value = _required(
                predicted, field, metric="offer truth predicted", index=index
            )
            correct[field] += int(_exact_value(expected_value, predicted_value))
        total += 1
    return {
        "evaluated": total,
        **{
            f"{field}_correct": correct[field]
            for field in fields
        },
        **{
            f"{field}_accuracy": _ratio(correct[field], total)
            for field in fields
        },
        **{
            f"{field}_accuracy_ci95": _wilson(correct[field], total)
            for field in fields
        },
    }


def strata_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compte les supports obligatoires de scénario, langue et verticale."""

    scenarios: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    verticals: Counter[str] = Counter()
    total = 0
    for index, case in _iter_cases(cases, "strata"):
        scenario = _required(case, "scenario_type", metric="strata", index=index)
        language = _required(case, "language", metric="strata", index=index)
        vertical = _required(case, "vertical", metric="strata", index=index)
        if scenario not in SCENARIO_TYPES:
            raise ValueError(f"strata: case {index} has unsupported scenario_type")
        if language not in LANGUAGES:
            raise ValueError(f"strata: case {index} has unsupported language")
        if vertical not in VERTICALS:
            raise ValueError(f"strata: case {index} has unsupported vertical")
        scenarios[scenario] += 1
        languages[language] += 1
        verticals[vertical] += 1
        total += 1
    return {
        "evaluated": total,
        "scenario_counts": {name: scenarios[name] for name in SCENARIO_TYPES},
        "language_counts": {name: languages[name] for name in LANGUAGES},
        "vertical_counts": {name: verticals[name] for name in VERTICALS},
    }


def entity_resolution_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Mesure les erreurs asymétriques sur des relations ``same/different``.

    Un gold ambigu reste non mesurable. En revanche, une prédiction ambiguë,
    absente ou explicitement abstentionniste sur un gold déterminé est comptée
    comme une erreur. Ce contrat fail-closed empêche un système qui s'abstient
    partout d'afficher artificiellement un taux de faux merge nul.
    """
    false_merges = false_splits = negatives = positives = excluded = abstained = 0
    variant_correct = variant_total = variant_excluded = variant_not_applicable = 0
    for index, case in _iter_cases(cases, "entity resolution"):
        actual = case.get("actual")
        predicted = case.get("predicted")
        if actual == "ambiguous":
            excluded += 1
        else:
            if actual not in ("same", "different"):
                raise ValueError(
                    "entity resolution: case "
                    f"{index} field 'actual' has unsupported value {actual!r}"
                )
            if predicted not in ("same", "different", "ambiguous", "abstain", None):
                raise ValueError(
                    "entity resolution: case "
                    f"{index} field 'predicted' has unsupported value {predicted!r}"
                )
            is_abstention = predicted in ("ambiguous", "abstain", None)
            abstained += int(is_abstention)
            if actual == "different":
                negatives += 1
                false_merges += int(predicted != "different")
            else:
                positives += 1
                false_splits += int(predicted != "same")

        actual_variant = case.get("actual_variant", _MISSING)
        predicted_variant = case.get("predicted_variant", _MISSING)
        if actual_variant is _MISSING and predicted_variant is _MISSING:
            continue
        if actual_variant is _MISSING or predicted_variant is _MISSING:
            raise ValueError(
                "entity resolution: actual_variant and predicted_variant must be "
                "provided together"
            )
        if actual_variant not in ("same", "different", "not_applicable", "ambiguous"):
            raise ValueError(
                "entity resolution: case "
                f"{index} field 'actual_variant' has unsupported value "
                f"{actual_variant!r}"
            )
        if (
            (actual == "different" and actual_variant != "not_applicable")
            or (actual == "same" and actual_variant == "not_applicable")
            or (actual == "ambiguous" and actual_variant != "ambiguous")
        ):
            raise ValueError(
                "entity resolution: case "
                f"{index} has inconsistent product and variant gold relations"
            )
        if predicted_variant not in (
            "same",
            "different",
            "not_applicable",
            "ambiguous",
            "abstain",
            None,
        ):
            raise ValueError(
                "entity resolution: case "
                f"{index} field 'predicted_variant' has unsupported value "
                f"{predicted_variant!r}"
            )
        if actual_variant == "ambiguous":
            variant_excluded += 1
        elif actual_variant == "not_applicable":
            variant_not_applicable += 1
        else:
            variant_total += 1
            variant_correct += int(predicted_variant == actual_variant)
    entity_correct = positives + negatives - false_merges - false_splits
    return {
        "evaluated": positives + negatives,
        "entity_match_correct": entity_correct,
        "entity_match_accuracy": _ratio(entity_correct, positives + negatives),
        "entity_match_accuracy_ci95": _wilson(
            entity_correct, positives + negatives
        ),
        "excluded_ambiguous": excluded,
        "abstained_predictions": abstained,
        "false_merges": false_merges,
        "different_pairs": negatives,
        "false_merge_rate": _ratio(false_merges, negatives),
        "false_merge_ci95": _wilson(false_merges, negatives),
        "false_splits": false_splits,
        "same_pairs": positives,
        "false_split_rate": _ratio(false_splits, positives),
        "false_split_ci95": _wilson(false_splits, positives),
        "variant_pairs": variant_total,
        "variant_excluded_ambiguous": variant_excluded,
        "variant_excluded_not_applicable": variant_not_applicable,
        "variant_relation_correct": variant_correct,
        "variant_relation_accuracy": _ratio(variant_correct, variant_total),
        "variant_relation_accuracy_ci95": _wilson(variant_correct, variant_total),
    }


def attachment_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Mesure l'attachement uniquement pour les offres gold éligibles.

    L'absence historique de ``eligibility`` reste acceptée si un identifiant
    gold non nul est fourni. Une éligibilité explicite, elle, est autoritaire.
    """
    correct = total = 0
    offers = eligibility_correct = noneligible_offers = false_eligible = 0
    for index, case in _iter_cases(cases, "offer attachment"):
        eligibility = case.get("eligibility", _MISSING)
        if eligibility is not _MISSING and eligibility not in (
            "eligible",
            "quarantine",
            "reject",
        ):
            raise ValueError(
                "offer attachment: case "
                f"{index} field 'eligibility' has unsupported value {eligibility!r}"
            )
        expected = _required(
            case, "expected_variant_id", metric="offer attachment", index=index
        )
        if expected is not None and not isinstance(expected, str):
            raise TypeError(
                "offer attachment: case "
                f"{index} field 'expected_variant_id' must be a string or None"
            )
        predicted = _required(
            case, "predicted_variant_id", metric="offer attachment", index=index
        )
        if predicted is not None and not isinstance(predicted, str):
            raise TypeError(
                "offer attachment: case "
                f"{index} field 'predicted_variant_id' must be a string or None"
            )
        predicted_eligibility = case.get("predicted_eligibility", "eligible")
        if predicted_eligibility not in ("eligible", "quarantine", "reject"):
            raise ValueError(
                "offer attachment: case "
                f"{index} field 'predicted_eligibility' has unsupported value "
                f"{predicted_eligibility!r}"
            )
        if eligibility is _MISSING:
            if expected is None:
                continue
            eligibility = "eligible"
        if eligibility == "eligible" and expected is None:
            raise ValueError(
                "offer attachment: case "
                f"{index} is eligible but has no expected_variant_id"
            )
        if eligibility != "eligible" and expected is not None:
            raise ValueError(
                "offer attachment: case "
                f"{index} is non-eligible but has an expected_variant_id"
            )

        offers += 1
        eligibility_correct += int(predicted_eligibility == eligibility)
        if eligibility != "eligible":
            noneligible_offers += 1
            false_eligible += int(predicted_eligibility == "eligible")
            continue

        total += 1
        correct += int(expected == predicted and predicted_eligibility == "eligible")
    return {
        "evaluated": total,
        "correct": correct,
        "accuracy": _ratio(correct, total),
        "accuracy_ci95": _wilson(correct, total),
        "offers": offers,
        "eligibility_correct": eligibility_correct,
        "eligibility_accuracy": _ratio(eligibility_correct, offers),
        "eligibility_accuracy_ci95": _wilson(eligibility_correct, offers),
        "noneligible_offers": noneligible_offers,
        "false_eligible_offers": false_eligible if noneligible_offers else None,
    }


def variant_resolution_metrics(
    cases: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Mesure l'égalité exacte entre la variante gold et la variante prédite."""
    exact_matches = total = 0
    for index, case in _iter_cases(cases, "variant resolution"):
        expected = _required(
            case, "expected_variant", metric="variant resolution", index=index
        )
        predicted = _required(
            case, "predicted_variant", metric="variant resolution", index=index
        )
        if not isinstance(expected, Mapping) or not isinstance(predicted, Mapping):
            raise TypeError(
                "variant resolution: case "
                f"{index} expected_variant and predicted_variant must be mappings"
            )
        for field, value in (
            ("expected_variant", expected),
            ("predicted_variant", predicted),
        ):
            resolution = value.get("resolution")
            variant_key = value.get("variant_key")
            if resolution not in ("resolved", "ambiguous", "insufficient_evidence"):
                raise ValueError(
                    f"variant resolution: case {index} {field} has invalid resolution"
                )
            if resolution == "resolved":
                if not isinstance(variant_key, str) or not variant_key:
                    raise ValueError(
                        f"variant resolution: case {index} resolved {field} requires variant_key"
                    )
            elif variant_key is not None:
                raise ValueError(
                    f"variant resolution: case {index} non-resolved {field} forbids variant_key"
                )
        total += 1
        exact_matches += int(_exact_value(expected, predicted))

    accuracy = _ratio(exact_matches, total)
    return {
        "evaluated": total,
        "exact_matches": exact_matches,
        "exact_match_accuracy": accuracy,
        "exact_match_ci95": _wilson(exact_matches, total),
    }


def _dcg(relevant: set[str], ranked: Sequence[str], k: int) -> float:
    return sum(
        1.0 / math.log2(index + 2)
        for index, item in enumerate(ranked[:k])
        if item in relevant
    )


def retrieval_metrics(
    cases: Iterable[Mapping[str, Any]], *, recall_k: int = 50, ndcg_k: int = 10
) -> dict[str, Any]:
    recall_k = _positive_int(recall_k, field="recall_k")
    ndcg_k = _positive_int(ndcg_k, field="ndcg_k")
    recalls: list[float] = []
    recalls_at_10: list[float] = []
    ndcgs: list[float] = []
    precisions: dict[int, list[float]] = {1: [], 3: [], 5: []}
    top_3_relevance_hits = 0
    constraint_violations_at_10 = 0
    total_queries = resolution_correct = 0
    no_match_queries = no_match_correct = no_match_false_positive_queries = 0
    ambiguous_queries = ambiguous_correct = 0
    exact_product_queries = exact_product_top1_correct = 0
    for index, case in _iter_cases(cases, "retrieval"):
        actual_resolution = _required(
            case, "actual_resolution", metric="retrieval", index=index
        )
        predicted_resolution = _required(
            case, "predicted_resolution", metric="retrieval", index=index
        )
        allowed_resolutions = {"matched", "no_match", "ambiguous"}
        if actual_resolution not in allowed_resolutions:
            raise ValueError(
                f"retrieval: case {index} field 'actual_resolution' has "
                f"unsupported value {actual_resolution!r}"
            )
        if predicted_resolution not in allowed_resolutions:
            raise ValueError(
                f"retrieval: case {index} field 'predicted_resolution' has "
                f"unsupported value {predicted_resolution!r}"
            )
        relevant_ids = _product_ids(
            _required(case, "relevant_product_ids", metric="retrieval", index=index),
            field="relevant_product_ids",
            index=index,
        )
        exact_product_ids = _product_ids(
            _required(case, "exact_product_ids", metric="retrieval", index=index),
            field="exact_product_ids",
            index=index,
        )
        if len(relevant_ids) > 50:
            raise ValueError(
                f"retrieval: case {index} has more than 50 relevant_product_ids"
            )
        retrieved = _product_ids(
            _required(case, "retrieved_product_ids", metric="retrieval", index=index),
            field="retrieved_product_ids",
            index=index,
        )
        violating = _product_ids(
            _required(
                case,
                "constraint_violating_product_ids",
                metric="retrieval",
                index=index,
            ),
            field="constraint_violating_product_ids",
            index=index,
        )
        relevant = set(relevant_ids)
        if (actual_resolution == "matched") != bool(relevant_ids):
            raise ValueError(
                f"retrieval: case {index} actual resolution contradicts relevant products"
            )
        if (predicted_resolution == "matched") != bool(retrieved):
            raise ValueError(
                f"retrieval: case {index} predicted resolution contradicts retrieved products"
            )
        overlap = relevant.intersection(violating)
        if overlap:
            raise ValueError(
                f"retrieval: case {index} relevant and constraint-violating "
                "product IDs must be disjoint"
            )
        total_queries += 1
        resolution_correct += int(predicted_resolution == actual_resolution)
        constraint_violations_at_10 += len(set(violating).intersection(retrieved[:10]))
        scenario_type = _required(
            case, "scenario_type", metric="retrieval", index=index
        )
        if scenario_type not in SCENARIO_TYPES:
            raise ValueError(
                f"retrieval: case {index} has unsupported scenario_type"
            )
        exact_products = set(exact_product_ids)
        if scenario_type == "exact_product" and actual_resolution == "matched":
            if not exact_products:
                raise ValueError(
                    f"retrieval: case {index} matched exact_product requires "
                    "exact_product_ids"
                )
            if not exact_products.issubset(relevant):
                raise ValueError(
                    f"retrieval: case {index} exact_product_ids must be a subset "
                    "of relevant_product_ids"
                )
        elif exact_products:
            raise ValueError(
                f"retrieval: case {index} exact_product_ids must be empty outside "
                "matched exact_product retrieval"
            )
        if actual_resolution == "no_match":
            no_match_queries += 1
            no_match_correct += int(predicted_resolution == "no_match")
            no_match_false_positive_queries += int(bool(retrieved))
            continue
        if actual_resolution == "ambiguous":
            ambiguous_queries += 1
            ambiguous_correct += int(predicted_resolution == "ambiguous")
            continue
        if scenario_type == "exact_product":
            exact_product_queries += 1
            exact_product_top1_correct += int(
                predicted_resolution == "matched"
                and bool(retrieved)
                and retrieved[0] in exact_products
            )
        top_3_relevance_hits += int(bool(relevant.intersection(retrieved[:3])))
        recalls.append(len(relevant.intersection(retrieved[:recall_k])) / len(relevant))
        recalls_at_10.append(len(relevant.intersection(retrieved[:10])) / len(relevant))
        for precision_k, values in precisions.items():
            values.append(
                len(relevant.intersection(retrieved[:precision_k])) / precision_k
            )
        ideal = sum(
            1.0 / math.log2(index + 2) for index in range(min(ndcg_k, len(relevant)))
        )
        ndcg = _dcg(relevant, retrieved, ndcg_k) / ideal
        ndcgs.append(min(1.0, max(0.0, ndcg)))

    mean_recall = sum(recalls) / len(recalls) if recalls else None
    mean_recall_at_10 = (
        sum(recalls_at_10) / len(recalls_at_10) if recalls_at_10 else None
    )
    mean_ndcg = sum(ndcgs) / len(ndcgs) if ndcgs else None
    return {
        "total_queries": total_queries,
        "queries": len(recalls),
        "answerable_queries": len(recalls),
        "resolution_correct": resolution_correct,
        "resolution_accuracy": _ratio(resolution_correct, total_queries),
        "resolution_accuracy_ci95": _wilson(resolution_correct, total_queries),
        "no_match_queries": no_match_queries,
        "no_match_correct": no_match_correct,
        "no_match_accuracy": _ratio(no_match_correct, no_match_queries),
        "no_match_accuracy_ci95": _wilson(no_match_correct, no_match_queries),
        "no_match_false_positive_queries": (
            no_match_false_positive_queries if no_match_queries else None
        ),
        "absurd_result_rate": _ratio(
            no_match_false_positive_queries,
            no_match_queries,
        ),
        "absurd_result_rate_ci95": _wilson(
            no_match_false_positive_queries,
            no_match_queries,
        ),
        "ambiguous_queries": ambiguous_queries,
        "ambiguous_correct": ambiguous_correct,
        "ambiguous_accuracy": _ratio(ambiguous_correct, ambiguous_queries),
        "ambiguous_accuracy_ci95": _wilson(ambiguous_correct, ambiguous_queries),
        "exact_product_queries": exact_product_queries,
        "exact_product_top1_correct": exact_product_top1_correct,
        "exact_product_match_accuracy": _ratio(
            exact_product_top1_correct,
            exact_product_queries,
        ),
        "exact_product_match_accuracy_ci95": _wilson(
            exact_product_top1_correct,
            exact_product_queries,
        ),
        "top_3_relevance_hits": top_3_relevance_hits,
        "top_3_relevance": _ratio(top_3_relevance_hits, len(recalls)),
        "top_3_relevance_ci95": _wilson(top_3_relevance_hits, len(recalls)),
        **{
            f"precision_at_{precision_k}": (
                sum(values) / len(values) if values else None
            )
            for precision_k, values in precisions.items()
        },
        **{
            f"precision_at_{precision_k}_ci95": _bounded_mean_ci95(values)
            for precision_k, values in precisions.items()
        },
        "recall_at_10": mean_recall_at_10,
        f"recall_at_{recall_k}": mean_recall,
        f"recall_at_{recall_k}_ci95": _bounded_mean_ci95(recalls),
        f"ndcg_at_{ndcg_k}": (
            min(1.0, max(0.0, mean_ndcg)) if mean_ndcg is not None else None
        ),
        f"ndcg_at_{ndcg_k}_ci95": _bounded_mean_ci95(ndcgs),
        "constraint_violations_at_10": (
            constraint_violations_at_10 if total_queries else None
        ),
    }


def decision_safety_metrics(cases: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    total = violations = unsupported = sourced = coverage_total = 0
    correct_answer = correct_abstention = wrong_answer = wrong_abstention = 0
    matrix_complete = True
    for index, case in _iter_cases(cases, "decision"):
        case_violations = _non_negative_int(
            _required(case, "constraint_violations", metric="decision", index=index),
            field="constraint_violations",
            index=index,
        )
        case_unsupported = _non_negative_int(
            _required(case, "unsupported_claims", metric="decision", index=index),
            field="unsupported_claims",
            index=index,
        )
        explanation_sourced = _required(
            case, "explanation_sourced", metric="decision", index=index
        )
        if type(explanation_sourced) is not bool:
            raise TypeError(
                "decision: case "
                f"{index} field 'explanation_sourced' must be a boolean"
            )
        has_coverage = "coverage_eligible" in case
        explicit_coverage = case.get("coverage_eligible", _MISSING)
        if has_coverage and type(explicit_coverage) is not bool:
            raise TypeError(
                "decision: case "
                f"{index} field 'coverage_eligible' must be a boolean"
            )
        has_outcome = "outcome" in case
        outcome = case.get("outcome", _MISSING)
        if has_outcome:
            if outcome not in ("recommend", "wait", "abstain"):
                raise ValueError(
                    "decision: case "
                    f"{index} field 'outcome' has unsupported value {outcome!r}"
                )
            outcome_is_answer = outcome != "abstain"
            if has_coverage and outcome_is_answer != explicit_coverage:
                raise ValueError(
                    "decision: case "
                    f"{index} fields 'outcome' and 'coverage_eligible' are inconsistent"
                )
            coverage_eligible = outcome_is_answer
        elif has_coverage:
            coverage_eligible = explicit_coverage
            outcome_is_answer = explicit_coverage
        else:
            coverage_eligible = True
            outcome_is_answer = True
        has_correct = "correct" in case
        gold_correct = case.get("correct", _MISSING)
        if has_correct and type(gold_correct) is not bool:
            raise TypeError(
                f"decision: case {index} field 'correct' must be a boolean"
            )
        case_matrix_measurable = has_correct and (has_outcome or has_coverage)
        matrix_complete = matrix_complete and case_matrix_measurable
        total += 1
        violations += case_violations
        unsupported += case_unsupported
        if case_matrix_measurable:
            if gold_correct and outcome_is_answer:
                correct_answer += 1
            elif gold_correct:
                correct_abstention += 1
            elif outcome_is_answer:
                wrong_answer += 1
            else:
                wrong_abstention += 1
        if coverage_eligible:
            coverage_total += 1
            sourced += int(explanation_sourced)
    outcome_matrix_total = (
        correct_answer + correct_abstention + wrong_answer + wrong_abstention
    )
    matrix_measurable = total > 0 and matrix_complete
    if (
        matrix_measurable and outcome_matrix_total != total
    ):  # pragma: no cover - invariant interne
        raise AssertionError("decision outcome matrix must cover every decision")
    return {
        "decisions": total,
        "constraint_violations": violations if total else None,
        "unsupported_claims": unsupported if total else None,
        "coverage_eligible_decisions": coverage_total,
        "sourced_explanations": sourced,
        "sourced_explanation_coverage": _ratio(sourced, coverage_total),
        "sourced_explanation_coverage_ci95": _wilson(sourced, coverage_total),
        "correct_answer": correct_answer if matrix_measurable else None,
        "correct_abstention": correct_abstention if matrix_measurable else None,
        "wrong_answer": wrong_answer if matrix_measurable else None,
        "wrong_abstention": wrong_abstention if matrix_measurable else None,
        "outcome_matrix_total": outcome_matrix_total if matrix_measurable else None,
    }


def calibration_metrics(
    cases: Iterable[Mapping[str, Any]], *, bins: int = 10
) -> dict[str, Any]:
    bins = _positive_int(bins, field="bins")
    rows: list[tuple[float, int]] = []
    for index, case in _iter_cases(cases, "calibration"):
        confidence = case.get("confidence")
        correct = case.get("correct")
        numeric_confidence: float | None = None
        if confidence is not None and (
            isinstance(confidence, bool) or not isinstance(confidence, Number)
        ):
            raise TypeError(
                "calibration: case " f"{index} field 'confidence' must be a real number"
            )
        if confidence is not None:
            try:
                numeric_confidence = float(confidence)
            except (OverflowError, TypeError, ValueError) as error:
                raise TypeError(
                    "calibration: case "
                    f"{index} field 'confidence' must be a real number"
                ) from error
            if (
                not math.isfinite(numeric_confidence)
                or not 0.0 <= numeric_confidence <= 1.0
            ):
                raise ValueError(
                    "calibration: case "
                    f"{index} field 'confidence' must be finite and between 0 and 1"
                )
        if correct is not None and type(correct) is not bool:
            raise TypeError(
                f"calibration: case {index} field 'correct' must be a boolean"
            )
        if confidence is None or correct is None:
            continue
        assert numeric_confidence is not None
        rows.append((numeric_confidence, int(correct)))

    if not rows:
        return {
            "evaluated": 0,
            "ece": None,
            "ece_ci95": None,
            "brier_score": None,
            "bins": bins,
        }
    ece = _ece(rows, bins)
    return {
        "evaluated": len(rows),
        "ece": min(1.0, max(0.0, ece)),
        "ece_ci95": _ece_bootstrap_ci95(rows, bins),
        "brier_score": sum(
            (confidence - correct) ** 2 for confidence, correct in rows
        )
        / len(rows),
        "bins": bins,
    }
