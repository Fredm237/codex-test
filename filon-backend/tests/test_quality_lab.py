from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from quality_lab import evaluate as evaluate_module
from quality_lab.annotation_workflow import (
    adjudicate_disagreements,
    main as annotation_main,
    merge_completed_packs,
    prepare_adjudication_pack,
    prepare_pack,
)
from quality_lab.integrity import (
    DATASETS,
    LANGUAGES,
    SCHEMA_FILES,
    SCENARIO_TYPES,
    VERTICALS,
    canonical_json,
    case_fingerprint,
    completed_pack_fingerprint,
    disagreement_fingerprint,
    input_fingerprint,
    label_invariant_errors,
    pack_fingerprint,
    read_jsonl,
    require_identifier,
    schema_fingerprint,
    split_for_group,
    strict_loads,
)
from quality_lab.readiness import (
    _annotation_integrity_errors,
    _bootstrap_report,
    build_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
QUALITY = ROOT / "quality"
MANIFEST = QUALITY / "manifest.json"


def _group_for_split(prefix: str, target: str) -> str:
    for index in range(10_000):
        value = f"{prefix}-{index}"
        if split_for_group(value) == target:
            return value
    raise AssertionError(f"no deterministic {target} group found")


def _test_group(prefix: str) -> str:
    return _group_for_split(prefix, "test")


def _strata(index: int) -> dict[str, str]:
    return {
        "scenario_type": SCENARIO_TYPES[index % len(SCENARIO_TYPES)],
        "language": LANGUAGES[index % len(LANGUAGES)],
        "vertical": VERTICALS[index % len(VERTICALS)],
    }


def _case_and_label(dataset: str) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = f"{dataset}-case"
    stratum_index = {
        "taxonomy": 7,
        "entity_resolution": 1,
        "variant_resolution": 3,
        "offer_attachment": 4,
        "offer_truth": 6,
        "retrieval": 0,
        "decision": 10,
    }[dataset]
    common = {
        "case_id": case_id,
        "group_id": _test_group(dataset),
        "strata": _strata(stratum_index),
    }
    if dataset == "taxonomy":
        return (
            {**common, "observation": {"name": "Téléphone modèle 1"}},
            {
                "category": "electronics",
                "subcategory": "smartphones",
                "product_role": "primary_product",
            },
        )
    if dataset == "entity_resolution":
        return (
            {
                **common,
                "left": {"source_ref": "left", "name": "Produit noir"},
                "right": {"source_ref": "right", "name": "Produit black"},
            },
            {"product_relation": "same", "variant_relation": "same"},
        )
    if dataset == "variant_resolution":
        return (
            {**common, "observation": {"name": "Chaussure noire 42"}},
            {
                "expected_variant": {
                    "variant_key": "shoe-black-42",
                    "attributes": {"colour": "black", "size": "42"},
                    "resolution": "resolved",
                }
            },
        )
    if dataset == "offer_attachment":
        return (
            {**common, "offer": {"merchant": "merchant-a", "sku": "sku-1"}},
            {"expected_variant_id": "variant-1", "eligibility": "eligible"},
        )
    if dataset == "offer_truth":
        return (
            {**common, "offer": {"source_ref": "merchant:item-1"}},
            {
                "price": {"amount_minor": 99900, "currency": "EUR"},
                "stock": "in_stock",
                "shipping": {"amount_minor": 0, "currency": "EUR"},
                "affiliate_link": "https://merchant.example/item-1",
            },
        )
    if dataset == "retrieval":
        return (
            {
                **common,
                "locale": common["strata"]["language"],
                "query": "chaussures noires",
                "hard_constraints": {"colour": "black"},
            },
            {
                "resolution": "matched",
                "relevant_product_ids": ["product-1"],
                "exact_product_ids": ["product-1"],
                "constraint_violating_product_ids": [],
            },
        )
    return (
        {
            **common,
            "request": {
                "query": "ordinateur portable sous 500 €",
                "locale": common["strata"]["language"],
                "reference_time": "2026-08-29T10:00:00Z",
                "offers": [
                    {
                        "candidate_id": "product-1",
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
                        "evidence_refs": ["evidence-1"],
                    }
                ],
            },
            "candidate_ids": ["product-1"],
            "evidence": [
                {"evidence_ref": "evidence-1", "source_ref": "product-1"}
            ],
        },
        {
            "acceptable_outcomes": ["recommend"],
            "forbidden_claims": [],
            "claim_evidence": [
                {"claim": "available", "evidence_refs": ["evidence-1"]}
            ],
        },
    )


def _completed_pack(
    dataset: str,
    case: dict[str, Any],
    label: dict[str, Any],
    annotator: str,
) -> list[dict[str, Any]]:
    pack = prepare_pack(dataset, [case], annotator_id=annotator)
    pack[0]["annotation"].update(label=deepcopy(label), confidence="certain")
    return pack


def _final_record_from(
    dataset: str,
    case: dict[str, Any],
    label: dict[str, Any],
) -> dict[str, Any]:
    first = _completed_pack(dataset, case, label, f"{dataset}-human-a")
    second = _completed_pack(dataset, case, label, f"{dataset}-human-b")
    result = merge_completed_packs(dataset, first + second)
    assert result.errors == ()
    assert result.disagreements == ()
    return result.accepted[0]


def _final_record(dataset: str) -> dict[str, Any]:
    return _final_record_from(dataset, *_case_and_label(dataset))


def _alternate_final_record(
    dataset: str,
    suffix: str,
    label: dict[str, Any],
) -> dict[str, Any]:
    case, _default_label = _case_and_label(dataset)
    case["case_id"] = f"{dataset}-{suffix}"
    case["group_id"] = _test_group(f"{dataset}-{suffix}")
    stratum_index = {
        ("entity_resolution", "different"): 2,
        ("offer_attachment", "noneligible"): 5,
        ("retrieval", "no-match"): 9,
        ("retrieval", "ambiguous"): 8,
    }.get((dataset, suffix))
    if stratum_index is not None:
        case["strata"] = _strata(stratum_index)
    if dataset == "entity_resolution":
        case["left"]["source_ref"] = f"left-{suffix}"
        case["right"]["source_ref"] = f"right-{suffix}"
    elif dataset == "offer_attachment":
        case["offer"]["sku"] = f"sku-{suffix}"
    elif dataset == "retrieval":
        case["query"] = f"requête {suffix}"
        case["locale"] = case["strata"]["language"]
    return _final_record_from(dataset, case, label)


def _retrieval_scenario_record(stratum_index: int) -> dict[str, Any]:
    case, _label = _case_and_label("retrieval")
    scenario = SCENARIO_TYPES[stratum_index]
    case["case_id"] = f"retrieval-{scenario}"
    case["group_id"] = _test_group(f"retrieval-{scenario}")
    case["strata"] = _strata(stratum_index)
    case["locale"] = case["strata"]["language"]
    case["query"] = f"requête {scenario}"
    label = {
        "resolution": "matched",
        "relevant_product_ids": [f"product-{scenario}"],
        "exact_product_ids": [],
        "constraint_violating_product_ids": [],
    }
    return _final_record_from("retrieval", case, label)


def _support_complete_records() -> dict[str, list[dict[str, Any]]]:
    records = {dataset: [_final_record(dataset)] for dataset in DATASETS}
    records["entity_resolution"].append(
        _alternate_final_record(
            "entity_resolution",
            "different",
            {
                "product_relation": "different",
                "variant_relation": "not_applicable",
            },
        )
    )
    records["offer_attachment"].append(
        _alternate_final_record(
            "offer_attachment",
            "noneligible",
            {"expected_variant_id": None, "eligibility": "reject"},
        )
    )
    records["retrieval"].extend(
        [
            *[
                _retrieval_scenario_record(index)
                for index in range(1, 8)
            ],
            _alternate_final_record(
                "retrieval",
                "no-match",
                {
                    "resolution": "no_match",
                    "relevant_product_ids": [],
                    "exact_product_ids": [],
                    "constraint_violating_product_ids": [],
                },
            ),
            _alternate_final_record(
                "retrieval",
                "ambiguous",
                {
                    "resolution": "ambiguous",
                    "relevant_product_ids": [],
                    "exact_product_ids": [],
                    "constraint_violating_product_ids": [],
                },
            ),
        ]
    )
    return records


def _write_relaxed_test_quality(
    tmp_path: Path,
    records: dict[str, dict[str, Any] | list[dict[str, Any]]],
) -> Path:
    quality = tmp_path / "quality"
    (quality / "datasets").mkdir(parents=True)
    (quality / "schemas").mkdir()
    for schema_file in (*SCHEMA_FILES.values(), "manifest.schema.json"):
        (quality / "schemas" / schema_file).write_text(
            (QUALITY / "schemas" / schema_file).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    manifest_schema_path = quality / "schemas" / "manifest.schema.json"
    manifest_schema = json.loads(manifest_schema_path.read_text(encoding="utf-8"))
    for dataset in DATASETS:
        config = manifest_schema["$defs"][f"{dataset}_config"]["properties"]
        config["minimum_cases"] = {"const": 1}
        config["minimum_test_cases"] = {"const": 1}
    manifest_schema_path.write_text(
        json.dumps(manifest_schema, ensure_ascii=False), encoding="utf-8"
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["measurement_support"] = {
        name: 1 for name in manifest["measurement_support"]
    }
    for dataset in DATASETS:
        manifest["datasets"][dataset]["minimum_cases"] = 1
        manifest["datasets"][dataset]["minimum_test_cases"] = 1
        manifest["datasets"][dataset]["schema_fingerprint"] = schema_fingerprint(
            dataset,
            quality,
        )
        path = quality / manifest["datasets"][dataset]["path"]
        dataset_records = records[dataset]
        if isinstance(dataset_records, dict):
            dataset_records = [dataset_records]
        path.write_text(
            "".join(canonical_json(record) + "\n" for record in dataset_records),
            encoding="utf-8",
        )
    manifest["bootstrap"]["path"] = "datasets/missing-bootstrap.json"
    manifest_path = quality / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    return manifest_path


def test_quality_lab_reste_rouge_sans_annotations_reelles():
    report = build_readiness_report(MANIFEST)
    assert report["integrity_valid"] is True
    assert report["ready"] is False
    assert report["status"] == "not_ready"
    assert set(report["datasets"]) == set(DATASETS)
    assert all(dataset["cases"] == 0 for dataset in report["datasets"].values())
    assert all(dataset["minimum_test_cases"] > 0 for dataset in report["datasets"].values())
    assert report["bootstrap"]["cases"] == 14
    assert report["bootstrap"]["passed"] == report["bootstrap"]["assertions"]
    assert report["bootstrap"]["eligible_for_launch_gate"] is False


@pytest.mark.parametrize("strict, expected_exit", [(False, 0), (True, 1)])
def test_cli_distingue_sous_volume_valide_et_readiness_stricte(
    strict,
    expected_exit,
    monkeypatch,
    capsys,
):
    argv = [evaluate_module.__name__, "--manifest", str(MANIFEST)]
    if strict:
        argv.append("--strict")
    monkeypatch.setattr(sys, "argv", argv)

    assert evaluate_module.main() == expected_exit
    report = json.loads(capsys.readouterr().out)
    assert report["integrity_valid"] is True
    assert report["ready"] is False


def test_cli_strict_accepte_un_quality_lab_pret(tmp_path, monkeypatch, capsys):
    manifest_path = _write_relaxed_test_quality(
        tmp_path,
        _support_complete_records(),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            evaluate_module.__name__,
            "--manifest",
            str(manifest_path),
            "--strict",
        ],
    )

    assert evaluate_module.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["integrity_valid"] is True
    assert report["ready"] is True


@pytest.mark.parametrize("strict", [False, True])
def test_cli_refuse_un_manifeste_invalide_meme_sans_mode_strict(
    strict,
    tmp_path,
    monkeypatch,
    capsys,
):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    argv = [evaluate_module.__name__, "--manifest", str(manifest_path)]
    if strict:
        argv.append("--strict")
    monkeypatch.setattr(sys, "argv", argv)

    assert evaluate_module.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["integrity_valid"] is False
    assert report["status"] == "invalid_manifest"


def test_cli_non_strict_refuse_un_dataset_present_corrompu(
    tmp_path,
    monkeypatch,
    capsys,
):
    manifest_path = _write_relaxed_test_quality(
        tmp_path,
        _support_complete_records(),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_path = manifest_path.parent / manifest["datasets"]["retrieval"]["path"]
    dataset_path.write_text('{"case_id":', encoding="utf-8")
    output_path = tmp_path / "readiness.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            evaluate_module.__name__,
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
        ],
    )

    assert evaluate_module.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert json.loads(output_path.read_text(encoding="utf-8")) == report
    assert report["integrity_valid"] is False
    assert report["datasets"]["retrieval"]["integrity_valid"] is False


def test_cli_non_strict_refuse_un_bootstrap_present_invalide(
    tmp_path,
    monkeypatch,
    capsys,
):
    manifest_path = _write_relaxed_test_quality(
        tmp_path,
        _support_complete_records(),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bootstrap_path = manifest_path.parent / manifest["bootstrap"]["path"]
    bootstrap_path.write_text(
        '{"cases":[{"id":"empty-expected","expected_current":{}}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [evaluate_module.__name__, "--manifest", str(manifest_path)],
    )

    assert evaluate_module.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["integrity_valid"] is False
    assert report["bootstrap"]["error"] == "invalid bootstrap cases"


def test_cli_non_strict_refuse_une_regression_apres_statut_ready(
    tmp_path,
    monkeypatch,
    capsys,
):
    manifest_path = _write_relaxed_test_quality(
        tmp_path,
        _support_complete_records(),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "ready"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    missing_volume_path = (
        manifest_path.parent / manifest["datasets"]["retrieval"]["path"]
    )
    missing_volume_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [evaluate_module.__name__, "--manifest", str(manifest_path)],
    )

    assert evaluate_module.main() == 2
    report = json.loads(capsys.readouterr().out)
    assert report["integrity_valid"] is False
    assert report["ready"] is False
    assert report["datasets"]["retrieval"]["integrity_valid"] is True
    assert "computed status is authoritative" in report["manifest_status_warning"]


def test_manifest_vide_ou_incomplet_est_invalide_pas_ready(tmp_path):
    quality = tmp_path / "quality"
    (quality / "schemas").mkdir(parents=True)
    (quality / "schemas" / "manifest.schema.json").write_text(
        (QUALITY / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest_path = quality / "manifest.json"
    manifest_path.write_text('{"datasets":{}}', encoding="utf-8")

    report = build_readiness_report(manifest_path)

    assert report["ready"] is False
    assert report["integrity_valid"] is False
    assert report["status"] == "invalid_manifest"
    assert report["datasets"] == {}
    assert report["manifest_errors"]


def test_manifest_datasets_null_reste_un_report_invalide(tmp_path):
    quality = tmp_path / "quality"
    (quality / "schemas").mkdir(parents=True)
    (quality / "schemas" / "manifest.schema.json").write_text(
        (QUALITY / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest_path = quality / "manifest.json"
    manifest_path.write_text('{"datasets":null}', encoding="utf-8")

    report = build_readiness_report(manifest_path)

    assert report["ready"] is False
    assert report["integrity_valid"] is False
    assert report["status"] == "invalid_manifest"
    assert report["manifest_errors"]


def test_manifest_profond_invalide_reste_un_report_fail_closed(tmp_path):
    quality = tmp_path / "quality"
    (quality / "schemas").mkdir(parents=True)
    (quality / "schemas" / "manifest.schema.json").write_text(
        (QUALITY / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest_path = quality / "manifest.json"
    deep_value = "[" * 1_200 + "0" + "]" * 1_200
    manifest_path.write_text(
        '{"datasets":{},"extra":' + deep_value + "}",
        encoding="utf-8",
    )

    report = build_readiness_report(manifest_path)

    assert report["ready"] is False
    assert report["integrity_valid"] is False
    assert report["status"] == "invalid_manifest"
    assert report["manifest_fingerprint"] is None
    assert any(
        "manifest fingerprint unavailable" in error
        for error in report["manifest_errors"]
    )


@pytest.mark.parametrize(
    "payload, message",
    [
        ('{"case_id":"a","case_id":"b"}', "duplicate JSON key"),
        ('{"confidence":NaN}', "non-finite JSON number"),
        ('{"confidence":Infinity}', "non-finite JSON number"),
        ('{"confidence":1e9999}', "non-finite JSON number"),
    ],
)
def test_json_strict_refuse_les_ambiguities(payload, message):
    with pytest.raises(ValueError, match=message):
        strict_loads(payload)


def test_jsonl_preserve_les_separateurs_unicode_dans_une_chaine(tmp_path):
    record = {"text": "avant\u0085milieu\u2028suite\u2029après"}
    path = tmp_path / "unicode.jsonl"
    path.write_text(canonical_json(record) + "\n", encoding="utf-8")

    assert read_jsonl(path) == [record]


def test_json_canonique_convertit_profondeur_excessive_en_value_error_stable():
    value: Any = "leaf"
    for _ in range(2_000):
        value = [value]

    with pytest.raises(ValueError, match="cannot be encoded as canonical JSON"):
        canonical_json(value)


def test_readiness_annotation_profonde_echoue_sans_recursion_error():
    row = _final_record("variant_resolution")
    value: Any = "leaf"
    for _ in range(2_000):
        value = [value]
    row["annotations"][0]["label"]["expected_variant"]["attributes"][
        "deep"
    ] = value

    errors = _annotation_integrity_errors("variant_resolution", row)

    assert any("cannot be normalized" in error for error in errors)


def test_bootstrap_invalide_reste_fail_closed_sans_exception(tmp_path):
    path = tmp_path / "bootstrap.json"
    path.write_text(
        json.dumps(
            {
                "cases": [
                    "pas-un-objet",
                    {"name": "Produit", "expected_current": []},
                ]
            }
        ),
        encoding="utf-8",
    )

    report = _bootstrap_report(
        path,
        {"independent": True, "eligible_for_launch_gate": True},
    )

    assert report["eligible_for_launch_gate"] is False
    assert report["error"] == "invalid bootstrap cases"
    assert len(report["errors"]) == 2


@pytest.mark.parametrize(
    "expected_current",
    [
        {},
        {"category": []},
        {"unknown_target": "value"},
    ],
)
def test_bootstrap_refuse_attente_vide_mal_typee_ou_inconnue(
    expected_current,
    tmp_path,
):
    path = tmp_path / "bootstrap.json"
    path.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "bootstrap-case",
                        "name": "Produit",
                        "expected_current": expected_current,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = _bootstrap_report(
        path,
        {"independent": False, "eligible_for_launch_gate": False},
    )

    assert report["error"] == "invalid bootstrap cases"
    assert report["eligible_for_launch_gate"] is False


def test_split_vectors_stables_et_identifiants_stricts():
    assert split_for_group("g0") == "train"
    assert split_for_group("g1") == "dev"
    assert split_for_group("g2") == "test"
    with pytest.raises(ValueError, match="surrounding whitespace"):
        split_for_group(" g2")
    with pytest.raises(ValueError, match="NFC-normalized"):
        require_identifier("cafe\u0301", "group_id")


def test_pack_projette_une_allowlist_et_refuse_une_fuite_recursive():
    case, _ = _case_and_label("entity_resolution")
    case["source_metadata"] = {"model_output": "same"}
    pack = prepare_pack("entity_resolution", [case], annotator_id="human-a")
    assert set(pack[0]["input"]) == {"strata", "left", "right"}
    assert "source_metadata" not in pack[0]["input"]

    leaked = deepcopy(case)
    leaked["left"]["attributes"] = {"expected_answer": "same"}
    with pytest.raises(ValueError, match="reserved input field"):
        prepare_pack("entity_resolution", [leaked], annotator_id="human-a")

    engine_leak = deepcopy(case)
    engine_leak["left"]["attributes"] = {"engine_output": "same"}
    with pytest.raises(ValueError, match="engine_output"):
        prepare_pack("entity_resolution", [engine_leak], annotator_id="human-a")

    legitimate_engine = deepcopy(case)
    legitimate_engine["left"]["attributes"] = {
        "engine_type": "electric",
        "engine_power": "110 kW",
    }
    assert prepare_pack(
        "entity_resolution", [legitimate_engine], annotator_id="human-a"
    )

    for leaked_field in (
        "engine_decision",
        "engine_label",
        "engine_score",
        "engine_confidence",
        "engine_answer",
    ):
        semantic_leak = deepcopy(case)
        semantic_leak["left"]["attributes"] = {leaked_field: "same"}
        with pytest.raises(ValueError, match=leaked_field):
            prepare_pack(
                "entity_resolution", [semantic_leak], annotator_id="human-a"
            )


def test_prepare_et_merge_refusent_un_input_metier_incomplet_sans_exception():
    case, label = _case_and_label("entity_resolution")
    invalid_candidate = deepcopy(case)
    del invalid_candidate["left"]["source_ref"]
    with pytest.raises(ValueError, match="input candidat invalide"):
        prepare_pack("entity_resolution", [invalid_candidate], annotator_id="human-a")

    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    for pack in (first, second):
        task = pack[0]
        del task["input"]["left"]["source_ref"]
        task["input_fingerprint"] = input_fingerprint(
            "entity_resolution",
            task["case_id"],
            task["group_id"],
            task["split"],
            task["input"],
        )
        task["pack_fingerprint"] = pack_fingerprint(
            "entity_resolution",
            task["annotation"]["annotator_id"],
            task["schema_fingerprint"],
            [task["input_fingerprint"]],
        )

    result = merge_completed_packs("entity_resolution", first + second)

    assert result.accepted == ()
    assert any("input invalide" in error for error in result.errors)


def test_merge_est_atomique_et_refuse_split_ou_pack_altere():
    case, label = _case_and_label("entity_resolution")
    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    second[0]["split"] = "train"

    result = merge_completed_packs("entity_resolution", first + second)

    assert result.accepted == ()
    assert result.disagreements == ()
    assert any("split non canonique" in error for error in result.errors)


def test_merge_refuse_deux_generations_de_pack_incompletes():
    first_case, label = _case_and_label("entity_resolution")
    second_case = deepcopy(first_case)
    second_case["case_id"] = "entity-second"
    second_case["group_id"] = _test_group("entity-second")
    pack_a = prepare_pack(
        "entity_resolution", [first_case, second_case], annotator_id="human-a"
    )
    pack_b = prepare_pack(
        "entity_resolution", [first_case, second_case], annotator_id="human-b"
    )
    for task in pack_a + pack_b:
        task["annotation"].update(label=deepcopy(label), confidence="certain")

    result = merge_completed_packs("entity_resolution", pack_a + pack_b[:1])

    assert result.accepted == ()
    assert any("empreinte de pack invalide" in error for error in result.errors)
    assert any("mêmes case_id" in error for error in result.errors)


@pytest.mark.parametrize("dataset", DATASETS)
def test_accord_humain_produit_une_enveloppe_v03_valide(dataset):
    record = _final_record(dataset)
    schema = strict_loads(
        (QUALITY / "schemas" / SCHEMA_FILES[dataset]).read_text(encoding="utf-8")
    )
    assert list(Draft202012Validator(schema).iter_errors(record)) == []
    assert record["dataset"] == dataset
    assert record["schema_fingerprint"] == schema_fingerprint(dataset)
    assert record["case_fingerprint"] == case_fingerprint(record)
    assert len(record["annotations"]) == 2
    assert len(record["source_pack_fingerprints"]) == 2


def test_empreinte_pack_complete_engage_labels_et_remplace_les_ids_assignation():
    case, label = _case_and_label("entity_resolution")
    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    assignment_ids = {
        first[0]["pack_fingerprint"],
        second[0]["pack_fingerprint"],
    }
    original_digest = completed_pack_fingerprint(
        first[0]["pack_fingerprint"], first
    )
    altered = deepcopy(first)
    altered[0]["annotation"]["label"]["variant_relation"] = "different"

    assert completed_pack_fingerprint(
        altered[0]["pack_fingerprint"], altered
    ) != original_digest
    merged = merge_completed_packs("entity_resolution", first + second)
    assert merged.errors == ()
    source_ids = set(merged.accepted[0]["source_pack_fingerprints"])
    assert len(source_ids) == 2
    assert source_ids.isdisjoint(assignment_ids)


def test_retrieval_ordres_semantiques_differents_produisent_un_gold_canonique():
    case, _label = _case_and_label("retrieval")
    first_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-2", "product-1"],
        "exact_product_ids": ["product-2", "product-1"],
        "constraint_violating_product_ids": ["product-4", "product-3"],
    }
    second_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-1", "product-2"],
        "exact_product_ids": ["product-1", "product-2"],
        "constraint_violating_product_ids": ["product-3", "product-4"],
    }
    first = _completed_pack("retrieval", case, first_label, "human-a")
    second = _completed_pack("retrieval", case, second_label, "human-b")

    merged = merge_completed_packs("retrieval", first + second)

    assert merged.errors == ()
    assert merged.disagreements == ()
    assert merged.accepted[0]["gold"] == second_label
    assert all(
        annotation["label"] == second_label
        for annotation in merged.accepted[0]["annotations"]
    )


def test_decision_ordres_semantiques_differents_sont_normalises():
    case, _label = _case_and_label("decision")
    case["evidence"].append(
        {"evidence_ref": "evidence-2", "source_ref": "product-1"}
    )
    first_label = {
        "acceptable_outcomes": ["wait", "recommend"],
        "forbidden_claims": ["forbidden-z", "forbidden-a"],
        "claim_evidence": [
            {
                "claim": "claim-b",
                "evidence_refs": ["evidence-2", "evidence-1"],
            },
            {"claim": "claim-a", "evidence_refs": ["evidence-2"]},
        ],
    }
    second_label = {
        "acceptable_outcomes": ["recommend", "wait"],
        "forbidden_claims": ["forbidden-a", "forbidden-z"],
        "claim_evidence": [
            {"claim": "claim-a", "evidence_refs": ["evidence-2"]},
            {
                "claim": "claim-b",
                "evidence_refs": ["evidence-1", "evidence-2"],
            },
        ],
    }
    first = _completed_pack("decision", case, first_label, "human-a")
    second = _completed_pack("decision", case, second_label, "human-b")

    merged = merge_completed_packs("decision", first + second)

    assert merged.errors == ()
    assert merged.disagreements == ()
    assert merged.accepted[0]["gold"] == second_label
    assert all(
        annotation["label"] == second_label
        for annotation in merged.accepted[0]["annotations"]
    )


def test_variant_nombres_entiers_int_et_float_sont_un_meme_accord():
    case, label = _case_and_label("variant_resolution")
    first_label = deepcopy(label)
    first_label["expected_variant"]["attributes"]["quantity"] = 1
    second_label = deepcopy(label)
    second_label["expected_variant"]["attributes"]["quantity"] = 1.0
    first = _completed_pack("variant_resolution", case, first_label, "human-a")
    second = _completed_pack("variant_resolution", case, second_label, "human-b")

    merged = merge_completed_packs("variant_resolution", first + second)

    assert merged.errors == ()
    assert merged.disagreements == ()
    assert merged.accepted[0]["gold"]["expected_variant"]["attributes"][
        "quantity"
    ] == 1
    assert all(
        isinstance(
            annotation["label"]["expected_variant"]["attributes"]["quantity"],
            int,
        )
        for annotation in merged.accepted[0]["annotations"]
    )


@pytest.mark.parametrize(
    "dataset,label,message",
    [
        (
            "entity_resolution",
            {"product_relation": "different", "variant_relation": "different"},
            "different products require variant_relation not_applicable",
        ),
        (
            "variant_resolution",
            {
                "expected_variant": {
                    "variant_key": "variant-impossible",
                    "attributes": {},
                    "resolution": "ambiguous",
                }
            },
            "non-resolved variant requires null variant_key",
        ),
        (
            "retrieval",
            {
                "resolution": "matched",
                "relevant_product_ids": ["product-1"],
                "exact_product_ids": ["product-1"],
                "constraint_violating_product_ids": ["product-1"],
            },
            "must be disjoint",
        ),
        (
            "decision",
            {
                "acceptable_outcomes": ["recommend"],
                "forbidden_claims": ["claim-a"],
                "claim_evidence": [
                    {"claim": "claim-a", "evidence_refs": ["evidence-1"]}
                ],
            },
            "disjoint from forbidden_claims",
        ),
        (
            "decision",
            {
                "acceptable_outcomes": ["recommend"],
                "forbidden_claims": [],
                "claim_evidence": [
                    {"claim": "claim-a", "evidence_refs": ["unknown-evidence"]}
                ],
            },
            "unknown input evidence",
        ),
        (
            "decision",
            {
                "acceptable_outcomes": ["wait"],
                "forbidden_claims": [],
                "claim_evidence": [],
            },
            "non-abstain decision outcomes require non-empty claim_evidence",
        ),
    ],
)
def test_merge_refuse_les_labels_metier_incoherents(dataset, label, message):
    case, _valid_label = _case_and_label(dataset)
    first = _completed_pack(dataset, case, label, "human-a")
    second = _completed_pack(dataset, case, label, "human-b")

    merged = merge_completed_packs(dataset, first + second)

    assert merged.accepted == ()
    assert merged.disagreements == ()
    assert any(message in error for error in merged.errors)


def test_decision_refuse_les_claim_evidence_dupliques_par_nom():
    case, _valid_label = _case_and_label("decision")
    case["evidence"].append(
        {"evidence_ref": "evidence-2", "source_ref": "product-1"}
    )
    label = {
        "acceptable_outcomes": ["recommend"],
        "forbidden_claims": [],
        "claim_evidence": [
            {"claim": "claim-a", "evidence_refs": ["evidence-1"]},
            {"claim": "claim-a", "evidence_refs": ["evidence-2"]},
        ],
    }
    first = _completed_pack("decision", case, label, "human-a")
    second = _completed_pack("decision", case, label, "human-b")

    merged = merge_completed_packs("decision", first + second)

    assert any("claims must be unique" in error for error in merged.errors)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("locale", "locale must equal strata language"),
        ("candidate", "must match request offers in canonical order"),
        ("evidence", "reference unknown input evidence"),
        ("time", "reference_time must be an offset-aware ISO datetime"),
    ],
)
def test_decision_input_cross_invariants_are_fail_closed(mutation, message):
    case, label = _case_and_label("decision")
    if mutation == "locale":
        case["request"]["locale"] = (
            "en" if case["strata"]["language"] != "en" else "fr"
        )
    elif mutation == "candidate":
        case["candidate_ids"] = ["product-2"]
    elif mutation == "evidence":
        case["request"]["offers"][0]["evidence_refs"] = ["unknown-evidence"]
    else:
        case["request"]["reference_time"] = "2026-99-99T10:00:00+00:00"

    errors = label_invariant_errors("decision", label, case)

    assert any(message in error for error in errors)


def test_desaccord_exige_un_troisieme_humain_et_preserve_les_labels_initiaux():
    case, first_label = _case_and_label("entity_resolution")
    second_label = {
        "product_relation": "different",
        "variant_relation": "not_applicable",
    }
    first = _completed_pack("entity_resolution", case, first_label, "human-a")
    second = _completed_pack("entity_resolution", case, second_label, "human-b")
    merged = merge_completed_packs("entity_resolution", first + second)
    assert merged.accepted == ()
    assert len(merged.disagreements) == 1

    with pytest.raises(ValueError, match="troisième humain distinct"):
        prepare_adjudication_pack(
            "entity_resolution", merged.disagreements, adjudicator_id="human-a"
        )

    tasks = prepare_adjudication_pack(
        "entity_resolution", merged.disagreements, adjudicator_id="human-c"
    )
    assert "annotations" not in tasks[0]
    tasks[0]["adjudication"].update(
        label=deepcopy(first_label),
        confidence="probable",
        rationale="Sources et identifiants revérifiés indépendamment",
    )
    result = adjudicate_disagreements("entity_resolution", merged.disagreements, tasks)

    assert result.errors == ()
    assert len(result.accepted) == 1
    final = result.accepted[0]
    assert final["gold"] == first_label
    assert {canonical_json(item["label"]) for item in final["annotations"]} == {
        canonical_json(first_label),
        canonical_json(second_label),
    }
    assert final["adjudication"]["adjudicator_id"] == "human-c"
    assert final["case_fingerprint"] == case_fingerprint(final)


def test_adjudication_refuse_un_label_retrieval_metier_incoherent():
    case, first_label = _case_and_label("retrieval")
    second_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-2"],
        "exact_product_ids": ["product-2"],
        "constraint_violating_product_ids": [],
    }
    first = _completed_pack("retrieval", case, first_label, "human-a")
    second = _completed_pack("retrieval", case, second_label, "human-b")
    merged = merge_completed_packs("retrieval", first + second)
    tasks = prepare_adjudication_pack(
        "retrieval", merged.disagreements, adjudicator_id="human-c"
    )
    tasks[0]["adjudication"].update(
        label={
            "resolution": "matched",
            "relevant_product_ids": ["product-1"],
            "exact_product_ids": ["product-1"],
            "constraint_violating_product_ids": ["product-1"],
        },
        confidence="certain",
        rationale="Vérification humaine indépendante",
    )

    result = adjudicate_disagreements("retrieval", merged.disagreements, tasks)

    assert result.accepted == ()
    assert any("must be disjoint" in error for error in result.errors)


def test_merge_refuse_exact_product_ids_hors_ensemble_pertinent():
    case, _label = _case_and_label("retrieval")
    invalid = {
        "resolution": "matched",
        "relevant_product_ids": ["target"],
        "exact_product_ids": ["substitute"],
        "constraint_violating_product_ids": [],
    }
    first = _completed_pack("retrieval", case, invalid, "human-a")
    second = _completed_pack("retrieval", case, invalid, "human-b")

    merged = merge_completed_packs("retrieval", first + second)

    assert merged.accepted == ()
    assert any("subset of relevant_product_ids" in error for error in merged.errors)


@pytest.mark.parametrize(
    "mutation, message",
    [
        ("status", "status de désaccord invalide"),
        ("annotations", "exactement deux annotations initiales"),
        ("source_packs", "exactement deux source_pack_fingerprints"),
        ("fingerprint", "disagreement_fingerprint invalide"),
    ],
)
def test_prepare_et_adjudicate_refusent_toute_enveloppe_de_desaccord_alteree(
    mutation,
    message,
):
    case, first_label = _case_and_label("entity_resolution")
    second_label = {
        "product_relation": "different",
        "variant_relation": "not_applicable",
    }
    first = _completed_pack("entity_resolution", case, first_label, "human-a")
    second = _completed_pack("entity_resolution", case, second_label, "human-b")
    merged = merge_completed_packs("entity_resolution", first + second)
    original = merged.disagreements[0]
    tasks = prepare_adjudication_pack(
        "entity_resolution", [original], adjudicator_id="human-c"
    )
    malformed = deepcopy(original)
    if mutation == "status":
        malformed["status"] = "resolved"
    elif mutation == "annotations":
        malformed["annotations"] = []
    elif mutation == "source_packs":
        malformed["source_pack_fingerprints"] = malformed[
            "source_pack_fingerprints"
        ][:1]
    else:
        malformed["disagreement_fingerprint"] = "sha256:" + "0" * 64
    if mutation != "fingerprint":
        malformed["disagreement_fingerprint"] = disagreement_fingerprint(malformed)

    with pytest.raises(ValueError, match=message):
        prepare_adjudication_pack(
            "entity_resolution", [malformed], adjudicator_id="human-c"
        )

    result = adjudicate_disagreements("entity_resolution", [malformed], tasks)
    assert result.accepted == ()
    assert any(message in error for error in result.errors)


def test_adjudicate_refuse_un_desaccord_non_objet_sans_exception():
    result = adjudicate_disagreements("entity_resolution", [None], [])

    assert result.accepted == ()
    assert any("objet attendu" in error for error in result.errors)


@pytest.mark.parametrize("payload", ["", "{json-invalide"])
def test_cli_prepare_convertit_entree_invalide_en_exit_2_sans_traceback(
    tmp_path,
    monkeypatch,
    capsys,
    payload,
):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text(payload, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "prepare",
            "--dataset",
            "entity_resolution",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--annotator-id",
            "human-a",
        ],
    )

    assert annotation_main() == 2
    assert capsys.readouterr().out.startswith("erreur workflow:")
    assert not output_path.exists()


def test_cli_refuse_collision_casefold_de_chemins_encore_inexistants(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "Result.jsonl"
    output_path = tmp_path / "result.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "prepare",
            "--dataset",
            "entity_resolution",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--annotator-id",
            "human-a",
        ],
    )

    assert annotation_main() == 2
    assert not input_path.exists()
    assert not output_path.exists()


def test_cli_exit_1_est_reserve_au_merge_valide_avec_desaccord(
    tmp_path,
    monkeypatch,
):
    case, first_label = _case_and_label("entity_resolution")
    second_label = {
        "product_relation": "different",
        "variant_relation": "not_applicable",
    }
    first = _completed_pack("entity_resolution", case, first_label, "human-a")
    second = _completed_pack("entity_resolution", case, second_label, "human-b")
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    output_path = tmp_path / "output.jsonl"
    disagreement_path = tmp_path / "disagreements.jsonl"
    first_path.write_text(canonical_json(first[0]) + "\n", encoding="utf-8")
    second_path.write_text(canonical_json(second[0]) + "\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "merge",
            "--dataset",
            "entity_resolution",
            "--input",
            str(first_path),
            "--input",
            str(second_path),
            "--output",
            str(output_path),
            "--disagreements",
            str(disagreement_path),
        ],
    )

    assert annotation_main() == 1
    assert read_jsonl(output_path) == []
    assert len(read_jsonl(disagreement_path)) == 1


