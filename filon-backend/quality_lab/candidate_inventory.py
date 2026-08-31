"""Inventaire immuable de candidats reels pour le FILON Quality Lab.

Ce module ne cree aucun gold et ne transforme pas une sortie FILON en verite.
Il extrait uniquement les champs publics necessaires a la constitution ulterieure
de packs humains aveugles. Les champs produits par le moteur (categorie FILON,
prix, stock, evidence, score et lien affilie) sont volontairement omis.
"""

from __future__ import annotations

import argparse
import os
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from .integrity import canonical_json, sha256_value, strict_loads


INVENTORY_VERSION = "quality-candidate-inventory/v1"
RECEIPT_VERSION = "quality-candidate-inventory-receipt/v1"
MAX_SNAPSHOT_BYTES = 8 * 1024 * 1024
MAX_INVENTORY_BYTES = 64 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_ITEMS_PER_SNAPSHOT = 200
MAX_SNAPSHOTS = 50
_RECORD_FINGERPRINT_DOMAIN = "filon.quality.candidate-inventory.record.v1"
_INVENTORY_FINGERPRINT_DOMAIN = "filon.quality.candidate-inventory.v1"

# L'API renvoie les libelles avec accents. Les valeurs ci-dessus restent ASCII
# pour rendre la CLI portable ; cette table est la seule conversion autorisee.
_API_FILTERS: dict[str, tuple[str, str]] = {
    "smartphones": ("Téléphonie", "Smartphones"),
    "laptops": ("Informatique", "Ordinateurs portables"),
    "tv": ("TV & Son", "Téléviseurs"),
    "headphones_audio": ("TV & Son", "Casques audio"),
    "appliances": ("Électroménager", "Gros électroménager"),
}

_OMITTED_ENGINE_FIELDS = (
    "category",
    "currency",
    "evidence_current",
    "image",
    "in_stock",
    "link",
    "observed_at",
    "offer_kind",
    "price",
    "subcategory",
)


def _nonblank(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} doit etre une chaine non vide sans bord blanc")
    if len(value) > 1_000:
        raise ValueError(f"{field} depasse 1000 caracteres")
    return unicodedata.normalize("NFC", value)


def _optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _nonblank(value, field)


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} doit etre un entier positif")
    return value


def _offset_datetime(value: str) -> str:
    candidate = _nonblank(value, "captured_at")
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("captured_at doit etre ISO 8601") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("captured_at doit inclure un offset")
    return candidate


def _canonical_source_url(value: str, vertical: str) -> str:
    candidate = _nonblank(value, f"source_url[{vertical}]")
    parsed = urlsplit(candidate)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.path.rstrip("/") != "/api/catalog/offers"
    ):
        raise ValueError(f"source_url[{vertical}] doit viser HTTPS /api/catalog/offers")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    expected_keys = {"category", "subcategory", "duplicates", "limit", "offset"}
    if set(query) != expected_keys or any(len(values) != 1 for values in query.values()):
        raise ValueError(f"source_url[{vertical}] a une requete non canonique")
    expected_category, expected_subcategory = _API_FILTERS[vertical]
    if query["category"] != [expected_category]:
        raise ValueError(f"source_url[{vertical}] categorie inattendue")
    if query["subcategory"] != [expected_subcategory]:
        raise ValueError(f"source_url[{vertical}] sous-categorie inattendue")
    if query["duplicates"] != ["true"] or query["limit"] != ["200"]:
        raise ValueError(f"source_url[{vertical}] doit demander duplicates=true et limit=200")
    try:
        offset = int(query["offset"][0])
    except ValueError:
        raise ValueError(f"source_url[{vertical}] offset invalide") from None
    if offset < 0 or offset % 200:
        raise ValueError(f"source_url[{vertical}] offset doit etre positif et multiple de 200")
    canonical_query = urlencode(
        [
            ("category", expected_category),
            ("subcategory", expected_subcategory),
            ("duplicates", "true"),
            ("limit", "200"),
            ("offset", str(offset)),
        ]
    )
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urlunsplit(("https", host, "/api/catalog/offers", canonical_query, ""))


