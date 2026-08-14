"""Compréhension minimale et explicable de l'objet réellement vendu.

Ce service ne résout pas encore une entité canonique et ne rapproche jamais deux
produits. Il décrit une *offre* à partir de ses libellés observés : rôle de
l'objet vendu, relations textuelles (compatibilité/remplacement) et attributs
commerciaux explicites. Une relation conserve donc un `target_text`, jamais un
identifiant produit imaginé.

Le périmètre v1 couvre les signaux les plus dangereux pour un comparateur :
coques, protections d’écran, pièces de remplacement, consommables, bundles et
tarifs contextuels. Tout autre cas reste `main_product` ou `unknown` selon la
preuve disponible.
"""

from __future__ import annotations

import re
from typing import Any

VERSION = "product-role-v1"

MAIN_PRODUCT = "main_product"
ACCESSORY = "accessory"
PROTECTIVE_CASE = "protective_case"
SCREEN_PROTECTOR = "screen_protector"
CHARGER = "charger"
CABLE = "cable"
BATTERY = "battery"
REPLACEMENT_PART = "replacement_part"
CONSUMABLE = "consumable"
ADAPTER = "adapter"
STAND = "stand"
MOUNT = "mount"
HOLDER = "holder"
BAG = "bag"
BUNDLE = "bundle"
SOFTWARE = "software"
SERVICE = "service"
SUBSCRIPTION = "subscription"
UNKNOWN = "unknown"

# Ce sont des relations entre le bien vendu et une cible mentionnée. Elles
# restent en texte tant que l’identité de cette cible n’est pas elle-même
# démontrée par les identifiants et le moteur de résolution.
COMPATIBLE_WITH = "compatible_with"
REPLACEMENT_FOR = "replacement_for"
INCLUDED_IN = "included_in"

# Les morceaux après les prépositions commerciales sont souvent la meilleure
# preuve de cible. Les bornes arrêtent le match avant les séparateurs de titre
# ou les conditions marketing ; la cible complète est conservée telle qu’elle
# a été observée, avec une normalisation d’espaces seulement.
_RELATION_PATTERNS: tuple[tuple[str, str], ...] = (
    (REPLACEMENT_FOR, r"\b(?:replacement|replace(?:ment)?|vervang(?:end|ing)?|remplacement)\s+(?:part|battery|batter(?:y|ie)|screen|display|scherm|pi[èe]ce)?\s*(?:for|pour)\s+(.+?)(?:\s*[-–|,;]|$)"),
    # La forme de l’objet vendu sert de borne : dans « compatible ink cartridge
    # for HP … », la cible est HP, pas la cartouche elle-même.
    (COMPATIBLE_WITH, r"\b(?:case|cover|coque|screen\s+protector|screenprotector|glass|verre|cartridge|cartouche)\b.*?\b(?:for|pour|compatible(?:\s+(?:with|avec))?)\s+(.+?)(?:\s*[-–|,;]|$)"),
    # Repli général seulement pour les formulations à relation explicite.
    (COMPATIBLE_WITH, r"\b(?:compatible\s+(?:with|avec)|geschikt\s+voor|pour)\s+(.+?)(?:\s*[-–|,;]|$)"),
)

_ROLE_PATTERNS: tuple[tuple[str, str], ...] = (
    (PROTECTIVE_CASE, r"\b(?:coques?|cases?|covers?|hoesjes?|h[üu]lles?)\b"),
    (SCREEN_PROTECTOR, r"\b(?:screen\s*protectors?|screenprotectors?|verres?\s+tremp[ée]s?|tempered\s+glass|beschermglas)\b"),
    (REPLACEMENT_PART, r"\b(?:replacement|replac(?:e|ement)|vervang(?:end|ing)?|pi[èe]ces?\s+d[ée]tach[ée]es?|spare\s+parts?|onderdelen?)\b"),
    (BATTERY, r"\b(?:batter(?:y|ies)|batterie(?:s)?)\b"),
    (CHARGER, r"\b(?:chargers?|chargeurs?|opladers?)\b"),
    (CABLE, r"\b(?:cables?|c[âa]bles?|kabels?)\b"),
    (CONSUMABLE, r"\b(?:ink\s+cartridges?|cartouches?\s+d['’ ]encre|toners?|filters?|filtres?|patrons?\s+de\s+couture|sewing\s+patterns?)\b"),
    (BAG, r"\b(?:sacs?\s+[àa]\s+dos|backpacks?|rugzakken?|handbags?|sacs?)\b"),
    (ACCESSORY, r"\b(?:casquettes?|caps?|hats?|chapeaux?)\b"),
    (ADAPTER, r"\b(?:adaptateurs?|adapters?)\b"),
    (STAND, r"\b(?:stands?|socles?|docks?)\b"),
    (MOUNT, r"\b(?:mounts?|montages?|fixations?)\b"),
    (HOLDER, r"\b(?:holders?|supports?)\b"),
    (SOFTWARE, r"\b(?:software|logiciels?|licen[cs]es?)\b"),
    (SUBSCRIPTION, r"\b(?:subscriptions?|abonnements?)\b"),
)

