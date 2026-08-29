from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from quality_lab import runner as runner_module
from quality_lab.integrity import (
    DATASETS,
    RECORD_VERSION,
    case_fingerprint,
    split_for_group,
)
from quality_lab.runner import (
    AdapterPrediction,
    AwinOfferTruthAdapter,
    CatalogRetrievalAdapter,
    EanEntityResolutionAdapter,
    GeneralDecisionAdapter,
    QualityAdapter,
    QualityRunnerError,
    TaxonomyProductRoleAdapter,
    builtin_adapters,
    write_run,
)


ROOT = Path(__file__).resolve().parents[2]
PREDICTION_SCHEMA = ROOT / "quality" / "schemas" / "prediction.schema.json"
MANIFEST_SHA256 = "sha256:" + "a" * 64


def _group_for(split: str) -> str:
    for index in range(1000):
        group_id = f"runner-{split}-{index}"
        if split_for_group(group_id) == split:
            return group_id
    raise AssertionError(f"no group found for {split}")


def _record(
    dataset: str,
    input_value: dict[str, Any],
    *,
    split: str = "train",
    case_id: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "record_version": RECORD_VERSION,
        "dataset": dataset,
        "case_id": case_id or f"runner-{dataset}",
        "group_id": _group_for(split),
        "split": split,
        "input": input_value,
        # Le contenu du gold est volontairement reconnaissable : le test spy
        # prouve qu'il ne franchit pas la frontiere de l'adaptateur.
        "gold": {"secret_gold_marker": "must-never-reach-engine"},
    }
    record["case_fingerprint"] = case_fingerprint(record)
    return record


