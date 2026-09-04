"""Recherche dans le catalogue interne FILON pour l'assistant.

Interroge la base de données (1,3M offres, 207 marchands) au lieu de Google Shopping.
Retourne des produits réels avec prix, marchand, image, lien affilié Awin.

Priorité : base interne > SerpApi (fallback).
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, not_, or_, select

from app.core.logging import get_logger
from app.core.observability import traced_dependency, traced_pipeline_stage
from app.db.session import session_scope
from app.db.models import Merchant, Offer
from app.intelligence.contracts import CoreOfferSnapshot
from app.intelligence.general_catalog import retrieve_general_offers
from app.intelligence.general_decision import compose_general_plan
from app.intelligence.intent_resolution import GeneralIntent, resolve_intent, resolve_intent_with_fallback
from app.services import decision, taxonomy
from app.services.catalog_paging import fetch_all_offer_rows
from app.services.currency import normalize_currency_code
from app.services.freshness import offer_observation_is_fresh
from app.services.offer_evidence import load_offer_evidence
from app.services.search import search_clause, terms_of

log = get_logger("catalog_search")


# Une requête d'assistant est rarement un titre de produit : « un ordinateur
# portable étudiant sous 800 € » contient une intention, un budget et des mots
# qui ne figurent jamais dans un feed. Les ancres ci-dessous servent uniquement
# à resserrer une recherche vers le rayon demandé ; elles ne fabriquent aucun
# résultat et ne font appel à aucune source externe.
_INTENT_ANCHORS: tuple[tuple[tuple[str, ...], str, tuple[str, ...]], ...] = (
    (
        ("ordinateur", "laptop", "notebook", "macbook", "computer", "pc portable", "montage", "video editing", "videomontage"),
        "laptop",
        ("housse", "hoes", "sleeve", "pochette", "sac", "support", "stand", "chargeur", "charger", "cable", "adaptateur", "keyboard", "clavier", "souris", "mouse"),
    ),
    (
        ("smartphone", "telephone", "telefoon", "iphone", "android"),
        "smartphone",
        # Les flux mélangent les pièces et l'appareil complet. Ces termes sont
        # exclus pour une demande de téléphone, sauf si l'utilisateur demande
        # explicitement une pièce dans sa requête (voir `_catalogue_intent`).
        ("coque", "case", "cover", "hoes", "protection", "protector", "verre", "glass", "chargeur", "charger", "cable", "adaptateur", "support", "ecran", "écran", "screen", "batterie", "battery", "adhesif", "adhésif", "kit", "piece", "pièce", "repair", "reparation", "réparation", "plaque", "pcb", "swap", "echange", "échange", "service pack", "cadre", "frame"),
    ),
    (
        ("casque", "headphone", "koptelefoon", "noise cancelling", "noise-cancelling"),
        "casque",
        ("housse", "hoes", "case", "cable", "adaptateur", "support", "earpad", "coussin", "ecouteur", "écouteur", "earbud", "in-ear", "in ear", "intra"),
    ),
    (
        ("machine a cafe", "machine à café", "cafetiere", "cafetière", "coffee machine", "koffiezetapparaat", "koffiemachine", "espresso", "cafe", "café", "coffee", "koffie"),
        "coffee_machine",
        ("capsule", "capsules", "dosette", "dosettes", "filtre", "filtres", "mug", "tasse", "tasses"),
    ),
    (
        ("aspirateur robot", "robot aspirateur", "robot vacuum", "robotstofzuiger", "roomba"),
        "robot_vacuum",
        ("filtre", "filter", "brosse", "brush", "serpillere", "serpillière", "mop", "sac", "bag", "batterie", "battery", "chargeur", "charger", "telecommande", "télécommande", "remote"),
    ),
)


# Un flux peut publier un prix technique (1 €) ou une garantie sous un nom de
# produit. Ces seuils ne donnent pas une valeur de marché : ils empêchent
# seulement qu'un produit principal soit présenté à un prix invraisemblable.
_PRIMARY_MIN_PRICE = {"laptop": 200.0, "smartphone": 80.0, "casque": 25.0, "coffee_machine": 30.0, "robot_vacuum": 80.0}

# Une occurrence textuelle de « smartphone » apparaît fréquemment dans des
# accessoires, ou dans la compatibilité d’un appareil tiers. L’assistant ne
# peut recommander un produit principal que si le Core le place aussi dans le
# sous-rayon public correspondant. Le garde-fou reste limité aux ancres dont
# la taxonomie est stable et vérifiable.
_INTENT_PRIMARY_SCOPE: dict[str, tuple[str, str]] = {
    "laptop": (taxonomy.INFORMATIQUE, "Ordinateurs portables"),
    "smartphone": (taxonomy.TELEPHONIE, "Smartphones"),
    "casque": (taxonomy.TV_SON, "Casques audio"),
    "coffee_machine": (taxonomy.ELECTROMENAGER, "Petit électroménager"),
    "robot_vacuum": (taxonomy.ELECTROMENAGER, "Aspirateurs"),
}


def _intent_primary_scope(anchor: str):
    """Retourne le filtre Core du produit principal, jamais celui d’un accessoire."""
    scope = _INTENT_PRIMARY_SCOPE.get(anchor)
    if not scope:
        return None
    category, subcategory = scope
    return and_(Offer.filon_category == category, Offer.filon_subcategory == subcategory)


def _intent_primary_impostor_terms(anchor: str) -> tuple[str, ...]:
    """Objets explicitement incompatibles avec un téléphone complet.

    Le Core peut contenir une erreur historique de taxonomie. Ces termes bornés
    aux intrus observés protègent donc l’Assistant sans supprimer des offres
    ambiguës du catalogue général ; le reclassement reste la correction durable.
    """
    return taxonomy.PHONE_PRIMARY_IMPOSTOR_TERMS if anchor == "smartphone" else ()


# Lorsqu’un visiteur cite une gamme ou une marque non ambiguë, l’ancre de rayon
# ne suffit pas. Retourner un autre smartphone que l’iPhone demandé est pire
# qu’un état « aucune offre vérifiée » : la contrainte doit donc être présente
# dans le titre que le marchand a effectivement fourni.
_COFFEE_AUTOMATIC_TERMS = ("automatique", "automatic", "automatisch", "volautomatisch")
_COFFEE_SEMI_AUTOMATIC_TERMS = (
    "semi-automatique", "semi automatique", "semiautomatique",
    "semi-automatic", "semi automatic", "semiautomatic",
    "half automatisch", "half-automatisch", "handmatig", "manual",
)


_EXACT_PRODUCT_TERMS = (
    "iphone", "ipad", "macbook", "airpods", "galaxy", "playstation",
    "xbox", "nintendo", "dyson",
)


def _required_name_terms(query: str, anchor: str) -> tuple[str, ...]:
    """Contraintes explicites que le titre du produit doit confirmer.

    Une demande « réduction de bruit » ne peut pas être satisfaite par un casque
    Bluetooth ordinaire. Si le feed ne porte pas cette caractéristique, l'absence
    d'offre vérifiée est plus honnête qu'une recommandation hors besoin.
    """
    normalized = " ".join(terms_of(query))
    exact = tuple(term for term in _EXACT_PRODUCT_TERMS if term in normalized)
    if exact:
        # « iPhone 15 » ne désigne pas n'importe quel iPhone. Le numéro ne doit
        # devenir une contrainte que lorsqu'il suit directement la gamme, pour
        # ne pas confondre un budget ou un nombre de stockage avec un modèle.
        if "iphone" in exact:
            tokens = terms_of(query)
            try:
                iphone_index = tokens.index("iphone")
                next_token = tokens[iphone_index + 1]
            except (ValueError, IndexError):
                next_token = ""
            if next_token.isdigit() and 1 <= int(next_token) <= 30:
                return ("iphone", next_token)
        return exact
    if anchor == "casque" and any(token in normalized for token in ("bruit", "noise", "cancellation", "cancelling", "anc")):
        # « anc » est un acronyme pertinent, mais une recherche SQL par sous-chaîne
        # le confond avec des couleurs comme « blanc ». Les formulations longues
        # restent des preuves textuelles sûres dans les titres de feed.
        return ("reduction de bruit", "noise", "cancel")
    return ()


def _coffee_automation_requirement(query: str) -> str | None:
    """Retourne uniquement une caractéristique explicitement nommée par l’utilisateur."""
    normalized = " ".join(terms_of(query))
    # Les mots composés (semi-automatique) sont conservés par le tokeniseur :
    # les rechercher avant « automatique » évite de les confondre avec une
    # machine entièrement automatique.
    if any(term in normalized for term in _COFFEE_SEMI_AUTOMATIC_TERMS):
        return "semi"
    if any(term in normalized for term in _COFFEE_AUTOMATIC_TERMS):
        return "automatic"
    return None


def _intent_feature_clause(query: str, anchor: str, lowered_name):
    """Construit la preuve SQL d’une caractéristique sans la deviner."""
    if anchor != "coffee_machine":
        return None
    requirement = _coffee_automation_requirement(query)
    if requirement == "semi":
        return or_(*[lowered_name.contains(term) for term in _COFFEE_SEMI_AUTOMATIC_TERMS])
    if requirement == "automatic":
        return and_(
            or_(*[lowered_name.contains(term) for term in _COFFEE_AUTOMATIC_TERMS]),
            not_(or_(*[lowered_name.contains(term) for term in _COFFEE_SEMI_AUTOMATIC_TERMS])),
        )
    return None


def _exact_model_title_terms(anchor: str, required: tuple[str, ...]) -> tuple[str, ...]:
    """Preuves de modèle qui empêchent un numéro technique de faire foi.

    « iPhone 16e 15,5 cm » contient le chiffre 15, mais ne peut pas remplacer
    un iPhone 15 : le nombre doit être adjacent au nom de gamme dans le titre.
    """
    if anchor == "smartphone" and len(required) == 2 and required[0] == "iphone":
        model = required[1]
        return (f"iphone {model}", f"iphone-{model}", f"iphone{model}")
    return ()


def _catalogue_intent(query: str) -> tuple[str, tuple[str, ...]] | None:
    """Retourne une ancre catalogue et les accessoires à exclure pour un besoin courant."""
    normalized = " ".join(terms_of(query))
    terms = terms_of(query)
    for triggers, anchor, excluded in _INTENT_ANCHORS:
        if any(trigger in normalized for trigger in triggers):
            # Demander explicitement une pièce doit rester possible ; les
            # exclusions concernent uniquement la recherche d'un produit complet.
            if any(term in excluded for term in terms):
                return None
            return anchor, excluded
    return None


def _search_query_for(query: str, intent: tuple[str, tuple[str, ...]] | None) -> tuple[str, tuple[str, ...]]:
    """Choisit une recherche compatible avec l'intention, sans diluer un modèle cité."""
    anchor = intent[0] if intent else ""
    required = _required_name_terms(query, anchor) if intent else ()
    # Une demande de modèle précis (par ex. iPhone) doit d'abord chercher ce
    # modèle. L'ancre « smartphone » ne sert que lorsque la demande est générique.
    return (" ".join(required) if required else (anchor if intent else query), required)