def test_cli_merge_necrit_rien_si_le_lot_est_invalide(tmp_path, monkeypatch):
    case, label = _case_and_label("entity_resolution")
    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    second[0]["split"] = "dev"
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    first_path.write_text(canonical_json(first[0]) + "\n", encoding="utf-8")
    second_path.write_text(canonical_json(second[0]) + "\n", encoding="utf-8")
    output = tmp_path / "output.jsonl"
    disagreements = tmp_path / "disagreements.jsonl"
    output.write_text("sentinel-output", encoding="utf-8")
    disagreements.write_text("sentinel-disagreements", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "merge",
            "--dataset",
            "entity_resolution",
            "--input",
            str(first_path),
            "--input",
            str(second_path),
            "--output",
            str(output),
            "--disagreements",
            str(disagreements),
        ],
    )

    assert annotation_main() == 2
    assert output.read_text(encoding="utf-8") == "sentinel-output"
    assert disagreements.read_text(encoding="utf-8") == "sentinel-disagreements"


def test_cli_merge_refuse_deux_sorties_identiques_sans_ecraser(tmp_path, monkeypatch):
    case, label = _case_and_label("entity_resolution")
    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    first_path.write_text(canonical_json(first[0]) + "\n", encoding="utf-8")
    second_path.write_text(canonical_json(second[0]) + "\n", encoding="utf-8")
    shared_output = tmp_path / "shared.jsonl"
    shared_output.write_text("sentinel", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "merge",
            "--dataset",
            "entity_resolution",
            "--input",
            str(first_path),
            "--input",
            str(second_path),
            "--output",
            str(shared_output),
            "--disagreements",
            str(shared_output),
        ],
    )

    assert annotation_main() == 2
    assert shared_output.read_text(encoding="utf-8") == "sentinel"


