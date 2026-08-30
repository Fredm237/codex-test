from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.annotation_workflow import prepare_pack
from quality_lab.candidate_inventory import (
    build_catalog_inventory,
    publish_immutable,
)
from quality_lab.curation_workflow import (
    CATALOG_DATASETS,
    finalize_curation,
    main,
    prepare_curation_pack,
    verify_curated_cases,
)
from quality_lab.integrity import canonical_json, sha256_value


SOURCE = (
    "https://catalog.example/api/catalog/offers?"
    "category=T%C3%A9l%C3%A9phonie&subcategory=Smartphones&"
    "duplicates=true&limit=200&offset=0"
)


def _snapshot(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "total": 2,
                "items": [
                    {
                        "id": 7,
                        "name": "Telephone public",
                        "brand": "Example",
                        "category": "Téléphonie",
                        "subcategory": "Smartphones",
                        "source_category": "Mobile phones",
                        "merchant": {"name": "Marchand", "slug": "marchand"},
                    },
                    {
                        "id": 8,
                        "name": "Coque possiblement mal classée",
                        "brand": None,
                        "category": "Téléphonie",
                        "subcategory": "Smartphones",
                        "source_category": "Phone cases",
                        "merchant": {"name": "Marchand", "slug": "marchand"},
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _inventory(tmp_path: Path):
    return build_catalog_inventory(
        [("smartphones", SOURCE, _snapshot(tmp_path / "snapshot.json"))],
        captured_at="2026-08-29T12:00:00+02:00",
    )


def _completed(tmp_path: Path):
    records, receipt = _inventory(tmp_path)
    tasks = prepare_curation_pack(records, receipt, curator_id="human-curator-a")
    tasks[0]["decision"] = {
        "include": True,
        "language": "fr",
        "scenario_type": "exact_product",
        # La strate d'échantillonnage n'est volontairement pas recopiée.
        "vertical": "appliances",
        "datasets": list(CATALOG_DATASETS),
    }
    tasks[1]["decision"] = {
        "include": False,
        "language": None,
        "scenario_type": None,
        "vertical": None,
        "datasets": [],
    }
    return records, receipt, tasks


def test_curation_produit_des_cas_sans_gold_et_annotables(tmp_path):
    records, receipt, tasks = _completed(tmp_path)

    cases, curated_receipt = finalize_curation(
        records,
        receipt,
        tasks,
        dataset="taxonomy",
    )

    assert len(cases) == 1
    assert cases[0]["strata"] == {
        "scenario_type": "exact_product",
        "language": "fr",
        "vertical": "appliances",
    }
    assert cases[0]["observation"] == records[0]["observation"]
    serialized = canonical_json(cases)
    assert "gold" not in serialized
    assert "annotation" not in serialized
    assert curated_receipt["labels_present"] is False
    assert curated_receipt["ready_for_annotation"] is True
    assert curated_receipt["blocked_on"] == ["independent_human_annotation"]
    verify_curated_cases(cases, curated_receipt)
    assert len(prepare_pack("taxonomy", cases, annotator_id="human-a")) == 1


def test_sortie_variant_reste_un_candidat_et_non_un_gold(tmp_path):
    records, receipt, tasks = _completed(tmp_path)

    cases, curated_receipt = finalize_curation(
        records,
        receipt,
        tasks,
        dataset="variant_resolution",
    )

    verify_curated_cases(cases, curated_receipt)
    pack = prepare_pack("variant_resolution", cases, annotator_id="human-b")
    assert pack[0]["annotation"]["label"] is None
    assert pack[0]["input"]["observation"]["identifiers"] == {"offer_id": 7}


@pytest.mark.parametrize(
    "decision, message",
    [
        (
            {
                "include": None,
                "language": None,
                "scenario_type": None,
                "vertical": None,
                "datasets": [],
            },
            "explicitement",
        ),
        (
            {
                "include": False,
                "language": "fr",
                "scenario_type": None,
                "vertical": None,
                "datasets": [],
            },
            "exclusion",
        ),
        (
            {
                "include": True,
                "language": "fr",
                "scenario_type": "exact_product",
                "vertical": "smartphones",
                "datasets": ["decision"],
            },
            "datasets",
        ),
    ],
)
def test_curation_incomplete_ou_hors_perimetre_est_refusee(
    tmp_path,
    decision,
    message,
):
    records, receipt, tasks = _completed(tmp_path)
    tasks[0]["decision"] = decision

    with pytest.raises(ValueError, match=message):
        finalize_curation(records, receipt, tasks, dataset="taxonomy")


def test_source_affectation_et_roster_sont_immuables(tmp_path):
    records, receipt, tasks = _completed(tmp_path)
    altered = deepcopy(tasks)
    altered[0]["observation"]["name"] = "Sortie moteur injectée"
    with pytest.raises(ValueError, match="altéré|fingerprint"):
        finalize_curation(records, receipt, altered, dataset="taxonomy")

    with pytest.raises(ValueError, match="exactement tout l'inventaire"):
        finalize_curation(records, receipt, tasks[:-1], dataset="taxonomy")

    altered_curator = deepcopy(tasks)
    altered_curator[1]["curator_id"] = "human-curator-b"
    with pytest.raises(ValueError, match="curator|affectation"):
        finalize_curation(records, receipt, altered_curator, dataset="taxonomy")


def test_recu_detecte_toute_alteration_de_sortie(tmp_path):
    records, receipt, tasks = _completed(tmp_path)
    cases, curated_receipt = finalize_curation(
        records,
        receipt,
        tasks,
        dataset="taxonomy",
    )
    altered = deepcopy(cases)
    altered[0]["observation"]["name"] = "Altéré"

    with pytest.raises(ValueError, match="output_fingerprint"):
        verify_curated_cases(altered, curated_receipt)

    wrong_counts = deepcopy(curated_receipt)
    wrong_counts["strata_counts"]["language"] = {"en": 1}
    with pytest.raises(ValueError, match="strates"):
        verify_curated_cases(cases, wrong_counts)

    leaked = deepcopy(cases)
    leaked[0]["gold"] = {"category": "injected"}
    with pytest.raises(ValueError, match="structure de cas"):
        verify_curated_cases(leaked, curated_receipt)


def test_pack_fingerprint_ne_peut_pas_etre_recalcule_apres_alteration(tmp_path):
    records, receipt, tasks = _completed(tmp_path)
    altered = deepcopy(tasks)
    altered[0]["sampling_vertical"] = "laptops"
    core_keys = (
        "curation_version",
        "inventory_fingerprint",
        "candidate_ref",
        "record_fingerprint",
        "sampling_vertical",
        "observation",
        "curator_id",
        "allowed_datasets",
    )
    altered[0]["task_fingerprint"] = sha256_value(
        "filon.quality.candidate-curation.task.v1",
        {key: altered[0][key] for key in core_keys},
    )

    with pytest.raises(ValueError, match="altéré"):
        finalize_curation(records, receipt, altered, dataset="taxonomy")


def test_cli_prepare_publie_immuablement_sans_label(tmp_path, monkeypatch):
    records, receipt = _inventory(tmp_path)
    inventory_path = tmp_path / "inventory.jsonl"
    inventory_receipt_path = tmp_path / "inventory-receipt.json"
    publish_immutable(
        inventory_path,
        inventory_receipt_path,
        records,
        receipt,
    )
    output = tmp_path / "curation-pack.jsonl"
    output_receipt = tmp_path / "curation-pack-receipt.json"
    argv = [
        "curation_workflow",
        "prepare",
        "--inventory",
        str(inventory_path),
        "--inventory-receipt",
        str(inventory_receipt_path),
        "--output",
        str(output),
        "--receipt",
        str(output_receipt),
        "--curator-id",
        "human-curator-a",
    ]
    monkeypatch.setattr("sys.argv", argv)

    assert main() == 0
    assert '"include":null' in output.read_text(encoding="utf-8")
    assert '"labels_present":false' in output_receipt.read_text(encoding="utf-8")
    assert main() == 2
