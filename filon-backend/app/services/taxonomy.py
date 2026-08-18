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


# Seules les formulations qui vendent explicitement un séjour sont globales.
# « Hôtel », « camping », « villa » ou « bungalow » seuls peuvent désigner un
# coussin, un coffre, un maillot, un meuble ou une gamme de produit.
_ACCOMMODATION = (
    r"\b(appartements? de vacances|maison(?:s)? de vacances|g[îi]tes?|"
    r"chambres? d['’ ]h[ôo]tel|hotel kamers?|vakantiehuis(?:jes)?|vakantieparken?|"
    r"ferienwohnungen?|ferienh[aä]user?|ferienparks?|holiday homes?|holiday parks?|"
    r"mobile homes?)\b"
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
# « Étui » seul désigne aussi un passeport, des stylos, une tête de lavage ou un
# accessoire animalier. Il ne devient technique qu'avec un appareil mobile
# explicitement nommé ; les autres familles restent des biens physiques.
_TECH_ACCESSORY = (
    r"\b(coques?|backcovers?|bookcases?|screen ?protectors?|chargeurs?|chargers?|"
    r"c[âa]bles? de charge|charging cables?|power ?banks?)\b"
    r"|\b[ée]tuis?\s+(?:pour\s+)?(?:t[ée]l[ée]phones?|smartphones?|iphone|ipad|"
    r"samsung(?:\s+galaxy)?|xiaomi|redmi|poco|honor|huawei|oppo|oneplus|"
    r"realme|google\s+pixel|motorola)\b"
)

# Certains mots sont intrinsèquement ambigus : un studio peut être un logement,
# un espace de création ou un produit. Le contexte explicite d’un marchand de
# réservation permet de les comprendre sans étendre aveuglément une règle à tout
# le catalogue.
_ACCOMMODATION_MERCHANT = r"\bbungalow\.net\b"
# Gites.fr est un flux de réservations vérifié. Le contexte permet de classer
# ses intitulés réduits sans transformer le mot « hôtel » en règle globale.
_ACCOMMODATION_BOOKING_MERCHANT = r"\bgites\b"
_ACCOMMODATION_MERCHANT_CATEGORY = (
    # Ces formes sont interprétées comme réservables uniquement avec le marchand
    # Bungalow.net : hors de ce contexte, un chalet ou un cottage peut être un
    # meuble, un produit de décoration ou un modèle commercial.
    r"\b(appartement(?:en)?s?|villas?|villen|woningen?|wohnungen?|studios?|studio's|"
    r"chalets?|cottages?|groepsaccommodaties?|group\s+(?:accommodations?|villas?)|"
    r"parcs?\s+de\s+vacances|ferienparks?|holiday parks?|bungalows?|"
    r"stacaravans?|mobilhomes?|mobile\s+homes?|mobilheime?|campings?|"
    r"chambres?\s+d['’ ]h[oô]tes|bed\s*(?:and|&)\s*breakfasts?|landgoederen)\b"
)

# Le flux autobandenmarkt expose seulement les codes de véhicule (PKW, MO,
# OFF, LLKW) et un identifiant numérique de gamme. Ces codes ne sont fiables
# que chez ce spécialiste de pneus ; ils ne deviennent jamais une règle globale.
_TYRE_MERCHANT = r"\b(?:autobandenmarkt|123pneus)\b"
_TYRE_REFERENCE = r"\b(?:pkw|mo|off|llkw)\b"
_TYRE_CATEGORY = r"\b(pneus?|tyres?|banden|reifen|pneumatici)\b"
_TYRE_DIMENSION = r"\b\d{3}/\d{2}\s*r\d{2}(?:[a-z]{0,4})?\b"

# Un accessoire informatique peut mentionner l'iPhone compatible sans être un
# téléphone. Les trois signaux sont nécessaires : source informatique explicite,
# objet informatique nommé, puis formulation de compatibilité. Cette règle ne
# transforme donc ni une coque ni un câble de recharge en périphérique PC.
_COMPUTING_SOURCE = r"\b(?:ordinateurs?|computers?|informatique|computer\s*&\s*office|pc\s*&\s*office)\b"
_COMPUTING_OBJECT = r"\b(?:usb(?:[-\s]?c)?|hdmi|ssd|nvme|rallonges?|extensions?|hubs?|docking|adapters?)\b"
_COMPUTING_COMPATIBILITY = r"\b(?:compatible\s+(?:avec|with)|pour|for)\s+(?:l['’])?(?:iphone|ipad|samsung\s+galaxy)\b"
_COMPUTING_PHONE_ACCESSORY = r"\b(?:coques?|cases?|covers?|protectors?|chargeurs?|chargers?|charging|c[âa]bles?)\b"

# Andlight est un marchand spécialisé en luminaires, mobilier et décoration.
# Son flux néerlandais peut omettre la catégorie brute et ne donner qu’un nom
# de collection (« Paletti », « Componibili ») : ce contexte est donc un dernier
# recours, après tous les signaux produits et rayons explicites.
_ANDLIGHT_MERCHANT = r"\bandlight\b"
# Bollywolly est un flux de mode féminine d'occasion vérifié par échantillon.
# Il faut toutefois la forme vestimentaire explicite : un nom de modèle seul
# reste non classé, et les vêtements génériques sans marqueur féminin ne sont
# pas inférés.
_BOLLYWOLLY_MERCHANT = r"\bbollywolly\b"
_BOLLYWOLLY_FEMME_FORM = r"\b(?:jurk|rok|tuniek|corset)\b"
# Lilo's Nature est un spécialiste animalier vérifié. Le contexte ne s'active
# qu'avec une mention explicite du chien ou du chat : les noms de gamme seuls et
# les valeurs manquantes restent non classés.
_LILOS_NATURE_MERCHANT = r"\blilo['’]?s\s+nature\b"
_LILOS_NATURE_ANIMAL = r"\b(?:katten|honden)\b"
# Les variantes de rangement, vaisselle et mobilier ci-dessous ont été vérifiées
# dans le flux MUJI. Elles restent scellées à ce marchand : « tasses » ou
# « boîte de rangement » peuvent autrement décrire un outil ou une pièce VEVOR.
_MUJI_MERCHANT = r"\bmuji(?:\s+france)?\b"
_MUJI_HOUSEHOLD_VARIANT = (
    r"\b(?:tasses?|bo[iî]tes?\s+de\s+rangement|paniers?\s+de\s+rangement|"
    r"cintres?|bancs?\s+en\s+bois\s+massif|[ée]tag[èe]res?)\b"
)
_MUJI_STATIONERY_SOURCE = r"\b(?:papeterie|stylos?\s+et\s+crayons)\b"
# 2dekansje fournit une arborescence néerlandaise détaillée. Ces six routes ont
# été recoupées sur douze libellés réels chacune ; elles restent scellées au
# marchand car un chemin source n'est jamais un signal universel.
_2DEKANSJE_MERCHANT = r"\b2dekansje\b"
_2DEKANSJE_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (MAISON, r"\bkerst\s*>\s*kerst(?:bomen|verlichting)\b"),
    (BAGAGERIE, r"\breizen\s*&\s*vrije\s*tijd\s*>\s*koffers?\s*&\s*reistassen\b"),
    (ANIMALERIE, r"\bwonen\s*&\s*koken\s*>\s*alles\s+voor\s+huisdieren\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*tafelen\b"),
    (ELECTROMENAGER, r"\bwonen\s*&\s*koken\s*>\s*klimaatbeheersing\s*>\s*luchtbevochtigers\b"),
    # Seconde vague : catégories homogènes vérifiées après la première campagne.
    (MAISON, r"\bkerst\s*>\s*kerstdecoratie\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*potten\s*&\s*pannen\b"),
    (ELECTROMENAGER, r"\bwonen\s*&\s*koken\s*>\s*klimaatbeheersing\s*>\s*elektrische\s*dekens\b"),
    (ELECTROMENAGER, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*fonduesets\s*&\s*friteuses\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*glazen\s*&\s*bekers\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*borden\b"),
    (ELECTROMENAGER, r"\bwonen\s*&\s*koken\s*>\s*klimaatbeheersing\s*>\s*aircoolers\s*&\s*luchtkoelers\b"),
    (ELECTROMENAGER, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*waterkokers\b"),
    # Troisième vague : ces routes restent toutes dans Maison & Déco, même
    # lorsque le sous-rayon dépend du libellé produit plutôt que de la source.
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*badkamer\s*&\s*sanitair\s*>\s*badkamermeubels\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*keukengerei\b"),
    (MAISON, r"\bwonen\s*&\s*koken\s*>\s*schoonmaken\s*&\s*opruimen\s*>\s*prullenbakken\s*&\s*vuilnisbakken\b"),
)
# Quatrième vague : les cinq sources ci-dessous sont hétérogènes. Chaque règle
# exige donc un objet positif en plus du marchand et du chemin source exact.
_2DEKANSJE_SMALL_KITCHEN_SOURCE = r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*kleine\s+keukenapparaten\b"
_2DEKANSJE_KITCHEN_ACCESSORY = r"\b(?:extra\s+)?(?:glazen\s+)?kan\b|\bblenderkan\b|\bbeker\b.*\bblender\b|\baccessoire"
_2DEKANSJE_OBJECT_ROUTES: tuple[tuple[str, str, str], ...] = (
    (ELECTROMENAGER,
     _2DEKANSJE_SMALL_KITCHEN_SOURCE,
     r"\b(?:poffertjes(?:pan|maker)|multigrill|citruspers|sapcentrifuge|worstenvuller|slowjuicer|hakmolen|(?:power\s+)?blender|keukenweegschaal|grillplaat|elektrische\s+kookplaat|espressomachine|multicooker|ijsblokjesmachine|soepmaker)\b"),
    (ELECTROMENAGER,
     r"\bwonen\s*&\s*koken\s*>\s*schoonmaken\s*&\s*opruimen\s*>\s*stofzuigen\s*&\s*schoonmaken\b",
     r"\b(?:robotstofzuiger|handstofzuiger|waszuiger|stoomreiniger|tafelsauger)\b"),
    (ELECTROMENAGER,
     r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*thee\s*&\s*koffie\b",
     r"\b(?:melkopschuimer|koffie(?:zetapparaat|machine)|waterkoker|contactgrill)\b"),
    (MAISON,
     r"\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*thee\s*&\s*koffie\b|\bwonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*kleine\s+keukenapparaten\b",
     r"\b(?:thermosbeker|koffiebeker|theepot|percolator|capsulehouder|koffie(?:blik|bewaarbus))\b"),
    (SANTE,
     r"\bmooi\s*&\s*gezond\s*>\s*massageapparaten\b",
     r"\b(?:massage\s*(?:gun|pistool|kussen|apparaat)|voetmassageapparaat|nekmassage|rugmassage|voetbadmassage|cupping)\b"),
    (ELECTROMENAGER,
     r"\bwonen\s*&\s*koken\s*>\s*klimaatbeheersing\s*>\s*ventilatoren\b",
     r"\b(?:[a-z]+)?ventilator(?:en)?\b|\bbladloze\s+ventilator\b"),
)

# YesStyle est un flux beauté dont certaines catégories sources sont
# homogènes sur les échantillons audités. Elles restent scellées au marchand :
# « Face », « Eyes » ou « Set » ne sont jamais des règles globales.
_YESSTYLE_MERCHANT = r"\byesstyle\b"
_YESSTYLE_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (BEAUTE, r"^(?:bath\s*&\s*shower|eyes|cheeks|face|hand\s+creams|acne\s+treatments|"
              r"exfoliators|hair\s+colors|skin\s+care|body\s+care|hair\s+accessory|"
              r"skin\s+care\s+tools|lens|tools\s*&\s*brushes|after\s+sun\s+care|conditioners)$"),
    (SANTE, r"^toothpaste$"),
)

# 1FoTeam agrège plusieurs univers, mais les routes ci-dessous sont homogènes
# dans le flux audité. Elles sont donc explicitement liées au marchand et à sa
# catégorie source exacte ; Câbles, Piles et Adaptateurs restent volontairement
# absents car leur destination dépend encore de l’objet précis.
_1FOTEAM_MERCHANT = r"\b1foteam\b"
_1FOTEAM_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (LOISIRS, r"^(?:famille\s+mod[ée]lisme\s+gamersgrass|pinceaux\s+citadel\s+gw|"
             r"mod[ée]lisme\s+citadel\s+gw|pinceaux\s+ak\s+interactive\s*&\s+abteilung\s+502)$"),
    (INFORMATIQUE, r"^(?:autres\s+[ée]l[ée]ments\s+de\s+refroidissement|carte\s+graphique|"
                   r"serveur\s+nas|logiciels\s+antivirus)$"),
    (JOUETS, r"^(?:jeux\s+de\s+cartes|jeux\s+d'ambiance|jeux\s+pour\s+joueurs\s+r[ée]guliers\s*/\s+confirm[ée]s|"
               r"star\s+wars|jeux\s+sp[ée]cialistes|jeux\s+d'apprentissage|zombicide|jeux\s+coop[ée]ratif|"
               r"jeux\s+pour\s+enfants|jeux\s+de\s+r[ôo]le)$"),
    (TV_SON, r"^casque$"),
)

# Sneakids : ces 28 chemins source ont été relus sur les 616 titres non classés
# correspondants. Chaque titre nomme explicitement l'objet annoncé. Les motifs
# restent donc attachés au marchand et n'absorbent ni les sources Lifestyle
# génériques ni les catégories de vêtements, accessoires ou puériculture encore
# à examiner dans une vague séparée.
_SNEAKIDS_MERCHANT = r"\bsneakids\b"
_SNEAKIDS_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (CHAUSSURES,
     r"^lifestyle\s*>\s*(?:ballerines|claquettes|bottines|tongs|chaussons|espadrilles|derbie)"
     r"\s*>\s*junior\s*>\s*(?:femme|homme|mixte)$"),
    (BAGAGERIE,
     r"^lifestyle\s*>\s*(?:trousse|sac\s+de\s+voyage|sacoche\s+banane|"
     r"sac\s+bandouli[èe]re|sacoche)(?:\s*>\s*(?:adulte|junior)\s*>\s*"
     r"(?:femme|homme|mixte))?$"),
)

# On Fight : les quatre racines retenues ont été lues exhaustivement sur 761
# offres. Elles désignent des équipements de training, sports de combat ou
# autoprotection ; aucun titre ne décrit un cours, coaching, stage ou formation.
# Le mot « Training » est autrement un signal de prestation : cette exception
# reste donc scellée au marchand, aux chemins source et aux titres physiques.
_ON_FIGHT_MERCHANT = r"\bon\s+fight\b"
_ON_FIGHT_PHYSICAL_SPORT_SOURCE = (
    r"^(?:training|kick-boxing|self-d[ée]fense|kali\s+arnis\s+eskrima)(?:\s*>\s*.+)?$"
)
_ON_FIGHT_SERVICE_TITLE = r"\b(?:cours|coaching|formation|stage|training\s+session)\b"

