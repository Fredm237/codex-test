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
VOYAGES = "Voyages & Séjours"

# Nature transactionnelle : elle dicte si un prix peut être comparé comme celui
# d'un produit physique. Cette dimension complète les rayons, elle ne s'y
# substitue pas.
PHYSICAL_PRODUCT = "physical_product"
TECH_ACCESSORY = "tech_accessory"
ACCOMMODATION = "accommodation"
SERVICE = "service"
DIGITAL_CONTENT = "digital_content"
UNKNOWN = "unknown"
EAN_COMPARABLE_KINDS = frozenset({PHYSICAL_PRODUCT, TECH_ACCESSORY})

ALL_CATEGORIES = [
    INFORMATIQUE, TELEPHONIE, PHOTO, GAMING, TV_SON, ELECTROMENAGER, MAISON,
    JARDIN, MODE_FEMME, MODE_HOMME, MODE_ENFANT, CHAUSSURES, BIJOUX, BEAUTE,
    SANTE, SPORT, AUTO, BEBE, ANIMALERIE, BAGAGERIE, CULTURE, ALIMENTATION,
    JOUETS, ACCESSOIRES, LOISIRS, MODE, VOYAGES,
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
    ("Voyages", [VOYAGES]),
]

_DEPARTMENT_OF = {c: d for d, cats in DEPARTMENTS for c in cats}


_ACCOMMODATION = (
    r"\b(appartements? de vacances|maison(?:s)? de vacances|g[îi]tes?|h[ôo]tels?|"
    r"chambres? d['’ ]h[ôo]tel|hotel kamers?|vakantiehuis(?:jes)?|vakantieparken?|"
    r"ferienwohnungen?|ferienh[aä]user?|ferienparks?|holiday homes?|holiday parks?|"
    r"villas?|bungalows?|mobile homes?|campings?|wohnungen?|woningen?)\b"
)
_DIGITAL_CONTENT = r"\b(licen[cs]e keys?|cd keys?|game keys?|activation keys?|gift cards?|cartes? cadeaux?|software download|t[ée]l[ée]chargement|download|abonnements?|subscriptions?)\b"
# Les mots « montage », « installation » et « réparation » figurent souvent dans
# la description d'un composant (kit, support, glissière, outil). Ils ne décrivent
# une prestation que si le texte ou la catégorie l'affirme explicitement.
_SERVICE_DIRECT = (
    r"\b(repair service|garantie [ée]tendue|extended warranty|assurance|"
    r"insurance|cours de|training|service\s+(?:de|d['’])\s*"
    r"(?:montage|installation|r[ée]paration|maintenance))\b"
)
_SERVICE_ACTION = r"\b(installation|montage|r[ée]paration)\b"
_SERVICE_CONTEXT = r"\b([àa]\s+domicile|sur\s+(?:site|place)|professionnel(?:le)?|intervention)\b"
_SERVICE_CATEGORY = r"\b(services?|prestations?)\b"
_TECH_ACCESSORY = r"\b(coques?|backcovers?|bookcases?|screen ?protectors?|chargeurs?|chargers?|c[âa]bles? de charge|charging cables?|power ?banks?|[ée]tuis?)\b"

# Certains mots sont intrinsèquement ambigus : un studio peut être un logement,
# un espace de création ou un produit. Le contexte explicite d’un marchand de
# réservation permet de les comprendre sans étendre aveuglément une règle à tout
# le catalogue.
_ACCOMMODATION_MERCHANT = r"\bbungalow\.net\b"
_ACCOMMODATION_MERCHANT_CATEGORY = (
    r"\b(appartement(?:en)?s?|villas?|villen|studios?|studio's|"
    r"parcs?\s+de\s+vacances|ferienparks?|holiday parks?|bungalows?)\b"
)

# Le flux autobandenmarkt expose seulement les codes de véhicule (PKW, MO,
# OFF, LLKW) et un identifiant numérique de gamme. Ces codes ne sont fiables
# que chez ce spécialiste de pneus ; ils ne deviennent jamais une règle globale.
_TYRE_MERCHANT = r"\b(?:autobandenmarkt|123pneus)\b"
_TYRE_REFERENCE = r"\b(?:pkw|mo|off|llkw)\b"
_TYRE_CATEGORY = r"\b(pneus?|tyres?|banden|reifen|pneumatici)\b"
_TYRE_DIMENSION = r"\b\d{3}/\d{2}\s*r\d{2}(?:[a-z]{0,4})?\b"

# Andlight est un marchand spécialisé en luminaires, mobilier et décoration.
# Son flux néerlandais peut omettre la catégorie brute et ne donner qu’un nom
# de collection (« Paletti », « Componibili ») : ce contexte est donc un dernier
# recours, après tous les signaux produits et rayons explicites.
_ANDLIGHT_MERCHANT = r"\bandlight\b"

# Profils de spécialistes vérifiés dans les flux réels : ils ne s'appliquent
# qu'en dernier recours, quand le nom et la catégorie marchande ne permettent
# pas déjà un classement plus précis. Chaque entrée reste donc réversible et
# ne transforme jamais ces noms en mots-clés globaux.
_SPECIALIST_MERCHANT_CONTEXTS: tuple[tuple[str, str], ...] = (
    (r"\bisotiger\b", AUTO),
    (r"\bgsmnet\b", TELEPHONIE),
    (r"\boverhemden\b", MODE_HOMME),
    (r"\bmilk\s+bar\s+babystore\b", BEBE),
    (r"\bbobshop\b", SPORT),
    (r"\btapis\.fr\b", MAISON),
)


