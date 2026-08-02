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


def categories_of_department(department: str) -> list[str]:
    """Rayons d'un département, désigné par son nom ou par son slug.

    Un département n'existe pas en base : c'est un regroupement de rayons.
    Filtrer dessus suppose donc de l'étendre à ses rayons — sans quoi
    sélectionner « Beauté & Santé » ne restreint rien.
    """
    wanted = (department or "").strip().lower()
    if not wanted:
        return []
    for label, categories in DEPARTMENTS:
        if wanted in (label.lower(), slug_of(label)):
            return list(categories)
    return []


# ── Couleurs composées ──────────────────────────────────────────────────────
# En français, une quantité de couleurs se nomment « <teinte> <objet> » :
# gris souris, bleu marine, vert olive, gris perle, bleu canard, jaune
# moutarde. Le second mot n'y désigne pas l'objet — il qualifie la teinte.
#
# Sans ce garde-fou, « Tissu tailleur de laine — Gris souris » atterrissait en
# Informatique, sous-rayon « Claviers & Souris », et le rayon informatique du
# catalogue affichait des coupons de tissu. Constaté en production.
#
# On neutralise donc le second terme avant tout classement : la teinte reste,
# l'objet disparaît. « Gris souris » devient « gris », qui ne classe rien.
_TEINTES = (
    "gris|grise|bleu|bleue|vert|verte|rouge|jaune|rose|beige|brun|brune|noir|"
    "noire|blanc|blanche|orange|violet|violette|taupe|kaki|bordeaux|ivoire|"
    "anthracite|marron|mauve|turquoise|corail|sable|creme|crème"
)
_COULEUR_COMPOSEE = re.compile(
    rf"\b({_TEINTES})[\s-]+"
    r"(souris|marine|olive|perle|canard|moutarde|p[êe]che|amande|brique|"
    r"cha(?:r|)bon|charbon|petrole|pétrole|lavande|prune|abricot|caramel|"
    r"chocolat|caf[ée]|paille|argent|or|bronze|cuivre|nuit|ciel|ardoise|"
    r"anthracite|poudr[ée]e?|glac[ée]e?|clair|claire|fonc[ée]e?|pastel)\b",
    re.IGNORECASE,
)