def test_cli_merge_restaure_les_deux_sorties_si_le_second_replace_echoue(
    tmp_path,
    monkeypatch,
):
    case, label = _case_and_label("entity_resolution")
    first = _completed_pack("entity_resolution", case, label, "human-a")
    second = _completed_pack("entity_resolution", case, label, "human-b")
    first_path = tmp_path / "first.jsonl"
    second_path = tmp_path / "second.jsonl"
    first_path.write_text(canonical_json(first[0]) + "\n", encoding="utf-8")
    second_path.write_text(canonical_json(second[0]) + "\n", encoding="utf-8")
    output = tmp_path / "output.jsonl"
    disagreements = tmp_path / "disagreements.jsonl"
    output.write_text("sentinel-output", encoding="utf-8")
    disagreements.write_text("sentinel-disagreements", encoding="utf-8")

    import quality_lab.annotation_workflow as workflow

    real_replace = workflow.os.replace
    failure_injected = False

    def fail_second_publication(source, destination):
        nonlocal failure_injected
        if (
            not failure_injected
            and Path(destination) == disagreements
            and str(source).endswith(".tmp")
        ):
            failure_injected = True
            raise OSError("second replace intentionally failed")
        return real_replace(source, destination)

    monkeypatch.setattr(workflow.os, "replace", fail_second_publication)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "annotation_workflow",
            "merge",
            "--dataset",
            "entity_resolution",
            "--input",
            str(first_path),
            "--input",
            str(second_path),
            "--output",
            str(output),
            "--disagreements",
            str(disagreements),
        ],
    )

    assert annotation_main() == 2
    assert output.read_text(encoding="utf-8") == "sentinel-output"
    assert disagreements.read_text(encoding="utf-8") == "sentinel-disagreements"
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.rollback"))


