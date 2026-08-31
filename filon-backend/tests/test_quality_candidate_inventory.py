from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from quality_lab.candidate_inventory import (
    build_catalog_inventory,
    main,
    publish_immutable,
    verify_catalog_inventory,
)
from quality_lab.integrity import sha256_value


SOURCE = (
    "https://catalog.example/api/catalog/offers?"
    "category=T%C3%A9l%C3%A9phonie&subcategory=Smartphones&"
    "duplicates=true&limit=200&offset=0"
)


def _snapshot(path: Path, *, offer_id: int = 7) -> Path:
    path.write_text(
        json.dumps(
            {
                "total": 1,
                "items": [
                    {
                        "id": offer_id,
                        "name": "Telephone public",
                        "brand": "Example",
                        "category": "Téléphonie",
                        "subcategory": "Smartphones",
                        "source_category": "Mobile phones",
                        "offer_kind": "physical_product",
                        "price": 399.0,
                        "currency": "EUR",
                        "in_stock": True,
                        "observed_at": "2026-08-29T10:00:00Z",
                        "evidence_current": True,
                        "image": "https://merchant.example/image.jpg",
                        "link": "https://merchant.example/?affiliate=secret",
                        "merchant": {"name": "Marchand", "slug": "marchand"},
                    }
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


def test_inventaire_omet_verites_moteur_et_liens_affilies(tmp_path):
    records, receipt = _inventory(tmp_path)

    assert len(records) == 1
    serialized = json.dumps(records, ensure_ascii=False)
    for forbidden in (
        "399.0",
        "affiliate=secret",
        "evidence_current",
        "in_stock",
        "offer_kind",
        "observed_at",
    ):
        assert forbidden not in serialized
    assert records[0]["observation"]["name"] == "Telephone public"
    assert records[0]["curation"]["include"] is None
    assert records[0]["curation"]["vertical"] is None
    assert records[0]["sampling_vertical"] == "smartphones"
    assert receipt["labels_present"] is False
    assert receipt["ready_for_annotation"] is False
    verify_catalog_inventory(records, receipt)


def test_inventaire_est_deterministe(tmp_path):
    records_a, receipt_a = _inventory(tmp_path)
    records_b, receipt_b = build_catalog_inventory(
        [("smartphones", SOURCE, tmp_path / "snapshot.json")],
        captured_at="2026-08-29T12:00:00+02:00",
    )

    assert records_a == records_b
    assert receipt_a == receipt_b


@pytest.mark.parametrize(
    "source",
    [
        SOURCE.replace("https://", "http://"),
        SOURCE.replace("duplicates=true", "duplicates=false"),
        SOURCE.replace("subcategory=Smartphones", "subcategory=Coques"),
        SOURCE + "&token=sensible",
    ],
)
def test_source_non_canonique_est_refusee(tmp_path, source):
    with pytest.raises(ValueError):
        build_catalog_inventory(
            [("smartphones", source, _snapshot(tmp_path / "snapshot.json"))],
            captured_at="2026-08-29T12:00:00+02:00",
        )


def test_snapshot_mauvaise_strate_est_refuse(tmp_path):
    path = _snapshot(tmp_path / "snapshot.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["subcategory"] = "Coques & Protections"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="subcategory"):
        build_catalog_inventory(
            [("smartphones", SOURCE, path)],
            captured_at="2026-08-29T12:00:00+02:00",
        )


def test_verification_refuse_toute_curation_ou_alteration(tmp_path):
    records, receipt = _inventory(tmp_path)
    altered = deepcopy(records)
    altered[0]["curation"]["language"] = "fr"

    with pytest.raises(ValueError):
        verify_catalog_inventory(altered, receipt)


def test_verification_refuse_champ_moteur_rajoute(tmp_path):
    records, receipt = _inventory(tmp_path)
    altered = deepcopy(records)
    altered[0]["observation"]["price"] = 399.0
    core = dict(altered[0])
    core.pop("record_fingerprint")
    altered[0]["record_fingerprint"] = sha256_value(
        "filon.quality.candidate-inventory.record.v1", core
    )

    with pytest.raises(ValueError, match="observation"):
        verify_catalog_inventory(altered, receipt)


def test_verification_refuse_snapshot_ou_compte_altere(tmp_path):
    records, receipt = _inventory(tmp_path)
    altered = deepcopy(receipt)
    altered["snapshots"][0]["rows"] = 2

    with pytest.raises(
        ValueError, match="lignes invalides|lignes par snapshot|compte de lignes"
    ):
        verify_catalog_inventory(records, altered)


def test_verification_refuse_source_dupliquee_entre_strates(tmp_path):
    records, receipt = _inventory(tmp_path)
    duplicate = deepcopy(records[0])
    duplicate["sampling_vertical"] = "laptops"
    duplicate["candidate_ref"] = f"catalog:laptops:{duplicate['observation']['source_ref']}"
    core = dict(duplicate)
    core.pop("record_fingerprint")
    duplicate["record_fingerprint"] = sha256_value(
        "filon.quality.candidate-inventory.record.v1", core
    )
    altered_records = sorted([*records, duplicate], key=lambda item: item["candidate_ref"])
    altered_receipt = deepcopy(receipt)
    altered_receipt["rows"] = 2
    altered_receipt["sampling_vertical_counts"] = {"laptops": 1, "smartphones": 1}

    with pytest.raises(ValueError):
        verify_catalog_inventory(altered_records, altered_receipt)


def test_filtre_moteur_ne_devient_jamais_verticale_gold(tmp_path):
    path = _snapshot(tmp_path / "snapshot.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["name"] = "Parfum mal classe"
    payload["items"][0]["source_category"] = "Beauty & Health"
    path.write_text(json.dumps(payload), encoding="utf-8")

    records, _receipt = build_catalog_inventory(
        [("smartphones", SOURCE, path)],
        captured_at="2026-08-29T12:00:00+02:00",
    )

    assert records[0]["sampling_vertical"] == "smartphones"
    assert records[0]["curation"]["vertical"] is None


def test_publication_immuable_refuse_ecrasement(tmp_path):
    records, receipt = _inventory(tmp_path)
    output = tmp_path / "inventory.jsonl"
    receipt_path = tmp_path / "receipt.json"
    publish_immutable(output, receipt_path, records, receipt)

    assert output.exists()
    assert receipt_path.exists()
    with pytest.raises(ValueError, match="existe deja"):
        publish_immutable(output, receipt_path, records, receipt)


def test_cli_verify_recalcule_les_empreintes(tmp_path, monkeypatch):
    records, receipt = _inventory(tmp_path)
    output = tmp_path / "inventory.jsonl"
    receipt_path = tmp_path / "receipt.json"
    publish_immutable(output, receipt_path, records, receipt)
    monkeypatch.setattr(
        "sys.argv",
        [
            "candidate_inventory",
            "verify",
            "--input",
            str(output),
            "--receipt",
            str(receipt_path),
        ],
    )

    assert main() == 0


def test_cli_verify_refuse_un_recu_hors_borne(tmp_path, monkeypatch):
    records, receipt = _inventory(tmp_path)
    output = tmp_path / "inventory.jsonl"
    receipt_path = tmp_path / "receipt.json"
    publish_immutable(output, receipt_path, records, receipt)
    with receipt_path.open("ab") as handle:
        handle.truncate(1024 * 1024 + 1)
    monkeypatch.setattr(
        "sys.argv",
        [
            "candidate_inventory",
            "verify",
            "--input",
            str(output),
            "--receipt",
            str(receipt_path),
        ],
    )

    assert main() == 2