# Les noms de vrais téléphones ne contiennent pas systématiquement « smartphone »
# (ex. « Samsung Galaxy S25 »). Ces familles sont donc une porte d'entrée
# lexicale, toujours doublée du sous-rayon Core : elles n’élargissent jamais une
# recherche générique vers les accessoires ou les autres rayons.
_INTENT_PRODUCT_TITLE_TERMS: dict[str, tuple[str, ...]] = {
    "smartphone": (
        "smartphone", "telephone", "telefoon", "iphone", "galaxy", "pixel",
        "samsung", "xiaomi", "redmi", "poco", "oneplus", "oppo", "motorola",
        "huawei", "honor", "realme", "nothing", "fairphone", "xperia", "zenfone",
    ),
    "laptop": ("laptop", "notebook", "macbook", "chromebook", "thinkpad", "vivobook", "ideapad"),
    "casque": ("casque", "headphone", "koptelefoon", "headset"),
    "coffee_machine": (
        "machine a cafe", "machine à café", "cafetiere", "cafetière", "coffee machine",
        "koffiezetapparaat", "koffiemachine", "espressomachine", "espresso",
    ),
    "robot_vacuum": (
        "aspirateur robot", "robot aspirateur", "robot vacuum", "robotstofzuiger", "roomba",
    ),
}


