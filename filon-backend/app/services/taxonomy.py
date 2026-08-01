"""Taxonomie FILON — ramener 154 marchands à un vocabulaire commun.

Chaque marchand nomme ses catégories comme il l'entend, dans sa langue, et
parfois à tort : Voghion range ses robes sous « Men's Clothing ». Afficher ces
libellés bruts rendait toute navigation impossible et produisait des rayons
incohérents.

On classe donc chaque offre dans une catégorie FILON, à partir de deux signaux :
la catégorie déclarée et le libellé du produit. Le libellé l'emporte en cas de
contradiction — un marchand se trompe plus souvent de rayon que de nom.

Les règles sont volontairement lisibles et ordonnées : la première qui
correspond gagne. Une classification qu'on ne peut pas relire ne se corrige pas.
"""

from __future__ import annotations

import re

# Catégories FILON. Stables : elles servent d'URL, de filtres et de menus.
INFORMATIQUE = "Informatique"
TELEPHONIE = "Téléphonie"
PHOTO = "Photo"
GAMING = "Gaming"
TV_SON = "TV & Son"
ELECTROMENAGER = "Électroménager"
MAISON = "Maison & Déco"
JARDIN = "Jardin & Bricolage"
MODE_FEMME = "Mode femme"
MODE_HOMME = "Mode homme"
MODE_ENFANT = "Mode enfant"
CHAUSSURES = "Chaussures"
BIJOUX = "Bijoux & Montres"
BEAUTE = "Beauté & Parfum"
SANTE = "Santé"
SPORT = "Sport & Plein air"
AUTO = "Auto & Moto"
BEBE = "Bébé & Puériculture"
ANIMALERIE = "Animalerie"
BAGAGERIE = "Bagagerie"
CULTURE = "Livres & Culture"
ALIMENTATION = "Alimentation & Boissons"
JOUETS = "Jeux & Jouets"
ACCESSOIRES = "Accessoires"
# Rayon générique : un vêtement dont le public n'est pas identifiable vaut mieux
# ici que dans un rayon genré au hasard, ou nulle part.
MODE = "Mode"
LOISIRS = "Loisirs créatifs"

ALL_CATEGORIES = [
    INFORMATIQUE, TELEPHONIE, PHOTO, GAMING, TV_SON, ELECTROMENAGER, MAISON,
    JARDIN, MODE_FEMME, MODE_HOMME, MODE_ENFANT, CHAUSSURES, BIJOUX, BEAUTE,
    SANTE, SPORT, AUTO, BEBE, ANIMALERIE, BAGAGERIE, CULTURE, ALIMENTATION,
    JOUETS, ACCESSOIRES, LOISIRS, MODE,
]

# ─────────────────────────────────────────────────────────────────────────────
# Départements — le premier niveau de navigation.
#
# Vingt-six rayons dans une liste plate ne se parcourent pas. Les marchands
# sérieux présentent deux niveaux : un département qu'on balaie du regard, puis
# ses rayons. L'ordre ci-dessous est celui du menu.
# ─────────────────────────────────────────────────────────────────────────────
DEPARTMENTS: list[tuple[str, list[str]]] = [
    ("Mode & Accessoires", [MODE_FEMME, MODE_HOMME, MODE_ENFANT, MODE, CHAUSSURES,
                            ACCESSOIRES, BAGAGERIE, BIJOUX]),
    ("High-Tech", [INFORMATIQUE, TELEPHONIE, TV_SON, PHOTO, GAMING]),
    ("Maison", [MAISON, ELECTROMENAGER, JARDIN]),
    ("Beauté & Santé", [BEAUTE, SANTE]),
    ("Sport & Loisirs", [SPORT, JOUETS, CULTURE, LOISIRS]),
    ("Famille & Quotidien", [BEBE, ANIMALERIE, AUTO, ALIMENTATION]),
]

_DEPARTMENT_OF = {c: d for d, cats in DEPARTMENTS for c in cats}


def department_of(category: str) -> str | None:
    """Département d'un rayon, ou None s'il n'est rattaché à aucun."""
    return _DEPARTMENT_OF.get(category)


# Marqueurs de public, testés avant tout classement de mode.
# « women » contient « men » : l'ordre d'évaluation n'est pas négociable.
_ENFANT = r"\b(enfant|kids?|child|children|kinder|jongens|meisjes|garçon|fille|boys?|girls?|junior)\b"
_FEMME = r"\b(femme|femmes|women|women's|woman|dames|dame|ladies|lady|feminin|féminin)\b"
_HOMME = r"\b(homme|hommes|men|men's|mens|heren|male|masculin)\b"