def strip_colour_compounds(text: str) -> str:
    """Retire l'objet d'une couleur composée, en gardant la teinte.

    « Gris souris » → « gris ». « Bleu canard » → « bleu ». Sans quoi le
    second terme est lu comme le produit lui-même.
    """
    if not text:
        return text
    return _COULEUR_COMPOSEE.sub(lambda m: m.group(1), text)


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
    # « souris » exige un contexte informatique : seul, il désigne bien plus
    # souvent un animal, un imprimé de tissu ou une pièce de puzzle. Constaté en
    # production — le rayon informatique affichait des coupons de tissu et des
    # patrons de couture. Le qualificatif peut précéder ou suivre le mot.
    (INFORMATIQUE,
     r"(?=.*\bsouris\b)(?=.*\b(?:sans[-\s]?fil|optique|gamer|gaming|ergonomiques?|"
     r"bluetooth|filaires?|verticales?|usb|dpi|laser|rechargeables?|claviers?|"
     r"combo|molette)\b)"),
    (INFORMATIQUE, r"\btapis de souris\b"),
    (INFORMATIQUE, r"\b(ordinateurs?|laptops?|pc\b|macbook|notebooks?|claviers?|"
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


# ─────────────────────────────────────────────────────────────────────────────
# Troisième niveau — les sous-rayons.
#
# « Chaussures » ne se parcourt pas : on cherche des baskets ou des bottes. Les
# motifs sont évalués dans l'ordre au sein du rayon déjà déterminé, ce qui les
# rend beaucoup plus sûrs qu'au premier niveau — « bottes » ne peut plus être
# confondu avec autre chose une fois qu'on sait qu'on est dans les chaussures.
# ─────────────────────────────────────────────────────────────────────────────
SUBCATEGORIES: dict[str, list[tuple[str, str]]] = {
    CHAUSSURES: [
        ("Baskets & Sneakers", r"\b(baskets?|sneakers?|running|trainers?)\b"),
        ("Bottes & Bottines", r"\b(bottes?|bottines?|boots?|laarzen)\b"),
        ("Escarpins & Talons", r"\b(escarpins?|talons?|heels?|stiletto|mules?)\b"),
        ("Sandales", r"\b(sandales?|sandals?|tongs?|claquettes?)\b"),
        ("Mocassins & Ville", r"\b(mocassins?|derbies?|richelieu|habill[ée]es?|loafers?)\b"),
        ("Chaussons", r"\b(chaussons?|pantoufles?|slippers?)\b"),
        ("Semelles & Entretien", r"\b(semelles?|insoles?|lacets?|cirage)\b"),
    ],
    MODE_FEMME: [
        ("Robes", r"\b(robes?|dress(es)?|jurk)\b"),
        ("Jupes", r"\b(jupes?|skirts?|rok)\b"),
        ("Hauts & T-shirts", r"\b(tops?|t-shirts?|blouses?|chemisiers?|d[ée]bardeurs?)\b"),
        ("Pulls & Sweats", r"\b(pulls?|sweats?|sweaters?|hoodies?|gilets?|cardigans?)\b"),
        ("Pantalons & Jeans", r"\b(pantalons?|jeans?|leggings?|shorts?|trousers?)\b"),
        ("Manteaux & Vestes", r"\b(manteaux?|vestes?|jackets?|blousons?|parkas?|trench)\b"),
        ("Lingerie & Nuit", r"\b(lingerie|soutien-gorge|culottes?|pyjamas?|nuisettes?|sleepwears?)\b"),
        ("Maillots de bain", r"\b(maillots? de bain|bikinis?|swimwear)\b"),
    ],
    MODE_HOMME: [
        ("Chemises", r"\b(chemises?|overhemd|shirts?)\b"),
        ("T-shirts & Polos", r"\b(t-shirts?|polos?|d[ée]bardeurs?|maillots?|tops?)\b"),
        ("Pulls & Sweats", r"\b(pulls?|sweats?|sweaters?|hoodies?|gilets?|cardigans?)\b"),
        ("Pantalons & Jeans", r"\b(pantalons?|jeans?|chinos?|shorts?|trousers?|broek)\b"),
        ("Manteaux & Vestes", r"\b(manteaux?|vestes?|jackets?|blousons?|parkas?|jas)\b"),
        ("Sous-vêtements", r"\b(cale[çc]ons?|boxers?|slips?|underwear|ondergoed)\b"),
        ("Chaussettes", r"\b(chaussettes?|socks?|sokken)\b"),
        ("Costumes", r"\b(costumes?|suits?|blazers?|smoking)\b"),
    ],
    MODE_ENFANT: [
        ("Bébé (0-2 ans)", r"\b(b[ée]b[ée]s?|baby|naissance|body|bodys?)\b"),
        ("Fille", r"\b(filles?|girls?|meisjes)\b"),
        ("Garçon", r"\b(gar[çc]ons?|boys?|jongens)\b"),
        ("Manteaux & Vestes", r"\b(manteaux?|vestes?|jackets?|blousons?)\b"),
    ],
    INFORMATIQUE: [
        ("Ordinateurs portables", r"\b(ordinateurs? portables?|laptops?|macbook|notebooks?)\b"),
        ("Écrans", r"\b([ée]crans?|monitors?|moniteurs?)\b"),
        # Même garde-fou qu'au premier niveau : « souris » seul ne suffit pas.
        ("Claviers & Souris",
         r"\b(claviers?|keyboards?|mice)\b|"
         r"(?=.*\bsouris\b)(?=.*\b(?:sans[-\s]?fil|optique|gamer|gaming|"
         r"ergonomiques?|bluetooth|filaires?|verticales?|usb|dpi|laser|combo)\b)"),
        ("Stockage", r"\b(ssd|disques? durs?|cl[ée]s? usb|hdd|nvme|cartes? m[ée]moire)\b"),
        ("Imprimantes", r"\b(imprimantes?|scanners?|cartouches?|toner)\b"),
        ("Réseau", r"\b(routeurs?|switch|wifi|r[ée]p[ée]teurs?|modems?)\b"),
        ("Câbles & Adaptateurs", r"\b(c[âa]bles?|adaptateurs?|hubs?|docking)\b"),
    ],
    TELEPHONIE: [
        ("Smartphones", r"\b(smartphones?|iphone|galaxy|t[ée]l[ée]phones? mobiles?)\b"),
        ("Coques & Protections", r"\b(coques?|[ée]tuis?|prot[èe]ge-[ée]crans?|verre tremp[ée])\b"),
        ("Chargeurs & Batteries", r"\b(chargeurs?|powerbanks?|batteries?|c[âa]bles? de charge)\b"),
        ("Écouteurs", r"\b([ée]couteurs?|airpods|earbuds|oreillettes?)\b"),
        ("Montres connectées", r"\b(montres? connect[ée]es?|smartwatch|bracelets? connect[ée]s?)\b"),
    ],
    TV_SON: [
        ("Téléviseurs", r"\b(t[ée]l[ée]viseurs?|\btv\b|oled|qled)\b"),
        ("Casques audio", r"\b(casques?|headphones?|koptelefoon)\b"),
        ("Enceintes", r"\b(enceintes?|speakers?|haut-parleurs?)\b"),
        ("Barres de son", r"\b(barres? de son|soundbars?|home cinema)\b"),
        ("Platines & Hi-Fi", r"\b(platines?|amplis?|hifi|hi-fi|vinyles?)\b"),
    ],
    BIJOUX: [
        ("Colliers & Pendentifs", r"\b(colliers?|necklaces?|pendentifs?|pendants?|cha[îi]nes?|ketting)\b"),
        ("Bracelets", r"\b(bracelets?|joncs?|gourmettes?)\b"),
        ("Bagues", r"\b(bagues?|rings?|alliances?|chevali[èe]res?)\b"),
        ("Boucles d'oreilles", r"\b(boucles? d'oreilles?|earrings?|cr[ée]oles?|puces?)\b"),
        ("Montres", r"\b(montres?|watch(es)?|horloges?)\b"),
    ],
    BAGAGERIE: [
        ("Sacs à main", r"\b(sacs? [àa] main|handbags?|handtas|cabas|besaces?|bandouli[èe]res?)\b"),
        ("Sacs à dos", r"\b(sacs? [àa] dos|backpacks?|rugzak)\b"),
        ("Valises & Bagages", r"\b(valises?|suitcases?|bagages?|luggage|trolleys?)\b"),
        ("Portefeuilles", r"\b(portefeuilles?|wallets?|porte-cartes?|porte-monnaie)\b"),
        ("Sacs banane & Pochettes", r"\b(sacs? banane|bananes?|pochettes?|sacoches?)\b"),
    ],
    ACCESSOIRES: [
        ("Lunettes de soleil", r"\b(lunettes? de soleil|sunglasses|solaires?)\b"),
        ("Ceintures", r"\b(ceintures?|belts?|riemen)\b"),
        ("Chapeaux & Casquettes", r"\b(chapeaux?|casquettes?|bonnets?|b[ée]rets?|hats?|caps?|bobs?)\b"),
        ("Écharpes & Foulards", r"\b([ée]charpes?|foulards?|ch[èa]les?|scarf|scarves)\b"),
        ("Gants", r"\b(gants?|gloves|moufles?)\b"),
        ("Cravates", r"\b(cravates?|ties?|n[oœ]uds? papillon)\b"),
    ],
    BEAUTE: [
        ("Parfums", r"\b(parfums?|eaux? de parfum|eaux? de toilette|fragrances?)\b"),
        ("Maquillage", r"\b(maquillage|make\s?up|rouges? [àa] l[èe]vres|lipstick|mascaras?|"
                       r"fonds? de teint|eyeliner|fards?)\b"),
        ("Soins visage", r"\b(soins? visage|cr[èe]mes?|s[ée]rums?|skincare|huidverzorging|"
                         r"gezicht|toner|masques?)\b"),
        ("Cheveux", r"\b(shampooings?|shampoo|conditioner|apr[èe]s-shampooing|haircare|"
                     r"haarverzorging|colorations?|perruques?|wigs?|extensions?)\b"),
        ("Ongles", r"\b(ongles?|nails?|vernis|manucure)\b"),
    ],
    MAISON: [
        ("Meubles", r"\b(meubles?|canap[ée]s?|fauteuils?|tables?|chaises?|armoires?|"
                     r"[ée]tag[èe]res?|meubel)\b"),
        ("Luminaires", r"\b(lampes?|luminaires?|suspensions?|appliques?|verlichting|ampoules?)\b"),
        ("Linge de maison", r"\b(linge de lit|draps?|couettes?|serviettes?|rideaux?|"
                             r"coussins?|plaids?|tapis)\b"),
        ("Vaisselle & Cuisine", r"\b(vaisselle|assiettes?|verres?|couverts?|casseroles?|po[êe]les?)\b"),
        ("Décoration", r"\b(d[ée]corations?|cadres?|bougies?|vases?|miroirs?)\b"),
        ("Entretien", r"\b(schoonmaak|nettoyage|entretien|lessives?|d[ée]tergents?)\b"),
    ],
    ELECTROMENAGER: [
        ("Gros électroménager", r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateurs?|frigos?|"
                                 r"cong[ée]lateurs?|fours?|wasmachines?|koelkast)\b"),
        ("Petit électroménager", r"\b(cafeti[èe]res?|bouilloires?|grille-pains?|blenders?|"
                                  r"robots? cuiseur|friteuses?|micro-ondes)\b"),
        ("Aspirateurs", r"\b(aspirateurs?|vacuum cleaners?|balais? vapeur)\b"),
        ("Climatisation & Chauffage", r"\b(ventilateurs?|climatiseurs?|chauffages?|"
                                       r"radiateurs?|purificateurs?|humidificateurs?)\b"),
    ],
    SPORT: [
        ("Fitness & Musculation", r"\b(fitness|musculation|halt[èe]res?|tapis de course|yoga)\b"),
        ("Cyclisme", r"\b(v[ée]los?|cyclisme|fietsen|casques? v[ée]lo)\b"),
        ("Running", r"\b(running|course [àa] pied|jogging)\b"),
        ("Sports collectifs", r"\b(football|basket-?ball|handball|rugby|volley)\b"),
        ("Camping & Randonnée", r"\b(camping|randonn[ée]e|tentes?|sacs? de couchage)\b"),
        ("Sports d'hiver", r"\b(ski|snowboard|luges?)\b"),
    ],
    AUTO: [
        ("Pneus", r"\b(pneus?|tyres?|banden)\b"),
        ("Jantes & Roues", r"\b(jantes?|wheels?|enjoliveurs?)\b"),
        ("Éclairage", r"\b([ée]clairages?|phares?|ampoules?|led|fog lights?|headlights?)\b"),
        ("Entretien", r"\b(huiles? moteur|filtres?|batteries?|essuie-glaces?)\b"),
        ("Accessoires auto", r"\b(tapis de sol|housses?|supports? t[ée]l[ée]phone|chargeurs? allume-cigare)\b"),
    ],
    BEBE: [
        ("Poussettes & Sièges auto", r"\b(poussettes?|strollers?|si[èe]ges? auto|maxi-cosi)\b"),
        ("Repas & Biberons", r"\b(biberons?|bavoirs?|slabbetjes?|chaises? hautes?|"
                              r"st[ée]rilisateurs?)\b"),
        ("Couches & Toilette", r"\b(couches?|luiers?|lingettes?|tables? [àa] langer)\b"),
        ("Chambre bébé", r"\b(lits? b[ée]b[ée]|berceaux?|matelas b[ée]b[ée]|tours? de lit)\b"),
    ],
    ANIMALERIE: [
        ("Chien", r"\b(chiens?|dogs?|hond|hondenvoer)\b"),
        ("Chat", r"\b(chats?|cats?|\bkat\b|kattenvoer|liti[èe]res?)\b"),
        ("Petits animaux", r"\b(rongeurs?|lapins?|hamsters?|oiseaux?|aquarium|poissons?)\b"),
    ],
    GAMING: [
        ("Consoles", r"\b(consoles?|playstation|ps5|ps4|xbox|nintendo|switch)\b"),
        ("Jeux vidéo", r"\b(jeux? vid[ée]o|video\s?games?|cd keys?|steam)\b"),
        ("Accessoires gaming", r"\b(manettes?|controllers?|casques? gaming|si[èe]ges? gamer|"
                                r"tapis de souris)\b"),
    ],
    JARDIN: [
        ("Outillage", r"\b(perceuses?|visseuses?|scies?|outillages?|gereedschap|tournevis)\b"),
        ("Jardinage", r"\b(tondeuses?|taille-haies?|arrosages?|tuingereedschap|s[ée]cateurs?)\b"),
        ("Mobilier de jardin", r"\b(salons? de jardin|parasols?|barbecues?|transats?)\b"),
        ("Revêtements", r"\b(parquets?|carrelages?|peintures?|papiers? peints?)\b"),
    ],
}


def classify_subcategory(
    category: str | None, name: str | None = None, merchant_category: str | None = None
) -> str | None:
    """Sous-rayon d'une offre à l'intérieur de son rayon, ou None.

    Le rayon est déjà connu, ce qui rend les motifs bien plus sûrs qu'au premier
    niveau : « bottes » ne peut plus être confondu avec autre chose une fois
    qu'on sait qu'on est dans les chaussures.
    """
    rules = SUBCATEGORIES.get(category or "")
    if not rules:
        return None
    for text in (
        strip_colour_compounds((name or "").strip()),
        strip_colour_compounds((merchant_category or "").strip()),
    ):
        if not text:
            continue
        for label, pattern in rules:
            if _has(pattern, text):
                return label
    return None


def subcategories_of(category: str) -> list[str]:
    """Sous-rayons publiés d'un rayon, dans l'ordre du menu."""
    return [label for label, _ in SUBCATEGORIES.get(category, [])]


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
    # Les couleurs composées sont neutralisées avant tout : « gris souris » ne
    # doit pas être lu comme une souris d'ordinateur.
    name = strip_colour_compounds((name or "").strip())
    merchant_category = strip_colour_compounds((merchant_category or "").strip())
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
