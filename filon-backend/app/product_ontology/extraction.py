"""Extracteur Product Ontology v1, déterministe et fail-closed.

La taxonomie et le moteur de rôle historiques restent des signaux de migration.
Ils ne peuvent pas, seuls, transformer un objet ambigu en produit principal ni
une cible textuelle en Variant canonique.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping

from app.services import product_role as legacy_roles
from app.services import taxonomy


EXTRACTOR_VERSION = "product-ontology-extractor/v1"
POLICY_VERSION = "product-ontology-policy/v1"


class ProductOntologyExtractionError(ValueError):
    """Entrée hors contrat : aucune assertion partielle n'est produite."""


_PRODUCT_TYPES: tuple[tuple[str, str, str, str, str, str, str, str | None], ...] = (
    (r"\b(?:protective\s+case|phone\s+case|coques?|screen\s+protectors?)\b", "electronics.accessories", "Accessoires électroniques", "electronics.accessories.protection", "Protection", "protective_case", "Coque ou protection", taxonomy.TELEPHONIE),
    (r"\b(?:replacement\s+(?:screen|display)|pi[èe]ce\s+de\s+remplacement)\b", "electronics.parts", "Pièces électroniques", "electronics.parts.replacement", "Pièces de remplacement", "replacement_screen", "Écran de remplacement", taxonomy.TELEPHONIE),
    (r"\b(?:ink\s+cartridges?|cartouches?\s+d['’ ]encre|toners?)\b", "office.printing", "Impression", "office.printing.consumables", "Consommables d'impression", "ink_cartridge", "Cartouche d'encre", taxonomy.INFORMATIQUE),
    (r"\b(?:holiday\s+apartments?|appartements?\s+de\s+vacances|holiday\s+homes?)\b", "travel.accommodation", "Hébergement", "travel.accommodation.rental", "Location de vacances", "accommodation", "Hébergement", taxonomy.VOYAGES),
    (r"\b(?:software\s+licen[cs]e|licen[cs]e\s+logicielle|software\s+download)\b", "digital.software", "Logiciels", "digital.software.licence", "Licences", "software_licence", "Licence logicielle", taxonomy.CULTURE),
    (r"\b(?:installation\s+service|service\s+d['’]installation)\b", "services.installation", "Services", "services.installation", "Installation", "installation_service", "Service d'installation", None),
    (r"\b(?:smartphones?|mobile\s+phones?|t[ée]l[ée]phones?\s+mobiles?)\b", "electronics.telephony", "Téléphonie", "electronics.telephony.smartphones", "Smartphones", "smartphone", "Smartphone", taxonomy.TELEPHONIE),
    (r"\b(?:laptops?|notebooks?|ordinateurs?\s+portables?)\b", "electronics.computing", "Informatique", "electronics.computing.laptops", "Ordinateurs portables", "laptop", "Ordinateur portable", taxonomy.INFORMATIQUE),
    (r"\b(?:tyres?|tires?|pneus?)\b", "automotive.tyres", "Pneus", "automotive.tyres.passenger", "Pneus véhicule", "tyre", "Pneu", taxonomy.AUTO),
    (r"\b(?:air\s+conditioners?|climatiseurs?)\b", "home.appliances", "Électroménager", "home.appliances.hvac", "Climatisation", "air_conditioner", "Climatiseur", taxonomy.ELECTROMENAGER),
    (r"\b(?:jackets?|vestes?|manteaux?)\b", "apparel.clothing", "Mode", "apparel.clothing.outerwear", "Vêtements d'extérieur", "jacket", "Veste", taxonomy.MODE),
    (r"\b(?:travel\s+guides?|guides?\s+de\s+voyage)\b", "media.books", "Livres", "media.books.travel", "Guides de voyage", "travel_guide", "Guide de voyage", taxonomy.CULTURE),
    (r"\b(?:bundles?|lots?)\b", "bundles", "Lots", "bundles.mixed", "Lots mixtes", "bundle", "Lot", None),
)

_PRIMARY_OBJECT = re.compile(
    r"\b(?:smartphones?|phones?|mobile\s+phones?|t[ée]l[ée]phones?\s+mobiles?|laptops?|"
    r"notebooks?|ordinateurs?\s+portables?|tyres?|tires?|pneus?|air\s+conditioners?|"
    r"climatiseurs?|jackets?|vestes?|manteaux?|travel\s+guides?|"
    r"guides?\s+de\s+voyage)\b",
    re.IGNORECASE,
)