# (catégorie, motif). La première correspondance gagne : du plus spécifique au
# plus général.
_RULES: list[tuple[str, str]] = [
    (BEBE, r"\b(b[ée]b[ée]s?|baby|babys|poussettes?|stroller|couches?|luiers?|biberons?|"
           r"puericulture|puéricultur|bavoirs?|slabbetjes?|mother\s*&\s*kids|tricycles?|"
           r"draagzak|maternit[ée])\b"),
    (ANIMALERIE, r"\b(chiens?|chats?|dogs?|cats?|hond|kat|hondenvoer|kattenvoer|animal|"
                 r"animalerie|croquettes?|aquarium|liti[èe]re|dierenvoeding)\b"),
    (AUTO, r"\b(pneus?|tyres?|banden|wheels?|jantes?|voitures?|autos?|automotive|motos?|"
           r"scooters?|v[ée]hicules?|car\s?parts?|huile moteur|car\b|autoteile)\b"),
    (TELEPHONIE, r"\b(smartphones?|t[ée]l[ée]phones?|iphone|samsung galaxy|mobiles?|gsm|"
                 r"coques?|chargeurs?|powerbanks?|[ée]couteurs? sans fil|airpods|cellphones?|"
                 r"telecommunications?)\b"),
    (GAMING, r"\b(gaming|jeux? vid[ée]o|video\s?games?|consoles?|playstation|ps5|ps4|xbox|"
             r"nintendo|steam|manettes?|gamer|videogames?)\b"),
    (INFORMATIQUE, r"\b(ordinateurs?|laptops?|pc\b|macbook|notebooks?|claviers?|souris|"
                   r"[ée]crans?|monitors?|ssd|disques? durs?|imprimantes?|routeurs?|usb|"
                   r"tablettes?|software)\b"),
    (PHOTO, r"\b(appareils? photo|cameras?|caméras?|objectifs?|reflex|drones?|gopro|"
            r"tr[ée]pieds?|photographie)\b"),
    (TV_SON, r"\b(t[ée]l[ée]viseurs?|\btv\b|home cinema|barres? de son|soundbars?|enceintes?|"
             r"casques? audio|hifi|hi-fi|platines?|headphones?)\b"),
    (ELECTROMENAGER, r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateurs?|frigos?|"
                     r"cong[ée]lateurs?|fours?|micro-ondes|aspirateurs?|cafeti[èe]res?|"
                     r"robots? cuiseur|wasmachines?|koelkast|home appliances?|"
                     r"huishoudelijke|ventilateurs?|vacuum cleaners?|wassen, strijken)\b"),
    (BEAUTE, r"\b(parfums?|eaux? de parfum|eaux? de toilette|fragrances?|maquillage|make\s?up|"
             r"cosm[ée]tiques?|cosmetics?|beauty|cr[èe]mes?|s[ée]rums?|shampooings?|shampoo|"
             r"conditioner|soins? visage|skincare|haircare|hair care|haarverzorging|"
             r"verzorgingsproducten|gezicht|huidverzorging|toner|lipstick|eyeliner|nails?|"
             r"ongles?|perruques?|wigs?|hair extensions?|vernis)\b"),
    (SANTE, r"\b(compl[ée]ments? alimentaires?|vitamines?|pharmacie|m[ée]dical|orthop[ée]dique|"
            r"tensiom[èe]tre|hygi[èeë]ne|huiles? essentielles?)\b"),
    (BIJOUX, r"\b(bijoux?|jewelry|jewellery|bagues?|rings?|colliers?|necklaces?|pendants?|"
             r"bracelets?|boucles? d'oreille|earrings?|montres?|watch(es)?|horloges?|"
             r"sieraden|ketting)\b"),
    (CHAUSSURES, r"\b(chaussures?|shoes?|baskets?|sneakers?|bottes?|boots?|escarpins?|heels?|"
                 r"mules?|sandales?|sandals?|schoenen|mocassins?|semelles?|insoles?|"
                 r"pantoufles?|slippers?)\b"),
    (BAGAGERIE, r"\b(sacs? [àa] main|sacs? [àa] dos|handbags?|backpacks?|valises?|suitcases?|"
                r"bagages?|luggage|trolleys?|portefeuilles?|wallets?|maroquinerie|handtas|"
                r"rugzak|bags?)\b"),
    (ACCESSOIRES, r"\b(accessoires?|accessories|lunettes? de soleil|sunglasses|ceintures?|"
                  r"belts?|[ée]charpes?|scarf|scarves|chapeaux?|hats?|casquettes?|caps?|"
                  r"gants?|gloves|bonnets?|cravates?|ties?|riemen)\b"),
    (SPORT, r"\b(sports?|deportivo|deporte|sportartikelen|fitness|musculation|yoga|jogging|"
            r"v[ée]los?|cyclisme|running|randonn[ée]e|camping|ski|natation|fietsen|"
            r"[ée]quipements? sportifs?)\b"),
    (JARDIN, r"\b(jardins?|jardinage|tondeuses?|bricolage|perceuses?|outillage|tuin|"
             r"tuingereedschap|gereedschap|parquet|peinture murale|garden tools?)\b"),
    (MAISON, r"\b(canap[ée]s?|fauteuils?|tables?|chaises?|lampes?|luminaires?|matelas|"
             r"linge de lit|rideaux?|d[ée]coration|meubles?|vaisselle|assiettes?|cuisine|"
             r"meubel|verlichting|schoonmaak|nettoyage|serviettes?|tissus?|textile|"
             r"home\s*&\s*garden|huishouden)\b"),
    (JOUETS, r"\b(jouets?|lego|playmobil|peluches?|puzzles?|jeux? de soci[ée]t[ée]|speelgoed|"
             r"toys?)\b"),
    # « couture » est écarté : en français il désigne aussi une piqûre de
    # vêtement, et « pyjama sans couture » atterrissait ici.
    (LOISIRS, r"\b(patrons? de couture|patrons?|tricot|laine [àa] tricoter|mercerie|"
              r"loisirs? cr[ée]atifs?|scrapbooking)\b"),
    (CULTURE, r"\b(livres?|romans?|manga|dvd|blu-ray|vinyles?|boek|books?)\b"),
    (ALIMENTATION, r"\b(alimentation|[ée]picerie|caf[ée]|th[ée]|vins?|bi[èe]res?|chocolats?|"
                   r"snacks?|boissons?|voeding|wijn)\b"),
]


