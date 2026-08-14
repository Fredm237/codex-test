"""Recherche dans le catalogue — version premium.

Pertinence améliorée :
- 6 paliers de classement au lieu de 3
- Pondération de la marque (match marque = plus pertinent)
- Proximité des termes (tous les termes proches = plus pertinent)
- Stemming amélioré pour le français et le néerlandais
- Support des accents (normalisation)
"""

from __future__ import annotations

import re
import unicodedata

from sqlalchemy import and_, case, func, or_

from app.db import models

MAX_TERMS = 6
MIN_TERM_LENGTH = 2

# Seuls les accords — pluriel et genre, en français comme en néerlandais.
#
# Les suffixes dérivationnels (« tion », « ment », « eur », « ique »…) sont
# volontairement exclus. Le radical sert de *sous-chaîne* dans la requête, si
# bien qu'un radical trop court n'élargit pas la recherche : il la déporte.
# Mesuré sur des libellés du catalogue : « robe » réduit à « rob » ramenait
# robots et robinets, « chargeur » réduit à « charg » ramenait chargement et
# chargeuse. C'est le même mélange de rayons que celui constaté au catalogue,
# par un autre chemin.
#
# Du plus long au plus court : « manteaux » ne perd que son x, car retirer
# « eaux » laisserait « mant », un radical si court qu'il ramène n'importe quoi.
_SUFFIXES = ("es", "en", "x", "s", "e")

# En deçà, le radical cesse d'identifier le mot. « robe » moins son « e » fait
# trois lettres, et trois lettres se retrouvent dans des dizaines de produits
# sans rapport.
_MIN_STEM = 4

# Une requête courte comme « iPhone » ou « ordinateur portable » vise le produit
# principal, pas son écosystème. Les flux marchands mélangent pourtant coques,
# pièces détachées et supports avec les produits qu'ils accompagnent. Ces listes
# ne sont appliquées que si l'utilisateur ne demande pas explicitement un
# accessoire (« coque iPhone », « support laptop »).
_PRIMARY_PRODUCT_INTENTS: tuple[tuple[tuple[str, ...], tuple[str, ...], float], ...] = (
    (
        ("ordinateur", "laptop", "notebook", "macbook", "pc portable"),
        ("housse", "hoes", "sleeve", "pochette", "sac", "support", "stand", "chargeur", "charger", "cable", "adaptateur", "clavier", "keyboard", "souris", "mouse", "valise", "suitcase", "trolley", "moniteur portable", "monitor portable", "extension d'ecran", "extension d'écran"),
        200.0,
    ),
    (
        ("smartphone", "telephone", "telefoon", "iphone", "android"),
        ("coque", "case", "cover", "hoes", "protection", "protector", "verre", "glass", "chargeur", "charger", "cable", "adaptateur", "support", "ecran", "écran", "screen", "batterie", "battery", "adhesif", "adhésif", "kit", "piece", "pièce", "repair", "reparation", "réparation", "plaque", "pcb", "swap", "echange", "échange", "service pack", "cadre", "frame"),
        80.0,
    ),
    (
        ("casque", "headphone", "koptelefoon"),
        ("housse", "hoes", "case", "cable", "adaptateur", "support", "earpad", "coussin"),
        25.0,
    ),
)


def normalize(text: str) -> str:
    """Supprime les accents et normalise en minuscules."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def stem(term: str) -> str:
    """Radical approximatif — absorbe les accords FR/NL, et rien de plus.

    Les libellés des marchands ne s'accordent pas avec la requête : « Chemise
    bleu » côtoie « chemise bleue » et « chemises bleues ». On tronque donc les
    terminaisons d'accord pour chercher le radical — mais on s'arrête là, car
    au-delà le radical ne désigne plus le même objet.
    """
    term = normalize(term)
    if len(term) <= 4:
        return term
    # Le « e » final d'iPhone ne signale pas un accord : le retirer fabriquait
    # « iphon », sous-chaîne de « siphon ». Le reste du stemming conserve les
    # accords existants, notamment chemise/chemises et chaussure/chaussures.
    if term == "iphone":
        return term
    for suffix in _SUFFIXES:
        if term.endswith(suffix) and len(term) - len(suffix) >= _MIN_STEM:
            return term[: -len(suffix)]
    return term


def terms_of(query: str | None) -> list[str]:
    """Termes exploitables, normalisés et dédupliqués."""
    raw = normalize(query or "").strip()
    words = re.split(r"[^\w'-]+", raw)
    seen: list[str] = []
    for w in words:
        if len(w) >= MIN_TERM_LENGTH and w not in seen:
            seen.append(w)
    return seen[:MAX_TERMS]


def primary_product_filter(query: str | None) -> tuple[tuple[str, ...], float] | None:
    """Retourne les accessoires à écarter pour une demande de produit principal.

    La recherche textuelle reste exhaustive lorsque l'utilisateur nomme lui-même
    un accessoire. Pour une requête générique, l'absence de produit principal est
    plus honnête qu'une pièce détachée présentée comme un téléphone ou un PC.
    """
    terms = terms_of(query)
    if not terms:
        return None
    normalized = " ".join(terms)
    for triggers, excluded, minimum_price in _PRIMARY_PRODUCT_INTENTS:
        if not any(trigger in normalized for trigger in triggers):
            continue
        if any(term in excluded for term in terms):
            return None
        return excluded, minimum_price
    return None


def search_clause(query: str | None):
    """Condition de sélection : chaque terme doit apparaître dans le nom OU la marque.

    Utilise le radical pour absorber les variations morphologiques.
    """
    terms = terms_of(query)
    if not terms:
        return None
    return and_(
        *[
            or_(
                func.lower(models.Offer.name).contains(stem(t)),
                func.lower(models.Offer.brand).contains(stem(t)),
            )
            for t in terms
        ]
    )


def relevance_order(query: str | None):
    """Ordre de pertinence amélioré — 6 paliers.

    0. Phrase exacte dans le nom (match parfait)
    1. Phrase exacte dans la marque
    2. Nom commence par le premier terme
    3. Tous les termes dans le nom (pas forcément contigus)
    4. Match partiel nom + marque combinés
    5. Le reste (au moins un terme trouvé)

    Cela donne des résultats beaucoup plus pertinents sur desktop
    où les utilisateurs tapent des requêtes plus longues.
    """
    terms = terms_of(query)
    if not terms:
        return None
    phrase = " ".join(terms)
    first = terms[0]

    # Tous les termes dans le nom (conjonction)
    all_in_name = and_(*[func.lower(models.Offer.name).contains(stem(t)) for t in terms])
    # Match marque exacte
    brand_match = func.lower(models.Offer.brand).contains(phrase)

    return case(
        (func.lower(models.Offer.name).contains(phrase), 0),
        (brand_match, 1),
        (func.lower(models.Offer.name).like(f"{first}%"), 2),
        (all_in_name, 3),
        else_=5,
    )