def _intent_search_terms(anchor: str) -> tuple[str, ...]:
    """Termes produit attestés pour une requête Assistant générique."""
    return _INTENT_PRODUCT_TITLE_TERMS.get(anchor, ())


def _intent_search_clause(
    search_query: str, intent: tuple[str, tuple[str, ...]] | None, required: tuple[str, ...]
):
    """Clause texte adaptée aux formulations naturelles et aux titres de feed.

    Pour une marque ou un modèle explicitement demandé, tous les mots restent
    obligatoires. Pour une intention générique, un des noms de famille de produit
    suffit, car les titres marchands n’emploient pas tous le mot « smartphone ».
    """
    if not intent:
        return search_clause(search_query)
    if required:
        # « réduction de bruit », « noise » et « cancelling » sont
        # des formulations alternatives d’une même attente. Les exiger toutes
        # dans un titre rendait une demande de casque ANC impossible alors que
        # le catalogue contenait des casques « noise cancelling » ou « ANC ».
        # Les modèles explicites (iPhone 15, Galaxy…) gardent en revanche leur
        # conjonction stricte afin de ne jamais substituer un autre modèle.
        if intent[0] == "casque":
            return or_(*[search_clause(term) for term in required])
        return search_clause(search_query)
    terms = _intent_search_terms(intent[0])
    if not terms:
        return search_clause(search_query)
    return or_(*[search_clause(term) for term in terms])