def _specialist_aisle(merchant_name: str | None) -> str | None:
    for pattern, category in _SPECIALIST_MERCHANT_CONTEXTS:
        if _has(pattern, merchant_name or ""):
            return category
    return None


def _is_tyre_specialist_reference(name: str | None, merchant_name: str | None) -> bool:
    return bool(
        name and merchant_name
        and _has(_TYRE_MERCHANT, merchant_name)
        and _has(_TYRE_REFERENCE, name)
    )


def classify_offer_kind(
    merchant_category: str | None,
    name: str | None = None,
    brand: str | None = None,
    merchant_name: str | None = None,
) -> str:
    """Nature transactionnelle observée, sans inférer un contexte d'achat.

    Les séjours sont volontairement reconnus avant les mots ambigus du commerce
    physique : « mobile home » doit devenir une réservation, pas un téléphone.
    """
    del brand  # Réservé au contrat stable de la fonction.
    name = strip_colour_compounds((name or "").strip())
    merchant_category = strip_colour_compounds((merchant_category or "").strip())
    merchant_name = (merchant_name or "").strip()
    text = " ".join(part for part in (name, merchant_category) if part)
    if not text:
        return UNKNOWN
    # « Camping » peut être le nom d’un modèle de pneu. Une dimension de pneu
    # explicite dans une catégorie pneu décrit un bien physique, pas un séjour.
    if _has(_TYRE_CATEGORY, merchant_category) and _has(_TYRE_DIMENSION, name):
        return PHYSICAL_PRODUCT
    if _has(_ACCOMMODATION, text) or (
        _has(_ACCOMMODATION_MERCHANT, merchant_name)
        and _has(_ACCOMMODATION_MERCHANT_CATEGORY, merchant_category)
    ):
        return ACCOMMODATION
    if _has(_DIGITAL_CONTENT, text):
        return DIGITAL_CONTENT
    if _has(_SERVICE_DIRECT, text) or (
        _has(_SERVICE_ACTION, name)
        and (_has(_SERVICE_CONTEXT, name) or _has(_SERVICE_CATEGORY, merchant_category))
    ):
        return SERVICE
    if _has(_TECH_ACCESSORY, text):
        return TECH_ACCESSORY
    return PHYSICAL_PRODUCT


def is_ean_comparable(offer_kind: str | None) -> bool:
    """Un EAN ne rend comparable que les biens physiques du même produit."""
    # Les anciennes offres NULL sont traitées comme physiques jusqu'au rattrapage
    # pour ne pas faire disparaître brusquement le catalogue existant.
    return offer_kind is None or offer_kind in EAN_COMPARABLE_KINDS


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

# Un objet fini fait d'une matière reste un objet fini : « housse de couette
# en percale » est du linge de maison, pas de la mercerie. La règle du support
# ne s'applique donc que si aucun nom d'objet fini n'apparaît — c'est le nom de
# tête qui décide, pas la matière qui le qualifie.
_OBJET_FINI = re.compile(
    r"\b(housses?|couettes?|draps?|taies?|rideaux?|voilages?|nappes?|"
    r"serviettes?|coussins?|plaids?|couvertures?|chemises?|chemisiers?|robes?|"
    r"pantalons?|jupes?|vestes?|manteaux?|pulls?|blouses?|tuniques?|"
    r"combinaisons?|tabliers?|torchons?|peignoirs?|pyjamas?|gigoteuses?|"
    r"[ée]charpes?|bonnets?|gants?|sacs?\s+[àa]\s+main|matelas|oreillers?|"
    # Néerlandais : « Zomerslaapzak Jersey » est une gigoteuse en jersey, pas
    # un coupon de jersey. Sans ces noms d'objet fini, le support gagnait et
    # l'article partait en Loisirs créatifs.
    r"slaapzakken?|zomerslaapzak|winterslaapzak|dekbedovertrekken?|"
    r"dekbedovertrek|hoeslakens?|kussenslopen?|kussensloop|handdoeken?|"
    r"badjassen?|badjas|rompers?|rompertjes?)\b",
    re.IGNORECASE,
)


