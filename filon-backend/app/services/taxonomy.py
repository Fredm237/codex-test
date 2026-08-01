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

ALL_CATEGORIES = [
    INFORMATIQUE, TELEPHONIE, PHOTO, GAMING, TV_SON, ELECTROMENAGER, MAISON,
    JARDIN, MODE_FEMME, MODE_HOMME, MODE_ENFANT, CHAUSSURES, BIJOUX, BEAUTE,
    SANTE, SPORT, AUTO, BEBE, ANIMALERIE, BAGAGERIE, CULTURE, ALIMENTATION,
    JOUETS,
]

# Marqueurs de public, testés avant tout classement de mode.
# « women » contient « men » : l'ordre d'évaluation n'est pas négociable.
_ENFANT = r"\b(enfant|kids?|child|children|kinder|jongens|meisjes|garçon|fille|boys?|girls?|junior)\b"
_FEMME = r"\b(femme|femmes|women|women's|woman|dames|dame|ladies|lady|feminin|féminin)\b"
_HOMME = r"\b(homme|hommes|men|men's|mens|heren|male|masculin)\b"

# (catégorie, motif). La première correspondance gagne : du plus spécifique au
# plus général.
_RULES: list[tuple[str, str]] = [
    (BEBE, r"\b(b[ée]b[ée]s?|baby|babys|poussettes?|stroller|couches?|luier|biberons?|puericulture|puéricultur)\b"),
    (ANIMALERIE, r"\b(chien|chat|dog|cat|hond|kat|hondenvoer|kattenvoer|animal|animalerie|croquette|aquarium|litiere|litière)\b"),
    (AUTO, r"\b(pneu|pneus|tyre|tyres|band(en)?|jante|voiture|auto|moto|scooter|v[ée]hicule|car\s?parts?|huile moteur)\b"),
    (TELEPHONIE, r"\b(smartphone|t[ée]l[ée]phone|iphone|samsung galaxy|mobile|gsm|coque|chargeur|powerbank|[ée]couteurs? sans fil|airpods)\b"),
    (INFORMATIQUE, r"\b(ordinateur|laptop|pc\b|macbook|notebook|clavier|souris|[ée]cran|monitor|ssd|disque dur|imprimante|routeur|usb)\b"),
    (GAMING, r"\b(gaming|jeu vid[ée]o|console|playstation|ps5|ps4|xbox|nintendo|switch|steam|manette|gamer)\b"),
    (PHOTO, r"\b(appareil photo|camera|caméra|objectif|reflex|drone|gopro|tr[ée]pied|photographie)\b"),
    (TV_SON, r"\b(t[ée]l[ée]viseur|\btv\b|home cinema|barre de son|soundbar|enceinte|casque audio|hifi|hi-fi|platine)\b"),
    (ELECTROMENAGER, r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateur|frigo|cong[ée]lateur|four|micro-ondes|aspirateur|cafeti[èe]re|robot cuiseur|wasmachine|koelkast)\b"),
    (BEAUTE, r"\b(parfum|eau de parfum|eau de toilette|maquillage|cosm[ée]tique|cr[èe]me|s[ée]rum|shampooing|soin visage|makeup|skincare|toner|lipstick)\b"),
    (SANTE, r"\b(compl[ée]ments? alimentaires?|vitamines?|pharmacie|m[ée]dical|orthop[ée]dique|tensiom[èe]tre)\b"),
    (BIJOUX, r"\b(bijou|bijoux|bague|collier|bracelet|boucles? d'oreille|montre|watch|horloge|sieraden|ketting)\b"),
    (CHAUSSURES, r"\b(chaussure|chaussures|basket|baskets|sneakers?|bottes?|boots?|escarpins?|sandales?|schoenen|mocassins?)\b"),
    (BAGAGERIE, r"\b(sac [àa] main|sac [àa] dos|valise|bagage|trolley|portefeuille|maroquinerie|handtas|rugzak)\b"),
    (SPORT, r"\b(sports?|fitness|musculation|yoga|jogging|v[ée]los?|cyclisme|running|randonn[ée]e|camping|ski|natation|fietsen)\b"),
    (JARDIN, r"\b(jardin|jardinage|tondeuses?|bricolage|perceuses?|outillage|tuin|gereedschap|parquet|peinture murale)\b"),
    (MAISON, r"\b(canap[ée]s?|fauteuils?|tables?|chaises?|lampes?|luminaires?|matelas|linge de lit|rideaux?|d[ée]coration|meubles?|vaisselle|cuisine|meubel|verlichting)\b"),
    (JOUETS, r"\b(jouets?|lego|playmobil|peluches?|puzzles?|jeu de soci[ée]t[ée]|speelgoed|toys?)\b"),
    (CULTURE, r"\b(livres?|romans?|manga|dvd|blu-ray|vinyles?|boek|books?)\b"),
    (ALIMENTATION, r"\b(alimentation|[ée]picerie|caf[ée]|th[ée]|vin|bi[èe]re|chocolat|snack|boisson|voeding|wijn)\b"),
]

# Vêtements : le rayon dépend du public, déterminé plus haut.
_VETEMENT = r"\b(v[êe]tement|clothing|kleding|robe|dress|jupe|pantalon|jean|jeans|chemise|shirt|t-shirt|pull|sweat|hoodie|manteau|veste|jacket|blouse|costume|short|legging|lingerie|maillot|overhemd|broek|jas|blazer|combinaison|jumpsuit)\b"


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
            # Public indéterminé : on ne tranche pas ici, mais on laisse les
            # autres règles s'exprimer — « pantalon de jogging » relève du sport.

        for category, pattern in _RULES:
            if _has(pattern, text):
                return category

    return None