def test_readiness_accepte_un_micro_lot_v04_coherent(tmp_path):
    records = _support_complete_records()
    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is True
    assert report["status"] == "ready"
    assert report["ready"] is True
    assert report["manifest_declared_status"] == "bootstrap_not_ready"
    assert report["status_authority"] == "computed_readiness_is_authoritative"
    assert "computed status is authoritative" in report["manifest_status_warning"]
    assert all(dataset["ready"] for dataset in report["datasets"].values())
    assert report["measurement_support"]["ready"] is True
    assert all(
        requirement["ready"]
        for requirement in report["measurement_support"]["requirements"].values()
    )


def test_readiness_reste_rouge_si_la_distribution_des_supports_est_insuffisante(
    tmp_path,
):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is True
    assert all(dataset["ready"] for dataset in report["datasets"].values())
    assert report["ready"] is False
    support = report["measurement_support"]
    assert support["ready"] is False
    assert support["requirements"]["entity_different_pairs_min"] == {
        "required": 1,
        "actual": 0,
        "ready": False,
    }
    assert support["requirements"]["offer_noneligible_cases_min"] == {
        "required": 1,
        "actual": 0,
        "ready": False,
    }
    assert support["requirements"]["scenario_generic_product_cases_min"] == {
        "required": 1,
        "actual": 0,
        "ready": False,
    }
    assert support["requirements"]["language_nl_cases_min"]["actual"] == 0