# Sport Is Good : 301 titres ont été lus dans quatorze racines de pratique ou
# d'équipement sportif. Aucun n'est un cours, une formation, une réservation ou
# une session. Les racines Lifestyle, Santé, Automobile, Workwear et Culture
# restent hors de ce périmètre et nécessitent une preuve distincte.
_SPORT_IS_GOOD_MERCHANT = r"\bsport\s+is\s+good\b"
_SPORT_IS_GOOD_PHYSICAL_SPORT_SOURCE = (
    r"^(?:[ée]quipement\s+du\s+cavalier|training|alpinisme|outdoor|nautisme|squash|"
    r"kick-boxing|roller|slackline|cirque|foot\s+us|self-d[ée]fense|baseball|"
    r"netball\s*&\s*korfball)(?:\s*>\s*.+)?$"
)
_SPORT_IS_GOOD_SERVICE_TITLE = r"\b(?:cours|coaching|formation|stage|r[ée]servation|booking|session)\b"
# Le résiduel Lifestyle a été relu titre par titre. Une destination exige deux
# preuves : le type source exact et le nom de l'objet. Les gourdes, masques,
# prothèses, combinés et chemins non listés restent hors de cette vague.
_SPORT_IS_GOOD_LIFESTYLE_FIXED_ROUTES: tuple[tuple[str, str, str], ...] = (
    (CHAUSSURES,
     r"^lifestyle\s*>\s*(?:bottines|tongs|ballerines|claquettes|chaussons|espadrilles|derbie)(?:\s*>\s*.+)?$",
     r"\b(?:bottines?|tongs?|ballerines?|claquettes?|chaussons?|espadrilles?|derbies?)\b"),
    (BAGAGERIE,
     r"^lifestyle\s*>\s*(?:trousse(?:\s+de\s+toilette)?|sac\s+de\s+voyage|sacoche\s+banane|sac\s+bandouli[èe]re|porte-monnaie|porte-cartes)(?:\s*>\s*.+)?$",
     r"\b(?:trousses?|sacs?(?:\s+de\s+voyage)?|sacoches?|porte[-\s]?monnaie|porte[-\s]?cartes)\b"),
    (ACCESSOIRES,
     r"^lifestyle\s*>\s*(?:lacets|jibbitz|bob|bandana|ruban|lunettes|cordons?\s+[àa]\s+lunettes|bandeau)(?:\s*>\s*.+)?$",
     r"\b(?:lacets?|jibbitz|bobs?|bandanas?|rubans?|lunettes?|cordons?\s+[àa]\s+lunettes|bandeaux?)\b"),
    (BIJOUX,
     r"^lifestyle\s*>\s*boucles?\s+d['’ ]oreilles?(?:\s*>\s*.+)?$",
     r"\bboucles?\s+d['’ ]oreilles?\b"),
)
_SPORT_IS_GOOD_LIFESTYLE_CLOTHING_SOURCE = (
    r"^lifestyle\s*>\s*(?:bomber|chemisier|blouson(?:\s+aviateur)?|gilet|body|shorty|"
    r"coupe-vent|cardigan|ensemble|surchemise|poncho)(?:\s*>\s*.+)?$"
)
_SPORT_IS_GOOD_LIFESTYLE_CLOTHING_NAME = (
    r"\b(?:bombers?|chemisiers?|chemiser|blousons?|gilets?|body|bodies|shorty|"
    r"coupe[-\s]?vent|cardigans?|ensembles?|surchemises?|ponchos?)\b"
)
# Huit offres résiduelles disposent encore d'une preuve complète : le chemin
# source exact et un objet nommé. Les gourdes, masques, combiné et glacière ne
# sont volontairement pas inclus, car leur destination FILON reste incertaine.
_SPORT_IS_GOOD_FINAL_EXPLICIT_ROUTES: tuple[tuple[str, str, str], ...] = (
    (SANTE,
     r"^sant[ée]\s+et\s+bien-[êe]tre\s*>\s*[ée]lectrolytes(?:\s*>\s*.+)?$",
     r"\b(?:electrolytes?|hydro)\b"),
    (SANTE,
     r"^sant[ée]\s+et\s+bien-[êe]tre\s*>\s*prot[ée]ine(?:\s*>\s*.+)?$",
     r"\b(?:whey|prot[ée]ine)\b"),
    (SANTE,
     r"^lifestyle\s*>\s*proth[èe]se\s+mammaire(?:\s*>\s*.+)?$",
     r"\bproth[èe]se\s+mammaire\b"),
    (AUTO,
     r"^automobile\s*>\s*baume\s+soin\s+cuir(?:\s*>\s*.+)?$",
     r"\bbaume\s+soin\s+(?:du\s+)?cuir\b"),
    (SPORT,
     r"^mobilit[ée]\s+urbaine\s*>\s*kit\s+de\s+protection\s+mobilit[ée]\s+urbaine(?:\s*>\s*.+)?$",
     r"\bkit\s+de\s+protection\b"),
)

# 2dekansje : les sources « Kleine keukenapparaten » et « Massageapparaten »
# sont hétérogènes et gardent leurs routes objet historiques. Les onze chemins
# ci-dessous ont au contraire été contrôlés homogènes dans le premier audit et
# peuvent rester des routes source exactes, localisées au marchand.
_2DEKANSJE_FIRST_BATCH_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (ELECTROMENAGER, r"^wonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*keukenmachines$"),
    (ELECTROMENAGER, r"^wonen\s*&\s*koken\s*>\s*koken\s*&\s*tafelen\s*>\s*magnetrons\s*&\s*kookplaten$"),
    (MAISON, r"^wonen\s*&\s*koken\s*>\s*wonen\s*>\s*klokken\s*&\s*wekkers$"),
    (MAISON, r"^wonen\s*&\s*koken\s*>\s*badkamer\s*&\s*sanitair\s*>\s*wastafel-\s*&\s*keukenkranen$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*persoonlijke\s+verzorging\s*>\s*mondverzorging$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*gezondheid\s*>\s*personenweegschalen$"),
    (TV_SON, r"^elektronica\s*>\s*beeld\s*&\s*geluid\s*>\s*hoofdtelefoons\s*&\s*oordopjes$"),
    (SPORT, r"^hobby\s*&\s*sport\s*>\s*sport\s*>\s*sup\s+board$"),
    (SPORT, r"^hobby\s*&\s*sport\s*>\s*sport\s*>\s*skeeleren,\s*step\s*&\s*skaten$"),
    (CULTURE, r"^hobby\s*&\s*sport\s*>\s*muziek\s*>\s*muziekinstrumenten$"),
    (BAGAGERIE, r"^hobby\s*&\s*sport\s*>\s*reizen\s*&\s*vrije\s+tijd\s*>\s*reistassen$"),
)
# Deuxième vague 2dekansje : 157 titres restants ont été contrôlés dans ces
# familles précises. Les sources parent et les catégories « Vertaald » restent
# hors de la règle ; aucune destination n'est déduite d'un simple rayon large.
_2DEKANSJE_SECOND_BATCH_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (SPORT, r"^hobby\s*&\s*sport\s*>\s*sport$"),
    (SPORT, r"^hobby\s*&\s*sport\s*>\s*sport\s*>\s*(?:overige\s*\(sport\)|gewichten|wintersport|vechtsport|tafeltennis)$"),
    (SPORT, r"^hobby\s*&\s*sport\s*>\s*reizen\s*&\s*vrije\s+tijd\s*>\s*tenten$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*gordels,\s*bandages\s*&\s*braces$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*gezondheid\s*>\s*thermometers$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*gezondheid\s*>\s*bloeddrukmeters$"),
    (SANTE, r"^mooi\s*&\s*gezond\s*>\s*gezondheid\s*>\s*supplementen$"),
    (TELEPHONIE, r"^elektronica\s*>\s*mobiele\s+telefoons\s*>\s*opladers,\s*batterijen\s*&\s*autoladers$"),
    (TELEPHONIE, r"^elektronica\s*>\s*mobiele\s+telefoons$"),
    (TELEPHONIE, r"^elektronica\s*>\s*huistelefoons$"),
    (TV_SON, r"^elektronica\s*>\s*beeld\s*&\s*geluid\s*>\s*beamers$"),
    (TV_SON, r"^elektronica\s*>\s*beeld\s*&\s*geluid\s*>\s*radio's,\s*cd-\s*&\s*platenspelers$"),
    (CULTURE, r"^hobby\s*&\s*sport\s*>\s*boeken$"),
)
# Bimba y Lola : le flux fournit des identifiants numériques opaques. Les quatre
# codes ci-dessous ont été contrôlés titre par titre : 439 offres de bagagerie,
# chaussures, bijoux ou mode femme, sans contre-exemple. Ils restent attachés au
# marchand et aux codes exacts ; les codes 166 et 167, hétérogènes, sont exclus.
_BIMBA_Y_LOLA_MERCHANT = r"\bbimba\s+y\s+lola\b"
_BIMBA_Y_LOLA_SOURCE_ROUTES: tuple[tuple[str, str], ...] = (
    (BAGAGERIE, r"^6551$"),
    (CHAUSSURES, r"^187$"),
    (BIJOUX, r"^188$"),
    (MODE_FEMME, r"^1604$"),
)
# Les codes 166 et 167 mélangent des familles. Une seconde lecture des seuls
# titres encore nuls y a établi 201 objets explicites, répartis entre bagagerie,
# accessoires, mode générique et bijoux. Les neuf formulations restantes (dont
# « Triangle », « Dessus » et « Ligne ») restent volontairement hors de la règle.
_BIMBA_Y_LOLA_MIXED_SOURCES = r"^(?:166|167)$"
_BIMBA_Y_LOLA_MIXED_SOURCE_LEXICAL_ROUTES: tuple[tuple[str, str], ...] = (
    (BAGAGERIE, r"\b(?:sacs?|sacoches?|pochettes?|trousses?|porte[-\s]?monnaie|"
                r"porte[-\s]?cartes|prot[èe]ge[-\s]?cartes|[ée]tui de passeport)\b"),
    (ACCESSOIRES, r"\b(?:porte[-\s]?cl[ée]s|ch[âaè]les?|parapluies?|lunettes?|barrettes?|"
                   r"chouchous?)\b|\bcharm\s+(?:sac|foulard)\b"),
    (MODE, r"\b(?:blousons?|trenchs?|camisoles?|bod(?:y|ies)|minijupes?|par[ée]os?)\b|"
           r"\bhauts?\s+(?:[^\s]+\s+){0,3}(?:dos\s+nu|[àa]\s+nouer)\b"),
    (BIJOUX, r"\bras[-\s]?de[-\s]?cou\b"),
)

# Profils de spécialistes vérifiés dans les flux réels : ils ne s'appliquent
# qu'en dernier recours, quand le nom et la catégorie marchande ne permettent
# pas déjà un classement plus précis. Chaque entrée reste donc réversible et
# ne transforme jamais ces noms en mots-clés globaux.
_SPECIALIST_MERCHANT_CONTEXTS: tuple[tuple[str, str], ...] = (
    # Spécialiste beauté vérifié : les bougies et diffuseurs conservent leurs
    # règles Maison explicites, évaluées avant ce dernier recours.
    (r"\bici\s+paris\s+xl\b", BEAUTE),
    # Flux vérifié d’habillement d’extérieur : les modèles courts sans type
    # (« Tiril », « Luna ») rejoignent Mode générique, sans inférer un public.
    (r"\bdidriksons?\b", MODE),
    # Marchands mono-famille vérifiés par échantillons de production. Une règle
    # produit explicite garde toujours la priorité sur ce filet de dernier recours.
    (r"\btissus\s+de\s+r[eê]ve\b", LOISIRS),
    (r"\bsmartphonehoesjes\b", TELEPHONIE),
    (r"\bprintabout\b", INFORMATIQUE),
    (r"\bhorloge\b", BIJOUX),
    (r"\bmaxi\s+zoo\b", ANIMALERIE),
    (r"\bfoot\s+store\b", CHAUSSURES),
    (r"\bisotiger\b", AUTO),
    (r"\bgsmnet\b", TELEPHONIE),
    (r"\boverhemden\b", MODE_HOMME),
    (r"\bmilk\s+bar\s+babystore\b", BEBE),
    (r"\bbobshop\b", SPORT),
    (r"\btapis\.fr\b", MAISON),
    # ASMC est un spécialiste militaire, tactique et outdoor vérifié. Les sacs,
    # vêtements et équipements ayant un signal explicite sont déjà classés plus
    # haut ; ce filet ne traite que les références très courtes restantes.
    (r"\basmc\b", SPORT),
    # Les reliquats de Maverton sont des cadeaux personnalisés Murrano (verres,
    # ardoises et objets décoratifs). Bijoux et vaisselle explicites conservent
    # leur priorité ; cette règle ne couvre que les titres réduits du flux.
    (r"\bmaverton\b", MAISON),
)


def _specialist_aisle(merchant_name: str | None) -> str | None:
    for pattern, category in _SPECIALIST_MERCHANT_CONTEXTS:
        if _has(pattern, merchant_name or ""):
            return category
    return None


# Les grands flux mode affichent souvent seulement le nom de modèle. Une marque
# ne suffit jamais : Nike, Adidas et Vans vendent aussi des vêtements. Ces motifs
# ne s'appliquent donc que quand la marque ET un modèle de chaussure observé dans
# le catalogue sont présents, et un vêtement explicite garde toujours la priorité.
_FOOTWEAR_MODELS_BY_BRAND: tuple[tuple[str, str], ...] = (
    (r"\badidas\b", r"\b(adilette(?:\s+22)?(?:\s+slides?)?|gazelle(?:\s+(?:indoor|bold))?|"
                  r"samba(?:\s+og)?|stan\s+smith|nmd\s+s1|climacool|sl\s*72|"
                  r"centennial\s+85|campus|superstar|handball\s+spezial|country\s+og)\b"),
    (r"\basics\b", r"\b(?:gel[-\s]?(?:1130|kayano|nimbus|lyte|venture|quantum|cumulus|nyc)|gt[-\s]?2160)\b"),
    (r"\bnew\s+balance\b", r"\b(?:[umwgc]{0,2})?(?:1000|1300|1906|2002r?|327|530|550|574|740|9060|990v?\d*|992)[a-z0-9]*\b"),
    (r"\bsalomon\b", r"\b(?:xa\s+pro\s+3d|xt[-\s]?(?:whisper|quest)|neuva\s+advanced|"
                    r"acs\s*(?:pro|ltr)?|rx\s+(?:slide|moc|marie[-\s]?jeanne)|"
                    r"genesis\s+advanced|orava\s+advanced|snowclog\s+advanced)\b"),
    (r"\bhoka(?:\s+one\s+one)?\b", r"\b(?:bondi\s*\d+|clifton\s*(?:\d+|one9)|mafate|"
                                  r"speedgoat|hopara|ora\s+primo)\b"),
    (r"\bconverse\b", r"\b(?:chuck\s*70|all\s+star\s+bb|as[-\s]?1\s+pro)\b"),
    (r"\bpuma\b", r"\b(?:deviate\s+nitro|brasil|arizona\s+(?:doelette|python|retro|venus)|"
                 r"all[-\s]?pro\s+nitro)\b"),
    # La marque On est un mot courant : on ne la reconnaît que dans le champ
    # marque et seulement avec un modèle Cloud vérifié dans le nom.
    (r"\bon\b", r"\bcloud\s*(?:6|away|boom|flow|surfer|tilt|vista)\b"),
    (r"\bautry(?:\s+action\s+shoes)?\b", r"\b(?:medalist|reelwind|malga|clc\s+low|"
                                             r"(?:0?1|1)\s+low)\b"),
    (r"\baxel\s+arigato\b", r"\b(?:clean\s+90|area\s+lo|dice\s+(?:lo|t[-\s]?toe|patchwork)|"
                              r"daze\s+runner)\b"),
    (r"\bbirkenstock\b", r"\b(?:arizona|boston|tokio|highwood|kyoto|loma|london|mantova|"
                          r"naples|oita|prescott)\b"),
    (r"\bugg\b", r"\b(?:tasman(?:\s+ii)?|classic\s+(?:micro|ultra\s+mini)|metropeak|peakmod|"
                 r"goldenglow|anders|ascot(?:\s+lug)?|neumel(?:\s+(?:moc|weather\s+hybrid))?)\b"),
    (r"\bjordan\b", r"\b(?:tatum|zion)\s*\d+\b"),
    (r"\bvans\b", r"\b(authentic(?:\s+reissue\s+44)?|old\s+skool|sk8[-\s]?hi|era|slip[-\s]?on|k\s*nu\s*skool)\b"),
    (r"\bnike\b", r"\b(acg\s+(?:air\s+exploraid|izy)|air\s+(?:max|force|180|foamposite|trainer\s+huarache)|"
                r"dunk|air\s+jordan|pegasus|vomero|zoomx?|astrograbber)\b"),
)