_FACET_RULES: Mapping[str, tuple[tuple[str, str, str], ...]] = {
    "use_case": ((r"\b(?:running|course\s+[àa]\s+pied)\b", "use_case.running", "Course à pied"),),
    "audience": (
        (r"\b(?:women|woman|femme)\b", "audience.women", "Femme"),
        (r"\b(?:men|man|homme)\b", "audience.men", "Homme"),
        (r"\b(?:kids?|children|enfants?)\b", "audience.children", "Enfant"),
    ),
    "style": ((r"\bcasual\b", "style.casual", "Casual"),),
    "material": ((r"\b(?:cotton|coton)\b", "material.cotton", "Coton"),),
    "season": (
        (r"\b(?:winter|hiver)\b", "season.winter", "Hiver"),
        (r"\b(?:summer|[ée]t[ée])\b", "season.summer", "Été"),
    ),
    "occasion": ((r"\b(?:wedding|mariage)\b", "occasion.wedding", "Mariage"),),
    "function": ((r"\b(?:waterproof|imperm[ée]able)\b", "function.waterproof", "Imperméable"),),
}

_LEGACY_ROLE_MAP = {
    legacy_roles.ACCESSORY: "ACCESSORY",
    legacy_roles.PROTECTIVE_CASE: "ACCESSORY",
    legacy_roles.SCREEN_PROTECTOR: "ACCESSORY",
    legacy_roles.CHARGER: "ACCESSORY",
    legacy_roles.CABLE: "ACCESSORY",
    legacy_roles.ADAPTER: "ACCESSORY",
    legacy_roles.STAND: "ACCESSORY",
    legacy_roles.MOUNT: "ACCESSORY",
    legacy_roles.HOLDER: "ACCESSORY",
    legacy_roles.BAG: "ACCESSORY",
    legacy_roles.REPLACEMENT_PART: "REPLACEMENT_PART",
    legacy_roles.CONSUMABLE: "CONSUMABLE",
    legacy_roles.BUNDLE: "BUNDLE",
}