_BUNDLE_PATTERN = r"\b(?:bundle|bundles|kits?|sets?|lot(?:s)?|maxi[-\s]?set|(?:starter|accessory|multi)[-\s]?packs?|packs?\s+of)\b"
_QUANTITY_PATTERN = r"\b(\d{1,2})\s*(?:x\s*)?(?:controllers?|manettes?|pi[èe]ces?|pcs?|pieces?)\b"
_STORAGE_PATTERN = r"\b(\d{2,4})\s*(gb|tb)\b"
_CONDITION_PATTERN = r"\b(refurbished|reconditionn[ée]|renewed|used|occasion)\b"
_ENGRAVING_PATTERN = r"\b(?:gravure|engraved|gegraveerd|personalized|personnalis[ée])\b"


def _normalise_target(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" .:-–|")


def _text(*values: str | None) -> str:
    return " ".join(value.strip() for value in values if value and value.strip())


def _relationship(text: str) -> dict[str, str] | None:
    for relation, pattern in _RELATION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        target = _normalise_target(match.group(1))
        if target:
            return {"type": relation, "target_text": target, "state": "observed"}
    return None


def _role(text: str, offer_kind: str | None) -> tuple[str, str]:
    """Retourne le rôle et la confiance, sans déduire un objet absent du texte."""
    if offer_kind in {"accommodation", "service"}:
        return SERVICE, "high"
    if offer_kind == "digital_content":
        return SOFTWARE, "high"
    # Une forme explicite (sac, coque, pièce…) prévaut sur un mot commercial
    # présent dans le nom de modèle, par exemple « Modular Pack » pour un sac.
    for role, pattern in _ROLE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return role, "high"
    if re.search(_BUNDLE_PATTERN, text, re.IGNORECASE):
        return BUNDLE, "high"
    # Une offre physique sans signal contradictoire a le droit d’être un produit
    # principal ; ce n’est toutefois pas une identité canonique ni une fusion.
    if offer_kind in {None, "physical_product"}:
        return MAIN_PRODUCT, "medium"
    return UNKNOWN, "low"


def _attributes(text: str) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    storage = re.search(_STORAGE_PATTERN, text, re.IGNORECASE)
    if storage:
        attributes["storage"] = f"{storage.group(1)}{storage.group(2).upper()}"
    condition = re.search(_CONDITION_PATTERN, text, re.IGNORECASE)
    if condition:
        value = condition.group(1).lower()
        attributes["condition"] = "refurbished" if value in {"refurbished", "reconditionné", "reconditionnee", "renewed"} else "used"
    if re.search(_ENGRAVING_PATTERN, text, re.IGNORECASE):
        attributes["personalisation"] = "engraving"
    return attributes


def _components(text: str, role: str) -> list[dict[str, Any]]:
    if role != BUNDLE:
        return []
    quantity = re.search(_QUANTITY_PATTERN, text, re.IGNORECASE)
    if quantity:
        return [{"type": "controller", "quantity": int(quantity.group(1)), "state": "observed"}]
    return []


def understand_offer(
    *,
    name: str | None,
    merchant_category: str | None = None,
    brand: str | None = None,
    offer_kind: str | None = None,
) -> dict[str, Any]:
    """Produit une compréhension explicable et non destructive d'une offre.

    Les valeurs retournées ne sont que des faits textuellement supportés ou un
    rôle `main_product` prudent. Aucune entité produit existante n’est modifiée
    et aucune relation ne pointe vers une identité canonique non vérifiée.
    """
    title = (name or "").strip()
    text = _text(title, merchant_category)
    if not text:
        return {
            "version": VERSION,
            "product_role": UNKNOWN,
            "confidence": "low",
            "attributes": {},
            "relationships": [],
            "components": [],
            "evidence": [],
            "missing": ["product_name"],
        }

    role, confidence = _role(text, offer_kind)
    # La catégorie source ne doit jamais prolonger une cible de compatibilité :
    # « … for HP DeskJet 4120e » sous « Computer & Office » reste HP DeskJet
    # 4120e, et non « HP DeskJet 4120e Computer & Office ».
    relation = _relationship(title)
    relationships = [relation] if relation else []
    attributes = _attributes(text)
    components = _components(text, role)
    evidence: list[dict[str, Any]] = [
        {
            "field": "product_role",
            "state": "observed" if role != UNKNOWN else "missing",
            "source": "offer_title_and_category",
            "method": VERSION,
            "value": role if role != UNKNOWN else None,
        }
    ]
    if relation:
        evidence.append(
            {
                "field": relation["type"],
                "state": "observed",
                "source": "offer_title",
                "method": VERSION,
                "value": {"target_text": relation["target_text"]},
            }
        )
    for key, value in attributes.items():
        evidence.append(
            {
                "field": key,
                "state": "observed",
                "source": "offer_title",
                "method": VERSION,
                "value": value,
            }
        )
    for component in components:
        evidence.append(
            {
                "field": "included_component",
                "state": "observed",
                "source": "offer_title",
                "method": VERSION,
                "value": component,
            }
        )

    missing: list[str] = []
    if not brand:
        missing.append("brand")
    if not relationships and role in {PROTECTIVE_CASE, SCREEN_PROTECTOR, REPLACEMENT_PART, CONSUMABLE}:
        missing.append("compatibility_target")
    if role == BUNDLE and not components:
        missing.append("bundle_components")
    return {
        "version": VERSION,
        "product_role": role,
        "confidence": confidence,
        "attributes": attributes,
        "relationships": relationships,
        "components": components,
        "evidence": evidence,
        "missing": missing,
    }