def test_readiness_support_variant_exclut_non_applicable_ambiguous_et_train(
    tmp_path,
):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    different = _alternate_final_record(
        "entity_resolution",
        "different-only",
        {
            "product_relation": "different",
            "variant_relation": "not_applicable",
        },
    )
    train_variant = _final_record("entity_resolution")
    train_variant["case_id"] = "entity-train-variant"
    train_variant["group_id"] = _group_for_split("entity-train-variant", "train")
    train_variant["split"] = "train"
    train_variant["case_fingerprint"] = case_fingerprint(train_variant)
    records["entity_resolution"] = [different, train_variant]

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    requirements = report["measurement_support"]["requirements"]
    assert requirements["entity_different_pairs_min"]["actual"] == 1
    assert requirements["entity_variant_pairs_min"]["actual"] == 0
    assert requirements["calibration_cases_min"]["actual"] == len(DATASETS)


@pytest.mark.parametrize("field", ["case_id", "group_id"])
def test_readiness_refuse_identifiants_non_nfc(field, tmp_path):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    tampered = records["entity_resolution"]
    tampered[field] = "cafe\u0301"
    tampered["case_fingerprint"] = case_fingerprint(tampered)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert report["ready"] is False
    assert any(
        f"{field} must be NFC-normalized" in error
        for error in report["datasets"]["entity_resolution"]["errors"]
    )