# ── Le support l'emporte sur le motif ───────────────────────────────────────
#
# Un tissu imprimé de souris est un tissu, pas un périphérique. Un patron de
# couture pour peluches est un article de mercerie, pas un jouet. Un livre sur
# les chiens est un livre, pas de l'animalerie. Une coque de téléphone à motif
# chat est un accessoire de téléphonie.
#
# C'est la cause principale des rayons incohérents constatés en production, et
# elle est bien plus large que le seul cas « souris » : sur un échantillon de
# quinze libellés de mercerie, un seul était correctement classé. Le motif
# imprimé sur un objet piège n'importe quel classement par mots-clés, quel que
# soit le rayon visé.
#
# Ces règles passent donc AVANT toutes les autres, et gagnent. Elles sont
# volontairement étroites : seuls des termes qui désignent le support sans
# ambiguïté y figurent. « Lin » en est absent — « chemise en lin » est un
# vêtement.
_SUPPORTS: list[tuple[str, str]] = [
    # Mercerie et tissus au mètre. Le nom du motif suit presque toujours un
    # tiret : « Popeline coton - Petites voitures ».
    (LOISIRS,
     r"\b(tissus?|jerseys?|popelines?|cretonnes?|tricotines?|gabardines?|"
     r"serg[ée]s?|mousselines?|batistes?|percales?|bord\s+c[ôo]tes?|"
     r"molletons?|cr[ée]pons?|bourrettes?|piqu[ée]s?\s+\d*\s*%?\s*coton|"
     r"sweat\s+molletonn[ée]|polaire\s+double\s+face|viscose\s+unie|"
     r"coupons?\s+de\s+\d|au\s+m[èe]tre|mercerie|toiles?\s+[àa]\s+patrons?|"
     r"kits?\s+(?:de\s+)?couture|patrons?\b|"
     r"patrons?\s+(?:burda|mccall(?:'s)?|simplicity|vogue|new\s+look|butterick|know\s+me)|"
     r"patrons?\s+(?:de|pour)\s+(?:couture|robes?|jupes?|pantalons?|manteaux?|vestes?|"
     r"chemises?|hauts?|tops?|combinaisons?|ensembles?|peluches?|enfants?)|"
     r"patrons?\s+(?:n[°ºo]|\d)|sewing\s+patterns?|schnittmuster|n[äa]hmuster|"
     r"fermetures?\s+[ée]clair|fil\s+[àa]\s+coudre|boutons?\s+(?:de\s+couture|mercerie))\b"),
    # Livres et affiches : le sujet ne détermine pas le rayon.
    (CULTURE,
     r"\b(livres?\s+sur|guides?\s+de|romans?|beaux?[-\s]livres?|"
     r"bandes?\s+dessin[ée]es?|mangas?)\b"),
    (MAISON,
     r"\b(affiches?|posters?|stickers?\s+muraux?|papiers?\s+peints?|"
     r"toiles?\s+imprim[ée]es?|cadres?\s+photo)\b"),
    # Coques et étuis : c'est de la téléphonie, quel que soit le dessin dessus.
    (TELEPHONIE, r"\b(coques?|[ée]tuis?)\s+(?:de\s+)?(?:t[ée]l[ée]phone|smartphone|iphone|samsung)\b"),
    # Accessoires de protection sous libellé marchand anglais : ~12 000 offres non
    # classées (Phone Cover, Tablet Cover, Screenprotector, Ereader Cover). Le
    # rayon Téléphonie les accueille, y compris pour tablette et liseuse, faute de
    # rayon dédié aux accessoires mobiles.
    (TELEPHONIE, r"\b(?:phone|tablet|ereader|e-reader)\s*[-–]?\s*"
                 r"(?:covers?|cases?|screenprotectors?|screen protectors?|"
                 r"buttons?|cord straps?)\b"),
    (TELEPHONIE, r"\b(?:screenprotectors?|bookcases?|backcovers?)\b"),
]