def _primary_image_url(value: str | None) -> str | None:
    """Conserve une URL image unique quand le feed en fournit plusieurs séparées par des virgules."""
    if not value:
        return None
    for candidate in value.split(","):
        url = candidate.strip()
        if url.startswith(("https://", "http://")):
            return url
    return None


@traced_pipeline_stage("decision")
async def _decisions_for_offers(session, offers: list[Offer]) -> dict[int, dict[str, Any]]:
    """Calcule les décisions des offres assistant à partir des mêmes preuves que les fiches.

    Les historiques et produits regroupés sont lus par lots : l'assistant ne doit
    pas déclencher une requête par carte ni posséder ses propres règles de score.
    """
    if not offers:
        return {}

    # `CatalogProduct.price_min/currency/*_count` est une projection legacy qui
    # mélange potentiellement plusieurs devises. La comparaison est donc
    # reconstruite en une seule lecture, par produit ET devise normalisée.
    product_ids = {offer.product_id for offer in offers if offer.product_id is not None}
    comparable_by_product_currency: dict[tuple[int, str], dict[str, Any]] = {}
    if product_ids:
        async with traced_dependency("postgres", "read"):
            grouped_offers = (
                await session.execute(
                    select(Offer).where(
                        Offer.product_id.in_(product_ids),
                        Offer.is_canonical.is_(True),
                        or_(Offer.is_adult.is_(False), Offer.is_adult.is_(None)),
                    )
                )
            ).scalars().all()
        # La comparaison de groupe n'a besoin que de prouver l'état courant.
        # L'historique complet est réservé aux offres finales ci-dessous.
        async with traced_dependency("postgres", "read"):
            grouped_evidence = await load_offer_evidence(
                session,
                list(grouped_offers),
                current_only=True,
            )
        reference = datetime.now(UTC)
        for grouped_offer in grouped_offers:
            kind = grouped_offer.offer_kind or taxonomy.classify_offer_kind(
                grouped_offer.category, grouped_offer.name, grouped_offer.brand
            )
            evidence = grouped_evidence.get(grouped_offer.id)
            if (
                not taxonomy.is_ean_comparable(kind)
                or evidence is None
                or not _offer_is_recommendable(
                    grouped_offer,
                    observed_at=evidence.current_observed_at,
                    now=reference,
                )
            ):
                continue
            currency = normalize_currency_code(grouped_offer.currency)
            product_id = grouped_offer.product_id
            if currency is None or product_id is None:
                continue
            key = (product_id, currency)
            aggregate = comparable_by_product_currency.setdefault(
                key,
                {"min_price": float(grouped_offer.price), "merchant_ids": set(), "offer_ids": set()},
            )
            aggregate["min_price"] = min(aggregate["min_price"], float(grouped_offer.price))
            aggregate["merchant_ids"].add(grouped_offer.merchant_id)
            aggregate["offer_ids"].add(grouped_offer.id)

    async with traced_dependency("postgres", "read"):
        evidence_by_offer = await load_offer_evidence(session, list(offers))

    decisions: dict[int, dict[str, Any]] = {}
    for offer in offers:
        currency = normalize_currency_code(offer.currency)
        evidence = evidence_by_offer.get(offer.id)
        history = list(evidence.history) if evidence is not None else []
        aggregate = (
            comparable_by_product_currency.get((offer.product_id, currency))
            if offer.product_id is not None and currency is not None
            else None
        )
        merchants_count = len(aggregate["merchant_ids"]) if aggregate else 1
        decisions[offer.id] = decision.compute_decision(
            price=offer.price,
            currency=currency,
            history=history,
            history_currency=(
                evidence.currency if evidence is not None and history else None
            ),
            cheapest_elsewhere=(
                aggregate["min_price"]
                if aggregate is not None and merchants_count >= 2
                else None
            ),
            comparison_currency=currency,
            merchants_count=merchants_count,
            offers_count=len(aggregate["offer_ids"]) if aggregate else 1,
            in_stock=offer.in_stock,
            updated_at=offer.updated_at,
            offer_kind=offer.offer_kind or taxonomy.classify_offer_kind(offer.category, offer.name, offer.brand),
        )
    return decisions