@pytest.mark.parametrize("surface", ["annotation", "gold"])
def test_readiness_refuse_invariant_retrieval_sur_annotation_ou_gold(
    surface,
    tmp_path,
):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    tampered = records["retrieval"]
    invalid_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-1"],
        "exact_product_ids": ["product-1"],
        "constraint_violating_product_ids": ["product-1"],
    }
    if surface == "annotation":
        tampered["annotations"][0]["label"] = invalid_label
    else:
        tampered["gold"] = invalid_label
    tampered["case_fingerprint"] = case_fingerprint(tampered)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    retrieval = report["datasets"]["retrieval"]
    assert retrieval["annotation_failures"] == 1
    assert any("must be disjoint" in error for error in retrieval["errors"])


def test_readiness_refuse_un_adjudication_metier_incoherente(tmp_path):
    case, first_label = _case_and_label("retrieval")
    second_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-2"],
        "exact_product_ids": ["product-2"],
        "constraint_violating_product_ids": [],
    }
    first = _completed_pack("retrieval", case, first_label, "human-a")
    second = _completed_pack("retrieval", case, second_label, "human-b")
    merged = merge_completed_packs("retrieval", first + second)
    tasks = prepare_adjudication_pack(
        "retrieval", merged.disagreements, adjudicator_id="human-c"
    )
    tasks[0]["adjudication"].update(
        label=deepcopy(first_label),
        confidence="certain",
        rationale="Vérification humaine indépendante",
    )
    adjudicated = adjudicate_disagreements("retrieval", merged.disagreements, tasks)
    assert adjudicated.errors == ()
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    records["retrieval"] = adjudicated.accepted[0]
    invalid_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-1"],
        "exact_product_ids": ["product-1"],
        "constraint_violating_product_ids": ["product-1"],
    }
    records["retrieval"]["gold"] = deepcopy(invalid_label)
    records["retrieval"]["adjudication"]["label"] = deepcopy(invalid_label)
    records["retrieval"]["case_fingerprint"] = case_fingerprint(
        records["retrieval"]
    )

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    retrieval = report["datasets"]["retrieval"]
    assert retrieval["annotation_failures"] == 1
    assert any("must be disjoint" in error for error in retrieval["errors"])


