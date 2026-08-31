"""Adaptateur lecture seule entre le catalogue FILON Core et les experts.

Aucune écriture, aucun appel affilié et aucun enrichissement marchand ne se fait
ici. Le retrieval Fashion utilise les rayons FILON *et* une preuve lexicale de
pièce : une erreur de classement isolée ne peut donc pas devenir une tenue.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace

from sqlalchemy import func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.intelligence.contracts import CoreOfferSnapshot
from app.services import taxonomy
from app.services.catalog_paging import fetch_all_offer_rows
from app.services.offer_evidence import load_offer_evidence


FASHION_CATEGORIES = frozenset(taxonomy.categories_of_department("Mode & Accessoires"))

_PRODUCT_WORDS = frozenset({
    "robe", "robes", "dress", "dresses", "jurk", "jurken",
    "veste", "vestes", "blazer", "blazers", "jacket", "jackets", "jas", "jassen", "manteau", "manteaux", "coat", "coats",
    "jupe", "jupes", "skirt", "skirts", "rok", "rokken",
    "pantalon", "pantalons", "jean", "jeans", "broek", "broeken", "pants",
    "chemise", "chemises", "shirt", "shirts", "hemd", "hemden", "tshirt", "t-shirt", "top", "tops",
    "chaussure", "chaussures", "shoe", "shoes", "schoen", "schoenen", "sneaker", "sneakers", "basket", "baskets",
    "sac", "sacs", "bag", "bags", "tas", "tassen", "handbag", "handtas",
})

# Une catégorie seule n’est pas une preuve de pièce : l’historique a déjà montré
# des accessoires de vestiaire dans « Robes » et des objets techniques dans
# « Chaussures ». Le nom ou la marque doit aussi porter un terme explicite.
_SCOPE_TERMS: dict[str, frozenset[str]] = {
    "dress": frozenset({"robe", "robes", "dress", "dresses", "jurk", "jurken"}),
    "outerwear": frozenset({"veste", "vestes", "blazer", "blazers", "jacket", "jackets", "jas", "jassen", "manteau", "manteaux", "coat", "coats"}),
    "skirt": frozenset({"jupe", "jupes", "skirt", "skirts", "rok", "rokken"}),
    "trouser": frozenset({"pantalon", "pantalons", "jean", "jeans", "broek", "broeken", "pants"}),
    "top": frozenset({"chemise", "chemises", "shirt", "shirts", "hemd", "hemden", "tshirt", "top", "tops"}),
    "footwear": frozenset({"chaussure", "chaussures", "shoe", "shoes", "schoen", "schoenen", "sneaker", "sneakers", "basket", "baskets", "boot", "boots", "botte", "bottes"}),
    "bag": frozenset({"sac", "sacs", "bag", "bags", "tas", "tassen", "handbag", "handtas", "pochette", "clutch"}),
}

# Une erreur historique de sous-rayon peut faire passer une parure dont le titre
# cite « dress » dans les Robes. Ces objets ne sont jamais une pièce principale :
# l’exclusion est limitée aux termes de joaillerie explicites et vérifiés.
_SCOPE_EXCLUSIONS: dict[str, frozenset[str]] = {
    "outerwear": frozenset({
        # « jacket » peut qualifier un sous-vêtement ou une couche technique.
        # Ces objets ne peuvent jamais remplir le rôle d’un blazer, d’une veste
        # ou d’un manteau dans Outfit Studio.
        "underwear", "lingerie", "crotch", "bra", "bralette", "panty", "panties",
        "culotte", "soutien", "gorge", "shapewear", "body shaper", "bodysuit",
    }),
    "dress": frozenset({
        "jewellery", "jewelry", "necklace", "necklaces", "earring", "earrings",
        "bracelet", "bracelets", "ring", "rings", "tiara", "brooch", "brooches",
        "collier", "colliers", "boucle", "boucles", "bague", "bagues",
        # Une destination « wedding dress » sur un sous-vêtement décrit l’usage
        # prévu, non une robe vendue comme pièce principale.
        "bra", "bras", "underwear", "lingerie", "bralette", "soutien", "gorge",
        # Les accessoires de silhouette décrivent une sous-couche ou un maintien,
        # non la robe demandée, même si le feed cite « wedding dress » comme usage.
        "shaper", "shapewear", "tummy", "waist trainer", "body shaper",
        # Les accessoires de cérémonie peuvent répéter « wedding dress » pour
        # leur destination : un voile ou un lot d’accessoires ne devient pas une robe.
        "veil", "voile", "accessory", "accessories", "bridal veil",
    }),
}


def _availability(in_stock: bool | None) -> str:
    if in_stock is True:
        return "in_stock"
    if in_stock is False:
        return "out_of_stock"
    return "unknown"


def _words(value: str | None) -> set[str]:
    return set(re.findall(r"[\wÀ-ÿ'-]+", (value or "").lower()))


def _search_terms(query: str | None) -> set[str]:
    return _words(query) & _PRODUCT_WORDS


def _fashion_scopes(query: str | None) -> list[str]:
    """Scopes Core indexables déclenchés uniquement par une pièce explicite."""
    terms = _search_terms(query)
    scopes: list[str] = []
    if terms & _SCOPE_TERMS["dress"]:
        scopes.append("dress")
    if terms & _SCOPE_TERMS["outerwear"]:
        scopes.append("outerwear")
    if terms & _SCOPE_TERMS["skirt"]:
        scopes.append("skirt")
    if terms & _SCOPE_TERMS["trouser"]:
        scopes.append("trouser")
    if terms & _SCOPE_TERMS["top"]:
        scopes.append("top")
    if terms & _SCOPE_TERMS["footwear"]:
        scopes.append("footwear")
    if terms & _SCOPE_TERMS["bag"]:
        scopes.append("bag")
    return scopes


# Une intention de mariage est le seul contexte sans pièce qui peut déclencher
# un retrieval M1 : les titres de robes portent explicitement cette occasion.
# Le fallback reste volontairement réduit à une base, des chaussures et un sac ;
# il ne transforme jamais une autre occasion en tenue supposée.
_OCCASION_FALLBACK_SCOPES: dict[str, tuple[str, ...]] = {
    "wedding": ("dress", "footwear", "bag"),
}

_OCCASION_TERMS: dict[str, frozenset[str]] = {
    # Seul le mariage est assez explicitement exprimé dans les titres Fashion
    # pour constituer un filtre M1. Les autres occasions restent visibles comme
    # contexte utilisateur et non comme une compatibilité prétendument prouvée.
    "wedding": frozenset({"wedding", "bridal", "bride", "mariage", "mariée", "mariée", "trouw", "bruids"}),
}


def _retrieval_scopes(query: str | None, occasion: str | None) -> list[str]:
    """Détermine les pièces à chercher, avec fallback mariage explicite seulement."""
    scopes = _fashion_scopes(query)
    if scopes:
        return scopes
    return list(_OCCASION_FALLBACK_SCOPES.get(occasion or "", ()))


def _occasion_clause(occasion: str | None):
    """Filtre SQL de l’occasion uniquement lorsqu’elle est prouvable dans le titre."""
    terms = _OCCASION_TERMS.get(occasion or "")
    if not terms:
        return None
    lowered_name = func.lower(models.Offer.name)
    lowered_brand = func.lower(models.Offer.brand)
    return or_(
        *[
            or_(lowered_name.contains(term), lowered_brand.contains(term))
            for term in terms
        ]
    )


def _scope_title_clause(scope: str):
    """Preuve SQL de pièce identique à celle vérifiée ensuite par `_matches_scope`."""
    terms = _SCOPE_TERMS[scope]
    lowered_name = func.lower(func.coalesce(models.Offer.name, ""))
    lowered_brand = func.lower(func.coalesce(models.Offer.brand, ""))
    return or_(*[
        or_(lowered_name.contains(term), lowered_brand.contains(term))
        for term in terms
    ])


def _scope_exclusion_clause(scope: str):
    """Objets incompatibles avec le rôle de pièce demandé, directement en SQL."""
    excluded = _SCOPE_EXCLUSIONS.get(scope, frozenset())
    if not excluded:
        return None
    # `brand` est fréquemment NULL dans les flux : sans coalesce, `false OR
    # NULL` devient NULL en SQL puis élimine aussi les vraies robes.
    lowered_name = func.lower(func.coalesce(models.Offer.name, ""))
    lowered_brand = func.lower(func.coalesce(models.Offer.brand, ""))
    return not_(or_(*[
        or_(lowered_name.contains(term), lowered_brand.contains(term))
        for term in excluded
    ]))


def _scope_clause(scope: str):
    if scope == "dress":
        return models.Offer.filon_subcategory == "Robes"
    if scope == "outerwear":
        return models.Offer.filon_subcategory == "Manteaux & Vestes"
    if scope == "skirt":
        return models.Offer.filon_subcategory == "Jupes"
    if scope == "trouser":
        return models.Offer.filon_subcategory == "Pantalons & Jeans"
    if scope == "top":
        return models.Offer.filon_subcategory == "Hauts & T-shirts"
    if scope == "footwear":
        return models.Offer.filon_category == taxonomy.CHAUSSURES
    if scope == "bag":
        return models.Offer.filon_category.in_((taxonomy.BAGAGERIE, taxonomy.ACCESSOIRES))
    raise ValueError(f"Unknown Fashion scope: {scope}")


def _matches_scope(scope: str, offer: models.Offer, occasion: str | None = None) -> bool:
    terms = _words(offer.name) | _words(offer.brand)
    if not terms & _SCOPE_TERMS[scope]:
        return False
    if terms & _SCOPE_EXCLUSIONS.get(scope, frozenset()):
        return False
    occasion_terms = _OCCASION_TERMS.get(occasion or "")
    # Une paire de chaussures complémentaire n'a pas besoin de répéter
    # « wedding » : la preuve porte alors sur la pièce principale. En revanche,
    # une robe de mariage doit nommer l’occasion explicitement.
    if occasion_terms and scope in {"dress", "outerwear", "skirt", "trouser", "top"}:
        return bool(terms & occasion_terms)
    return True


def _base_statement():
    return (
        select(models.Offer, models.Merchant)
        .join(models.Merchant, models.Offer.merchant_id == models.Merchant.id)
        .where(
            models.Offer.filon_category.in_(FASHION_CATEGORIES),
            models.Offer.offer_kind == taxonomy.PHYSICAL_PRODUCT,
            models.Offer.is_canonical.is_(True),
            # Même règle que le catalogue public : les lignes historiques sans
            # marquage sont visibles, les offres explicitement adultes ne le sont jamais.
            or_(models.Offer.is_adult.is_(False), models.Offer.is_adult.is_(None)),
            models.Offer.price.isnot(None),
            models.Offer.currency.isnot(None),
            models.Offer.image_url.isnot(None),
            models.Offer.image_url != "",
            or_(models.Offer.in_stock.is_(True), models.Offer.in_stock.is_(None)),
        )
    )


def _snapshot(offer: models.Offer, merchant: models.Merchant) -> CoreOfferSnapshot:
    return CoreOfferSnapshot(
        offer_id=offer.id,
        catalog_product_id=offer.product_id,
        name=offer.name,
        brand=offer.brand,
        filon_category=offer.filon_category,
        filon_subcategory=offer.filon_subcategory,
        offer_kind=offer.offer_kind,
        price=offer.price,
        currency=offer.currency,
        availability=_availability(offer.in_stock),
        image_url=offer.image_url,
        deep_link=offer.deep_link,
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        merchant_region=merchant.region,
        # Une mutation technique de l'offre ne constitue pas un relevé source.
        observed_at=None,
    )


async def retrieve_fashion_offers(
    session: AsyncSession,
    *,
    query: str | None = None,
    occasion: str | None = None,
    limit: int = 120,
) -> list[CoreOfferSnapshot]:
    """Retourne des offres Fashion admissibles sans modifier le Core.

    Le contrat M1 est strict : offre physique, publique, canonique, non adulte,
    avec image et prix, puis correspondance à la fois taxonomique et lexicale.
    Sans pièce explicitement nommée, le moteur s’abstient, sauf pour un mariage :
    une robe de mariage est alors une pièce principale explicitement prouvée par
    son titre, pas une déduction stylistique.
    """
    scopes = _retrieval_scopes(query, occasion)
    if not scopes:
        return []

    # `limit` était un plafond de récupération (120, au plus 180) : il coupait
    # une recherche avant que la composition ne puisse comparer toutes les pièces
    # admissibles. Il est maintenu dans la signature pour compatibilité appelant,
    # mais ne limite plus la lecture catalogue ; seul l’affichage final est borné.
    del limit
    explicit_scopes = set(_fashion_scopes(query))
    seen: set[int] = set()
    snapshots: list[CoreOfferSnapshot] = []
    for scope in scopes:
        # Une offre est éligible uniquement si le titre ou la marque prouve la
        # pièce demandée. Ce filtre reprenait auparavant après la lecture, ce qui
        # faisait transiter des milliers d’intrus de rayon sans élargir la
        # couverture réelle. Il est maintenant appliqué avant la pagination.
        stmt = _base_statement().where(_scope_clause(scope), _scope_title_clause(scope))
        scope_exclusion_clause = _scope_exclusion_clause(scope)
        if scope_exclusion_clause is not None:
            stmt = stmt.where(scope_exclusion_clause)
        # Lorsqu’une pièce n’est pas explicitement demandée, un complément de
        # mariage doit porter un marqueur cérémoniel dans son propre titre. C’est
        # exactement le contrat de `_matches_requested_piece` dans la composition
        # finale : on réduit seulement les intrus, jamais les offres admissibles.
        if occasion == "wedding" and (scope == "dress" or scope not in explicit_scopes):
            occasion_clause = _occasion_clause(occasion)
            if occasion_clause is not None:
                stmt = stmt.where(occasion_clause)
        # Lecture exhaustive par lots : aucune offre du rayon admissible n’est
        # perdue avant le filtrage lexical et la composition Outfit Studio.
        rows = await fetch_all_offer_rows(session.execute, stmt)
        for offer, merchant in rows:
            if offer.id in seen or not _matches_scope(scope, offer, occasion):
                continue
            seen.add(offer.id)
            snapshots.append(_snapshot(offer, merchant))
    evidence_by_offer = await load_offer_evidence(
        session,
        list(snapshots),
        current_only=True,
    )
    return [
        replace(
            snapshot,
            currency=evidence_by_offer.get(snapshot.offer_id).currency,
            observed_at=evidence_by_offer.get(snapshot.offer_id).current_observed_at,
        )
        if snapshot.offer_id in evidence_by_offer
        else replace(snapshot, currency=None, observed_at=None)
        for snapshot in snapshots
    ]
