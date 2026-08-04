"""Recherche dans le catalogue.

Deux responsabilités distinctes, volontairement séparées :

- `search_clause()` décide **ce qui entre** dans les résultats (chaque terme doit
  apparaître dans le nom ou la marque, radical compris) ;
- `relevance_order()` décide **dans quel ordre** ils sortent.

Le second point a longtemps été le maillon faible, et pas pour la raison qu'on
croit. Les six paliers de pertinence fonctionnaient ; c'est le *départage* à
l'intérieur d'un palier qui ruinait tout. Il se faisait par prix croissant, si
bien que sur « iphone 16 » les quatre premiers résultats mesurés en production
étaient des protections d'écran à 0,49 € — toutes rangées au même palier que le
téléphone, et toutes moins chères que lui. Un comparateur qui répond à « iphone »
par une coque à 0,49 € a perdu l'utilisateur avant la première comparaison.

Le prix ne peut pas départager la pertinence : dans presque toutes les
catégories, l'accessoire est moins cher que l'objet qu'il accessoirise. Le
classement s'appuie donc sur deux signaux qui, eux, ne se retournent pas :

1. **La concurrence marchande** (`catalog_products.merchants_count`). Un produit
   que plusieurs marchands référencent sous le même EAN est un produit réel et
   comparable ; une coque anonyme n'existe presque jamais en plusieurs
   exemplaires normalisés. C'est le signal le plus fort du catalogue, et il est
   déjà calculé et indexé.
2. **La nature accessoire du libellé**, reléguée seulement quand la requête ne
   la demande pas. Chercher « coque iphone » doit continuer à rendre des coques.
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


# ─────────────────────────────────────────────────────────────────────────────
# Accessoires
# ─────────────────────────────────────────────────────────────────────────────
#
# Ces mots ne disqualifient rien : ils *relèguent*, et seulement lorsque la
# requête ne les mentionne pas. La liste est délibérément courte et composée de
# termes qui désignent l'accessoire sans ambiguïté dans un libellé de feed.
#
# Deux pièges ont guidé la sélection :
#
# - « support » qualifie autant un support de téléphone qu'un soutien-gorge à
#   armatures dans les libellés de mode : il en est absent.
# - « housse » désigne un accessoire d'ordinateur mais aussi une housse de
#   couette, article de linge de maison à part entière : absent également.
#
# Un faux positif ici est coûteux — il enterre un vrai produit —, alors qu'un
# oubli laisse simplement les choses en l'état.
_ACCESSORY_WORDS = (
    "coque",
    "coques",
    "etui",
    "etuis",
    "protection",
    "protections",
    "protecteur",
    "verre trempe",
    "film protecteur",
    "screen protector",
    "case",
    "cases",
    "cover",
    "hoesje",
    "adaptateur",
    "adaptateurs",
    "cable",
    "cables",
    "chargeur",
    "chargeurs",
    "sacoche",
    "sacoches",
    "dragonne",
    "stylet",
    "autocollant",
    "autocollants",
    "sticker",
    "stickers",
    "porte-cle",
    "porte-cles",
)

# Le libellé est aussi lu comme un tout : « compatible avec … » et « pour
# iPhone 16 » sont les marques les plus fiables d'un article périphérique. Un
# fabricant ne vend pas « un téléphone pour iPhone ».
_ACCESSORY_PHRASES = (
    "compatible avec",
    "compatible with",
    "geschikt voor",
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


def query_wants_accessories(query: str | None) -> bool:
    """La requête demande-t-elle explicitement un accessoire ?

    Si oui, le classement ne doit surtout pas les reléguer : « coque iphone »
    attend des coques. On compare sur les radicaux pour absorber le pluriel.
    """
    terms = set(terms_of(query))
    if not terms:
        return False
    stems = {stem(t) for t in terms}
    for word in _ACCESSORY_WORDS:
        parts = word.split()
        if len(parts) > 1:
            # Expression composée (« verre trempe ») : tous ses mots présents.
            if all(any(stem(p) == s for s in stems) for p in parts):
                return True
        elif stem(word) in stems:
            return True
    return False


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


def accessory_penalty(query: str | None):
    """1 pour un libellé d'accessoire, 0 sinon — ou None si sans objet.

    Sert de **premier** critère de tri : un accessoire ne doit jamais devancer
    le produit qu'il accompagne, quel que soit son palier de pertinence. La
    pénalité s'annule dès que la requête mentionne un accessoire.

    Rend None quand elle ne s'applique pas, pour que l'appelant n'ajoute pas une
    colonne de tri inutile.
    """
    if not terms_of(query) or query_wants_accessories(query):
        return None
    name = func.lower(models.Offer.name)
    markers = [name.contains(p) for p in _ACCESSORY_PHRASES]
    # Mot entier : « case » ne doit pas capturer « casserole », ni « cable »
    # capturer un nom de marque qui le contiendrait. Les libellés de feed sont
    # trop irréguliers pour une regex — on encadre par les séparateurs usuels.
    for word in _ACCESSORY_WORDS:
        markers.extend(
            [
                name.startswith(f"{word} "),
                name.contains(f" {word} "),
                name.contains(f" {word},"),
                name.contains(f" {word}-"),
                name.endswith(f" {word}"),
            ]
        )
    return case((or_(*markers), 1), else_=0)


def relevance_order(query: str | None):
    """Ordre de pertinence — six paliers, du plus littéral au plus lâche.

    0. Phrase exacte dans le nom (match parfait)
    1. Phrase exacte dans la marque
    2. Nom commence par le premier terme
    3. Tous les termes dans le nom (pas forcément contigus)
    5. Le reste (au moins un terme trouvé, via le nom ou la marque)

    Ces paliers ne suffisent pas à eux seuls : sur une requête d'une poignée de
    mots, des milliers d'offres partagent le même. C'est `order_columns()` qui
    les départage.
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