# (catégorie, motif). La première correspondance gagne : du plus spécifique au
# plus général.
_RULES: list[tuple[str, str]] = [
    (BEBE, r"\b(b[ée]b[ée]s?|baby|babys|poussettes?|stroller|couches?|luiers?|biberons?|"
           r"puericulture|puéricultur|bavoirs?|slabbetjes?|mother\s*&\s*kids|tricycles?|"
           r"draagzak|maternit[ée]|kinderstoel|kinderwagen|babyfoon|wieg|wiegjes?|"
           r"slaapzakken?|zomerslaapzak|winterslaapzak|gigoteuses?|"
           r"si[èe]ges? auto|chaises? hautes?|tables? [àa] langer|st[ée]rilisateurs?)\b"),
    (ANIMALERIE, r"\b(chiens?|chats?|dogs?|cats?|hond|kat|hondenvoer|kattenvoer|animal|"
                 r"animalerie|croquettes?|aquarium|liti[èe]re|dierenvoeding|"
                 r"chiots?|puppy|puppies|chatons?|kittens?|niches?\s+pour|"
                 r"paniers?\s+pour\s+(?:chien|chat)|laisses?|colliers?\s+pour\s+(?:chien|chat))\b"),
    (AUTO, r"\b(pneus?|tyres?|banden|wheels?|jantes?|voitures?|autos?|automotive|motos?|"
           r"scooters?|v[ée]hicules?|car\s?parts?|huile moteur|car\b|autoteile|"
           r"zomerbanden?|winterbanden?|allseasonbanden?|vierseizoenenbanden?|"
           r"pneus? (?:[ée]t[ée]|hiver|4 saisons))\b"),
    # Dimension de pneu : « 225/60 R17 99H ». C'est le signal le plus fiable du
    # catalogue, et il ne peut désigner rien d'autre. Il rattrape les références
    # dont le nom ne dit que la gamme (« Sport Maxx Race 2 »).
    (AUTO, r"\b\d{3}/\d{2}\s*(?:z)?r\s?\d{2}\b"),
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
                   r"tablettes?|software|cartouches? d['’ ]encre|ink cartridges?|toner)\b"),
    # Stations d'alimentation et batteries nomades : famille absente de toute
    # règle jusqu'ici. « Station d'alimentation » exige un contexte électrique :
    # sans cela on capturait « Station d'alimentation pour oiseaux », qui est un
    # distributeur de graines de jardin.
    (INFORMATIQUE, r"\b(powerstations?|power\s+stations?|groupes? [ée]lectrog[èe]nes?|"
                   r"batteries? nomades?|onduleurs?)\b"),
    (INFORMATIQUE, r"\bstations? d'alimentation\b(?=.*\b(?:portables?|solaires?|"
                   r"[ée]lectriques?|batteries?|\d+\s*wh|\d+\s*w\b))"),
    (PHOTO, r"\b(appareils? photo|cameras?|caméras?|objectifs?|reflex|drones?|gopro|"
            r"tr[ée]pieds?|photographie)\b"),
    (TV_SON, r"\b(t[ée]l[ée]viseurs?|\btv\b|home cinema|barres? de son|soundbars?|enceintes?|"
             r"casques? audio|hifi|hi-fi|platines?|headphones?)\b"),
    (ELECTROMENAGER, r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateurs?|frigos?|"
                     r"cong[ée]lateurs?|fours?|micro-ondes|aspirateurs?|cafeti[èe]res?|"
                     r"robots? cuiseur|wasmachines?|koelkast|home appliances?|"
                     r"huishoudelijke|ventilateurs?|vacuum cleaners?|wassen, strijken)\b"),
    # « crème » n'y figure plus comme mot nu : en néerlandais c'est une teinte,
    # et le rayon affichait un salon de jardin « Bruin Crème », un paravent
    # « Uitschuifbaar – Crème » et une applique murale « wandlamp – crème ».
    # Constaté en production. Seules les crèmes qualifiées classent désormais.
    (BEAUTE, r"\b(parfums?|eaux? de parfum|eaux? de toilette|fragrances?|maquillage|make\s?up|"
             r"cosm[ée]tiques?|cosmetics?|beauty|s[ée]rums?|shampooings?|shampoo|"
             r"conditioner|soins? visage|skincare|haircare|hair care|haarverzorging|"
             r"verzorgingsproducten|gezicht|huidverzorging|toner|lipstick|eyeliner|nails?|"
             r"ongles?|perruques?|wigs?|hair extensions?|vernis|lentilles? color[ée]es?|"
             r"color(?:ed)? lenses?|contact lenses?)\b"),
    # Les crèmes qualifiées, elles, sont bien des soins. Le qualificatif peut
    # précéder (handcrème) ou suivre (crème hydratante) le mot.
    (BEAUTE, r"\bcr[èe]mes?\s+(?:hydratantes?|nourrissantes?|solaires?|de\s+jour|"
             r"de\s+nuit|anti[-\s]?[âa]ge|amincissantes?|d[ée]pilatoires?|lavantes?|"
             r"pour\s+les\s+mains|mains|corps|visage|contour\s+des\s+yeux)\b"),
    (BEAUTE, r"\b(?:hand|dag|nacht|body|zonne|oog|gezichts)cr[èe]mes?\b"),
    (BEAUTE, r"\bcr[èe]me\s+(?:soft|douche|de\s+douche)\b"),
    # Signaux échappés à la première passe : huiles de massage et parapharmacie.
    (BEAUTE, r"\b(?:huiles? de massage|massageolie|massage oils?|parapharmacie|"
             r"gommages?|scrubs?|d[ée]odorants?|deodorants?|savons?|zeep)\b"),
    # Familles de maquillage mesurées sur les offres réellement non classées en
    # base (`admin/unclassified`) : ~10 000 offres portaient un libellé marchand
    # de maquillage courant qu'aucune règle ne couvrait, en français comme en
    # néerlandais et en anglais.
    (BEAUTE, r"\b(?:foundations?|fonds? de teint|concealers?|anti[-\s]?cernes?|"
             r"mascaras?|lipglos+e?s?|lip\s?gloss|lippenstift(?:en)?|"
             r"rouges? à l[èe]vres|oogschaduw|fards? à paupi[èe]res|"
             r"eyeshadows?|wimpers|wenkbrauwen|nagels|nagellak|"
             r"gezichtsverzorging|lichaamsverzorging|huidverzorging|"
             r"bodywash|douchegel|face cleansers?|moisturi[sz]ers?|"
             r"scheren|ontharing|zonnebrand|sunscreens?|cr[èe]me & lotion)\b"),
    # « blush » est aussi un nom de couleur (robe blush, sneakers blush, coussin
    # blush) : mesuré comme régression sur trois rayons. Il n'est retenu que
    # qualifié ou seul en tête de libellé marchand.
    (BEAUTE, r"\bblush(?:es)?\s+(?:cr[èe]me|poudre|palette|stick|liquide|compact)\b"),
    (BEAUTE, r"^blush(?:es)?$"),
    # Pendules et horloges d'intérieur : placées AVANT Bijoux pour l'emporter sur
    # le « horloge » générique, qui désigne une montre chez les marchands belges.
    (MAISON, r"\bhorloges?\s+(?:murales?|de\s+parquet|comtoises?|à\s+coucou|de\s+table|"
             r"de\s+cuisine|d[ée]coratives?)\b"),
    (MAISON, r"\b(?:wandklokken?|wandklok|staande\s+klok|koekoeksklok)\b"),
    # Vaisselle et arts de la table : « tableware » et « eetset » manquaient, si
    # bien qu'un service de table « / Crème » n'était rangé nulle part.
    (MAISON, r"\b(?:tableware|eetsets?|servies|dinnerware|arts? de la table|"
             r"couverts?|cutlery|bestek)\b"),
    # Un luminaire décoré d'un ballon reste un luminaire : même principe que le
    # support qui l'emporte sur le motif. Placé avant Sport, sinon
    # « Lampe LED 3D avec impression ballon de football » partait en Sport.
    (MAISON, r"\b(?:lampes?|veilleuses?|lamps?|nachtlamp(?:jes?)?)\b(?=.*\b(?:led|3d|"
             r"d[ée]corative?s?|impression|murale?s?)\b)"),
    # Luminaires en danois/norvégien et néerlandais. `Lamper` (« lampes » en
    # danois) était à lui seul la 3e catégorie marchand non classée, avec 13 640
    # offres : le catalogue contient une quatrième langue, non anticipée au
    # diagnostic initial. Le mot est sans ambiguïté, contrairement à `pendant`.
    (MAISON, r"\b(?:lamper|lampen|binnenverlichting|buitenverlichting|"
             r"hanglamp(?:en)?|tafellamp(?:en)?|wandlamp(?:en)?|vloerlamp(?:en)?|"
             r"plafondlamp(?:en)?|staanlamp(?:en)?|lampenkap(?:pen)?)\b"),
    # Mobilier et décoration sous arborescence néerlandaise `Wonen & Koken`.
    (MAISON, r"\b(?:woondecoratie|overige meubels|tafels & stoelen|"
             r"woonaccessoires|keukenaccessoires)\b"),
    # Les pièges photographiques sont vendus avec un kit solaire : la caméra est
    # le produit, le panneau l'accessoire. Sans cette règle placée avant Jardin,
    # « panneaux solaires » l'emportait et les envoyait en Jardin & Bricolage.
    (PHOTO, r"\b(?:pi[èe]ges? photographiques?|cam[ée]ras? de chasse|"
            r"cam[ée]ras? pour la faune|trail cameras?|wildcameras?)\b"),
    (SANTE, r"\b(compl[ée]ments? alimentaires?|vitamines?|pharmacie|m[ée]dical|orthop[ée]dique|"
            r"tensiom[èe]tre|hygi[èeë]ne|huiles? essentielles?)\b"),
    # « ketting » et « pendant » sont retirés comme mots nus : en néerlandais
    # « kettingzaag » est une tronçonneuse et « fietsketting » une chaîne de vélo ;
    # en anglais « pendant lamp » est une suspension. Tous deux peuplaient le
    # rayon Bijoux & Montres en production.
    #
    # « horloge », en revanche, est CONSERVÉ ici. En Belgique francophone le mot
    # désigne commercialement une montre-bracelet : les flux marchands listent
    # « MIDO Ocean Star GMT Horloge » ou « Tissot PRC 100 Solar Horloge » en
    # catégorie « Watch ». Le retirer déplaçait 57 vraies montres vers Maison &
    # Déco sur un simple échantillon. Les pendules murales sont captées en amont
    # par une règle dédiée (« horloge murale », « wandklok »).
    (BIJOUX, r"\b(bijoux?|jewelry|jewellery|bagues?|rings?|colliers?|necklaces?|"
             r"pendentifs?|bracelets?|boucles? d'oreille|earrings?|montres?|"
             r"watch(es)?|horloges?|sieraden|halsketting|schakelketting)\b"),
    (BIJOUX, r"\bpendant\s+(?:necklaces?|charms?|earrings?)\b"),
    # Bracelets de montre : les flux les listent en catégorie « Strap », avec des
    # noms comme « Fossil Straps Flynn Sport Horlogeband ». Ils n'étaient rangés
    # nulle part.
    (BIJOUX, r"\b(?:horlogeband(?:en)?|bracelets? de montres?|watch straps?|"
             r"watchbands?)\b"),
    # Les mêmes bracelets apparaissent aussi en « … Sport band » ou « sport
    # bandje » sous la catégorie marchande « Strap » / « Smartwatch Strap ».
    # « band » seul est trop faible (bande de résistance, bandeau) : on exige le
    # contexte horloger apporté par « strap ».
    (BIJOUX, r"(?=.*\bstraps?\b)(?=.*\b(?:bandjes?|band|bands|horloge|watch|"
             r"smartwatch|fitbit|garmin)\b)"),
    (CHAUSSURES, r"\b(chaussures?|shoes?|baskets?|sneakers?|bottes?|boots?|escarpins?|heels?|"
                 r"mules?|sandales?|sandals?|schoenen|mocassins?|semelles?|insoles?|"
                 r"pantoufles?|slippers?)\b"),
    (BAGAGERIE, r"\b(sacs? [àa] main|sacs? [àa] dos|handbags?|backpacks?|valises?|suitcases?|"
                r"bagages?|luggage|trolleys?|portefeuilles?|wallets?|maroquinerie|handtas|"
                r"rugzak|bags?)\b"),
    (ACCESSOIRES, r"\b(accessoires?|accessories|lunettes? de soleil|sunglasses|ceintures?|"
                  r"belts?|[ée]charpes?|scarf|scarves|chapeaux?|hats?|casquettes?|caps?|"
                  r"gants?|gloves|bonnets?|cravates?|ties?|riemen)\b"),
    # « sport » seul ne classe plus : c'est un adjectif de gamme omniprésent dans
    # les noms commerciaux. « Potenza Sport » et « Cross Sport SP-9 » sont des
    # pneus Bridgestone, rangés en Sport & Loisirs en production. Un contexte
    # sportif explicite est désormais exigé, comme pour « souris ».
    (SPORT, r"\b(?:v[êée]tements?|chaussures?|maillots?|shorts?|brassi[èe]res?|sacs?|"
            r"[ée]quipements?|accessoires?|articles?|mat[ée]riels?|salles?|tenues?|"
            r"soutiens?[-\s]gorges?)\s+(?:de\s+)?sport\b"),
    (SPORT, r"\b(sportswear|sportartikelen|sportkleding|deportivo|deporte|"
            r"[ée]quipements? sportifs?)\b"),
    (SPORT, r"\b(fitness|musculation|halt[èe]res?|yoga|pilates|jogging|v[ée]los?|"
            r"cyclisme|running|course [àa] pied|randonn[ée]e|camping|ski|snowboard|"
            r"natation|fietsen|football|basket-?ball|handball|rugby|volley|tennis|"
            r"golf|boxe|escalade|kayak|p[ée]che|piscines?|spas? gonflables?|"
            r"zwembaden?)\b"),
    # « Surf » exige un contexte : c'est aussi une marque de lessive Unilever, dont
    # les références (« Surf Wasmiddel Berry Bliss ») atterrissaient en Sport.
    (SPORT, r"\b(?:planches? de surf|surfboards?|surfen|kitesurf|windsurf|"
            r"surf\s+(?:shop|camp|wax|leash)|combinaisons? de surf)\b"),
    # Angles morts constatés : ces familles n'étaient reconnues par aucune règle,
    # ce qui contribuait aux 20,3 % d'offres non rangées.
    (SPORT, r"\b(trottinettes?|steps?\s+elektrisch|elektrische\s+steps?|"
            r"gyroroues?|hoverboards?|monowheels?)\b"),
    # Plongée, snorkeling et masques de ski : familles absentes de toute règle,
    # ces masques n'étaient rangés nulle part.
    (SPORT, r"\b(?:plong[ée]e|diving|snorkel(?:ing|s)?|duiken|duikmaskers?|"
            r"masques? de plong[ée]e|tubas?|palmes?|apn[ée]e|skibrillen?|"
            r"snow(?:board)?\s+goggles?|ski\s+goggles?|masques? de ski)\b"),
    # Articles de baignade gonflables : « floating chair », « bouée », « luchtbed ».
    # Ces fauteuils flottants n'étaient rangés nulle part.
    (SPORT, r"\b(?:bou[ée]es?|zwembanden?|luchtbedden?|luchtbed|matelas gonflables?|"
            r"floating\s+(?:chairs?|loungers?|mats?)|pool\s+(?:floats?|loungers?)|"
            r"inflatable\s+(?:pool|lounge|float|floating)|brassards? de natation)\b"),
    (JARDIN, r"\b(jardins?|jardinage|tondeuses?|bricolage|perceuses?|outillage|tuin|"
             r"tuingereedschap|gereedschap|heimwerker[-\s]?zubeh[öo]r|parquet|peinture murale|garden tools?|"
             r"tron[çc]onneuses?|kettingzagen?|kettingzaag|panneaux? solaires?|"
             r"zonnepane(?:el|len)|barbecues?|salons? de jardin|tuinsets?|"
             r"tuinschermen?|tuinscherm|polyrattan)\b"),
    # Une arborescence marchand est une preuve plus forte qu’un titre minimal :
    # `Mobilier > …` et `Déco > …` décrivent explicitement la maison. Le motif
    # exige le séparateur hiérarchique pour ne pas absorber un mot isolé.
    (MAISON, r"\b(?:mobilier|d[ée]co)\s*>") ,
    # « tissus » est retiré de cette règle : il désigne la mercerie, traitée
    # plus haut par les supports. Le laisser ici renvoyait tous les coupons au
    # rayon Maison. Le linge de maison, lui, manquait entièrement.
    (MAISON, r"\b(canap[ée]s?|fauteuils?|tables?|chaises?|lampes?|luminaires?|matelas|"
             r"linge de (?:lit|maison)|housses? de (?:couette|coussin)|couettes?|"
             r"draps?(?:[-\s]housses?)?|taies? d'oreiller|oreillers?|plaids?|"
             r"rideaux?|voilages?|nappes?|d[ée]coration|meubles?|vaisselle|assiettes?|"
             r"cuisine|meubel|verlichting|schoonmaak|nettoyage|serviettes?|textile|"
             r"home\s*&\s*garden|huishouden|wandklokken?|wandklok|pendules?|"
             r"wandlampen?|wandlamp|appliques?|suspensions?|dekbedovertrekken?|"
             r"dekbedovertrek|hoeslakens?|kussenslopen?|kussensloop|handdoeken?|"
             r"paravents?|tuinkussens?|eetkamerstoel(?:en)?|eettafelstoel(?:en)?|salontafels?|"
             r"eettafels?|tafelspiegels?|tapijt(?:en)?|lampenvoet(?:en)?|armleuningen?)\b"),
    (MAISON, r"\bpendant\s+(?:lamps?|lights?|lighting)\b"),
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