def _roster(**records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {dataset: records.get(dataset, []) for dataset in DATASETS}


def _decision_input() -> dict[str, Any]:
    return {
        "request": {
            "query": "ordinateur portable sous 500 €",
            "locale": "fr",
            "reference_time": "2026-08-29T10:00:00Z",
            "offers": [
                {
                    "candidate_id": "candidate-1",
                    "offer_id": 1,
                    "catalog_product_id": 101,
                    "name": "Ordinateur portable étudiant",
                    "brand": "Test",
                    "filon_category": "Informatique",
                    "filon_subcategory": "Ordinateurs portables",
                    "offer_kind": "physical_product",
                    "price": 450.0,
                    "currency": "EUR",
                    "availability": "in_stock",
                    "merchant_id": 7,
                    "merchant_name": "Marchand test",
                    "merchant_region": "BE",
                    "observed_at": "2026-08-29T09:00:00Z",
                    "evidence_refs": ["price-1", "stock-1"],
                }
            ],
        },
        "candidate_ids": ["candidate-1"],
        "evidence": [
            {"evidence_ref": "price-1", "source_ref": "offer:1:price"},
            {"evidence_ref": "stock-1", "source_ref": "offer:1:stock"},
        ],
    }


class _SpyTaxonomyAdapter(QualityAdapter):
    dataset = "taxonomy"
    engine_id = "tests.synthetic-taxonomy-engine"
    engine_version = "v1"

    def __init__(self, *, engine_version: str = "v1") -> None:
        self.engine_version = engine_version
        self.inputs: list[Mapping[str, Any]] = []

    async def predict(self, engine_input: Mapping[str, Any]) -> AdapterPrediction:
        self.inputs.append(engine_input)
        return AdapterPrediction(
            prediction={
                "category": "Téléphonie",
                "subcategory": "Smartphones",
                "product_role": "primary_product",
            }
        )


@pytest.mark.asyncio
async def test_runner_is_blind_reproducible_and_hashes_all_artifacts(tmp_path: Path):
    case = _record(
        "taxonomy",
        {
            "strata": {
                "scenario_type": "no_match",
                "language": "fr",
                "vertical": "smartphones",
            },
            "observation": {
                "name": "iPhone 15 128GB",
                "merchant_category": "Smartphones",
            },
        },
    )
    adapter = _SpyTaxonomyAdapter()
    first = await write_run(
        _roster(taxonomy=[case]),
        output_dir=tmp_path / "first",
        system_version="git:test-system",
        gold_manifest_sha256=MANIFEST_SHA256,
        prediction_schema_path=PREDICTION_SCHEMA,
        adapters={"taxonomy": adapter},
        selected_splits=frozenset({"train"}),
    )
    second = await write_run(
        _roster(taxonomy=[case]),
        output_dir=tmp_path / "second",
        system_version="git:test-system",
        gold_manifest_sha256=MANIFEST_SHA256,
        prediction_schema_path=PREDICTION_SCHEMA,
        adapters={"taxonomy": adapter},
        selected_splits=frozenset({"train"}),
    )
    changed_engine = _SpyTaxonomyAdapter(engine_version="v2")
    third = await write_run(
        _roster(taxonomy=[case]),
        output_dir=tmp_path / "third",
        system_version="git:test-system",
        gold_manifest_sha256=MANIFEST_SHA256,
        prediction_schema_path=PREDICTION_SCHEMA,
        adapters={"taxonomy": changed_engine},
        selected_splits=frozenset({"train"}),
    )

    assert adapter.inputs == [
        {"observation": case["input"]["observation"]},
        {"observation": case["input"]["observation"]},
    ]
    assert first.run_id == second.run_id
    assert third.run_id != first.run_id
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()
    assert set(first.dataset_paths) == set(DATASETS)
    assert json.loads(first.manifest_path.read_text(encoding="utf-8"))["adapters"] == {
        "taxonomy": {
            "engine_id": "tests.synthetic-taxonomy-engine",
            "engine_version": "v1",
        }
    }
    assert json.loads(third.manifest_path.read_text(encoding="utf-8"))["adapters"] == {
        "taxonomy": {
            "engine_id": "tests.synthetic-taxonomy-engine",
            "engine_version": "v2",
        }
    }
    for dataset in DATASETS:
        assert (
            first.dataset_paths[dataset].read_bytes()
            == second.dataset_paths[dataset].read_bytes()
        )
    assert not list(tmp_path.glob(".*.publish.lock"))
    assert not list(tmp_path.glob(".*.staging-*"))


@pytest.mark.asyncio
async def test_runner_publication_failure_leaves_no_partial_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    case = _record(
        "taxonomy",
        {
            "strata": {
                "scenario_type": "exact_product",
                "language": "fr",
                "vertical": "smartphones",
            },
            "observation": {
                "name": "iPhone 15 128GB",
                "merchant_category": "Smartphones",
            },
        },
    )
    real_atomic_write = runner_module.atomic_write_text

    def fail_during_second_dataset(path: str | Path, text: str) -> None:
        if Path(path).name == "entity_resolution.jsonl":
            raise OSError("injected publication failure")
        real_atomic_write(path, text)

    monkeypatch.setattr(
        runner_module,
        "atomic_write_text",
        fail_during_second_dataset,
    )
    destination = tmp_path / "transactional-run"
    with pytest.raises(
        QualityRunnerError,
        match="unable to publish run artifacts: injected publication failure",
    ):
        await write_run(
            _roster(taxonomy=[case]),
            output_dir=destination,
            system_version="git:test-system",
            gold_manifest_sha256=MANIFEST_SHA256,
            prediction_schema_path=PREDICTION_SCHEMA,
            adapters={"taxonomy": _SpyTaxonomyAdapter()},
            selected_splits=frozenset({"train"}),
        )

    assert not destination.exists()
    assert not list(tmp_path.glob(".transactional-run.publish.lock"))
    assert not list(tmp_path.glob(".transactional-run.staging-*"))


@pytest.mark.asyncio
async def test_runner_atomic_publish_never_replaces_racing_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    case = _record(
        "taxonomy",
        {
            "strata": {
                "scenario_type": "exact_product",
                "language": "fr",
                "vertical": "smartphones",
            },
            "observation": {
                "name": "iPhone 15 128GB",
                "merchant_category": "Smartphones",
            },
        },
    )
    destination = tmp_path / "racing-run"
    real_publish = runner_module._rename_directory_noreplace

    def publish_after_racer(source: Path, target: Path) -> None:
        target.mkdir()
        (target / "competitor.txt").write_text("preserve me", encoding="utf-8")
        real_publish(source, target)

    monkeypatch.setattr(
        runner_module,
        "_rename_directory_noreplace",
        publish_after_racer,
    )

    with pytest.raises(QualityRunnerError, match="unable to publish run artifacts"):
        await write_run(
            _roster(taxonomy=[case]),
            output_dir=destination,
            system_version="git:test-system",
            gold_manifest_sha256=MANIFEST_SHA256,
            prediction_schema_path=PREDICTION_SCHEMA,
            adapters={"taxonomy": _SpyTaxonomyAdapter()},
            selected_splits=frozenset({"train"}),
        )

    assert (destination / "competitor.txt").read_text(encoding="utf-8") == "preserve me"
    assert not list(tmp_path.glob(".racing-run.publish.lock"))
    assert not list(tmp_path.glob(".racing-run.staging-*"))


@pytest.mark.asyncio
async def test_runner_refuses_nonempty_dataset_without_real_adapter(tmp_path: Path):
    case = _record(
        "variant_resolution",
        {
            "strata": {
                "scenario_type": "variant_sensitive",
                "language": "fr",
                "vertical": "smartphones",
            },
            "observation": {"name": "iPhone 15 128GB noir"},
        },
    )
    destination = tmp_path / "refused"
    with pytest.raises(
        QualityRunnerError,
        match="no real application adapter.*variant_resolution",
    ):
        await write_run(
            _roster(variant_resolution=[case]),
            output_dir=destination,
            system_version="git:test-system",
            gold_manifest_sha256=MANIFEST_SHA256,
            prediction_schema_path=PREDICTION_SCHEMA,
            adapters={"taxonomy": _SpyTaxonomyAdapter()},
            selected_splits=frozenset({"train"}),
        )
    assert not destination.exists()


@pytest.mark.asyncio
async def test_taxonomy_adapter_calls_current_taxonomy_and_product_role_engines():
    result = await TaxonomyProductRoleAdapter().predict(
        {
            "observation": {
                "name": "Apple iPhone 15 128GB",
                "merchant_category": "Téléphones > Smartphones",
                "brand": "Apple",
                "merchant_name": "Marchand test",
            }
        }
    )
    assert result.prediction == {
        "category": "Téléphonie",
        "subcategory": "Smartphones",
        "product_role": "primary_product",
    }
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_ean_entity_adapter_abstains_on_variant_and_missing_identity():
    adapter = EanEntityResolutionAdapter()
    same = await adapter.predict(
        {
            "left": {"identifiers": {"ean": "4006381333931"}},
            "right": {"identifiers": {"gtin": "4006381333931"}},
        }
    )
    different = await adapter.predict(
        {
            "left": {"identifiers": {"ean": "4006381333931"}},
            "right": {"identifiers": {"ean": "5901234123457"}},
        }
    )
    ambiguous = await adapter.predict(
        {"left": {"identifiers": {}}, "right": {"identifiers": {}}}
    )
    assert same.prediction == {
        "product_relation": "same",
        "variant_relation": "ambiguous",
    }
    assert different.prediction == {
        "product_relation": "different",
        "variant_relation": "not_applicable",
    }
    assert ambiguous.prediction == {
        "product_relation": "ambiguous",
        "variant_relation": "ambiguous",
    }


@pytest.mark.asyncio
async def test_awin_offer_truth_adapter_projects_only_observed_facts():
    result = await AwinOfferTruthAdapter().predict(
        {
            "offer": {
                "source_type": "awin_feed",
                "feed_id": "feed-1",
                "merchant_id": 42,
                "merchant_name": "Marchand",
                "observed_at": "2026-08-29T10:00:00Z",
                "row": {
                    "aw_product_id": "source-1",
                    "product_name": "Apple iPhone 15",
                    "search_price": "699,95",
                    "currency": "eur",
                    "in_stock": "yes",
                    "aw_deep_link": "https://merchant.example/product/1",
                },
            }
        }
    )
    assert result.prediction == {
        "price": {"amount_minor": 69995, "currency": "EUR"},
        "stock": "in_stock",
        "shipping": None,
        "affiliate_link": "https://merchant.example/product/1",
    }


@pytest.mark.asyncio
async def test_catalog_retrieval_adapter_uses_real_result_namespace_and_deduplicates():
    calls: list[tuple[str, float | None, str | None]] = []

    async def search(
        query: str,
        budget: float | None,
        *,
        country: str | None,
    ) -> list[dict[str, Any]]:
        calls.append((query, budget, country))
        return [
            {"product_ean": "4006381333931", "offer_id": 10},
            {"product_ean": "4006381333931", "offer_id": 11},
            {"product_ean": None, "offer_id": 12},
        ]

    result = await CatalogRetrievalAdapter(search=search).predict(
        {
            "locale": "nl",
            "query": "iPhone 15",
            "hard_constraints": {"budget_eur": 700, "country": "BE"},
        }
    )
    assert calls == [("iPhone 15", 700.0, "BE")]
    assert result.prediction == {
        "resolution": "matched",
        "retrieved_product_ids": ["ean:4006381333931", "offer:12"],
    }


@pytest.mark.asyncio
async def test_catalog_retrieval_refuses_unenforced_constraint():
    async def unused_search(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        raise AssertionError("search must not run")

    adapter = CatalogRetrievalAdapter(search=unused_search)
    with pytest.raises(QualityRunnerError, match="cannot enforce constraints: color"):
        await adapter.predict(
            {
                "locale": "fr",
                "query": "casque rouge",
                "hard_constraints": {"color": "red"},
            }
        )


@pytest.mark.asyncio
async def test_general_decision_adapter_recommends_only_sourced_candidates():
    result = await GeneralDecisionAdapter().predict(_decision_input())

    assert result.prediction == {
        "outcome": "recommend",
        "claims": [
            {
                "claim": "selected_candidate:candidate-1",
                "evidence_refs": ["price-1", "stock-1"],
            }
        ],
    }
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_general_decision_adapter_uses_the_fixed_reference_time():
    engine_input = _decision_input()
    first = await GeneralDecisionAdapter().predict(engine_input)
    second = await GeneralDecisionAdapter().predict(deepcopy(engine_input))

    assert first == second

    stale = deepcopy(engine_input)
    stale["request"]["reference_time"] = "2026-09-02T10:00:00Z"
    refused = await GeneralDecisionAdapter().predict(stale)
    assert refused.prediction == {"outcome": "abstain", "claims": []}


@pytest.mark.asyncio
async def test_general_decision_adapter_refuses_candidate_or_evidence_drift():
    mismatched = _decision_input()
    mismatched["candidate_ids"] = ["candidate-2"]
    with pytest.raises(QualityRunnerError, match="canonical order"):
        await GeneralDecisionAdapter().predict(mismatched)

    unknown_evidence = _decision_input()
    unknown_evidence["request"]["offers"][0]["evidence_refs"] = ["unknown"]
    with pytest.raises(QualityRunnerError, match="absent from inventory"):
        await GeneralDecisionAdapter().predict(unknown_evidence)


def test_builtin_adapters_include_real_decision_but_not_graph_placeholders():
    adapters = builtin_adapters()

    assert set(adapters) == {
        "taxonomy",
        "entity_resolution",
        "offer_truth",
        "retrieval",
        "decision",
    }
    assert "variant_resolution" not in adapters
    assert "offer_attachment" not in adapters


@pytest.mark.asyncio
async def test_runner_writes_a_real_decision_prediction(tmp_path: Path):
    decision_input = _decision_input()
    decision_input["strata"] = {
        "scenario_type": "constraint_heavy",
        "language": "fr",
        "vertical": "laptops",
    }
    case = _record("decision", decision_input)

    artifacts = await write_run(
        _roster(decision=[case]),
        output_dir=tmp_path / "decision-run",
        system_version="git:test-decision",
        gold_manifest_sha256=MANIFEST_SHA256,
        prediction_schema_path=PREDICTION_SCHEMA,
        adapters={"decision": GeneralDecisionAdapter()},
        selected_splits=frozenset({"train"}),
    )

    output = json.loads(
        artifacts.dataset_paths["decision"].read_text(encoding="utf-8")
    )
    assert output["prediction"] == {
        "outcome": "recommend",
        "claims": [
            {
                "claim": "selected_candidate:candidate-1",
                "evidence_refs": ["price-1", "stock-1"],
            }
        ],
    }
    assert output["confidence"] == 0.0