def _offer_is_recommendable(
    offer: Offer,
    *,
    observed_at: datetime | None = None,
    now: datetime | None = None,
) -> bool:
    """Valide les faits minimaux avant tout arrondi ou comparaison legacy."""

    price = offer.price
    return (
        price is not None
        and not isinstance(price, bool)
        and math.isfinite(price)
        and price > 0
        and normalize_currency_code(offer.currency) is not None
        and offer.in_stock is True
        and offer_observation_is_fresh(observed_at, now=now)
    )


def _normalize_general_snapshots(
    snapshots: list[CoreOfferSnapshot],
) -> list[CoreOfferSnapshot]:
    """Normalise la devise dans le snapshot immuable remis au planificateur."""

    normalized: list[CoreOfferSnapshot] = []
    for snapshot in snapshots:
        currency = normalize_currency_code(snapshot.currency)
        if currency is not None:
            normalized.append(replace(snapshot, currency=currency))
    return normalized


def _planned_general_offer_ids(intent: GeneralIntent, snapshots) -> list[int]:
    """Retourne seulement les offres retenues par la décision générale partagée.

    L’Assistant exploite le même moteur que Outfit Studio : la récupération reste
    exhaustive, mais le modèle conversationnel ne reçoit jamais un accessoire ou
    un produit hors besoin déjà éliminé par les preuves de pertinence.
    """
    plan = compose_general_plan(intent, snapshots, max_items=5)
    if plan.get("decision") != "recommend":
        return []
    return [int(item["offer_id"]) for item in plan.get("items", []) if item.get("offer_id") is not None]