def _snapshot_fingerprint(payload: bytes) -> str:
    import hashlib

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _public_observation(item: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    offer_id = _positive_int(item.get("id"), f"items[{index}].id")
    name = _nonblank(item.get("name"), f"items[{index}].name")
    brand = _optional_text(item.get("brand"), f"items[{index}].brand")
    source_category = _optional_text(
        item.get("source_category"), f"items[{index}].source_category"
    )
    merchant = item.get("merchant")
    if not isinstance(merchant, dict) or set(merchant) != {"name", "slug"}:
        raise ValueError(f"items[{index}].merchant invalide")
    merchant_name = _nonblank(merchant.get("name"), f"items[{index}].merchant.name")
    merchant_slug = _nonblank(merchant.get("slug"), f"items[{index}].merchant.slug")
    return {
        "source_ref": f"public-catalog:offer:{offer_id}",
        "name": name,
        "brand": brand,
        "identifiers": {"offer_id": offer_id},
        "attributes": {
            "merchant_name": merchant_name,
            "merchant_slug": merchant_slug,
            "source_category": source_category,
        },
    }


def build_catalog_inventory(
    snapshots: Iterable[tuple[str, str, Path]],
    *,
    captured_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Construit un inventaire sans label depuis des snapshots publics exacts."""

    captured = _offset_datetime(captured_at)
    entries = list(snapshots)
    if not entries:
        raise ValueError("au moins un snapshot est requis")
    if len(entries) > MAX_SNAPSHOTS:
        raise ValueError(f"au plus {MAX_SNAPSHOTS} snapshots sont autorises")
    records: list[dict[str, Any]] = []
    snapshot_receipts: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_refs: set[str] = set()

    for vertical, source_url, path in entries:
        if vertical not in _API_FILTERS:
            raise ValueError(f"vertical inconnu: {vertical}")
        canonical_url = _canonical_source_url(source_url, vertical)
        if canonical_url in seen_urls:
            raise ValueError(f"source_url dupliquee: {canonical_url}")
        seen_urls.add(canonical_url)
        payload = path.read_bytes() if path.exists() else b""
        if len(payload) < 2 or len(payload) > MAX_SNAPSHOT_BYTES:
            raise ValueError(f"snapshot {path} hors borne de taille")
        snapshot = strict_loads(payload, source=str(path))
        if not isinstance(snapshot, dict) or set(snapshot) != {"total", "items"}:
            raise ValueError(f"snapshot {path} doit contenir exactement total et items")
        total = snapshot.get("total")
        items = snapshot.get("items")
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError(f"snapshot {path}: total invalide")
        if not isinstance(items, list) or not items or len(items) > MAX_ITEMS_PER_SNAPSHOT:
            raise ValueError(f"snapshot {path}: items doit contenir 1 a 200 lignes")
        snapshot_fp = _snapshot_fingerprint(payload)
        expected_category, expected_subcategory = _API_FILTERS[vertical]
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"items[{index}] doit etre un objet")
            if item.get("category") != expected_category:
                raise ValueError(f"items[{index}].category inattendue pour {vertical}")
            if item.get("subcategory") != expected_subcategory:
                raise ValueError(f"items[{index}].subcategory inattendue pour {vertical}")
            observation = _public_observation(item, index=index)
            candidate_ref = f"catalog:{vertical}:{observation['source_ref']}"
            if candidate_ref in seen_refs:
                raise ValueError(f"candidat duplique: {candidate_ref}")
            seen_refs.add(candidate_ref)
            core = {
                "inventory_version": INVENTORY_VERSION,
                "candidate_ref": candidate_ref,
                # Le filtre du moteur sert seulement a echantillonner. Il ne
                # devient jamais la verticale gold : des erreurs reelles de
                # classement sont justement attendues dans cet inventaire.
                "sampling_vertical": vertical,
                "observation": observation,
                "source": {
                    "captured_at": captured,
                    "snapshot_fingerprint": snapshot_fp,
                },
                "curation": {
                    "include": None,
                    "language": None,
                    "scenario_type": None,
                    "vertical": None,
                    "datasets": [],
                },
            }
            records.append(
                {
                    **core,
                    "record_fingerprint": sha256_value(
                        _RECORD_FINGERPRINT_DOMAIN, core
                    ),
                }
            )
        snapshot_receipts.append(
            {
                "vertical": vertical,
                "source_url": canonical_url,
                "snapshot_fingerprint": snapshot_fp,
                "catalog_total": total,
                "rows": len(items),
            }
        )

    records.sort(key=lambda record: record["candidate_ref"])
    snapshot_receipts.sort(key=lambda receipt: receipt["source_url"])
    sampling_vertical_counts = dict(
        sorted(Counter(r["sampling_vertical"] for r in records).items())
    )
    inventory_fp = sha256_value(
        _INVENTORY_FINGERPRINT_DOMAIN,
        {
            "inventory_version": INVENTORY_VERSION,
            "record_fingerprints": [r["record_fingerprint"] for r in records],
            "snapshots": snapshot_receipts,
        }
    )
    receipt = {
        "receipt_version": RECEIPT_VERSION,
        "inventory_version": INVENTORY_VERSION,
        "captured_at": captured,
        "rows": len(records),
        "sampling_vertical_counts": sampling_vertical_counts,
        "snapshots": snapshot_receipts,
        "omitted_engine_fields": list(_OMITTED_ENGINE_FIELDS),
        "labels_present": False,
        "ready_for_annotation": False,
        "blocked_on": ["human_curation", "independent_human_annotation"],
        "inventory_fingerprint": inventory_fp,
    }
    return records, receipt


def verify_catalog_inventory(
    records: Iterable[Mapping[str, Any]], receipt: Mapping[str, Any]
) -> None:
    materialized = list(records)
    expected_receipt_keys = {
        "receipt_version",
        "inventory_version",
        "captured_at",
        "rows",
        "sampling_vertical_counts",
        "snapshots",
        "omitted_engine_fields",
        "labels_present",
        "ready_for_annotation",
        "blocked_on",
        "inventory_fingerprint",
    }
    if set(receipt) != expected_receipt_keys:
        raise ValueError("champs du recu incompatibles")
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        raise ValueError("receipt_version incompatible")
    if receipt.get("inventory_version") != INVENTORY_VERSION:
        raise ValueError("inventory_version incompatible")
    captured_at = _offset_datetime(receipt.get("captured_at"))
    snapshots = receipt.get("snapshots")
    if (
        not isinstance(snapshots, list)
        or not snapshots
        or len(snapshots) > MAX_SNAPSHOTS
    ):
        raise ValueError("snapshots du recu invalides")
    snapshot_fingerprints_by_vertical: dict[str, set[str]] = {}
    snapshot_rows: Counter[str] = Counter()
    seen_snapshot_urls: set[str] = set()
    seen_snapshot_fingerprints: set[str] = set()
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, Mapping) or set(snapshot) != {
            "vertical",
            "source_url",
            "snapshot_fingerprint",
            "catalog_total",
            "rows",
        }:
            raise ValueError(f"snapshot du recu {index}: structure invalide")
        vertical = snapshot.get("vertical")
        if vertical not in _API_FILTERS:
            raise ValueError(f"snapshot du recu {index}: verticale invalide")
        source_url = snapshot.get("source_url")
        canonical_url = _canonical_source_url(source_url, vertical)
        if source_url != canonical_url or source_url in seen_snapshot_urls:
            raise ValueError(f"snapshot du recu {index}: source_url invalide")
        seen_snapshot_urls.add(source_url)
        snapshot_fingerprint = snapshot.get("snapshot_fingerprint")
        if (
            not isinstance(snapshot_fingerprint, str)
            or len(snapshot_fingerprint) != 71
            or not snapshot_fingerprint.startswith("sha256:")
            or any(
                character not in "0123456789abcdef"
                for character in snapshot_fingerprint[7:]
            )
            or snapshot_fingerprint in seen_snapshot_fingerprints
        ):
            raise ValueError(f"snapshot du recu {index}: empreinte invalide")
        seen_snapshot_fingerprints.add(snapshot_fingerprint)
        catalog_total = snapshot.get("catalog_total")
        if (
            isinstance(catalog_total, bool)
            or not isinstance(catalog_total, int)
            or catalog_total < 0
        ):
            raise ValueError(f"snapshot du recu {index}: total invalide")
        rows = snapshot.get("rows")
        if (
            isinstance(rows, bool)
            or not isinstance(rows, int)
            or rows < 1
            or rows > MAX_ITEMS_PER_SNAPSHOT
            or rows > catalog_total
        ):
            raise ValueError(f"snapshot du recu {index}: lignes invalides")
        snapshot_fingerprints_by_vertical.setdefault(vertical, set()).add(
            snapshot_fingerprint
        )
        snapshot_rows[snapshot_fingerprint] = rows
    if receipt.get("omitted_engine_fields") != list(_OMITTED_ENGINE_FIELDS):
        raise ValueError("champs moteur omis incompatibles")
    if receipt.get("blocked_on") != [
        "human_curation",
        "independent_human_annotation",
    ]:
        raise ValueError("blocages du recu incompatibles")
    refs: list[str] = []
    source_refs: list[str] = []
    fingerprints: list[str] = []
    sampling_verticals: list[str] = []
    observed_snapshot_rows: Counter[str] = Counter()
    for index, record in enumerate(materialized):
        if not isinstance(record, Mapping) or set(record) != {
            "inventory_version",
            "candidate_ref",
            "sampling_vertical",
            "observation",
            "source",
            "curation",
            "record_fingerprint",
        }:
            raise ValueError(f"record {index}: objet attendu")
        core = dict(record)
        fingerprint = core.pop("record_fingerprint", None)
        if fingerprint != sha256_value(_RECORD_FINGERPRINT_DOMAIN, core):
            raise ValueError(f"record {index}: record_fingerprint invalide")
        if core.get("inventory_version") != INVENTORY_VERSION:
            raise ValueError(f"record {index}: inventory_version incompatible")
        curation = core.get("curation")
        if curation != {
            "include": None,
            "language": None,
            "scenario_type": None,
            "vertical": None,
            "datasets": [],
        }:
            raise ValueError(f"record {index}: inventaire deja annote ou altere")
        ref = _nonblank(core.get("candidate_ref"), f"record {index}.candidate_ref")
        sampling_vertical = core.get("sampling_vertical")
        if sampling_vertical not in _API_FILTERS:
            raise ValueError(f"record {index}: sampling_vertical invalide")
        observation = core.get("observation")
        if not isinstance(observation, Mapping) or set(observation) != {
            "source_ref",
            "name",
            "brand",
            "identifiers",
            "attributes",
        }:
            raise ValueError(f"record {index}: observation invalide")
        source_ref = _nonblank(
            observation.get("source_ref"), f"record {index}.observation.source_ref"
        )
        identifiers = observation.get("identifiers")
        if not isinstance(identifiers, Mapping) or set(identifiers) != {"offer_id"}:
            raise ValueError(f"record {index}: identifiers invalides")
        offer_id = _positive_int(
            identifiers.get("offer_id"), f"record {index}.identifiers.offer_id"
        )
        if source_ref != f"public-catalog:offer:{offer_id}":
            raise ValueError(f"record {index}: source_ref invalide")
        if ref != f"catalog:{sampling_vertical}:{source_ref}":
            raise ValueError(f"record {index}: candidate_ref invalide")
        _nonblank(observation.get("name"), f"record {index}.observation.name")
        _optional_text(observation.get("brand"), f"record {index}.observation.brand")
        attributes = observation.get("attributes")
        if not isinstance(attributes, Mapping) or set(attributes) != {
            "merchant_name",
            "merchant_slug",
            "source_category",
        }:
            raise ValueError(f"record {index}: attributes invalides")
        _nonblank(
            attributes.get("merchant_name"),
            f"record {index}.attributes.merchant_name",
        )
        _nonblank(
            attributes.get("merchant_slug"),
            f"record {index}.attributes.merchant_slug",
        )
        _optional_text(
            attributes.get("source_category"),
            f"record {index}.attributes.source_category",
        )
        source = core.get("source")
        if not isinstance(source, Mapping) or set(source) != {
            "captured_at",
            "snapshot_fingerprint",
        }:
            raise ValueError(f"record {index}: source invalide")
        if source.get("captured_at") != captured_at:
            raise ValueError(f"record {index}: captured_at incompatible")
        snapshot_fingerprint = source.get("snapshot_fingerprint")
        if snapshot_fingerprint not in snapshot_fingerprints_by_vertical.get(
            sampling_vertical, set()
        ):
            raise ValueError(f"record {index}: snapshot inconnu")
        refs.append(ref)
        source_refs.append(source_ref)
        sampling_verticals.append(sampling_vertical)
        fingerprints.append(fingerprint)
        observed_snapshot_rows[snapshot_fingerprint] += 1
    if refs != sorted(refs) or len(refs) != len(set(refs)):
        raise ValueError("candidate_ref non canoniques ou dupliques")
    if len(source_refs) != len(set(source_refs)):
        raise ValueError("source_ref dupliques entre strates")
    if observed_snapshot_rows != snapshot_rows:
        raise ValueError("comptes de lignes par snapshot invalides")
    expected_counts = dict(sorted(Counter(sampling_verticals).items()))
    rows = receipt.get("rows")
    if isinstance(rows, bool) or not isinstance(rows, int) or rows < 1:
        raise ValueError("compte de lignes du recu invalide")
    if rows != len(materialized) or rows != sum(snapshot_rows.values()):
        raise ValueError("compte de lignes du recu invalide")
    if receipt.get("sampling_vertical_counts") != expected_counts:
        raise ValueError("comptes de verticales d'echantillonnage invalides")
    expected_fp = sha256_value(
        _INVENTORY_FINGERPRINT_DOMAIN,
        {
            "inventory_version": INVENTORY_VERSION,
            "record_fingerprints": fingerprints,
            "snapshots": receipt.get("snapshots"),
        }
    )
    if receipt.get("inventory_fingerprint") != expected_fp:
        raise ValueError("inventory_fingerprint invalide")
    if receipt.get("labels_present") is not False:
        raise ValueError("le recu doit confirmer l'absence de labels")
    if receipt.get("ready_for_annotation") is not False:
        raise ValueError("un inventaire brut ne peut pas etre pret pour annotation")


def _stage(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def publish_immutable(
    output: Path,
    receipt_path: Path,
    records: Iterable[Mapping[str, Any]],
    receipt: Mapping[str, Any],
) -> None:
    output_key = unicodedata.normalize("NFC", str(output.resolve())).casefold()
    receipt_key = unicodedata.normalize("NFC", str(receipt_path.resolve())).casefold()
    if output_key == receipt_key:
        raise ValueError("output et receipt doivent etre distincts")
    if output.exists() or receipt_path.exists():
        raise ValueError("publication refusee: une cible existe deja")
    inventory_payload = "".join(
        canonical_json(record) + "\n" for record in records
    ).encode("utf-8")
    receipt_payload = (canonical_json(receipt) + "\n").encode("utf-8")
    staged_output = _stage(output, inventory_payload)
    try:
        staged_receipt = _stage(receipt_path, receipt_payload)
    except BaseException:
        staged_output.unlink(missing_ok=True)
        raise
    published: list[Path] = []
    try:
        os.link(staged_output, output)
        published.append(output)
        os.link(staged_receipt, receipt_path)
        published.append(receipt_path)
        for parent in sorted({output.parent.resolve(), receipt_path.parent.resolve()}, key=str):
            descriptor = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except BaseException:
        for path in reversed(published):
            path.unlink(missing_ok=True)
        raise
    finally:
        staged_output.unlink(missing_ok=True)
        staged_receipt.unlink(missing_ok=True)


def _snapshot_argument(value: list[str]) -> tuple[str, str, Path]:
    vertical, source_url, path = value
    return vertical, source_url, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventaire reel et sans label des candidats Quality Lab"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser("collect-catalog")
    collect.add_argument(
        "--snapshot",
        action="append",
        nargs=3,
        metavar=("VERTICAL", "SOURCE_URL", "PATH"),
        required=True,
    )
    collect.add_argument("--captured-at", required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--receipt", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--input", type=Path, required=True)
    verify.add_argument("--receipt", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "collect-catalog":
            records, receipt = build_catalog_inventory(
                (_snapshot_argument(value) for value in args.snapshot),
                captured_at=args.captured_at,
            )
            verify_catalog_inventory(records, receipt)
            publish_immutable(args.output, args.receipt, records, receipt)
        else:
            if args.input.stat().st_size > MAX_INVENTORY_BYTES:
                raise ValueError("inventaire hors borne de taille")
            input_payload = args.input.read_bytes()
            if len(input_payload) > MAX_INVENTORY_BYTES:
                raise ValueError("inventaire hors borne de taille")
            records = [
                strict_loads(line, source=f"{args.input}:{index}")
                for index, line in enumerate(input_payload.splitlines(), 1)
                if line.strip()
            ]
            if args.receipt.stat().st_size > MAX_RECEIPT_BYTES:
                raise ValueError("recu hors borne de taille")
            receipt_payload = args.receipt.read_bytes()
            if len(receipt_payload) > MAX_RECEIPT_BYTES:
                raise ValueError("recu hors borne de taille")
            receipt = strict_loads(receipt_payload, source=str(args.receipt))
            if not isinstance(receipt, dict):
                raise ValueError("le recu doit etre un objet")
            verify_catalog_inventory(records, receipt)
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"erreur inventaire: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