def test_readiness_refuse_labels_externes_non_canoniquement_ordonnes(tmp_path):
    case, _label = _case_and_label("retrieval")
    canonical_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-1", "product-2"],
        "exact_product_ids": ["product-1", "product-2"],
        "constraint_violating_product_ids": ["product-3", "product-4"],
    }
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    records["retrieval"] = _final_record_from("retrieval", case, canonical_label)
    reversed_label = {
        "resolution": "matched",
        "relevant_product_ids": ["product-2", "product-1"],
        "exact_product_ids": ["product-2", "product-1"],
        "constraint_violating_product_ids": ["product-4", "product-3"],
    }
    records["retrieval"]["gold"] = deepcopy(reversed_label)
    for annotation in records["retrieval"]["annotations"]:
        annotation["label"] = deepcopy(reversed_label)
    records["retrieval"]["case_fingerprint"] = case_fingerprint(
        records["retrieval"]
    )

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert report["ready"] is False
    assert any(
        "not semantically canonical" in error
        for error in report["datasets"]["retrieval"]["errors"]
    )


@pytest.mark.parametrize("surface", ["annotations", "source_pack_fingerprints"])
def test_readiness_refuse_ordre_non_canonique_de_lenveloppe(surface, tmp_path):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    records["entity_resolution"][surface].reverse()
    records["entity_resolution"]["case_fingerprint"] = case_fingerprint(
        records["entity_resolution"]
    )

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    entity = report["datasets"]["entity_resolution"]
    assert entity["annotation_failures"] == 1
    assert any("not canonically ordered" in error for error in entity["errors"])