# Usage sportif explicite : il tranche avant le public.
#
# Un maillot de football reste un article de sport, qu'il soit taillé pour homme,
# femme ou enfant. Ne figurent ici que des termes qui désignent la pratique
# elle-même, jamais une simple coupe : « sportif » ou « sport » nus en sont
# absents, sans quoi tout survêtement de ville y passerait.
_USAGE_SPORTIF = (
    r"\b(football|voetbal|basket-?ball|handball|rugby|volley(?:-?ball)?|tennis|"
    r"natation|swimming|zwemmen|cyclisme|v[ée]lo|wielrennen|running|jogging|"
    r"trail|marathon|fitness|musculation|yoga|pilates|ski|snowboard|escalade|"
    r"randonn[ée]e|trekking|boxe|judo|karat[ée]|athl[ée]tisme|gymnastique|"
    r"[ée]quitation|golf|hockey|badminton|padel|kayak|aviron|"
    r"maillots? de bain|zwembroek|badpak)\b"
    # « surf » n'est pas repris nu ici non plus : marque de lessive.
    r"|\b(?:planches? de surf|surfboards?|kitesurf|windsurf|surfen)\b"
    # « vêtements de sport », « tenue de sport » : le mot « sport » n'y est plus
    # nu, il est qualifié par le nom qu'il complète. On l'accepte donc ici.
    # Attention : la classe [ée] ne couvre pas « ê ». « Vêtements » s'écrit avec
    # un circonflexe (U+00EA) et échappait donc à ce motif.
    r"|\b(?:v[êée]tements?|tenues?|habits?|maillots?|brassi[èe]res?|shorts?|"
    r"leggings?|surv[êée]tements?|soutiens?[-\s]gorges?|chaussettes?|"
    r"sacs?|[ée]quipements?|articles?)\s+(?:de\s+)?sport\b"
    r"|\b(?:sportkleding|sportswear|sporttenues?|multisports?|sportartikelen)\b"
)