def _brand_footwear(brand: str | None, name: str | None) -> bool:
    """Vrai seulement pour une marque et un modèle de chaussure explicitement vérifiés."""
    if not brand or not name:
        return False
    return any(_has(brand_pattern, brand) and _has(model_pattern, name)
               for brand_pattern, model_pattern in _FOOTWEAR_MODELS_BY_BRAND)


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
    if _has(_ACCOMMODATION, text) or _has(_ACCOMMODATION_BOOKING_MERCHANT, merchant_name) or (
        _has(_ACCOMMODATION_MERCHANT, merchant_name)
        and _has(_ACCOMMODATION_MERCHANT_CATEGORY, merchant_category)
    ):
        return ACCOMMODATION
    if _has(_DIGITAL_CONTENT, text):
        return DIGITAL_CONTENT
    # Le flux On Fight emploie « Training » comme racine de produits physiques.
    # Sans ce garde-fou marchand, les 690 équipements relevés étaient masqués
    # comme services ; un titre qui décrit explicitement une formation reste
    # néanmoins un service.
    if (
        _has(_ON_FIGHT_MERCHANT, merchant_name)
        and _has(_ON_FIGHT_PHYSICAL_SPORT_SOURCE, merchant_category)
        and not _has(_ON_FIGHT_SERVICE_TITLE, name)
    ):
        return PHYSICAL_PRODUCT
    if (
        _has(_SPORT_IS_GOOD_MERCHANT, merchant_name)
        and _has(_SPORT_IS_GOOD_PHYSICAL_SPORT_SOURCE, merchant_category)
        and not _has(_SPORT_IS_GOOD_SERVICE_TITLE, name)
    ):
        return PHYSICAL_PRODUCT
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
     r"(?:satin|r[ée]sille)\b(?:\s+[^\s]+){0,4}\s+(?:pour|[àa])\s+lingerie|"
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
    # Les composés néerlandais ne créent pas de frontière après « baby ».
    # Chacun désigne explicitement un soin ou une toilette pour nourrisson.
    (BEBE, r"\b(?:babydoekjes?|babyolie|babybad|babyshampoo|babyverzorging|"
             r"babyverzorgings(?:olie|balsem)|babyborstel|badsteun|badstoel|badthermometer|"
             r"toilettrainer|verschoningsmat|luierzakjes?|badjesset\s+voor\s+pasgeborenen)\b"),
        (ANIMALERIE, r"\b(chiens?|chats?|dogs?|cats?|hond|kat|hondenvoer|kattenvoer|animal|"
                  r"animalerie|croquettes?|aquarium|liti[èe]re|dierenvoeding|"
                  r"chiots?|puppy|puppies|chatons?|kittens?|niches?\s+pour|"
                  r"paniers?\s+pour\s+(?:chien|chat)|laisses?|colliers?\s+pour\s+(?:chien|chat)|"
                  r"honden(?:mand|riem|tuig)|kattenmand|kattengrot|looplijn|jachtlijn|"
                  r"halsband|tekenband)\b"),

    (AUTO, r"\b(pneus?|tyres?|banden|wheels?|jantes?|voitures?|autos?|automotive|motos?|"
           r"scooters?|v[ée]hicules?|car\s?parts?|huile moteur|car\b|autoteile|"
           r"zomerbanden?|winterbanden?|allseasonbanden?|vierseizoenenbanden?|"
           r"pneus? (?:[ée]t[ée]|hiver|4 saisons)|crics? (?:hydrauliques?|de plancher))\b"),
    # Dimension de pneu : « 225/60 R17 99H ». C'est le signal le plus fiable du
    # catalogue, et il ne peut désigner rien d'autre. Il rattrape les références
    # dont le nom ne dit que la gamme (« Sport Maxx Race 2 »).
    (AUTO, r"\b\d{3}/\d{2}\s*(?:z)?r\s?\d{2}\b"),
    # Les équipements de remorque et de carrosserie sont explicitement nommés
    # dans les titres VEVOR ; ils ne sont jamais inférés depuis « camion » seul.
    (AUTO, r"\b(?:attelage(?:\s+de\s+(?:r[ée]partition\s+du\s+poids|remorque))?|"
           r"kits?\s+d['’]arrimage\s+(?:pour\s+)?camions?|bo[iî]tes?\s+de\s+rangement\s+pour\s+lit\s+de\s+camion|"
           r"d[ée]bosselage\s+(?:sans\s+peinture|carrosserie)|catalyseurs?\s+d['’][ée]chappement|"
           r"cl[ée]s?\s+[àa]\s+choc.*(?:automobile|m[ée]canicien))\b"),
    # Les « classeurs » VEVOR peuvent être des tendeurs de chaîne pour remorque,
    # jamais des classeurs de bureau. Les deux preuves — mécanisme d’arrimage et
    # contexte charge/transport — sont indispensables avant de quitter Culture.
    (AUTO, r"(?=.*\b(?:classeurs?\s+(?:à\s+)?cliquet|classeurs?\s+(?:[àa]|de)\s+cha[iî]ne|classeurs?\s+de\s+charge)\b)(?=.*\b(?:arrimage|remorquage|transport|charge\s+(?:de\s+)?travail|g(?:70|80))\b)"),
    # Équipements de véhicule VEVOR : les deux dimensions de la preuve sont
    # exigées (fonction et contexte camion/remorque/bateau), jamais le véhicule nu.
    (AUTO, r"(?=.*\b(?:e-track|rails?\s+d['’]arrimage|kits?\s+d['’]arrimage)\b)(?=.*\b(?:camions?|remorques?)\b)"),
    (AUTO, r"(?=.*\b(?:chauffages?|r[ée]chauffeurs?\s+d['’]air)\s+diesel\b)(?=.*\b(?:camions?|bateaux?|rv)\b)"),
    (AUTO, r"(?=.*\bpompes?\s+hydrauliques?\b)(?=.*\b(?:camions?\s+[àa]\s+benne|remorques?|nacelles?|bennage)\b)"),
    # Un étui devient un accessoire mobile seulement quand le modèle compatible
    # est explicite. Cela exclut les étuis à lunettes ou à instrument.
    (TELEPHONIE, r"\b[ée]tuis?\s+(?:magsafe\s+)?(?:pour\s+)?(?:apple\s+)?"
                  r"(?:iphone|ipad|samsung(?:\s+galaxy)?|xiaomi|redmi|poco|honor|huawei|oppo|oneplus|realme|google\s+pixel|motorola)\b"),
    (TELEPHONIE, r"\b(smartphones?|t[ée]l[ée]phones?|iphone|samsung galaxy|mobiles?|gsm|"
                 r"coques?|chargeurs?|powerbanks?|[ée]couteurs? sans fil|airpods|earbuds?|airbuds?|"
                 r"ear\s*phones?|inpods?|headsets?|smartwatch(?:es)?|fitnesstrackers?|cellphones?|telecommunications?)\b"),
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
    # Les câbles techniques sont classés seulement avec un protocole ou une
    # interface informatique explicite : RJ45, Thunderbolt, HDMI, PS/2 ou DB9.
    # « Câble » seul reste volontairement insuffisant.
    (INFORMATIQUE, r"(?=.*\b(?:c[âa]bles?|cables?|kabels?)\b)(?=.*\b(?:rj(?:12|45)|ethernet|thunderbolt|hdmi|ps/2|null\s+modem|db(?:9|25)|oculus|meta\s+quest)\b)"),
    (INFORMATIQUE, r"\b(ordinateurs?|laptops?|pc\b|macbook|notebooks?|claviers?|"
                   r"scanners?\s+3d|(?:pla|petg|abs|tpu)\s+filaments?|filaments?\s+(?:pla|petg|abs|tpu)|"
                   r"[ée]crans?|monitors?|ssd|disques? durs?|memory\s+cards?|micro\s*sd|microsd|"
                   r"tf\s+(?:flash\s+)?(?:memory\s+)?cards?|imprimantes?|routeurs?|switch(?:es)?|"
                   r"r[ée]p[ée]teurs?\s+wifi|wifi\s+mesh|adaptateurs?\s+cpl|cartes?\s+r[ée]seau|"
                   r"points? d['’ ]acc[èe]s|usb|tablettes?|software|cartouches? d['’ ]encre|"
                   r"ink cartridges?|toner|"
                   r"webcams?|processeurs?|cpu|cartes? m[èe]res?|motherboards?|watercooling|"
                   r"m[ée]moire ram|domotique|prises? connect[ée]es?)\b"),
    # Stations d'alimentation et batteries nomades : famille absente de toute
    # règle jusqu'ici. « Station d'alimentation » exige un contexte électrique :
    # sans cela on capturait « Station d'alimentation pour oiseaux », qui est un
    # distributeur de graines de jardin.
    (INFORMATIQUE, r"\b(powerstations?|power\s+stations?|groupes? [ée]lectrog[èe]nes?|"
                   r"batteries? nomades?|onduleurs?)\b"),
    (INFORMATIQUE, r"\bstations? d'alimentation\b(?=.*\b(?:portables?|solaires?|"
                   r"[ée]lectriques?|batteries?|\d+\s*wh|\d+\s*w\b))"),
    (PHOTO, r"\b(appareils? photo|cameras?|caméras?|objectifs?|reflex|drones?|gopro|"
            r"tr[ée]pieds?|selfie\s+sticks?|phone\s+tripods?|photographie)\b"),
    (TV_SON, r"\b(t[ée]l[ée]viseurs?|\btv\b|home cinema|barres? de son|soundbars?|enceintes?|"
             r"speakers?|loudspeakers?|luidsprekers?|haut[- ]?parleurs?|casques? audio|hifi|hi-fi|platines?|headphones?)\b"),
    # Un câble ne rejoint TV & Son que si un connecteur audiovisuel ET sa nature
    # de câble/adaptateur sont explicites. Un simple « jack » textile ou câble
    # technique générique reste donc hors de ce rayon.
    (TV_SON, r"(?=.*\b(?:audio|aux|stereo|rca|toslink|optische|antenne|hdmi|minijack|jack)\b)"
             r"(?=.*(?:kabel|cable|adapter|splitter|verleng(?:kabel|snoer)|omvormer)\b)"),
    (TV_SON, r"\b(?:universele?|universal)\s+(?:afstandsbediening|t[ée]l[ée]commande)\b"),
    # Un projecteur devient audiovisuel seulement si un signal vidéo est aussi
    # explicite. Cette double preuve évite de capter un projecteur de chantier.
    (TV_SON, r"(?=.*\bproject(?:eurs?|ors?)\b)(?=.*\b(?:1080p|720p|netflix|dolby|lcd|ansi|wifi|"
             r"home\s+cinema|home\s+theater|led)\b)"),
    (ELECTROMENAGER, r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateurs?|frigos?|"
                     r"cong[ée]lateurs?|fours?|micro-ondes|aspirateurs?|cafeti[èe]res?|broodroosters?|"
                     r"milk\s+frothers?|coffee\s+frothers?|humidifiers?|cuiseurs?\s+[àa]\s+riz|"
                     r"robots? cuiseur|wasmachines?|koelkast|home appliances?|"
                     r"huishoudelijke|ventilateurs?|vacuum cleaners?|wassen, strijken|gaufriers?|"
                     r"hachoirs?\s+[àa]\s+viande|distillateurs?\s+d['’]eau|chauffe-plats?|"
                     r"poussoirs?\s+[àa]\s+saucisses?|d[ée]shydrateurs?\s+alimentaires?|"
                     r"machines?\s+[àa]\s+barbe\s+[àa]\s+papa|scies?\s+[àa]\s+os\s+de\s+boucher)\b"),
    # « crème » n'y figure plus comme mot nu : en néerlandais c'est une teinte,
    # et le rayon affichait un salon de jardin « Bruin Crème », un paravent
    # « Uitschuifbaar – Crème » et une applique murale « wandlamp – crème ».
    # Constaté en production. Seules les crèmes qualifiées classent désormais.
    (BEAUTE, r"\b(parfums?|eaux? de parfum|eaux? de toilette|fragrances?|maquillage|make\s?up|"
             r"cosm[ée]tiques?|cosmetics?|beauty|schoonheidsavontagenda|"
             r"toiletartikelen\s+adventskalender|s[ée]rums?|shampooings?|shampoo|"
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
    # Produits de bain corporels observés dans le flux néerlandais. Les jouets de
    # bain sont exclus : ils sont traités plus bas dans Jeux & Jouets.
    (BEAUTE, r"\b(?:badzeep|bath salts?|bath\s*&\s*shower bubbles|douchebellen|"
                 r"badsponzen?|bath\s+sponge(?:s)?|bubble\s+bath|kinderzonnebrandcr[eè]me|nagelknippers?|"
                 r"fleurs?\s+de\s+douche|brosses?\s+de\s+douche|disques?\s+de\s+coton|papier\s+matifiant)\b"),
    # Soins anglais observés sans catégorie source fiable. Les expressions
    # qualifiées évitent de considérer « treatment » seul comme une preuve.
    (BEAUTE, r"\b(?:cleansing\s+(?:oil|water|foam|bar)|acne\s+patch(?:es)?|"
             r"hair\s+(?:milk|ampoules?|treatments?)|scalp\s+(?:therapy|ampoules?)|"
             r"color\s+charge|cuticle\s+oil)\b"),
    # Soins explicitement décrits dans le catalogue multimarque Kastner & Öhler.
    # « Lotion » et « crème » seuls restent trop ambigus : une zone ou un usage
    # précis est nécessaire pour prouver qu'il s'agit bien d'un produit de beauté.
    (BEAUTE, r"\b(?:apr[èe]s[-\s]?rasage|after\s+shave|soins?\s+(?:pour|des)\s+yeux|"
             r"laits?\s+corporels?|beurres?\s+corporels?|baumes?\s+corps|gels?\s+douche|"
             r"blushing\s+blush|fards?\s+[àa]\s+joues|artliner|stay[-\s]?matte\s+powder|"
             r"super[-\s]?poudre|poudre\s+double\s+face|cr[èe]mes?\s+pour\s+le\s+visage|"
             r"eye\s+essence|lotion\s+clarifiante)\b"),
    # Expressions complètes observées dans les offres MUJI. « Lait », « gel »
    # ou « lotion » nus restent exclus : ils peuvent décrire l'alimentation,
    # l'entretien ou une texture, pas nécessairement un soin du visage.
    (BEAUTE, r"\b(?:eaux?\s+toniques?\s+pour\s+peaux?\s+sensibles?|"
             r"laits?\s+hydratants?\s+pour\s+peaux?\s+sensibles?|"
             r"gels?\s+hydratants?\s+tout[-\s]?en[-\s]?un\s+pour\s+peaux?\s+sensibles?|"
             r"lotion\s+essence\s+booster\s+ferment[ée]e?)\b"),
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
             r"scheren|ontharing|zonnebrand|sunscreens?|cr[èe]me & lotion|"
             r"coiffant|styling|brow\s+(?:pen|definer)|eyebrow|sourcils?|"
             r"poudre\s+(?:libre|fixatrice)|base\s+de\s+teint|primer|body\s+mist|"
             r"face\s+masks?|mask\s+sheet|lips?|cleanser|nettoyant|cleansing\s+balm|"
             r"toners?|oogserum|eye\s+care|hair\s+(?:masks?|treatments?)|"
             r"setting\s+poeder|losse?\s+poeder|bronzer|pinceau(?:x)?\s+(?:poudre|blush))\b"),
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
    (MAISON, r"\b(?:marmites?|faitouts?|po[êe]les?|autocuiseurs?|casseroles?|bouilloires?|"
             r"carafes?|saladiers?|sucriers?|pots?\s+[àa]\s+lait|tire[-\s]?bouchons?|"
             r"presse[-\s]?agrumes|presse[-\s]?pur[ée]e|blocs?\s+[àa]\s+couteaux|"
             r"hachoirs?\s+[àa]\s+herbes|moulins?\s+[àa]\s+poivre|"
             r"machines?\s+[àa]\s+expresso|espressokocher|tapis\s+de\s+bain|badetuch|badteppich)\b"),
    # Familles MUJI observées en lecture seule : chaque expression désigne un
    # objet domestique fini, ce qui exclut les matières et les mots ambigus.
    (MAISON, r"\b(?:tasses?\s+en\s+(?:gr[èe]s|acier\s+inoxydable|porcelaine)|"
             r"bols?\s+[àa]\s+riz|tasses?\s+[àa]\s+sak[ée]|"
             r"r[ée]cipients?\s+alimentaires?\s+en\s+verre|bacs?\s+[àa]\s+gla[çc]ons|"
             r"bo[iî]tes?\s+de\s+rangement\s+transparentes?|"
             r"paniers?\s+de\s+rangement\s+tress[ée]s?|corbeilles?\s+[àa]\s+linge|"
             r"[ée]tag[èe]res?\s+en\s+(?:pin|ch[êe]ne|noyer|bambou)|"
             r"lits?\s+(?:super\s+king|large\s+double|simple)\s+en\s+(?:pin|h[ée]v[ée]a|noyer)|"
             r"t[êe]tes?\s+de\s+lit\s+plateforme)\b"),
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
    # Hygiène bucco-dentaire multilingue : brosse, tête de brosse et dentifrice
    # sont des signaux de santé explicites, y compris pour enfant.
    (SANTE, r"\b(?:kindertandenborstel|tandenborstel(?:s|koppen)?|tandpasta|toothbrush(?:es|\s+heads?)?|toothpaste)\b"),
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
             r"pendentifs?|bracelets?|boucles? d['’]oreilles?|earrings?|montres?|"
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
    # « Bottines » est une chaussure autonome, distincte de « bottes » : son
    # absence empêchait de classer les familles Junior et Femme réellement vues.
    (CHAUSSURES, r"\b(chaussures?|shoes?|baskets?|sneakers?|bottes?|bottines?|boots?|escarpins?|heels?|"
                 r"mules?|sandales?|sandals?|schoenen|mocassins?|semelles?|insoles?|"
                 r"pantoufles?|slippers?)\b"),
    (BAGAGERIE, r"\b(sacs? [àa] main|sacs? [àa] dos|sacs? boston|trousses? de toilette|"
                r"handbags?|backpacks?|valises?|suitcases?|bagages?|luggage|trolleys?|"
                r"portefeuilles?|wallets?|maroquinerie|handtas|rugzak|bags?)\b"),
    # Les titres de maroquinerie peuvent n'indiquer que la forme du sac. Les
    # qualificatifs sont exigés : « sac de couchage » et les usages techniques
    # restent hors de cette règle.
    (BAGAGERIE, r"\b(?:mini|petits?)\s+sacs?(?!\s+de\s+couchage)\b|"
                r"\bsacs?\s+(?:bandouli[eè]res?|shopping|hobo|panier|seau|cabas|"
                r"fourre[-\s]tout|d['’][ée]paule)\b"),
    (ACCESSOIRES, r"\b(accessoires?|accessories|lunettes? de soleil|sunglasses|ceintures?|"
                  r"belts?|[ée]charpes?|foulards?|scarf|scarves|chapeaux?|hats?|casquettes?|caps?|"
                  r"snapbacks?|beanies?|gants?|gloves?|bonnets?|cravates?|ties?|riemen)\b"),
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
            r"cyclisme|vtt|bmx|running|course [àa] pied|randonn[ée]e|camping|ski|snowboard|"
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
    # Le niveau laser est un outil de mesure de chantier, pas un produit photo.
    (JARDIN, r"\bniveaux?\s+laser\b"),
    # Les outils de chantier et de manutention VEVOR sont décrits sans ambiguïté
    # dans leurs titres : ils relèvent du bricolage, pas de l'électronique.
    (JARDIN, r"\b(?:marteaux?(?:-piqueurs?|\s+de\s+d[ée]molition)|scies?\s+cloches?|"
             r"[ée]taux?(?:\s+d['’]?[ée]tabli|\s+atelier)?|raboteuses?|meuleuses?|"
             r"poin[çc]onneuses?|kits?\s+de\s+perforation\s+hydraulique|treuils?|palans?)\b"),
    # Une pompe de puits ou un extracteur de miel décrit un équipement de jardinage
    # et d'apiculture ; « pompe » nu reste volontairement hors de la règle.
    (JARDIN, r"\b(?:pompes?\s+(?:immerg[ée]es?|de\s+puits|[àa]\s+eau\s+pour\s+puits)|"
             r"extracteurs?\s+de\s+miel)\b"),
    (JARDIN, r"\b(?:films?\s+[àa]\s+effet\s+de\s+serre|scies?\s+[àa]\s+[ée]laguer|"
             r"range[-\s]?b[ûu]ches?|effeuilleuses?)\b"),
    # Outillage d'atelier explicite : la fonction décrite prime sur le mot
    # générique « machine », qui reste insuffisant à lui seul.
    (JARDIN, r"\b(?:outils?\s+oscillant(?:s)?|machines?\s+de\s+pulv[ée]risation|"
             r"postes?\s+[àa]\s+souder|coupe[-\s]?carreaux|cintreuses?|tours?\s+[àa]\s+m[ée]taux|"
             r"pinces?\s+[àa]\s+sertir|machines?\s+[àa]\s+d[ée]nuder|trappes?\s+de\s+visite)\b"),
    # Équipements d'atelier et d'électricité VEVOR : chaque motif désigne une
    # fonction professionnelle précise, jamais une « machine » ou une pompe nue.
    (JARDIN, r"\b(?:presses?\s+hydrauliques?\s+d['’]atelier|levage\s+magn[ée]tique|"
             r"chariots?\s+de\s+soudage|cages?\s+de\s+s[ée]curit[ée]\s+chariots?\s+[ée]l[ée]vateurs?|"
             r"porte[-\s]?f[ûu]ts?|balais?\s+magn[ée]tiques?|pinces?\s+amp[èe]rem[ée]triques?|"
             r"bo[iî]tes?\s+de\s+distribution\s+[ée]lectrique|coffrets?\s+[ée]lectriques?|"
             r"kits?\s+de\s+recharge\s+de\s+r[ée]frig[ée]rant|pompes?\s+[àa]\s+vide\s+frigoriste|"
             r"rubans?\s+[àa]\s+poisson|extenseurs?\s+de\s+tubes?|coupleurs?\s+hydrauliques?)\b"),
    (JARDIN, r"\b(?:[ée]chasses?\s+(?:plaquiste|pour\s+cloison\s+s[èe]che)|gabarits?\s+de\s+trou\s+de\s+poche|"
             r"coupe[-\s]?c[âa]bles?\s+[àa]\s+cliquet|serre[-\s]?joints?|kit\s+de\s+filetage\s+de\s+tuyau|"
             r"fil\s+de\s+soudage|pinces?\s+de\s+forge|tenailles?\s+de\s+forge|mandrins?\s+de\s+tour\s+[àa]\s+bois|"
             r"ventouses?\s+de\s+carrelage|fraises?\s+annulaires?|pistolets?\s+[àa]\s+graisse)\b"),
    (JARDIN, r"\b(?:toiles?\s+de\s+paillage|tentes?\s+de\s+culture|chambres?\s+de\s+culture)\b"),
    (MAISON, r"\b(?:armoires?\s+[àa]\s+cl[ée]s|coffres?[-\s]?forts?|serrures?\s+anti[-\s]?panique)\b"),
    (MAISON, r"\b(?:mains?\s+courantes?|rampes?\s+d['’]escalier|auvents?\s+de\s+porte)\b"),
    (LOISIRS, r"\b(?:pyrogravure|pyrograveurs?)\b"),
    # Boîtes aux lettres et boîtes à colis sont des éléments de maison, distincts
    # des simples boîtes de rangement ou de matériel industriel.
    (MAISON, r"\b(?:bo[iî]tes?\s+[àa]\s+colis|bo[iî]tes?\s+aux\s+lettres)\b"),
    # Les kits et machines à badges explicitement nommés relèvent du loisir
    # créatif ; « badge » isolé reste insuffisant, car il peut désigner une carte.
    (LOISIRS, r"\b(?:badges?\s+personnalis[ée]s?|machines?\s+[àa]\s+badges?)\b"),
    (JARDIN, r"\b(jardins?|jardinage|tondeuses?|bricolage|perceuses?|outillage|tuin|"
             r"tuingereedschap|gereedschap|heimwerker[-\s]?zubeh[öo]r|parquet|peinture murale|garden tools?|"
             r"tron[çc]onneuses?|kettingzagen?|kettingzaag|panneaux? solaires?|"
             r"zonnepane(?:el|len)|barbecues?|salons? de jardin|tuinsets?|"
             r"tuinschermen?|tuinscherm|polyrattan)\b"),
    # Une arborescence marchand est une preuve plus forte qu’un titre minimal :
    # `Mobilier > …`, `Déco > …` et `Furniture > Cabinets` décrivent
    # explicitement un meuble. Le séparateur hiérarchique évite les mots isolés.
    (MAISON, r"\b(?:mobilier|d[ée]co)\s*>") ,
    (MAISON, r"\bfurniture\s*>\s*cabinets?\b"),
    # « tissus » est retiré de cette règle : il désigne la mercerie, traitée
    # plus haut par les supports. Le laisser ici renvoyait tous les coupons au
    # rayon Maison. Le linge de maison, lui, manquait entièrement.
    (MAISON, r"\b(canap[ée]s?|fauteuils?|tables?|chaises?|"
               r"lits?\s+(?:plateforme|double|simple|super\s+king|king|en\s+(?:bois|ch[êe]ne|noyer))|"
               r"(?:[ée]tag[èe]res?|shelves?)\s+(?:en\s+(?:acier|bois|ch[êe]ne|noyer)|\d+\s+niveaux)|"
               r"tiroirs?\s+de\s+rangement|coussins?|aroma\s+diffuseurs?|lampes?|luminaires?|cabinet\s+lights?|"
               r"wardrobe\s+lamps?|closet\s+lighting|matelas|"
             r"linge de (?:lit|maison)|housses? de (?:couette|coussin)|couettes?|"
             r"draps?(?:[-\s]housses?)?|taies? d'oreiller|oreillers?|plaids?|"
             r"rideaux?|voilages?|nappes?|d[ée]coration|meubles?|vaisselle|assiettes?|"
             r"cuisine|meubel|verlichting|schoonmaak|nettoyage|serviettes?|textile|"
             r"bougies?|duftkerzen?|geurkaars(?:en)?|theelichtjes?|waxinelichtjes?|"
             r"lichtketting(?:en)?|kettinglamp(?:en)?|sterrengordijn(?:en)?|kerstbal(?:len)?|"
             r"topsters?|sneeuwbol(?:len)?|glitterslinger(?:s)?|decoratielint|kerstpapier|scented\s+candles?|"
             r"diffuseurs?\s+d['’ ]ambiance|b[âa]tonnets?\s+parfum[ée]s?|geurstokjes|"
             r"home\s*&\s*garden|huishouden|wandklokken?|wandklok|pendules?|"
             r"wandlampen?|wandlamp|appliques?|suspensions?|dekbedovertrekken?|"
             r"dekbedovertrek|hoeslakens?|kussenslopen?|kussensloop|handdoeken?|"
             r"paravents?|tuinkussens?|eetkamerstoel(?:en)?|eettafelstoel(?:en)?|salontafels?|"
             r"eettafels?|tafelspiegels?|tapijt(?:en)?|lampenvoet(?:en)?|armleuningen?|"
             r"kurkentrekker|mandoline)\b"),
    (MAISON, r"\bpendant\s+(?:lamps?|lights?|lighting)\b"),
    (JOUETS, r"\b(jouets?|lego|playmobil|peluches?|puzzles?|jeux? de soci[ée]t[ée]|speelgoed|"
             r"toys?|warhammer|games\s+workshop|age\s+of\s+sigmar)\b"),
    # Les composés « badspeelgoed » et « badspeeltje » décrivent un jouet de bain,
    # pas un produit de soin ou un savon.
    (JOUETS, r"\b(?:badspeelgoed|badspeeltjes?|bath\s+squirters?|bad\s+squirters?)\b"),
    # « couture » est écarté : en français il désigne aussi une piqûre de
    # vêtement, et « pyjama sans couture » atterrissait ici.
    (LOISIRS, r"\b(patrons? de couture|patrons?|tricot|laine [àa] tricoter|mercerie|"
              r"handnaaimachine|loisirs? cr[ée]atifs?|scrapbooking)\b"),
    # Les outils de dessin et peinture exigent une preuve de pratique créative :
    # « pen » ou « marker » seuls restent volontairement non classés car ils
    # peuvent désigner une fourniture de bureau générale.
    (LOISIRS, r"\b(?:watercolou?r|acrylic|oil\s+painting|painting\s+brush(?:es)?|"
              r"art\s+brush(?:es)?|graffiti\s+painting|crayon(?:s)?\s+(?:oil\s+)?painting)\b"),
    # Les équipements de fabrication créative exigent leur nature explicite :
    # un mot « laser » isolé peut encore décrire une mesure ou une lumière.
    (LOISIRS, r"\b(?:graveurs?|graveuses?|d[ée]coupeuses?|machines?\s+de\s+gravure)\s+laser\b|"
              r"\b(?:gravure\s+laser|lit\s+laser|rouleau\s+rotatif|presse\s+[àa]\s+chaud|"
              r"papier\s+de\s+sublimation)\b"),
    (LOISIRS, r"\b(?:tours?\s+de\s+potier|roues?\s+de\s+poterie)\b"),
    # Catégories sources explicites observées dans les reliquats : elles
    # décrivent l'objet vendu, sans nécessiter de contexte marchand global.
    (INFORMATIQUE, r"\b(?:computer\s*&\s*office|computer\s+office|kabels?)\b"),
    (ANIMALERIE, r"\b(?:animaux|animals?)\b"),
    (BAGAGERIE, r"\b(?:[ée]quipement\s+militaire\s*>\s*sacs?|military\s+(?:equipment|gear)\s*>\s*bags?)\b"),
    (LOISIRS, r"\b(?:peintures?\s+ak\s+interactive|mod[ée]lisme\s+ak\s+interactive|peintures?\s+citadel\s+gw)\b"),
    (JOUETS, r"\b(?:figuren\s*&\s*actiehelden|figures?\s*(?:&|and)\s*action\s*heroes?)\b"),
    # Papeterie : les objets sont nommés dans leur forme fonctionnelle. Un
    # « stylo plume » ou « pen » nu reste non classé, conformément au garde-fou
    # déjà en place pour les fournitures trop générales.
    (CULTURE, r"\b(?:stylos?\s+(?:[àa]\s+bille|[àa]\s+encre)|blocs?[-\s]?notes?|"
              r"classeurs?|carnets?|feuilles?\s+volantes?|pochettes?\s+perfor[ée]es?|"
              r"enveloppes?|papier\s+[àa]\s+lettres)\b"),
    # Les catégories « Papeterie » et « Stylos et crayons » décrivent un produit
    # de bureau explicite. Hors de cette source, un stylo plume nu reste exclu.
    (CULTURE, r"\b(?:papeterie|stylos?\s+et\s+crayons)\b"),
    (BIJOUX, r"\b(?:polshorloges?|wristwatches?)\b"),
    (SANTE, r"\b(?:tandheelkunde|health\s+(?:products?|wellness)|health\s*(?:&|and)\s*wellness|"
            r"hygi(?:è|Ã«)ne|mondwater|floss|massage\s*(?:&|and)\s*welzijn)\b"),
    (BEAUTE, r"\b(?:hand-?\s*&\s*voetverzorging|hand\s*(?:&|and)\s*foot\s+care|"
             r"cr[eè]me,\s*gel\s*(?:&|and)\s*olie|sonnebrandcreme\s*(?:&|and)\s*aftersun)\b"),
    (MAISON, r"\b(?:reinigingsmiddel|keuken|wonen\s*&\s*koken\s*>\s*wonen\s*>\s*(?:kasten|beddengoed)|"
             r"furniture\s*>\s*office\s+furniture\s*>\s*office\s*(?:&|and)\s*desk\s+chairs|"
             r"wonen\s*&\s*koken\s*>\s*klimaatbeheersing\s*>\s*verwarming)\b"),
    (JARDIN, r"\b(?:carrelage\s+(?:mur|sol)\s+int[ée]rieur|wall\s+tiles?)\b"),
    (MODE, r"\b(?:habillement\s*>\s*couvre-chef|intiem)\b"),
    (SPORT, r"\b(?:sports?\s*(?:&|and)\s*outdoor|multisports?\s*>\s*doudoune|training\s*>\s*[ée]lastique|"
            r"hobby\s*(?:&|and)\s*sport\s*>\s*reizen\s*(?:&|and)\s*vrije\s*tijd\s*>\s*kampeerartikelen)\b"),
    (CHAUSSURES, r"\b(?:lifestyle\s*>\s*sabots)\b"),
    (JOUETS, r"\b(?:jeux?\s+pour\s+famille\s*/\s*amis|family\s*(?:&|and)\s*friends?\s+games?)\b"),
    (CULTURE, r"\b(livres?|romans?|manga|dvd|blu-ray|vinyles?|boek|books?|librairie|magazines?)\b"),
    (ALIMENTATION, r"\b(alimentation|[ée]picerie|caf[ée]|th[ée]|vins?|bi[èe]res?|chocolats?|"
                   r"snacks?|boissons?|soupes?|chips?|croustilles|currys?|guimauves?|craquants?\s+au\s+fromage|"
                   r"voeding|wijn|eten\s*(?:&|and)\s*drinken|"
                   r"koro\s+new\s*>\s*c\s*>\s*petit-d[ée]j['’]?\s+prot[ée]in[ée])\b"),
]


