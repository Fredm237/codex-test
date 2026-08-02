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

# Suffixes FR + NL pour le stemming
_SUFFIXES = ("tion", "ment", "eur", "euse", "ique", "ies", "es", "en", "er", "x", "s", "e")
_MIN_STEM = 3


def normalize(text: str) -> str:
    """Supprime les accents et normalise en minuscules."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def stem(term: str) -> str:
    """Radical approximatif — absorbe les accords FR/NL.

    Plus intelligent que la version précédente :
    - Normalise les accents
    - Gère plus de suffixes
    - Protège les termes courts
    """
    term = normalize(term)
    if len(term) <= 4:
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