# Vêtements : le rayon dépend du public, déterminé plus haut.
_VETEMENT = (
    r"\b(v[êe]tements?|clothing|kleding|apparel|robes?|dress(es)?|jupes?|pantalons?|"
    r"trousers?|jeans?|chemises?|shirts?|t-shirts?|tops?|pulls?|sweats?|sweaters?|hoodies?|"
    r"manteaux?|vestes?|jackets?|blouses?|costumes?|shorts?|leggings?|lingerie|underwear|"
    r"sleepwears?|pyjamas?|maillots?|chaussettes?|socks?|polos?|overhemd|broek|jas|blazers?|"
    r"combinaisons?|jumpsuits?|nachtkleding|ondergoed|"
    # « Débardeur Proact Sport », catégorisé « Multisports > Débardeur », n'était
    # rangé nulle part : le mot manquait à la liste, donc la branche vêtement
    # n'était jamais atteinte et l'usage sportif ne pouvait pas s'exprimer.
    r"d[ée]bardeurs?|tank\s?tops?|sweatshirts?|hemdjes?|singlets?)\b"
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
        ("Imprimantes & Consommables", r"\b(imprimantes?|scanners?|cartouches?|toner|ink cartridges?)\b"),
        ("Réseau", r"\b(routeurs?|switch|wifi|r[ée]p[ée]teurs?|modems?)\b"),
        ("Câbles & Adaptateurs", r"\b(c[âa]bles?|adaptateurs?|hubs?|docking)\b"),
    ],
    TELEPHONIE: [
        # Les accessoires portent très souvent le nom du téléphone compatible.
        # Ces règles doivent donc précéder « Smartphones » : une coque iPhone 15
        # n'est pas un iPhone 15, même si le modèle est son mot le plus visible.
        ("Coques & Protections", r"\b(coques?|[ée]tuis?|backcovers?|bookcases?|"
                                 r"phone\s+(?:cases?|covers?)|hoe(?:s|sjes)?|"
                                 r"prot[èe]ge-[ée]crans?|screen\s*protectors?|"
                                 r"screenprotectors?|verre\s+tremp[ée]|tempered\s+glass)\b"),
        ("Chargeurs & Batteries", r"\b(chargeurs?|chargers?|power\s*banks?|powerbanks?|"
                                  r"batteries?|c[âa]bles? de charge|charging\s+cables?)\b"),
        ("Smartphones", r"\b(smartphones?|iphone|galaxy|t[ée]l[ée]phones? mobiles?)\b"),
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
        ("Lentilles & Regard", r"\b(lentilles? color[ée]es?|color(?:ed)? lenses?|contact lenses?)\b"),
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
    LOISIRS: [
        ("Patrons & Kits de couture", r"\b(patrons?\b|patrons?\s+(?:burda|mccall(?:'s)?|simplicity|vogue|new\s+look|butterick|know\s+me)|"
                                      r"patrons?\s+(?:de|pour)\s+(?:couture|robes?|jupes?|pantalons?|manteaux?|vestes?|"
                                      r"chemises?|hauts?|tops?|combinaisons?|ensembles?|peluches?|enfants?)|"
                                      r"kits?\s+(?:de\s+)?couture|sewing\s+patterns?|schnittmuster|n[äa]hmuster)\b"),
        ("Tissus & Mercerie", r"\b(tissus?|jerseys?|popelines?|cretonnes?|gabardines?|mousselines?|"
                                r"toiles?\s+[àa]\s+patrons?|coupons?\s+de\s+\d|fil\s+[àa]\s+coudre|"
                                r"fermetures?\s+[ée]clair|boutons?\s+(?:de\s+couture|mercerie))\b"),
    ],
    SPORT: [
        ("Fitness & Musculation", r"\b(fitness|musculation|halt[èe]res?|tapis de course|yoga)\b"),
        ("Cyclisme", r"\b(v[ée]los?|cyclisme|fietsen|casques? v[ée]lo)\b"),
        ("Running", r"\b(running|course [àa] pied|jogging)\b"),
        ("Sports collectifs", r"\b(football|basket-?ball|handball|rugby|volley)\b"),
        ("Camping & Randonnée", r"\b(camping|randonn[ée]e|tentes?|sacs? de couchage)\b"),
        ("Sports d'hiver", r"\b(ski|snowboard|luges?)\b"),
    ],
    VOYAGES: [
        ("Locations de vacances", r"\b(appartements? de vacances|maison(?:s)? de vacances|g[îi]tes?|vakantiehuis(?:jes)?|ferienwohnungen?|ferienh[aä]user?|holiday homes?)\b"),
        ("Hôtels", r"\b(h[ôo]tels?|chambres? d['’ ]h[ôo]tel|hotel kamers?)\b"),
        ("Villas & Appartements", r"\b(villas?|villen|appartements?|appartementen|studios?|wohnungen?|woningen?)\b"),
        ("Campings & Parcs", r"\b(campings?|bungalows?|mobile homes?|parcs?\s+de\s+vacances|vakantieparken?|ferienparks?|holiday parks?)\b"),
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
    category: str | None,
    name: str | None = None,
    merchant_category: str | None = None,
    merchant_name: str | None = None,
) -> str | None:
    """Sous-rayon d'une offre à l'intérieur de son rayon, ou None.

    Le rayon est déjà connu, ce qui rend les motifs bien plus sûrs qu'au premier
    niveau : « bottes » ne peut plus être confondu avec autre chose une fois
    qu'on sait qu'on est dans les chaussures.
    """
    # Les références réduites du spécialiste de pneus ne portent pas le mot
    # « pneu ». Le contexte marchand explicite leur donne un sous-rayon sans
    # faire classer tout « PKW » ou « MO » observé ailleurs.
    if category == AUTO and _is_tyre_specialist_reference(name, merchant_name):
        return "Pneus"
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


def _support_de_tete(text: str) -> str | None:
    """Rayon du support, s'il tient la tête du libellé — sinon None.

    Le principe est le même dans les deux sens : c'est le nom de tête qui
    décide, et ce qui suit ne fait que le qualifier. « Housse de couette en
    percale » est du linge de maison ; « Tissu chemise 100% coton » est du
    tissu, vendu pour en coudre une chemise.

    Comparer les deux positions dit lequel des deux est le nom de tête. Le
    faire par un simple « s'il y a un objet fini, on abandonne le support »
    envoyait ce second cas en Mode — il est au catalogue, chez un marchand
    qui ne vend que du tissu.
    """
    fini = _OBJET_FINI.search(text)
    limite = fini.start() if fini else len(text)
    meilleur: tuple[int, str] | None = None
    for category, pattern in _SUPPORTS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m and m.start() < limite and (meilleur is None or m.start() < meilleur[0]):
            meilleur = (m.start(), category)
    return meilleur[1] if meilleur else None


def classify(
    merchant_category: str | None,
    name: str | None = None,
    brand: str | None = None,
    merchant_name: str | None = None,
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

    # La nature transactionnelle est plus structurante que le rayon : un séjour
    # ne doit jamais être aspiré par Maison, Sport ou Téléphonie sur un mot isolé.
    if classify_offer_kind(merchant_category, name, brand, merchant_name) == ACCOMMODATION:
        return VOYAGES

    if _has(_TYRE_CATEGORY, merchant_category) and _has(_TYRE_DIMENSION, name):
        return AUTO

    if _is_tyre_specialist_reference(name, merchant_name):
        return AUTO

    # Le support d'abord : un tissu imprimé de souris reste un tissu. Sans ce
    # passage préalable, le motif l'emportait et éparpillait la mercerie dans
    # tous les rayons du catalogue.
    for text in (name, merchant_category):
        if not text:
            continue
        support = _support_de_tete(text)
        if support:
            return support

    # Un signal peut n'exister qu'en croisant les deux sources. Les flux
    # horlogers listent « Calvin Klein 459300030 Gauge Sport band » sous la
    # catégorie « Strap » : ni le nom ni la catégorie ne suffisent seuls, mais
    # ensemble ils désignent sans ambiguïté un bracelet de montre. Sans ce
    # croisement, ces références partaient en Sport ou nulle part.
    if _has(r"\bstraps?\b", merchant_category) and _has(
        r"\b(?:bandjes?|bands?|horlogeband(?:en)?|watch|horloge)\b", name
    ):
        return BIJOUX

    # Le nom d'abord, la catégorie du marchand ensuite : l'ordre porte la règle.
    for text in (name, merchant_category):
        if not text:
            continue

        # Vêtements : le rayon dépend du public, qu'on cherche dans les deux
        # sources avant de trancher.
        if _has(_VETEMENT, text):
            other = merchant_category if text is name else name
            # Mais l'usage l'emporte sur le public quand il est explicite : un
            # maillot de football est un article de sport, pas de la mode homme.
            # Le libellé « Maillot arbitre Macron », catégorisé
            # « Football > Maillot > Adulte > Homme », partait en Mode homme —
            # le genre était tranché avant qu'on regarde le sport.
            for source in (text, other):
                if source and _has(_USAGE_SPORTIF, source):
                    return SPORT
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

    if clothing:
        return MODE
    if classify_offer_kind(merchant_category, name, brand, merchant_name) == PHYSICAL_PRODUCT:
        if _has(_ANDLIGHT_MERCHANT, merchant_name or ""):
            return MAISON
        return _specialist_aisle(merchant_name)
    return None