# Usage sportif explicite : il tranche avant le public.
#
# Un maillot de football reste un article de sport, qu'il soit taillé pour homme,
# femme ou enfant. Ne figurent ici que des termes qui désignent la pratique
# elle-même, jamais une simple coupe : « sportif » ou « sport » nus en sont
# absents, sans quoi tout survêtement de ville y passerait.
_USAGE_SPORTIF = (
    r"\b(football|voetbal|basket-?ball|handball|rugby|volley(?:-?ball)?|tennis|"
    r"natation|swimming|zwemmen|cyclisme|v[ée]lo|wielrennen|vtt|bmx|running|jogging|"
    r"trail|marathon|fitness|musculation|yoga|pilates|ski|snowboard|escalade|"
    r"randonn[ée]e|trekking|boxe|judo|karat[ée]|taekwondo|jiu[-\s]?jitsu|bud[ōo]|kung[-\s]?fu|mma|kickboxing|"
    r"p[êe]che|fishing|athl[ée]tisme|gymnastique|"
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
    r"trousers?|pants?|trackpants?|joggers?|jeans?|chemises?|chemisiers?|shirts?|t[-\s]?shirts?|tees?|tops?|pulls?|gilets?|cardigans?|sweats?|sweaters?|hood(?:y|ies)?|hoodies?|crewnecks?|longsleeves?|"
    r"manteaux?|vestes?|jackets?|blouses?|costumes?|shorts?|bermudas?|leggings?|cuissards?|doudounes?|parkas?|boxers?|cale[çc]ons?|lingerie|underwear|"
    r"soutiens?[-\s]?gorges?|brassi[èe]res?|bras?|culottes?|slips?|strings?|bodies?|collants?|"
         r"sleepwears?|pyjamas?|pyjamashirts?|maillots?|chaussettes?|socks?|str[üu]mpfe|strumpfhose|kniestr[üu]mpfe|so[c]?quettes?|polos?|poloshirts?|overhemd|broek|jas|blazers?|sakko|"

    r"combinaisons?|jumpsuits?|nachtkleding|ondergoed|b[ée]rets?|tabliers?|polaires?|fleece|"
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
        # « Rubber boot » désigne une botte de pluie, même si un flux la publie
        # sous Sneakers ou commence son titre par « Baskets enfant ».
        ("Bottes & Bottines", r"^(?!.*\bultraboost\b).*\b(?:(?:rubber|rain)\s+boots?|bottes?|bottines?|boots?|laarzen)\b"),
        # Ultraboost est un modèle de sneaker explicite ; il doit gagner avant le
        # mot « boot » quand les deux apparaissent dans une collaboration Adidas.
        ("Baskets & Sneakers", r"\b(baskets?|sneakers?|running|trainers?|ultraboost)\b"),
        ("Escarpins & Talons", r"\b(escarpins?|talons?|heels?|stiletto|mules?)\b"),
        ("Sandales", r"\b(sandales?|sandals?|tongs?|claquettes?)\b"),
        ("Mocassins & Ville", r"\b(mocassins?|derbies?|richelieu|habill[ée]es?|loafers?)\b"),
        ("Chaussons", r"\b(chaussons?|pantoufles?|slippers?)\b"),
        ("Semelles & Entretien", r"\b(semelles?|insoles?|lacets?|cirage)\b"),
    ],
    MODE_FEMME: [
        # Les costumes nomment fréquemment une « robe », mais leur usage de fête
        # explicite mérite un sous-rayon distinct plutôt qu'un mélange avec la ville.
        ("Déguisements & Costumes", r"\b(?:d[ée]guisements?|halloween|carnaval|verkleed(?:kleding)?)\b"),
        # Nightgown, pyjama ou robe de chambre restent des tenues de nuit même
        # lorsqu'un vendeur les décrit également comme « skirt » ou « dress ».
        ("Lingerie & Nuit", r"\b(lingerie|soutien-gorge|culottes?|pyjamas?|pajamas?|nuisettes?|nightgowns?|"
                             r"sleepwears?|home\s+wear|bathrobes?|dressing\s+gowns?)\b"),
        ("Robes", r"\b(robes?|dress(es)?|jurk)\b"),
        ("Jupes", r"\b(jupes?|skirts?|rok)\b"),
        # Une forme d'extérieur explicite prime sur cardigan : un coat ou blazer
        # n'est pas un pull, tandis qu'un cardigan simple reste dans Pulls & Sweats.
        ("Manteaux & Vestes", r"\b(manteaux?|vestes?|jackets?|blousons?|parkas?|trench|blazers?|coats?|overcoats?)\b"),
        # Pull, sweater et pullover priment sur le mot générique « top ».
        ("Pulls & Sweats", r"\b(pulls?|sweats?|sweaters?|hoodies?|gilets?|cardigans?|pullovers?)\b"),
        ("Hauts & T-shirts", r"\b(tops?|t-shirts?|blouses?|chemisiers?|d[ée]bardeurs?|tuniques?|tuniek|corsets?)\b"),
        # Short est un terme de coupe ; il ne doit pas envoyer une chaussette dans
        # Pantalons & Jeans lorsque l'objet chaussette est explicitement nommé.
        ("Chaussettes", r"\b(chaussettes?|socks?|sokken)\b"),
        ("Pantalons & Jeans", r"\b(pantalons?|jeans?|leggings?|shorts?|trousers?)\b"),
        ("Maillots de bain", r"\b(maillots? de bain|bikinis?|swimwear)\b"),
    ],
    MODE_HOMME: [
        # Un « polo shirt » contient aussi le mot shirt : le polo doit donc être
        # reconnu avant la chemise générique pour conserver le bon sous-rayon.
        ("T-shirts & Polos", r"\b(t-shirts?|polos?|polo\s+shirts?|d[ée]bardeurs?|maillots?|tops?)\b"),
        ("Chemises", r"\b(chemises?|overhemd|(?<!polo\s)shirts?)\b"),
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
        ("Stockage", r"\b(ssd|disques? durs?|cl[ée]s? usb|hdd|nvme|cartes? m[ée]moire|"
                      r"memory\s+cards?|micro\s*sd|microsd|tf\s+(?:flash\s+)?(?:memory\s+)?cards?)\b"),
        ("Impression 3D & Scan", r"\b(?:scanners?\s+3d|(?:pla|petg|abs|tpu)\s+filaments?|"
                                  r"filaments?\s+(?:pla|petg|abs|tpu))\b"),
        ("Imprimantes & Consommables", r"\b(imprimantes?|scanners?|cartouches?|toner|ink cartridges?)\b"),
        ("Réseau", r"\b(routeurs?|switch|wifi|r[ée]p[ée]teurs?|modems?)\b"),
        ("Composants PC", r"\b(?:ventilateurs?\s+(?:de\s+)?(?:bo[iî]tier|processeur|cpu)|(?:cpu|case)\s+fans?)\b"),
        ("Câbles & Adaptateurs", r"\b(c[âa]bles?|adaptateurs?|hubs?|docking)\b"),
    ],
    TELEPHONIE: [
        # Les accessoires portent très souvent le nom du téléphone compatible.
        # Ces règles doivent donc précéder « Smartphones » : une coque iPhone 15
        # n'est pas un iPhone 15, même si le modèle est son mot le plus visible.
        ("Coques & Protections", r"\b(coques?|[ée]tuis?|housses?(?:\s+de\s+protection)?|polsband(?:en)?|"
                                 r"backcovers?|book\s*covers?|covers?|cases?|"
                                 r"(?:hard|bumper\s+hard)cases?|phone\s+(?:cases?|covers?)|"
                                 r"(?:tablet|tablette)(?:hoes(?:je|jes)?|\s*(?:covers?|cases?))|"
                                 r"(?:smartwatch|watch)\s+(?:covers?|cases?)|"
                                 r"(?:smartphone|telefoon)hoes(?:je|jes)?|hoes(?:je|jes)?|"
                                 r"(?:camera|lens)\s+protectors?|camera\s+protector|"
                                 r"protections?\s+d['’]objectif|(?:kits?|packs?)\s+(?:de\s+)?protections?|"
                                 r"kits?\s+protecteurs?|films?\s+de\s+protection|protection\s+film|"
                                 r"scherm(?:beschermers?|protectors?)|prot[èe]ge-[ée]crans?|screen\s*(?:protectors?|protection)|screenprotectors?|"
                                 r"verre(?:\s+de)?\s+protection(?:\s+tremp[ée])?|verre\s+tremp[ée]|tempered\s+glass|"
                                 r"supports?\s+de\s+table(?:\s+[\w-]+){0,8}\s+(?:pour\s+)?(?:smartphones?|t[ée]l[ée]phones?)|"
                                 r"(?:supports?(?:\s+universels?)?|brackets?|holders?|mounts?)\s+"
                                 r"(?:(?:de|pour)\s+)?(?:smartphones?|t[ée]l[ée]phones?)|"
                                 r"(?:mobile|cell)\s+phone\s+(?:brackets?|holders?|mounts?))\b"),
        # Un headset peut contenir un microphone sans être une pièce de téléphone.
        # Il doit donc gagner sur « microphone » mais reste avant Smartphones.
        ("Écouteurs", r"\b([ée]couteurs?|airpods|earbuds?|airbuds?|ear\s*phones?|inpods?|"
                         r"headsets?|headphones?|oreillettes?|oordopjes|koptelefoon)\b"),
        # Un écran de remplacement, un support SIM ou une nappe cite presque
        # toujours le téléphone compatible. Il s'agit d'une pièce, pas du mobile.
        ("Pièces détachées", r"\b([ée]crans?(?:\s+tactiles?)?|displays?|lcd|oled|"
                              r"buzzers?|connecteurs?|connectors?|nappes?|flex(?:\s+cables?)?|"
                              r"pcb|supports?\s+(?:sim|pcb|de\s+travail(?:\s+reballing)?)|"
                              r"tiroirs?\s+sim|lecteurs?\s+sim|ch[âa]ssis|cadres?|vibreurs?|"
                              r"microphones?|cam[ée]ras?|oca)\b"),
        ("Chargeurs & Batteries", r"\b(chargeurs?|chargers?|opladers?|power\s*banks?|powerbanks?|"
                                  r"batteries?|c[âa]bles? de charge|charging(?:\s+cables?)?|"
                                  r"wireless\s+charging|oplaad(?:kabels?|adapter[s]?)|snelladers?|"
                                  r"home\s+chargers?|lightning\s+docks?|docks?|(?:usb[-\s]?[ac])?\s*adapters?)\b"),
        ("Montres connectées", r"\b(montres? connect[ée]es?|smartwatch|watch(?:es)?|galaxy\s+watch\d*|"
                               r"bracelets? connect[ée]s?|horloges?|polsband(?:en)?)\b"),
        ("Tablettes", r"\b(tablettes?|ipad|galaxy\s+tab)\b"),
        ("Smartphones", r"\b(smartphones?|iphone|galaxy|t[ée]l[ée]phones? mobiles?)\b"),
    ],
    TV_SON: [
        ("Vidéoprojecteurs", r"\bproject(?:eurs?|ors?)\b"),
        ("Téléviseurs", r"\b(t[ée]l[ée]viseurs?|\btv\b|oled|qled)\b"),
        ("Casques audio", r"\b(casques?|headphones?|koptelefoon)\b"),
        ("Enceintes", r"\b(enceintes?|speakers?|loudspeakers?|luidsprekers?|haut[- ]?parleurs?)\b"),
        ("Barres de son", r"\b(barres? de son|soundbars?|home cinema)\b"),
        ("Platines & Hi-Fi", r"\b(platines?|amplis?|hifi|hi-fi|vinyles?)\b"),
        ("Câbles audio & vidéo", r"(?=.*\b(?:audio|aux|stereo|rca|toslink|optische|antenne|hdmi|minijack|jack)\b)"
                               r"(?=.*(?:kabel|cable|adapter|splitter|verleng(?:kabel|snoer)|omvormer)\b)"),
        ("Télécommandes", r"\b(?:universele?|universal)\s+(?:afstandsbediening|t[ée]l[ée]commande)\b"),
    ],
    BIJOUX: [
        ("Colliers & Pendentifs", r"\b(colliers?|necklaces?|pendentifs?|pendants?|cha[îi]nes?|ketting)\b"),
        ("Bracelets", r"\b(bracelets?|joncs?|gourmettes?)\b"),
        ("Bagues", r"\b(bagues?|rings?|alliances?|chevali[èe]res?)\b"),
        ("Boucles d'oreilles", r"\b(boucles? d['’]oreilles?|earrings?|cr[ée]oles?|puces?)\b"),
        ("Montres", r"\b(montres?|watch(es)?|horloges?)\b"),
    ],
    BAGAGERIE: [
        ("Sacs à main", r"\b(sacs? [àa] main|sacs? boston|handbags?|handtas|cabas|besaces?|bandouli[èe]res?|"
                         r"(?:shoulder|messenger|tote|crossbody)\s+bags?|"
                         r"(?:mini|petits?)\s+sacs?|sacs?\s+(?:bandouli[eè]res?|shopping|hobo|panier|"
                         r"seau|cabas|fourre[-\s]tout|d['’][ée]paule))\b"),
        ("Sacs à dos", r"\b(sacs? [àa] dos|backpacks?|rugzak)\b"),
        ("Valises & Bagages", r"\b(valises?|suitcases?|bagages?|luggage|trolleys?|koffers?|reistassen?)\b"),
        ("Portefeuilles", r"\b(portefeuilles?|wallets?|porte-cartes?|porte-monnaie)\b"),
        ("Sacs banane & Pochettes", r"\b(sacs? banane|bananes?|pochettes?|sacoches?|trousses? de toilette)\b"),
    ],
    ACCESSOIRES: [
        ("Lunettes de soleil", r"\b(lunettes? de soleil|sunglasses|solaires?)\b"),
        ("Ceintures", r"\b(ceintures?|belts?|riemen)\b"),
        ("Chapeaux & Casquettes", r"\b(chapeaux?|casquettes?|bonnets?|b[ée]rets?|hats?|caps?|bobs?|snapbacks?|beanies?)\b"),
        ("Écharpes & Foulards", r"\b([ée]charpes?|foulards?|ch[èa]les?|scarf|scarves)\b"),
        ("Gants", r"\b(gants?|gloves?|moufles?)\b"),
        ("Cravates", r"\b(cravates?|ties?|n[oœ]uds? papillon)\b"),
    ],
    BEAUTE: [
        ("Parfums", r"\b(parfums?|eaux? de parfum|eaux? de toilette|fragrances?)\b"),
        ("Coffrets & Calendriers", r"\b(?:schoonheidsavontagenda|toiletartikelen\s+adventskalender)\b"),
        # Une tondeuse corporelle peut inclure un accessoire à sourcils : l'appareil
        # principal reste du rasage/épilation, pas un produit de maquillage.
        ("Rasage & Épilation", r"\b(tondeuses?|rasoirs?|[ée]pilation|epilation|ladyshaves?|shavers?)\b"),
        ("Maquillage", r"\b(maquillage|make\s?up|rouges? [àa] l[èe]vres|lipstick|mascaras?|"
                       r"fonds? de teint|eyeliner|fards?|sourcils?|eyebrow|brow\s+(?:pen|definer)|"
                       r"poudre\s+(?:libre|fixatrice)|base\s+de\s+teint|primer|lips?|"
                       r"blushing\s+blush|fards?\s+[àa]\s+joues|artliner|stay[-\s]?matte\s+powder|"
                       r"super[-\s]?poudre|poudre\s+double\s+face)\b"),
        ("Soins visage", r"\b(soins? visage|cr[èe]mes?|s[ée]rums?|skincare|huidverzorging|"
                         r"gezicht|toner|masques?|cleansing\s+(?:oil|water|foam|bar)|acne\s+patch(?:es)?|"
                         r"papier\s+matifiant|apr[èe]s[-\s]?rasage|after\s+shave|soins?\s+(?:pour|des)\s+yeux|"
                         r"cr[èe]mes?\s+pour\s+le\s+visage|eye\s+essence|lotion\s+clarifiante|"
                         r"eaux?\s+toniques?\s+pour\s+peaux?\s+sensibles?|"
                         r"laits?\s+hydratants?\s+pour\s+peaux?\s+sensibles?|"
                         r"gels?\s+hydratants?\s+tout[-\s]?en[-\s]?un\s+pour\s+peaux?\s+sensibles?|"
                         r"lotion\s+essence\s+booster\s+ferment[ée]e?)\b"),
        ("Bain & Corps", r"\b(badzeep|bath salts?|bath\s*&\s*shower bubbles|douchebellen|"
                           r"badsponzen?|bath\s+sponge(?:s)?|bubble\s+bath|kinderzonnebrandcr[eè]me|"
                           r"fleurs?\s+de\s+douche|brosses?\s+de\s+douche|disques?\s+de\s+coton|"
                           r"laits?\s+corporels?|beurres?\s+corporels?|baumes?\s+corps|gels?\s+douche)\b"),
        ("Cheveux", r"\b(shampooings?|shampoo|conditioner|apr[èe]s-shampooing|haircare|"
                     r"haarverzorging|colorations?|perruques?|wigs?|extensions?|coiffant|styling|"
                     r"hair\s+(?:milk|ampoules?|treatments?)|scalp\s+(?:therapy|ampoules?)|color\s+charge)\b"),
        ("Ongles", r"\b(ongles?|nails?|vernis|manucure|cuticle\s+oil|nagelknippers?)\b"),
        ("Lentilles & Regard", r"\b(lentilles? color[ée]es?|color(?:ed)? lenses?|contact lenses?)\b"),
    ],
    SANTE: [
        ("Hygiène bucco-dentaire", r"\b(?:kindertandenborstel|tandenborstel(?:s|koppen)?|tandpasta|toothbrush(?:es|\s+heads?)?|toothpaste)\b"),
        ("Massage & Bien-être", r"\b(?:massage\s*(?:gun|pistool|kussen|apparaat)|voetmassageapparaat|nekmassage|rugmassage|voetbadmassage|cupping)\b"),
    ],
    CULTURE: [
        ("Papeterie & Bureau", r"\b(?:stylos?\s+(?:[àa]\s+bille|[àa]\s+encre)|blocs?[-\s]?notes?|"
                               r"classeurs?|carnets?|feuilles?\s+volantes?|pochettes?\s+perfor[ée]es?|"
                               r"enveloppes?|papier\s+[àa]\s+lettres|papeterie|stylos?\s+et\s+crayons)\b"),
    ],
    MAISON: [
        # Les armoires à clés sont des équipements de sécurité, non du mobilier générique.
        ("Sécurité & Quincaillerie", r"\b(?:armoires?\s+[àa]\s+cl[ée]s|coffres?[-\s]?forts?|serrures?\s+anti[-\s]?panique)\b"),
        ("Auvents & Rampes", r"\b(?:mains?\s+courantes?|rampes?\s+d['’]escalier|auvents?\s+de\s+porte)\b"),
        ("Meubles", r"\b(meubles?|canap[ée]s?|fauteuils?|tables?|chaises?|"
                     r"lits?\s+(?:plateforme|double|simple|super\s+king|king|en\s+(?:bois|pin|ch[êe]ne|noyer|bambou))|"
                     r"t[êe]tes?\s+de\s+lit\s+plateforme|tiroirs?\s+de\s+rangement|armoires?|cabinets?(?!\s+(?:lights?|lamps?))|"
                     r"(?:[ée]tag[èe]res?|shelves?)\s+(?:en\s+(?:acier|bois|pin|ch[êe]ne|noyer|bambou)|\d+\s+niveaux)|"
                     r"(?=.*\b[ée]tag[èe]res?\b)(?=.*\b(?:bambou|ch[êe]ne|noyer)\b)|"
                     r"[ée]tag[èe]res?\s+de\s+(?:bureau|rangement)|bancs?\s+en\s+bois\s+massif|meubel|"
                     r"(?:locker|garderobe|draaideur|roldeur|hangmappen|postvakken)kasten?)\b"),
        ("Luminaires", r"\b(lampes?|luminaires?|cabinet\s+lights?|wardrobe\s+lamps?|closet\s+lighting|"
                         r"lichtketting(?:en)?|kettinglamp(?:en)?|sterrengordijn(?:en)?|"
                         r"suspensions?|appliques?|verlichting|ampoules?)\b"),
        ("Linge de maison", r"\b(linge de lit|draps?|couettes?|serviettes?|rideaux?|"
                             r"coussins?|plaids?|tapis)\b"),
        ("Vaisselle & Cuisine", r"\b(vaisselle|assiettes?|verres?|couverts?|casseroles?|po[êe]les?|"
                                  r"tasses?|bols?|mugs?|th[ée]i[èe]res?|tasses?\s+[àa]\s+sak[ée]|bols?\s+[àa]\s+riz|"
                                  r"r[ée]cipients?\s+alimentaires?|bacs?\s+[àa]\s+gla[çc]ons|onderzetters?|placemats?|"
                                  r"thermosbekers?|koffiebekers?|theepotten?|percolators?|capsulehouders?|"
                                  r"serveerplank(?:en)?|saladeschalen?|(?:koeken|braad|soep|grill|sauteer)pan(?:nen)?|"
                                  r"(?:thee|wijn|champagne)?glazen|mokken?|borden?|kurkentrekker|mandoline|marmites?|faitouts?|"
                                  r"autocuiseurs?|bouilloires?|carafes?|saladiers?|sucriers?|pots?\s+[àa]\s+lait|"
                                  r"tire[-\s]?bouchons?|presse[-\s]?agrumes|presse[-\s]?pur[ée]e|"
                                  r"blocs?\s+[àa]\s+couteaux|hachoirs?\s+[àa]\s+herbes|moulins?\s+[àa]\s+poivre|"
                                  r"machines?\s+[àa]\s+expresso|espressokocher)\b"),
        ("Décoration", r"\b(d[ée]corations?|cadres?|bougies?|geurkaars(?:en)?|theelichtjes?|"
                         r"waxinelichtjes?|kerstbal(?:len)?|(?:kunst)?kerstbo(?:om|men)|kerstdecoratie|kerstversiering|kerstfiguren?|topsters?|sneeuwbol(?:len)?|glitterslinger(?:s)?|"
                         r"decoratielint|kerstpapier|aroma\s+diffuseurs?|vases?|miroirs?)\b"),
        ("Rangement & Boîtes aux lettres", r"\b(?:bo[iî]tes?\s+[àa]\s+colis|bo[iî]tes?\s+aux\s+lettres|"
                                           r"bo[iî]tes?\s+de\s+rangement|paniers?\s+de\s+rangement|"
                                           r"cintres?|corbeilles?\s+[àa]\s+linge)\b"),
        ("Entretien", r"\b(schoonmaak|nettoyage|entretien|lessives?|d[ée]tergents?)\b"),
    ],
    ELECTROMENAGER: [
        ("Gros électroménager", r"\b(lave-linge|lave-vaisselle|r[ée]frig[ée]rateurs?|frigos?|"
                                 r"cong[ée]lateurs?|fours?|wasmachines?|koelkast)\b"),
        ("Petit électroménager", r"\b(cafeti[èe]res?|bouilloires?|grille-pains?|broodroosters?|blenders?|"
                                  r"milk\s+frothers?|coffee\s+frothers?|cuiseurs?\s+[àa]\s+riz|robots? cuiseur|friteuses?|micro-ondes|"
                                  r"gaufriers?|hachoirs?\s+[àa]\s+viande|distillateurs?\s+d['’]eau|chauffe-plats?|"
                                  r"poussoirs?\s+[àa]\s+saucisses?|d[ée]shydrateurs?\s+alimentaires?|"
                                  r"machines?\s+[àa]\s+barbe\s+[àa]\s+papa|scies?\s+[àa]\s+os\s+de\s+boucher|"
                                  r"airfryers?|contactgrills?|gourmetstellen?|tosti(?:\s+apparaten?)?|waterkokers?|heetwaterdispensers?|"
                                  r"poffertjes(?:pan|maker)|multigrills?|citruspersen?|sapcentrifuges?|slowjuicers?|hakmolens?|"
                                  r"(?:power\s+)?blenders?|keukenweegschalen?|grillplaten?|elektrische\s+kookplaten?|"
                                  r"espressomachines?|multicookers?|ijsblokjesmachines?|soepmakers?|melkopschuimers?|koffie(?:zetapparaten|machines?))\b"),
        ("Aspirateurs", r"\b(aspirateurs?|vacuum cleaners?|balais? vapeur|(?:robot|hand|steel)?stofzuigers?|waszuigers?|tafelsaugers?|stoomreinigers?)\b"),
        ("Climatisation & Chauffage", r"\b(ventilateurs?|climatiseurs?|chauffages?|"
                                       r"radiateurs?|purificateurs?|humidificateurs?|humidifiers?|aircoolers?|luchtkoelers?|"
                                       r"(?:toren|tafel|vloer|statief|box|radiator)?ventilator(?:en)?|bladloze\s+ventilator|"
                                       r"(?:mobiele\s+)?airco(?:'s)?|elektrische\s+(?:warmte)?dekens?|onderdekens?|"
                                       r"voetenwarmers?|warmtekussens?|lucht(?:bevochtigers?|ontvochtigers?|zuiveraars?))\b"),
    ],
    LOISIRS: [
        ("Patrons & Kits de couture", r"\b(patrons?\b|patrons?\s+(?:burda|mccall(?:'s)?|simplicity|vogue|new\s+look|butterick|know\s+me)|"
                                      r"patrons?\s+(?:de|pour)\s+(?:couture|robes?|jupes?|pantalons?|manteaux?|vestes?|"
                                      r"chemises?|hauts?|tops?|combinaisons?|ensembles?|peluches?|enfants?)|"
                                      r"kits?\s+(?:de\s+)?couture|sewing\s+patterns?|schnittmuster|n[äa]hmuster)\b"),
        ("Tissus & Mercerie", r"\b(tissus?|jerseys?|popelines?|cretonnes?|gabardines?|mousselines?|"
                                r"flanelles?|ottoman(?:\s+de\s+coton)?|whipcord|[ée]tamine|twill|tweed|jacquard|"
                                r"maille\s+milano|double\s+gaze|double\s+cr[êe]pe|velours(?:\s+(?:lisse|c[oô]tel[ée]))?|"
                                r"cr[êe]pe(?:\s+(?:satin|envers\s+satin|lourd))?|satin\s+(?:cuir|de\s+coton)|[ée]toffe|"
                                r"ouate\s+de\s+cachemire|toiles?\s+[àa]\s+patrons?|coupons?\s+de\s+\d|"
                                r"fil\s+(?:[àa]\s+coudre|pour\s+tout\s+coudre)|canettes?\s+(?:universelles?|en\s+(?:plastique|acier)|plates?|bomb[ée]es?)|"
                                r"pied[-\s]?de[-\s]?biche|bo[iî]tier\s+de\s+canette|m[èe]tre\s+ruban|[ée]pingles?|d[ée]couseur|"
                                r"craie\s+tailleur|r[èe]gle\s+(?:de\s+couture|pour\s+ourlet)|enfile[-\s]?aiguilles?|coupe[-\s]?fils?|"
                                r"thermocollant|boutons?\s+[àa]\s+coudre|[ée]lastique\s+(?:fronceur\s+de\s+)?couture|retourne[-\s]?biais|"
                                r"fermetures?\s+[ée]clair|boutons?\s+(?:de\s+couture|mercerie)|handnaaimachine)\b"),
        ("Dessin & Peinture", r"\b(?:watercolou?r|acrylic|oil\s+painting|painting\s+brush(?:es)?|"
                               r"art\s+brush(?:es)?|graffiti\s+painting|crayon(?:s)?\s+(?:oil\s+)?painting)\b"),
        ("Gravure & Sublimation", r"\b(?:graveurs?|graveuses?|d[ée]coupeuses?|machines?\s+de\s+gravure)\s+laser\b|"
                                  r"\b(?:gravure\s+laser|lit\s+laser|rouleau\s+rotatif|presse\s+[àa]\s+chaud|"
                                  r"papier\s+de\s+sublimation)\b"),
        ("Poterie & Céramique", r"\b(?:tours?\s+de\s+potier|roues?\s+de\s+poterie)\b"),
        ("Création de badges", r"\b(?:badges?\s+personnalis[ée]s?|machines?\s+[àa]\s+badges?)\b"),
        ("Pyrogravure & Travail du bois", r"\b(?:pyrogravure|pyrograveurs?)\b"),
    ],
    SPORT: [
        ("Fitness & Musculation", r"\b(fitness|musculation|halt[èe]res?|tapis de course|yoga)\b"),
        ("Cyclisme", r"\b(v[ée]los?|cyclisme|fietsen|vtt|bmx|casques? v[ée]lo|manivelles?)\b"),
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
        ("Outils & Levage", r"\b(crics?\s+(?:hydrauliques?|de\s+plancher)|treuils?|palans?)\b"),
        ("Remorquage & Carrosserie", r"\b(attelage(?:\s+de\s+(?:r[ée]partition\s+du\s+poids|remorque))?|"
                                      r"kits?\s+d['’]arrimage\s+(?:pour\s+)?camions?|bo[iî]tes?\s+de\s+rangement\s+pour\s+lit\s+de\s+camion|"
                                      r"d[ée]bosselage\s+(?:sans\s+peinture|carrosserie)|catalyseurs?\s+d['’][ée]chappement|"
                                      r"cl[ée]s?\s+[àa]\s+choc.*(?:automobile|m[ée]canicien))\b"),
        ("Arrimage & Hydraulique", r"(?=.*\b(?:e-track|rails?\s+d['’]arrimage|kits?\s+d['’]arrimage|pompes?\s+hydrauliques?|classeurs?\s+(?:à\s+)?cliquet|classeurs?\s+(?:[àa]|de)\s+cha[iî]ne|classeurs?\s+de\s+charge)\b)(?=.*\b(?:camions?|remorques?|nacelles?|bennage|arrimage|remorquage|transport|charge\s+(?:de\s+)?travail|g(?:70|80))\b)"),
        ("Chauffage véhicule", r"(?=.*\b(?:chauffages?|r[ée]chauffeurs?\s+d['’]air)\s+diesel\b)(?=.*\b(?:camions?|bateaux?|rv)\b)"),
        ("Accessoires auto", r"\b(tapis de sol|housses?|supports? t[ée]l[ée]phone|chargeurs? allume-cigare)\b"),
    ],
    BEBE: [
        ("Poussettes & Sièges auto", r"\b(poussettes?|strollers?|si[èe]ges? auto|maxi-cosi)\b"),
        ("Repas & Biberons", r"\b(biberons?|bavoirs?|slabbetjes?|chaises? hautes?|"
                              r"st[ée]rilisateurs?)\b"),
        ("Couches & Toilette", r"\b(couches?|luiers?|lingettes?|tables? [àa] langer|"
                              r"babydoekjes?|babyolie|babybad|babyshampoo|babyverzorging|"
                              r"babyverzorgings(?:olie|balsem)|babyborstel|badsteun|badstoel|badthermometer|"
                              r"toilettrainer|verschoningsmat|luierzakjes?|badjesset\s+voor\s+pasgeborenen)\b"),
        ("Chambre bébé", r"\b(lits? b[ée]b[ée]|berceaux?|matelas b[ée]b[ée]|tours? de lit)\b"),
    ],
    ANIMALERIE: [
        ("Chien", r"\b(chiens?|dogs?|hond|hondenvoer|honden(?:mand|riem|tuig)|looplijn|jachtlijn)\b"),
        ("Chat", r"\b(chats?|cats?|\bkat\b|kattenvoer|liti[èe]res?|kattenmand|kattengrot|kattenboom|krabpaal)\b"),
        ("Petits animaux", r"\b(rongeurs?|lapins?|hamsters?|oiseaux?|aquarium|poissons?)\b"),
    ],
    GAMING: [
        ("Consoles", r"\b(consoles?|playstation|ps5|ps4|xbox|nintendo|switch)\b"),
        ("Jeux vidéo", r"\b(jeux? vid[ée]o|video\s?games?|cd keys?|steam)\b"),
        ("Accessoires gaming", r"\b(manettes?|controllers?|casques? gaming|si[èe]ges? gamer|"
                                r"tapis de souris)\b"),
    ],
    JOUETS: [
        ("Jeux de bain", r"\b(?:badspeelgoed|badspeeltjes?|bath\s+squirters?|bad\s+squirters?)\b"),
    ],
    JARDIN: [
        ("Outillage", r"\b(perceuses?|visseuses?|scies?|outillages?|gereedschap|tournevis|niveaux?\s+laser|"
                       r"marteaux?(?:-piqueurs?|\s+de\s+d[ée]molition)|scies?\s+cloches?|[ée]taux?(?:\s+d['’]?[ée]tabli|\s+atelier)?|"
                       r"raboteuses?|meuleuses?|poin[çc]onneuses?|kits?\s+de\s+perforation\s+hydraulique|treuils?|palans?|"
                       r"outils?\s+oscillant(?:s)?|machines?\s+de\s+pulv[ée]risation|postes?\s+[àa]\s+souder|"
                       r"coupe[-\s]?carreaux|cintreuses?|tours?\s+[àa]\s+m[ée]taux|pinces?\s+[àa]\s+sertir|"
                       r"machines?\s+[àa]\s+d[ée]nuder|trappes?\s+de\s+visite|presses?\s+hydrauliques?\s+d['’]atelier|"
                       r"levage\s+magn[ée]tique|chariots?\s+de\s+soudage|cages?\s+de\s+s[ée]curit[ée]\s+chariots?\s+[ée]l[ée]vateurs?|"
                       r"porte[-\s]?f[ûu]ts?|balais?\s+magn[ée]tiques?|pinces?\s+amp[èe]rem[ée]triques?|"
                       r"bo[iî]tes?\s+de\s+distribution\s+[ée]lectrique|coffrets?\s+[ée]lectriques?|"
                       r"kits?\s+de\s+recharge\s+de\s+r[ée]frig[ée]rant|pompes?\s+[àa]\s+vide\s+frigoriste|"
                       r"rubans?\s+[àa]\s+poisson|extenseurs?\s+de\s+tubes?|coupleurs?\s+hydrauliques?|"
                       r"[ée]chasses?\s+(?:plaquiste|pour\s+cloison\s+s[èe]che)|gabarits?\s+de\s+trou\s+de\s+poche|"
                       r"coupe[-\s]?c[âa]bles?\s+[àa]\s+cliquet|serre[-\s]?joints?|kit\s+de\s+filetage\s+de\s+tuyau|"
                       r"fil\s+de\s+soudage|pinces?\s+de\s+forge|tenailles?\s+de\s+forge|mandrins?\s+de\s+tour\s+[àa]\s+bois|"
                       r"ventouses?\s+de\s+carrelage|fraises?\s+annulaires?|pistolets?\s+[àa]\s+graisse)\b"),
        ("Pompes & Arrosage", r"\b(pompes?\s+(?:immerg[ée]es?|de\s+puits|[àa]\s+eau\s+pour\s+puits))\b"),
        ("Jardinage & Apiculture", r"\b(extracteurs?\s+de\s+miel|tondeuses?|taille-haies?|arrosages?|tuingereedschap|s[ée]cateurs?|"
                                    r"films?\s+[àa]\s+effet\s+de\s+serre|scies?\s+[àa]\s+[ée]laguer|range[-\s]?b[ûu]ches?|effeuilleuses?|"
                                    r"toiles?\s+de\s+paillage|tentes?\s+de\s+culture|chambres?\s+de\s+culture)\b"),
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
    # Dans les flux beauté, « Styling » est une catégorie marchande plus forte
    # que le mot « crème » du nom : une crème coiffante reste un soin capillaire,
    # non un soin du visage. Cette exception reste bornée au rayon Beauté.
    if category == BEAUTE and _has(r"\b(?:coiffant|styling|hair\s*styling)\b", merchant_category or ""):
        return "Cheveux"

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

    # PRM Coupons Couture, BOHIN et Gütermann fournissent des matières et outils
    # de mercerie. La marque seule ne suffit pas : elle doit s’ajouter à un nom
    # de support concret, et un vêtement fini garde toujours sa propre catégorie.
    if (
        _has(r"\b(?:coupons\s+couture|bohin|g[üu]termann)\b", brand or "")
        and not _OBJET_FINI.search(name or "")
        and _has(
            r"\b(?:flanelle|ottoman(?:\s+de\s+coton)?|whipcord|[ée]tamine|"
            r"twill|tweed|jacquard|maille\s+milano|double\s+gaze|double\s+cr[êe]pe|"
            r"velours(?:\s+(?:lisse|c[oô]tel[ée]))?|cr[êe]pe(?:\s+(?:satin|envers\s+satin|lourd))?|"
            r"satin\s+(?:cuir|de\s+coton)|[ée]toffe|ouate\s+de\s+cachemire|"
            r"fil\s+pour\s+tout\s+coudre|fil\s+[àa]\s+coudre|canettes?\s+(?:universelles?|en\s+(?:plastique|acier)|plates?|bomb[ée]es?)|"
            r"(?:pied[-\s]?de[-\s]?biche|bo[iî]tier\s+de\s+canette|m[èe]tre\s+ruban|[ée]pingles?|d[ée]couseur|"
            r"craie\s+tailleur|r[èe]gle\s+(?:de\s+couture|pour\s+ourlet)|enfile[-\s]?aiguilles?|coupe[-\s]?fils?|"
            r"thermocollant|boutons?\s+[àa]\s+coudre|[ée]lastique\s+(?:fronceur\s+de\s+)?couture|retourne[-\s]?biais))\b",
            name,
        )
    ):
        return LOISIRS

    # Lilo's Nature est un spécialiste animalier vérifié. Les mentions isolées
    # « katten » ou « honden » ne deviennent Animalerie que dans ce contexte,
    # afin de ne jamais détourner ailleurs un livre ou un motif animalier.
    if _has(_LILOS_NATURE_MERCHANT, brand or "") and _has(_LILOS_NATURE_ANIMAL, name):
        return ANIMALERIE

    # Bollywolly est un flux féminin vérifié ; le contexte marchand ne suffit
    # jamais seul, il s'ajoute obligatoirement à une forme vêtement féminine
    # explicite. Les noms de modèles et les sweats non genrés restent donc hors
    # de cette règle.
    if _has(_BOLLYWOLLY_MERCHANT, merchant_name or "") and _has(_BOLLYWOLLY_FEMME_FORM, name):
        return MODE_FEMME

    # MUJI France : seconde vague lue dans les résidus produits. Le contexte
    # marchand est obligatoire afin de ne pas classer une presse à tasses ou une
    # boîte technique d'un autre flux comme article de maison.
    if _has(_MUJI_MERCHANT, merchant_name or ""):
        if _has(_MUJI_HOUSEHOLD_VARIANT, name):
            return MAISON
        if _has(_MUJI_STATIONERY_SOURCE, merchant_category):
            return CULTURE

    # 2dekansje : la catégorie source détaillée et le marchand sont exigés
    # ensemble. Les libellés de produit peuvent donc rester courts ou contenir
    # une marque sans sacrifier la traçabilité de la destination FILON.
    if _has(_2DEKANSJE_MERCHANT, merchant_name or ""):
        for category, source_pattern in _2DEKANSJE_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
        for category, source_pattern, object_pattern in _2DEKANSJE_OBJECT_ROUTES:
            if _has(source_pattern, merchant_category) and _has(object_pattern, name):
                if (
                    _has(_2DEKANSJE_SMALL_KITCHEN_SOURCE, merchant_category)
                    and _has(_2DEKANSJE_KITCHEN_ACCESSORY, name)
                ):
                    continue
                return category

    # YesStyle : cette vague repose sur le marchand et sur une catégorie source
    # exacte, relevée et homogène. Les catégories larges (« Lifestyle », « Set »)
    # restent exclues : elles doivent garder une preuve de produit individuelle.
    if _has(_YESSTYLE_MERCHANT, merchant_name or ""):
        for category, source_pattern in _YESSTYLE_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category

    # 1FoTeam : ces chemins décrivent respectivement du modélisme, des composants
    # informatiques, des jeux et des casques audio. Les familles techniques mixtes
    # ne passent pas cette route sans une preuve de nom plus précise.
    if _has(_1FOTEAM_MERCHANT, merchant_name or ""):
        for category, source_pattern in _1FOTEAM_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
    # Sneakids : les chemins ci-dessous sont bornés aux formes réellement auditées.
    # Un chemin source voisin mais absent de la liste reste volontairement soumis
    # aux preuves lexicales générales ou à une vague d'audit ultérieure.
    if _has(_SNEAKIDS_MERCHANT, merchant_name or ""):
        for category, source_pattern in _SNEAKIDS_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
    # On Fight : les racines source auditées décrivent des équipements physiques
    # de training et d'arts martiaux. Les catégories Santé, Outdoor et Ju-Jitsu
    # restent hors de la règle jusqu'à un audit distinct.
    if (
        _has(_ON_FIGHT_MERCHANT, merchant_name or "")
        and _has(_ON_FIGHT_PHYSICAL_SPORT_SOURCE, merchant_category)
        and not _has(_ON_FIGHT_SERVICE_TITLE, name)
    ):
        return SPORT
    # Sport Is Good : les quatorze racines auditées décrivent des équipements et
    # pratiques sportives explicites ; les autres racines restent en abstention.
    if (
        _has(_SPORT_IS_GOOD_MERCHANT, merchant_name or "")
        and _has(_SPORT_IS_GOOD_PHYSICAL_SPORT_SOURCE, merchant_category)
        and not _has(_SPORT_IS_GOOD_SERVICE_TITLE, name)
    ):
        return SPORT
    if _has(_SPORT_IS_GOOD_MERCHANT, merchant_name or ""):
        for category, source_pattern, name_pattern in _SPORT_IS_GOOD_LIFESTYLE_FIXED_ROUTES:
            if _has(source_pattern, merchant_category) and _has(name_pattern, name):
                return category
        if (
            _has(_SPORT_IS_GOOD_LIFESTYLE_CLOTHING_SOURCE, merchant_category)
            and _has(_SPORT_IS_GOOD_LIFESTYLE_CLOTHING_NAME, name)
        ):
            if _has(_ENFANT, merchant_category):
                return MODE_ENFANT
            if _has(_FEMME, merchant_category):
                return MODE_FEMME
            if _has(_HOMME, merchant_category):
                return MODE_HOMME
            return MODE
        for category, source_pattern, name_pattern in _SPORT_IS_GOOD_FINAL_EXPLICIT_ROUTES:
            if _has(source_pattern, merchant_category) and _has(name_pattern, name):
                return category
    if _has(_2DEKANSJE_MERCHANT, merchant_name or ""):
        for category, source_pattern in _2DEKANSJE_FIRST_BATCH_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
        for category, source_pattern in _2DEKANSJE_SECOND_BATCH_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
    # Bimba y Lola : les codes source opaques ne sont interprétables qu'avec le
    # marchand. Les deux codes mixtes de la même source restent volontairement
    # hors de ce mapping et doivent conserver leur preuve lexicale individuelle.
    if _has(_BIMBA_Y_LOLA_MERCHANT, merchant_name or ""):
        for category, source_pattern in _BIMBA_Y_LOLA_SOURCE_ROUTES:
            if _has(source_pattern, merchant_category):
                return category
        # Les codes mixtes ne transportent aucune destination par eux-mêmes : le
        # nom de l'objet reste obligatoire pour chaque route ci-dessous.
        if _has(_BIMBA_Y_LOLA_MIXED_SOURCES, merchant_category):
            for category, name_pattern in _BIMBA_Y_LOLA_MIXED_SOURCE_LEXICAL_ROUTES:
                if _has(name_pattern, name):
                    return category

    # Le modèle compatible suit toujours le produit principal : une rallonge USB-C,
    # un SSD ou un adaptateur HDMI explicitement rattaché à une catégorie
    # informatique ne devient pas un smartphone parce que son titre mentionne
    # « compatible avec iPhone ». La règle exige trois preuves complémentaires.
    if (
        merchant_category
        and _has(_COMPUTING_SOURCE, merchant_category)
        and _has(_COMPUTING_OBJECT, name)
        and _has(_COMPUTING_COMPATIBILITY, name)
        and not _has(_COMPUTING_PHONE_ACCESSORY, name)
    ):
        return INFORMATIQUE

    # Un ventilateur de boîtier ou de processeur est un composant PC, pas un
    # appareil de climatisation. Le contexte matériel est obligatoire : le mot
    # « ventilateur » seul conserve donc son classement électroménager.
    if any(_has(
        r"\b(?:ventilateurs?\s+(?:de\s+)?(?:bo[iî]tier|processeur|cpu)|"
        r"(?:cpu|case)\s+fans?)\b", text
    ) for text in (name, merchant_category) if text):
        return INFORMATIQUE

    # « Garde-robe » et « robe » peuvent décrire un meuble, une porte ou une
    # poignée. Les constructions de quincaillerie explicites l'emportent sur ce
    # faux signal vestimentaire, sans transformer le mot « robe » seul.
    if _has(
        r"\b(?:poign[ée]es?\s+de\s+porte|portes?\s+coulissantes?(?:\s+de\s+placard)?|"
        r"poign[ée]es?\s+(?:de\s+)?(?:tirage|pouss[ée]e)|meubles?\s+(?:de\s+)?placard)\b",
        name,
    ):
        return JARDIN

    # La « jupe » d'un comptoir de stand ou d'une housse de chaise est un élément
    # de mobilier événementiel, pas un vêtement. Les objets hôtes explicites sont
    # exigés pour ne pas élargir la règle au mot jupe seul.
    if _has(
        r"\b(?:comptoirs?\s+(?:de\s+)?(?:stand|bar)|tables?\s+de\s+bar|"
        r"housses?\s+de\s+chaise|chaises?\s+pliantes?)\b",
        name,
    ):
        return MAISON

    # Une étagère d'armoire ou de garde-robe reste un meuble, même si le mot
    # « robe » fait partie de l'expression. Les deux preuves — le meuble et son
    # contexte de rangement — évitent de détourner une robe sur étagère.
    if _has(r"\b(?:[ée]tag[èe]res?|shelves?)\b", name) and _has(
        r"\b(?:armoire|placard|garde[- ]robe)\b", name
    ):
        return MAISON

    # « Red Robe » peut être un nom de gamme de maquillage. Une palette
    # d'ombres à paupières est explicite et doit gagner avant le mot « robe ».
    if _has(r"\b(?:eye\s?shadows?|oogschaduw|fards?\s+[àa]\s+paupi[èe]res?)\b", name) and _has(
        r"\b(?:palette|make\s?up|maquillage)\b", name
    ):
        return BEAUTE

    # « Lady » peut décrire un motif ou une collection (« Space Lady »), et ne
    # suffit pas à contredire une catégorie marchande explicitement masculine.
    # Les marqueurs forts (women, femme, dames…) du titre gardent naturellement
    # priorité : ils ne passent pas par ce garde-fou.
    if _has(_HOMME, merchant_category) and _has(_VETEMENT, name) and _has(r"\blady\b", name) and not _has(
        r"\b(?:femme|femmes|women|women's|woman|dames|dame|ladies|feminin|f[ée]minin)\b", name
    ):
        return MODE_HOMME

    # Un nom de gamme peut contenir « robe » ou « lingerie » sans désigner un
    # vêtement. Les motifs ci-dessous sont volontairement étroits : chaque famille
    # a été reproduite dans l’API publique avec un objet ou une source explicite.
    if _has(r"\bguerlain\b", name) and _has(r"\bla petite robe noire\b", name) and _has(
        r"\b(?:eau de parfum|eau de toilette|parfum|body milk|lait corps|flacon)\b", name
    ):
        return BEAUTE
    if _has(r"\b(?:rouges? [àa] l[èe]vres|lip\s?gloss|lipglos+e?s?|make\s?up|maquillage)\b", name):
        return BEAUTE
    if _has(r"\bnyx\b", brand or "") and _has(r"\bmake\s?up\b", merchant_category):
        return BEAUTE
    if _has(r"\b(?:fijnwasmiddel|delicate wash|lingerie soap|lessive|d[ée]tergent)\b", name):
        return MAISON
    if _has(r"\b(?:liner|super absorption|sanitary)\b", name) and _has(
        r"\b(?:skincare|hygiene|hygi[èe]ne)\b", merchant_category
    ):
        return SANTE
    if _has(r"\b(?:tondeuse|rasoir|rasage|[ée]pilation|epilation|ladyshave|shaver)\b", name) and _has(
        r"\b(?:rasage|[ée]pilation|epilation)\b", merchant_category
    ):
        return BEAUTE
    # Les perruques, sacs et paniers de table à langer citent parfois « short »,
    # « top », « women » ou « basket » dans leur nom commercial. Le type d'objet
    # explicite doit gagner avant la branche vestimentaire : les trois motifs ne
    # reposent jamais sur le mot ambigu seul.
    if _has(r"\b(?:perruques?|wigs?|hair\s+extensions?)\b", name):
        return BEAUTE
    if _has(r"\b(?:shoulder|messenger|tote|crossbody)\s+bags?\b", name):
        return BAGAGERIE
    if _has(r"\bchanging\s+table\b", name) and _has(r"\bbaskets?\b", name):
        return BEBE
    # « WMNS » est le marquage féminin Adidas. Ici, il est combiné à la forme
    # vestimentaire legging : le mot « boot » de la collaboration Moon Boot ne
    # peut donc pas transformer ce vêtement en chaussure.
    if _has(r"\bwmns\b", name) and _has(r"\bleggings?\b", name):
        return MODE_FEMME
    # Ultraboost est un modèle de chaussure de course Adidas vérifiable, pas une
    # botte malgré le co-branding Moon Boot présent dans certains titres.
    if _has(r"\bultraboost\b", name):
        return CHAUSSURES
    # « Nettoyant robe cheval » concerne le pelage d'un cheval, pas un vêtement.
    # Les deux preuves évitent de déplacer un soin capillaire humain vers Animalerie.
    if _has(r"\banimal\s+cheval\b", merchant_category) and _has(
        r"\b(?:conditionneur|coat\s+shine|shampooing|nettoyant)\b", name
    ):
        return ANIMALERIE
    if _has(r"\bcrochets? de garde[- ]robe\b", name):
        return JARDIN
    if _has(r"\btoiture en chaume artificielle\b", name) and _has(r"\bjupe de toit\b", name):
        return JARDIN
    if _has(r"\blego\b", name):
        return JOUETS
    if _has(r"\bd[ée]guisement\b", name) and _has(r"\bjeux? et jouets?\b", merchant_category):
        return JOUETS

    # Les modèles de chaussures vérifiés suivent les supports, mais précèdent les
    # règles génériques : un « Gazelle Indoor » n'est pas un article inconnu.
    # Un vêtement explicite doit toutefois rester un vêtement, même si sa marque
    # commercialise aussi une chaussure du même nom.
    if not any(_has(_VETEMENT, text) for text in (name, merchant_category) if text) and _brand_footwear(brand, name):
        return CHAUSSURES

    # Certaines catégories sources décrivent directement une pratique : VTT,
    # taekwondo, jiu-jitsu ou pêche. Elles doivent classer même lorsqu’aucun mot
    # de vêtement n’est présent dans le nom (cassette, plastron, leurre). Le motif
    # exclut volontairement « sport » nu afin de ne pas aspirer les collections
    # de ville qui emploient seulement l’adjectif sportif.
    if merchant_category and _has(_USAGE_SPORTIF, merchant_category):
        return SPORT

    # « LIP » est aussi un mot de maquillage. Sur les offres horlogères dont le
    # titre dit « Horloge » et la source dit « Watch », cette coïncidence les
    # faisait entrer en Beauté avant la règle Bijoux. Les deux signaux combinés
    # identifient ici une montre commerciale, pas un produit cosmétique.
    if _has(r"\b(?:montres?|horloges?|watches?)\b", name) and _has(
        r"\b(?:watch(?:es)?|montres?|horloges?)\b", merchant_category
    ):
        return BIJOUX

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
            # Le caleçon est un sous-vêtement masculin explicite, même lorsqu'un
            # flux ne fournit ni catégorie ni marqueur de genre.
            if _has(r"\bcale[çc]ons?\b", text):
                return MODE_HOMME
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


# ── Contrôle de cohérence des classements publiés ─────────────────────────────
#
# La taxonomie classe les nouvelles offres ; ce détecteur relit les décisions
# déjà publiées et signale uniquement des contradictions à forte certitude. Il
# n'essaie jamais de « corriger » une offre : la correction reste une campagne
# explicite, testée et reprenable.
QUALITY_SEWING_SUPPORT_IN_FASHION = "sewing_support_in_fashion"
QUALITY_PHONE_PART_AS_SMARTPHONE = "phone_part_as_smartphone"
QUALITY_PHYSICAL_ITEM_AS_ACCOMMODATION = "physical_item_as_accommodation"
QUALITY_PHYSICAL_ITEM_AS_SERVICE = "physical_item_as_service"

_QUALITY_SEWING_HEAD = r"\b(?:patron(?:\s|$)|sewing\s+pattern|schnittmuster|n[äa]hmuster)"
_QUALITY_PHONE_PART = r"\b(?:coques?|backcovers?|screen\s+protectors?|[ée]cran|display|lcd|oled|connecteur|connector|nappe|flex\s+cable|buzzer|support\s+(?:pcb|sim)|frame|chassis|camera\s+module|batter(?:ie|y)|chargeurs?|chargers?)\b"
_QUALITY_PHYSICAL_HOTEL = r"\b(?:coussin|coffre-fort|bidon|bouteille|pneu|tyre|reifen)\b"
_QUALITY_PHYSICAL_SERVICE = r"\b(?:glissi[èe]re|rail|support|fixation|kit|composant|hardware|accessor(?:y|ies))\b"


def quality_signals(
    category: str | None,
    subcategory: str | None,
    offer_kind: str | None,
    name: str | None,
) -> list[str]:
    """Signale les contradictions certaines entre l'objet vendu et son classement.

    Les motifs représentent des erreurs réellement rencontrées en production.
    Une liste vide ne signifie pas « parfait » : uniquement qu'aucun des garde-
    fous connus ne s'applique à cette offre.
    """
    text = strip_colour_compounds(name or "")
    signals: list[str] = []
    if category in {MODE, MODE_FEMME, MODE_HOMME, MODE_ENFANT} and _has(_QUALITY_SEWING_HEAD, text):
        signals.append(QUALITY_SEWING_SUPPORT_IN_FASHION)
    if category == TELEPHONIE and subcategory == "Smartphones" and _has(_QUALITY_PHONE_PART, text):
        signals.append(QUALITY_PHONE_PART_AS_SMARTPHONE)
    if offer_kind == ACCOMMODATION and _has(_QUALITY_PHYSICAL_HOTEL, text):
        signals.append(QUALITY_PHYSICAL_ITEM_AS_ACCOMMODATION)
    if offer_kind == SERVICE and _has(_QUALITY_PHYSICAL_SERVICE, text):
        signals.append(QUALITY_PHYSICAL_ITEM_AS_SERVICE)
    return signals


def has_quality_signal(
    category: str | None,
    subcategory: str | None,
    offer_kind: str | None,
    name: str | None,
) -> bool:
    """Raccourci pour les audits qui n'ont besoin que du statut de contradiction."""
    return bool(quality_signals(category, subcategory, offer_kind, name))