def test_readiness_refuse_annotateur_non_nfc(tmp_path):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    records["entity_resolution"]["annotations"][0]["annotator_id"] = "cafe\u0301"
    records["entity_resolution"]["case_fingerprint"] = case_fingerprint(
        records["entity_resolution"]
    )

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert any(
        "annotator_id must be NFC-normalized" in error
        for error in report["datasets"]["entity_resolution"]["errors"]
    )


def test_readiness_lit_et_empreinte_chaque_snapshot_une_seule_fois(
    tmp_path,
    monkeypatch,
):
    records = _support_complete_records()
    manifest_path = _write_relaxed_test_quality(tmp_path, records)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    tracked = {
        manifest_path.resolve(),
        (root / "schemas" / "manifest.schema.json").resolve(),
    }
    expected_digests: dict[str, str] = {}
    for dataset in DATASETS:
        config = manifest["datasets"][dataset]
        dataset_path = (root / config["path"]).resolve()
        schema_path = (root / config["schema"]).resolve()
        tracked.update({dataset_path, schema_path})
        expected_digests[dataset] = (
            "sha256:" + hashlib.sha256(dataset_path.read_bytes()).hexdigest()
        )

    reads = {path: 0 for path in tracked}
    real_read_bytes = Path.read_bytes

    def counted_read_bytes(path):
        resolved = path.resolve()
        if resolved in reads:
            reads[resolved] += 1
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    report = build_readiness_report(manifest_path)

    assert report["ready"] is True
    assert set(reads.values()) == {1}
    assert {
        dataset: report["datasets"][dataset]["dataset_sha256"]
        for dataset in DATASETS
    } == expected_digests


def test_readiness_recalcule_split_et_fingerprint(tmp_path):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    tampered = records["entity_resolution"]
    tampered["split"] = "train"
    tampered["case_fingerprint"] = case_fingerprint(tampered)
    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    entity = report["datasets"]["entity_resolution"]
    assert report["ready"] is False
    assert entity["ready"] is False
    assert any("differs from canonical" in error for error in entity["errors"])


def test_readiness_integrite_refuse_empreinte_de_cas_alteree(tmp_path):
    records = _support_complete_records()
    tampered = records["entity_resolution"][0]
    tampered["case_fingerprint"] = "sha256:" + "0" * 64

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert any(
        "case_fingerprint mismatch" in error
        for error in report["datasets"]["entity_resolution"]["errors"]
    )


def test_readiness_integrite_refuse_case_id_duplique(tmp_path):
    records = _support_complete_records()
    duplicate = deepcopy(records["entity_resolution"][0])
    records["entity_resolution"].append(duplicate)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert duplicate["case_id"] in report["duplicate_case_ids"]


def test_readiness_integrite_refuse_entree_cloned_sous_nouvel_identifiant(tmp_path):
    records = _support_complete_records()
    clone = deepcopy(records["entity_resolution"][0])
    clone["case_id"] = "entity-content-clone"
    clone["case_fingerprint"] = case_fingerprint(clone)
    records["entity_resolution"].append(clone)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert report["duplicate_case_ids"] == []
    assert len(report["duplicate_input_fingerprints"]) == 1


def test_readiness_integrite_refuse_groupe_present_dans_plusieurs_splits(tmp_path):
    records = _support_complete_records()
    original = records["entity_resolution"][0]
    leaked = deepcopy(original)
    leaked["case_id"] = "entity-leaked-split"
    leaked["split"] = "train"
    leaked["case_fingerprint"] = case_fingerprint(leaked)
    records["entity_resolution"].append(leaked)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert original["group_id"] in report["leakage_groups"]


def test_readiness_integrite_refuse_schema_metier_present_corrompu(tmp_path):
    manifest_path = _write_relaxed_test_quality(
        tmp_path,
        _support_complete_records(),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema_path = manifest_path.parent / manifest["datasets"]["retrieval"]["schema"]
    schema_path.write_text('{"type":', encoding="utf-8")

    report = build_readiness_report(manifest_path)

    assert report["integrity_valid"] is False
    assert report["datasets"]["retrieval"]["integrity_valid"] is False
    assert any(
        "invalid annotation schema" in error
        for error in report["datasets"]["retrieval"]["errors"]
    )


def test_readiness_integrite_refuse_fuite_de_sortie_moteur(tmp_path):
    records = _support_complete_records()
    tampered = records["entity_resolution"][0]
    tampered["input"]["left"]["engine_output"] = "same"
    tampered["case_fingerprint"] = case_fingerprint(tampered)

    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    assert any(
        "reserved input field" in error
        for error in report["datasets"]["entity_resolution"]["errors"]
    )


def test_readiness_refuse_gold_recalcule_mais_non_soutenu_par_les_humains(tmp_path):
    records = {dataset: _final_record(dataset) for dataset in DATASETS}
    tampered = records["entity_resolution"]
    tampered["gold"] = {
        "product_relation": "different",
        "variant_relation": "not_applicable",
    }
    tampered["case_fingerprint"] = case_fingerprint(tampered)
    report = build_readiness_report(_write_relaxed_test_quality(tmp_path, records))

    assert report["integrity_valid"] is False
    entity = report["datasets"]["entity_resolution"]
    assert entity["annotation_failures"] == 1
    assert any("differs from final gold" in error for error in entity["errors"])
