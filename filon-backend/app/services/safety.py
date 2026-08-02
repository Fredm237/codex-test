"""Détection des articles pour adultes, pour les tenir hors du catalogue public.

Un annonceur Awin a refusé le partenariat avec le motif « Contenu pour
adultes » : des articles érotiques étaient visibles sur filon.be. Le flag
`adultcontent/0` du feed et la liste de marchands bannis n'ont pas suffi — un
marchand généraliste peut ranger quelques références érotiques au milieu d'un
catalogue ordinaire, et rien dans son flux ne les distingue.

Ce module tranche sur le libellé du produit et sa catégorie marchand. Il est
délibérément conservateur dans les deux sens :

- **Aucun mot isolé ambigu.** « sex » apparaît dans *Essex*, *Sussex*,
  *unisex* ; « anal » dans *analyse*, *canal*, *banal* ; « plug » désigne une
  prise électrique. On n'apparie donc que des expressions, aux frontières de
  mots.
- **« adult » seul ne suffit pas.** Les flux l'emploient au sens de « taille
  adulte » (*Adult Bikes*, *Adult Costumes*). Seules les tournures sans
  ambiguïté (*adult toys*, *adult store*) comptent.

Un faux négatif coûte une référence gênante ; un faux positif coûte des
milliers d'articles légitimes. Les deux comptent, d'où les tests dédiés.
"""

from __future__ import annotations

import re

# Expressions produit sans ambiguïté (FR / NL / EN).
_NAME_TERMS = (
    r"sex[\s-]?toys?",
    r"sextoys?",
    r"seksspeeltjes?",
    r"vibromasseur",
    r"vibrators?",
    r"godemich[ée]?t?",
    r"\bgodes?\b",
    r"dildos?",
    r"plug\s+anal",
    r"anal\s+plug",
    r"butt[\s-]?plug",
    r"anaal\s?plug",
    r"masturbateur",
    r"masturbators?",
    r"[œoe]ufs?\s+vibrants?",
    r"vibrating\s+eggs?",
    r"boules?\s+de\s+geisha",
    r"lubrifiants?\s+(intime|sexuel|anal)",
    r"glijmiddel",
    r"poup[ée]es?\s+gonflables?",
    r"sex\s+dolls?",
    r"\bbdsm\b",
    r"fetish",
    r"f[ée]tichis",
    r"crotchless",
    r"string\s+ouvert",
    r"lingerie\s+[ée]rotique",
    r"erotische?\s+lingerie",
    r"nuisette\s+[ée]rotique",
    r"cockrings?",
    r"cock\s+rings?",
    r"pr[ée]servatifs?",
    r"condooms?",
    r"\bcondoms?\b",
)

# Catégories marchand : ici l'expression désigne le rayon, pas l'article.
_CATEGORY_TERMS = (
    r"adult\s+(toys?|products?|stores?|shop|entertainment|novelt)",
    r"sexual\s+wellness",
    r"sex\s+shop",
    r"[ée]rotique",
    r"erotisch",
    r"erotiek",
    r"erotica",
    r"sexualit[ée]",
)

_NAME_RE = re.compile("|".join(_NAME_TERMS), re.IGNORECASE)
_CATEGORY_RE = re.compile("|".join(_CATEGORY_TERMS + _NAME_TERMS), re.IGNORECASE)


def is_adult(
    *,
    name: str | None,
    category: str | None = None,
    brand: str | None = None,
) -> bool:
    """Vrai si l'offre relève du rayon adulte et doit rester hors du public.

    La marque est examinée avec les règles du nom : certaines enseignes
    érotiques n'apparaissent que là, la catégorie du flux restant générique.
    """
    if name and _NAME_RE.search(name):
        return True
    if brand and _NAME_RE.search(brand):
        return True
    if category and _CATEGORY_RE.search(category):
        return True
    return False