# Vêtements : le rayon dépend du public, déterminé plus haut.
_VETEMENT = (
    r"\b(v[êe]tements?|clothing|kleding|apparel|robes?|dress(es)?|jupes?|pantalons?|"
    r"trousers?|jeans?|chemises?|shirts?|t-shirts?|tops?|pulls?|sweats?|sweaters?|hoodies?|"
    r"manteaux?|vestes?|jackets?|blouses?|costumes?|shorts?|leggings?|lingerie|underwear|"
    r"sleepwears?|pyjamas?|maillots?|chaussettes?|socks?|polos?|overhemd|broek|jas|blazers?|"
    r"combinaisons?|jumpsuits?|nachtkleding|ondergoed)\b"
)


_SLUG_OVERRIDES = {
    "TV & Son": "tv-son",
    "Maison & Déco": "maison-deco",
    "Jardin & Bricolage": "jardin-bricolage",
    "Bijoux & Montres": "bijoux-montres",
    "Beauté & Parfum": "beaute-parfum",
    "Sport & Plein air": "sport-plein-air",
    "Auto & Moto": "auto-moto",
    "Bébé & Puériculture": "bebe-puericulture",
    "Livres & Culture": "livres-culture",
    "Alimentation & Boissons": "alimentation-boissons",
    "Jeux & Jouets": "jeux-jouets",
    "Loisirs créatifs": "loisirs-creatifs",
    "Électroménager": "electromenager",
    "Téléphonie": "telephonie",
    "Santé": "sante",
}


def slug_of(category: str) -> str:
    """Identifiant d'URL d'une catégorie. Stable : il entre dans les liens."""
    if category in _SLUG_OVERRIDES:
        return _SLUG_OVERRIDES[category]
    text = category.lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("ô", "o"), ("&", " ")):
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


_BY_SLUG = {slug_of(c): c for c in ALL_CATEGORIES}


def from_slug(slug: str) -> str | None:
    """Catégorie correspondant à un slug d'URL, ou None si inconnu."""
    return _BY_SLUG.get((slug or "").lower())


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def classify(
    merchant_category: str | None,
    name: str | None = None,
    brand: str | None = None,
) -> str | None:
    """Rend la catégorie FILON d'une offre, ou None si rien n'est reconnu.

    `name` prime sur `merchant_category` : un marchand se trompe plus souvent de
    rayon que de libellé produit. Rendre None est un résultat acceptable — mieux
    vaut une offre non classée qu'une offre rangée au mauvais endroit.
    """
    name = (name or "").strip()
    merchant_category = (merchant_category or "").strip()
    if not name and not merchant_category:
        return None
    clothing = False

    # Le nom d'abord, la catégorie du marchand ensuite : l'ordre porte la règle.
    for text in (name, merchant_category):
        if not text:
            continue

        # Vêtements : le rayon dépend du public, qu'on cherche dans les deux
        # sources avant de trancher.
        if _has(_VETEMENT, text):
            other = merchant_category if text is name else name
            for source in (text, other):
                if not source:
                    continue
                if _has(_ENFANT, source):
                    return MODE_ENFANT
                if _has(_FEMME, source):
                    return MODE_FEMME
                if _has(_HOMME, source):
                    return MODE_HOMME
            # Pièces exclusivement féminines : le public est implicite.
            if _has(r"\b(robes?|jupes?|lingerie|blouses?|escarpins?)\b", text):
                return MODE_FEMME
            # Public indéterminé : les autres règles s'expriment d'abord
            # (« pantalon de jogging » relève du sport), et à défaut l'article
            # rejoint le rayon Mode générique plutôt qu'un rayon genré au hasard.
            clothing = True

        for category, pattern in _RULES:
            if _has(pattern, text):
                return category

    return MODE if clothing else None