_RELATION_MAP = {
    legacy_roles.COMPATIBLE_WITH: "COMPATIBLE_WITH",
    legacy_roles.REPLACEMENT_FOR: "REPLACEMENT_PART_FOR",
    legacy_roles.INCLUDED_IN: "INCLUDED_IN",
}


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ProductOntologyExtractionError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _positive_identifier(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ProductOntologyExtractionError(f"{field} must be a positive integer")
    return value


def _text(row: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _evidence(
    *,
    raw_source_record_id: int,
    source_type: str,
    source_ref: str,
    observed_at: datetime,
    field: str,
    transformation: str,
    strength: str,
) -> dict[str, Any]:
    return {
        "raw_source_record_id": raw_source_record_id,
        "source_type": source_type,
        "source_ref": source_ref,
        "observed_at": _iso(observed_at),
        "field": field,
        "transformation": transformation,
        "transformation_version": EXTRACTOR_VERSION,
        "evidence_strength": strength,
    }


def _unknown_concept() -> dict[str, Any]:
    return {"state": "unknown", "value": None, "evidence": []}


def _known_concept(key: str, label: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"state": "known", "value": {"concept_key": key, "label": label}, "evidence": [evidence]}


def _product_type(text: str) -> tuple[str, str, str, str, str, str, str | None] | None:
    for pattern, category_key, category_label, subcategory_key, subcategory_label, type_key, type_label, legacy_category in _PRODUCT_TYPES:
        if re.search(pattern, text, re.IGNORECASE):
            return category_key, category_label, subcategory_key, subcategory_label, type_key, type_label, legacy_category
    return None


def _role(
    *,
    title: str,
    source_text: str,
    offer_kind: str | None,
    legacy: Mapping[str, Any],
    evidence_factory,
) -> dict[str, Any]:
    if offer_kind == taxonomy.ACCOMMODATION:
        value, strength, transformation = "ACCOMMODATION", "observed_structured", "explicit_offer_kind"
    elif offer_kind == taxonomy.DIGITAL_CONTENT:
        value, strength, transformation = "DIGITAL_CONTENT", "observed_structured", "explicit_offer_kind"
    elif offer_kind == taxonomy.SERVICE:
        value, strength, transformation = "SERVICE", "observed_structured", "explicit_offer_kind"
    else:
        legacy_value = legacy["product_role"]
        mapped = _LEGACY_ROLE_MAP.get(legacy_value)
        if mapped is not None:
            value, strength, transformation = mapped, "weak_text", "explicit_role_lexeme"
        elif (
            legacy_value == legacy_roles.MAIN_PRODUCT
            and not legacy["relationships"]
            and _PRIMARY_OBJECT.search(title)
        ):
            value, strength, transformation = "PRIMARY_PRODUCT", "weak_text", "explicit_primary_object_lexeme"
        else:
            return {"state": "unknown", "value": "UNKNOWN", "evidence": []}
    return {
        "state": "known",
        "value": value,
        "evidence": [evidence_factory("product_role", transformation, strength)],
    }


def _attributes(legacy: Mapping[str, Any], evidence_factory) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    for key, raw in legacy["attributes"].items():
        if key == "storage" and isinstance(raw, str):
            match = re.fullmatch(r"(\d{1,4})(GB|TB)", raw)
            if not match:
                continue
            value = {"value_type": "integer", "value": int(match.group(1)), "unit": match.group(2)}
        elif key in {"condition", "personalisation"} and isinstance(raw, str) and raw:
            value = {"value_type": "string", "value": raw, "unit": None}
        else:
            continue
        assertions.append(
            {
                "attribute_key": key,
                "state": "known",
                "value": value,
                "evidence": [evidence_factory(key, "explicit_attribute_lexeme", "weak_text")],
            }
        )
    return assertions


def _relationships(legacy: Mapping[str, Any], evidence_factory) -> tuple[list[dict[str, Any]], bool]:
    assertions: list[dict[str, Any]] = []
    dropped = False
    for relation in legacy["relationships"]:
        relation_type = _RELATION_MAP.get(relation.get("type"))
        target = relation.get("target_text")
        if relation_type is None or not isinstance(target, str) or not target or len(target) > 512:
            dropped = True
            continue
        assertions.append(
            {
                "relationship_type": relation_type,
                "target_state": "observed_text",
                "target_variant_id": None,
                "target_text": target,
                "evidence": [evidence_factory("compatibility", "explicit_relationship_lexeme", "weak_text")],
            }
        )
    return assertions, dropped


def _facets(text: str, evidence_factory) -> dict[str, list[dict[str, Any]]]:
    result = {
        "use_case": [],
        "audience": [],
        "compatibility": [],
        "style": [],
        "material": [],
        "season": [],
        "occasion": [],
        "function": [],
    }
    for family, rules in _FACET_RULES.items():
        for pattern, key, label in rules:
            if re.search(pattern, text, re.IGNORECASE):
                result[family].append(
                    _known_concept(
                        key,
                        label,
                        evidence_factory(family, "explicit_facet_lexeme", "weak_text"),
                    )
                )
    return result


def extract_product_ontology(
    row: Mapping[str, Any],
    *,
    raw_source_record_id: int,
    source_type: str,
    source_ref: str,
    observed_at: datetime,
    evaluated_at: datetime,
    offer_id: int,
    variant_id: int | None,
) -> dict[str, Any]:
    """Projette une offre en assertion v1 sans write ni fallback favorable."""

    if not isinstance(row, Mapping):
        raise ProductOntologyExtractionError("row must be an object")
    raw_id = _positive_identifier(raw_source_record_id, "raw_source_record_id")
    offer = _positive_identifier(offer_id, "offer_id")
    if variant_id is not None:
        _positive_identifier(variant_id, "variant_id")
    if not isinstance(source_type, str) or not source_type or len(source_type) > 48:
        raise ProductOntologyExtractionError("source_type is invalid")
    if not isinstance(source_ref, str) or not source_ref or len(source_ref) > 255:
        raise ProductOntologyExtractionError("source_ref is invalid")
    observed = _aware(observed_at, "observed_at")
    evaluated = _aware(evaluated_at, "evaluated_at")
    if observed > evaluated:
        raise ProductOntologyExtractionError("observed_at cannot be after evaluated_at")

    title = _text(row, "product_name", "name") or ""
    merchant_category = _text(row, "merchant_category", "category")
    brand = _text(row, "brand_name", "brand")
    offer_kind = _text(row, "offer_kind")
    source_text = " ".join(value for value in (title, merchant_category or "") if value).strip()
    # La catégorie marchande alimente uniquement le mapping legacy ci-dessous.
    # Elle ne peut pas décider du rôle de l'objet vendu : un flux « Software »
    # peut contenir un laptop, comme un flux « Smartphones » peut contenir une
    # coque. Le rôle et les relations exigent donc un signal dans le titre.
    legacy = legacy_roles.understand_offer(
        name=title or None,
        merchant_category=None,
        brand=brand,
        offer_kind=offer_kind,
    )

    def evidence_factory(field: str, transformation: str, strength: str) -> dict[str, Any]:
        return _evidence(
            raw_source_record_id=raw_id,
            source_type=source_type,
            source_ref=source_ref,
            observed_at=observed,
            field=field,
            transformation=transformation,
            strength=strength,
        )

    product_type = _product_type(source_text)
    if product_type is None:
        classification = {
            "category": _unknown_concept(),
            "subcategory": _unknown_concept(),
            "product_type": _unknown_concept(),
        }
        expected_legacy = None
    else:
        category_key, category_label, subcategory_key, subcategory_label, type_key, type_label, expected_legacy = product_type
        classification = {
            "category": _known_concept(category_key, category_label, evidence_factory("category", "explicit_product_type_mapping", "weak_text")),
            "subcategory": _known_concept(subcategory_key, subcategory_label, evidence_factory("subcategory", "explicit_product_type_mapping", "weak_text")),
            "product_type": _known_concept(type_key, type_label, evidence_factory("product_type", "explicit_product_type_mapping", "weak_text")),
        }

    role = _role(
        title=title,
        source_text=source_text,
        offer_kind=offer_kind,
        legacy=legacy,
        evidence_factory=evidence_factory,
    )
    relationships, relationship_dropped = _relationships(legacy, evidence_factory)
    attributes = _attributes(legacy, evidence_factory)
    facets = _facets(source_text, evidence_factory)

    legacy_category = taxonomy.classify(merchant_category, title or None, brand, _text(row, "merchant_name"))
    legacy_subcategory = taxonomy.classify_subcategory(
        legacy_category,
        title or None,
        merchant_category,
        _text(row, "merchant_name"),
    )
    if legacy_category is None:
        migration_state = "unmapped"
        legacy_evidence: list[dict[str, Any]] = []
    elif expected_legacy is not None and legacy_category == expected_legacy:
        migration_state = "mapped_exact"
        legacy_evidence = [evidence_factory("legacy_category", "legacy_taxonomy_projection", "legacy_fallback")]
    elif product_type is not None:
        migration_state = "mapped_partial"
        legacy_evidence = [evidence_factory("legacy_category", "legacy_taxonomy_projection", "legacy_fallback")]
    else:
        migration_state = "fallback_only"
        legacy_evidence = [evidence_factory("legacy_category", "legacy_taxonomy_projection", "legacy_fallback")]

    reasons: list[str] = []
    if variant_id is None:
        status = "QUARANTINED"
        reasons.append("identity_unresolved")
    else:
        missing_category = classification["category"]["state"] != "known"
        missing_type = classification["product_type"]["state"] != "known"
        missing_role = role["state"] != "known"
        if not (missing_category or missing_type or missing_role):
            status = "VERIFIED"
            reasons.append("ontology_verified")
        else:
            status = "PARTIAL"
            if missing_category:
                reasons.append("category_unknown")
            if missing_type:
                reasons.append("product_type_unknown")
            if missing_role:
                reasons.append("product_role_unknown")
    if relationship_dropped:
        reasons.append("relationship_target_unresolved")
    if migration_state == "fallback_only":
        reasons.append("legacy_fallback_only")

    return {
        "contract_version": "1.0.0",
        "raw_source_record_id": raw_id,
        "offer_id": offer,
        "variant_id": variant_id,
        "ontology_status": status,
        "classification": classification,
        "product_role": role,
        "attributes": attributes,
        "relationships": relationships,
        "facets": facets,
        "legacy_taxonomy": {
            "category": legacy_category,
            "subcategory": legacy_subcategory,
            "migration_state": migration_state,
            "evidence": legacy_evidence,
        },
        "reason_codes": list(dict.fromkeys(reasons)),
        "extractor_version": EXTRACTOR_VERSION,
        "policy_version": POLICY_VERSION,
        "evaluated_at": _iso(evaluated),
    }