def order_columns(query: str | None, *, merchants_count=None) -> list:
    """Colonnes de tri complètes pour une recherche par pertinence.

    L'ordre des critères est le cœur du correctif :

    1. **Pénalité accessoire** — avant tout le reste. Un accessoire partage le
       palier de pertinence du produit qu'il nomme (« Coque iPhone 16 » contient
       « iphone 16 » aussi littéralement que le téléphone lui-même) : seul un
       critère placé en amont peut l'en séparer.
    2. **Palier de pertinence** — la correspondance textuelle.
    3. **Concurrence marchande** — décroissante. Un produit vendu par plusieurs
       marchands sous le même EAN est réel, comparable, et c'est exactement ce
       qu'un comparateur doit montrer en premier.
    4. **Longueur du libellé** — croissante. « iPhone 16 128 Go Noir » précède
       « … + 3 accessoires offerts + livraison ». Signal faible mais gratuit, et
       remarquablement discriminant sur les feeds, où l'accumulation de mentions
       promotionnelles accompagne rarement la référence principale.
    5. **Prix croissant** — en dernier recours seulement. Il reste utile pour
       fixer un ordre stable entre deux offres par ailleurs équivalentes ; il
       était simplement placé bien trop haut.

    `merchants_count` est la colonne jointe depuis `catalog_products`. Elle est
    optionnelle : un appelant qui ne fait pas la jointure obtient un tri
    dégradé, mais correct.
    """
    if not terms_of(query):
        return []
    columns = []
    penalty = accessory_penalty(query)
    if penalty is not None:
        columns.append(penalty.asc())
    relevance = relevance_order(query)
    if relevance is not None:
        columns.append(relevance.asc())
    if merchants_count is not None:
        columns.append(merchants_count.desc().nullslast())
    columns.append(func.length(models.Offer.name).asc())
    columns.append(models.Offer.price.asc().nullslast())
    return columns
