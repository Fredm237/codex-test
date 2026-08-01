"""Recherche dans le catalogue.

La première version cherchait la requête entière comme une sous-chaîne :
`name ILIKE '%chemise bleue gant%'`. Elle exigeait donc que les mots se suivent
dans cet ordre exact, et ne renvoyait rien dès que l'utilisateur tapait plus
d'un mot — c'est-à-dire presque toujours.

On cherche désormais chaque terme séparément, dans le nom ou la marque, et on
classe les résultats : phrase exacte d'abord, puis début de libellé, puis le
reste. Le tri porte la pertinence, la clause porte la sélection.
"""

from __future__ import annotations

import re

from sqlalchemy import and_, case, or_

from app.db import models

# Au-delà, la requête relève du copier-coller de description : les termes
# supplémentaires n'affinent plus, ils vident le résultat.
MAX_TERMS = 6
MIN_TERM_LENGTH = 2

# Le français accorde en genre et en nombre, pas les libellés des marchands :
# « Chemise bleu » côtoie « chemise bleue » et « chemises bleues ». Chercher la
# forme exacte saisie par l'utilisateur ne trouvait donc rien. On tronque les
# terminaisons les plus courantes pour chercher le radical.
#
# Du plus long au plus court. « manteaux » ne perd que son x : retirer « eaux »
# laissait « mant », un radical si court qu'il ramenait n'importe quoi.
_SUFFIXES = ("es", "x", "s", "e")
# En deçà, tronquer produit des radicaux trop courts, donc trop permissifs.
_MIN_STEM = 3


def stem(term: str) -> str:
    """Radical approximatif d'un terme, pour absorber les accords.

    Volontairement grossier : la sélection se fait déjà par sous-chaîne, et un
    radical trop agressif ramènerait n'importe quoi. « bleue » et « bleus »
    donnent « bleu » ; « robe » et « sony », trop courts, restent intacts.
    """
    if len(term) <= 4:
        return term
    for suffix in _SUFFIXES:
        if term.endswith(suffix) and len(term) - len(suffix) >= _MIN_STEM:
            return term[: -len(suffix)]
    return term


def terms_of(query: str | None) -> list[str]:
    """Termes exploitables d'une requête, dans l'ordre de saisie."""
    words = re.split(r"[^\w'-]+", (query or "").strip().lower())
    seen: list[str] = []
    for w in words:
        if len(w) >= MIN_TERM_LENGTH and w not in seen:
            seen.append(w)
    return seen[:MAX_TERMS]


def search_clause(query: str | None):
    """Condition de sélection : chaque terme doit apparaître quelque part.

    Rend None si la requête ne contient aucun terme exploitable — l'appelant
    n'applique alors aucun filtre, plutôt que d'écarter tout le catalogue.
    """
    terms = terms_of(query)
    if not terms:
        return None
    return and_(
        *[
            or_(
                models.Offer.name.ilike(f"%{stem(t)}%"),
                models.Offer.brand.ilike(f"%{stem(t)}%"),
            )
            for t in terms
        ]
    )


def relevance_order(query: str | None):
    """Ordre de pertinence, du plus au moins probable.

    Trois paliers seulement : la phrase exacte, le libellé qui commence par le
    premier terme, puis le reste. Une pondération plus fine donnerait une
    illusion de précision que ces données ne portent pas.
    """
    terms = terms_of(query)
    if not terms:
        return None
    phrase = " ".join(terms)
    return case(
        (models.Offer.name.ilike(f"%{phrase}%"), 0),
        (models.Offer.name.ilike(f"{terms[0]}%"), 1),
        else_=2,
    )