def _prefer_deterministic_model_intent(intent: GeneralIntent) -> bool:
    """Évite qu'un code modèle explicite soit élargi par une inférence de rayon.

    Lorsqu'aucun scope taxonomique n'est prouvé mais qu'un identifiant de modèle
    l'est, la recherche lexicale exacte est à la fois plus fidèle et beaucoup
    plus bornée qu'une lecture exhaustive d'un rayon proposé par le modèle.
    """

    return not intent.resolved and bool(intent.required_title_phrases)


@traced_pipeline_stage("retrieval")
async def search_internal_products(
    query: str, budget: float | None, *, limit: int = 20, country: str | None = None
) -> list[dict[str, Any]]:
    """Recherche dans le catalogue interne FILON.

    Retourne une liste de produits normalisés (même format que serpapi_shopping)
    pour être directement utilisable par recommend.py.
    """
    terms = terms_of(query)
    if not terms:
        return []

    try:
        async with session_scope() as session:
            if session is None:
                log.warning("Base de données non disponible")
                return []

            # La voie générale est la référence : elle résout la demande vers les
            # catégories et sous-catégories FILON, lit toutes les offres admissibles
            # puis seulement les classe. Les anciennes ancres ne servent plus que
            # d’ultime repli quand la taxonomie ne reconnaît aucune intention.
            deterministic_intent = resolve_intent(query)
            general_intent = (
                deterministic_intent
                if _prefer_deterministic_model_intent(deterministic_intent)
                else await resolve_intent_with_fallback(query)
            )
            from sqlalchemy.orm import joinedload as jl
            if general_intent.resolved:
                snapshots = _normalize_general_snapshots(
                    await retrieve_general_offers(session, general_intent)
                )
                # La couche générale est déjà fail-closed, mais ce filtre
                # protège ce caller historique contre les placeholders (vide,
                # ``unknown``, XXX) et propage la valeur normalisée au
                # planificateur avant tout classement ou budget.
                if budget is not None:
                    snapshots = [
                        snapshot for snapshot in snapshots
                        if snapshot.currency == "EUR"
                        and snapshot.price is not None
                        and snapshot.price <= budget
                    ]
                snapshot_ids = _planned_general_offer_ids(general_intent, snapshots)
                if snapshot_ids:
                    async with traced_dependency("postgres", "read"):
                        hydrated = (
                            await session.execute(
                                select(Offer)
                                .where(Offer.id.in_(snapshot_ids))
                                .options(jl(Offer.merchant))
                            )
                        ).scalars().all()
                    by_id = {offer.id: offer for offer in hydrated}
                    offers = [by_id[offer_id] for offer_id in snapshot_ids if offer_id in by_id]
                else:
                    offers = []
            else:
                intent = _catalogue_intent(query)
                search_query, required = _search_query_for(query, intent)
                clause = _intent_search_clause(search_query, intent, required)
                if clause is None:
                    return []
                stmt = (
                    select(Offer)
                    .join(Merchant, Offer.merchant_id == Merchant.id)
                    .where(
                        and_(
                            clause,
                            Offer.is_canonical == True,
                            Offer.is_adult == False,
                            Offer.price.isnot(None),
                            Offer.price > 0,
                            Offer.currency.isnot(None),
                            func.trim(Offer.currency) != "",
                            Offer.in_stock.is_(True),
                        )
                    )
                    .options(jl(Offer.merchant))
                )
                if intent:
                    anchor, excluded = intent
                    lowered_name = func.lower(Offer.name)
                    stmt = stmt.where(not_(or_(*[lowered_name.contains(term) for term in excluded])))
                    primary_scope = _intent_primary_scope(anchor)
                    if primary_scope is not None:
                        stmt = stmt.where(primary_scope)
                    impostor_terms = _intent_primary_impostor_terms(anchor)
                    if impostor_terms:
                        stmt = stmt.where(not_(or_(*[lowered_name.contains(term) for term in impostor_terms])))
                    min_primary_price = _PRIMARY_MIN_PRICE.get(anchor)
                    if min_primary_price is not None:
                        stmt = stmt.where(Offer.price >= min_primary_price)
                    feature_clause = _intent_feature_clause(query, anchor, lowered_name)
                    if feature_clause is not None:
                        stmt = stmt.where(feature_clause)
                    exact_model_terms = _exact_model_title_terms(anchor, required)
                    if exact_model_terms:
                        stmt = stmt.where(or_(*[lowered_name.contains(term) for term in exact_model_terms]))
                if budget is not None:
                    # Le budget Assistant historique est libellé en EUR. Une
                    # offre sans devise ou dans une devise étrangère ne peut
                    # pas le satisfaire sans conversion documentée.
                    stmt = stmt.where(
                        func.upper(func.trim(Offer.currency)) == "EUR",
                        Offer.price <= budget,
                    )
                del limit
                async with traced_dependency("postgres", "read"):
                    rows = await fetch_all_offer_rows(session.execute, stmt)
                offers = [row[0] for row in rows]

            # Revalider après l'hydratation protège aussi la voie résolue si
            # une offre change entre la lecture du snapshot et celle de la ligne.
            reference = datetime.now(UTC)
            async with traced_dependency("postgres", "read"):
                evidence_by_offer = await load_offer_evidence(
                    session,
                    list(offers),
                    current_only=True,
                )
            offers = [
                offer
                for offer in offers
                if (evidence := evidence_by_offer.get(offer.id)) is not None
                and _offer_is_recommendable(
                    offer,
                    observed_at=evidence.current_observed_at,
                    now=reference,
                )
            ]

            decisions = await _decisions_for_offers(session, offers)
            products: list[dict[str, Any]] = []
            for offer in offers:
                currency = normalize_currency_code(offer.currency)
                evidence = evidence_by_offer.get(offer.id)
                merchant_name = (
                    offer.merchant.name.strip()
                    if offer.merchant is not None
                    and isinstance(offer.merchant.name, str)
                    and offer.merchant.name.strip()
                    else None
                )
                if currency is None or evidence is None or merchant_name is None:
                    # Ultime garde-fou : aucune évolution des requêtes amont ne
                    # doit réintroduire un remplacement silencieux de devise ou
                    # de marchand, ni une observation sans horodatage probant.
                    continue
                products.append({
                    "offer_id": offer.id,
                    "product_ean": offer.ean if taxonomy.is_ean_comparable(offer.offer_kind) else None,
                    "offer_kind": offer.offer_kind or taxonomy.classify_offer_kind(offer.category, offer.name, offer.brand),
                    "name": offer.name,
                    "price": round(float(offer.price), 2),
                    # La devise est celle de l'offre relevée. Le pays de contexte
                    # choisi par l’utilisateur ne permet pas d'en déduire une autre.
                    "currency": currency,
                    "merchant": merchant_name,
                    "in_stock": True,
                    "observed_at": evidence.current_observed_at.isoformat(),
                    "image": _primary_image_url(offer.image_url),
                    "link": offer.deep_link or offer.product_url,
                    "delivery": None,
                    "rating": None,
                    "reviews": None,
                    "decision": decisions.get(offer.id),
                    "source": "filon_catalog",
                })

            log.info(
                "Catalogue Assistant exhaustif : %d offres évaluées",
                len(products),
            )
            return products

    except Exception as exc:
        log.warning(
            "Erreur recherche catalogue interne (error_type=%s) → repli appelant",
            type(exc).__name__,
        )
        raise
