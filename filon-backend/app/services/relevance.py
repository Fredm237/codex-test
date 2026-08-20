"""Pertinence d'une offre face à une demande en langage naturel.

Écrit après constat en production : sur 1,59 million d'offres, l'assistant
répondait « Carte Cadeau Crypto Voucher 10-150 Euro » à qui demandait un casque
audio de moins de 150 euros, et « Crazy Machines » à qui cherchait une machine à
café. Douze demandes, zéro bonne réponse.

Deux causes se combinaient, et aucune n'est une question de modèle :

1. Le filtre SQL unissait les termes par OU. Un seul mot commun suffisait, donc
   « machine à café » attrapait « Crazy **Machines** » et « maillot de bain
   **femme** » attrapait « La **Femme** Lipstick ».
2. La requête triait par prix croissant AVANT de limiter. On ne chargeait donc
   que les cent articles les moins chers contenant un mot — les bons candidats
   n'étaient jamais lus, et aucun classement en mémoire ne pouvait les rattraper.

D'où ce module : il donne un score de correspondance, et surtout un seuil en
dessous duquel il vaut mieux ne rien proposer. Tout est pur et testable sans
base — c'est ce qui permet de figer les douze cas constatés en tests.
"""

from __future__ import annotations

import re
import unicodedata

# Genres d'offre qui ne peuvent pas répondre à une demande d'objet physique.
# Une carte cadeau « 10-150 Euro » correspond lexicalement à un budget, jamais
# à un casque.
_KINDS_HORS_PRODUIT = {"digital_content", "accommodation", "service"}

# Cette version fait partie de la clé de cache Assistant. Toute évolution de la
# politique de pertinence doit donc l’avancer dans le même changement afin qu’une
# carte décidée sous une règle ancienne ne survive jamais au déploiement.
CATALOG_RELEVANCE_POLICY_VERSION = "2026-08-20.6"

# Familles d'articles satellites : elles portent le nom du produit recherché
# sans en être. « Lingettes nettoyantes casques » n'est pas un casque, « adhésif
# écran iPhone » n'est pas un iPhone, « housse » n'est pas un téléphone.
_SATELLITES = {
    "housse", "housses", "hoes", "sleeve", "laptopsleeve", "pochette", "etui", "case", "coque", "protection", "protecteur", "adhesif", "adhesive",
    "sticker", "autocollant", "lingette", "lingettes", "chiffon", "chiffons", "nettoyant", "nettoyante",
    "chargeur", "cable", "adaptateur", "support", "fixation", "vis", "cache",
    "brosse", "brosses", "brush", "brushes", "lavette", "mop", "dweildoek", "zijborstel",
    "oorkussen", "oorkussens", "earpad", "earpads", "earbud", "earbuds", "accessoireset",
    "rechange", "reparation", "kit", "sachet", "recharge",
    "bouchon", "bouchons", "filtre", "sac", "bag", "tas", "zak", "sacoche", "bandouliere", "kast",
    "carte", "cadeau", "voucher", "cle", "clé", "licence", "abonnement",
    "regulateur", "embout", "embouts", "lame", "collier", "timer", "boitier", "connexion",
    "chariot", "trolley", "demenagement", "ontkalkings", "detartrant", "descaler",
    "verre", "graisse", "grease", "lubricant", "band", "bandje", "strap",
    "chaussette", "chaussettes", "sock", "socks", "kous", "kousen", "poudre", "powder",
    # Outils, éléments de réparation et supports. Ces objets peuvent citer le
    # produit principal sans le constituer (vitre caméra, outil de montre,
    # porte-bidon) et ne sont conservés que lorsqu’ils sont demandés.
    "outil", "outils", "tool", "tools", "tournevis", "screwdriver", "screwdrivers",
    "vitre", "glass", "cadre", "frame",
    "couvercle", "cover", "holder", "porte", "mount", "service", "wire", "rail", "guidage", "bac", "gastronorme",
    "molybdene", "molybdenum", "repair", "repairing", "ajusteur", "adjuster", "cartouche", "cartridge", "ink", "encre",
    "bracelet", "bracelets", "armband", "armbanden", "chain", "chaine", "chaîne", "rope", "cord",
    "handgreep", "handle", "grip", "rig", "lunette", "lunettes", "glasses",
    "virtual", "reality", "vr", "ventilateur", "ventilator", "fan", "cooler", "cooling",
    "selfie", "selfiestick", "stick", "tripod", "statief", "remote", "afstandsbediening",
    "imprimante", "printer", "printers", "fotoprinter", "thermometre", "thermometer",
    "sensor", "sensors", "capteur", "capteurs", "appsensoren",
    "rebond", "rebound", "calibration", "tuning", "batterie", "battery", "selle", "zadel",
    "tapis", "mat", "trillingsmat", "vibration", "verhoger", "rehausseur", "poot", "poten",
    "exercise", "exercice", "fitness", "resistance", "poncho", "cape", "regencape",
    "compteur", "display", "dashboard", "warmtekussen", "heating", "kussen", "coussin", "pad",
    "veiligheidsvest", "veiligheidsvestje", "fluojas", "tussentuk", "tussenstuk", "stapelkit", "stacking",
    "bequille", "kickstand", "standaard", "stand", "tarp", "canopy", "doublure", "lining", "liner",
    "enceinte", "enceintes", "speaker", "speakers", "loudspeaker", "table", "desk", "plateau", "lapdesk",
    "clavier", "keyboard", "souris", "mouse", "dock", "docking", "hub", "stylus", "moniteur", "ecran", "écran", "display",
    "piquet", "piquets", "stake", "stakes", "ancrage", "anchor", "moustiquaire", "mosquito", "net",
    "clip", "clips", "couverts", "cutlery", "couteau", "fourchette", "cuillere", "cuillère", "coussins",
    # Une mention de "jacket" ne rend pas un sous-vêtement équivalent à une
    # veste. Ces couches et pièces de lingerie restent valides uniquement quand
    # l’utilisateur les demande explicitement.
    "underwear", "lingerie", "crotch", "bra", "bralette", "panty", "panties",
    "culotte", "soutien", "gorge", "shapewear", "bodysuit",
}

# Un article satellite reste légitime si la demande le nomme.
_INTENTION_SATELLITE = _SATELLITES - {"carte", "cle", "clé"}

# Équivalences lexicales limitées aux termes de mode et d’occasion utilisés par
# Outfit Studio. Elles relient les trois langues cibles sans prétendre déduire
# un style : « wedding dress » est une preuve textuelle de « robe de mariage ».
# Attributs fonctionnels explicitement déclarés dans une demande. Ils ne sont
# jamais déduits d’un scope : si l’utilisateur les nomme, le titre doit les
# prouver dans l’une des langues cibles avant toute recommandation.
_REQUIRED_FEATURE_PROOFS: tuple[tuple[re.Pattern[str], re.Pattern[str]], ...] = (
    (
        re.compile(r"(?:r[ée]duction\s+de\s+bruit|noise\s+cancell?ing|\banc\b|ruisonderdrukking)"),
        re.compile(r"(?:r[ée]duction\s+de\s+bruit|noise\s+cancell?ing|\banc\b|ruisonderdrukking)"),
    ),
    (
        re.compile(r"(?:connect[ée]e?|connected|smartwatch)"),
        re.compile(r"(?:connect[ée]e?|connected|smartwatch)"),
    ),
    (
        re.compile(r"(?:automatic\w*|automatique\w*|automatisch\w*|volautomatisch)\s+(?:coffee|koffie|caf[eé])"),
        re.compile(
            r"(?:(?:fully\s+automatic|volautomatisch\w*|automatisch\w*|automatique\w*|automatic\w*)(?:\s+[a-z0-9]+){0,2}\s+(?:coffee|koffie|caf[eé])|"
            r"(?:coffee|koffie|caf[eé])(?:\s+[a-z0-9]+){0,2}\s+(?:fully\s+automatic|volautomatisch\w*|automatisch\w*|automatique\w*|automatic\w*))"
        ),
    ),
    (
        re.compile(r"\b(?:4k|uhd)\b"),
        re.compile(r"\b(?:4k|uhd)\b"),
    ),
    (
        re.compile(r"(?:electric|electrique|elektrisch\w*)\s+(?:bike|bicycle|velo|fiets)"),
        re.compile(
            r"(?:(?:electric|electrique|elektrisch\w*)\s+(?:bike|bicycle|velo|fiets)|"
            r"(?:bike|bicycle|velo|fiets)(?:\s+[a-z0-9]+){0,2}\s+(?:electric|electrique|elektrisch\w*))"
        ),
    ),
)


_EQUIVALENCES = {
    "mariage": frozenset({"mariage", "wedding", "bruiloft", "bridal", "bride"}),
    "wedding": frozenset({"mariage", "wedding", "bruiloft", "bridal", "bride"}),
    "bruiloft": frozenset({"mariage", "wedding", "bruiloft", "bridal", "bride"}),
    "robe": frozenset({"robe", "dress", "jurk"}),
    "dress": frozenset({"robe", "dress", "jurk"}),
    "jurk": frozenset({"robe", "dress", "jurk"}),
    # Qualificatif de connectivité explicitement demandé. Le rapprochement
    # couvre les titres de catalogue FR/NL/EN sans déduire de fonctionnalité.
    "connectee": frozenset({"connectee", "connecte", "connected", "smartwatch"}),
    "connecte": frozenset({"connectee", "connecte", "connected", "smartwatch"}),
    "connected": frozenset({"connectee", "connecte", "connected", "smartwatch"}),
    "smartwatch": frozenset({"connectee", "connecte", "connected", "smartwatch"}),
}


def _plat(texte: str) -> str:
    """Minuscules sans accents : « été » et « ete » doivent se rencontrer."""
    sans = unicodedata.normalize("NFKD", (texte or "").lower())
    return "".join(c for c in sans if not unicodedata.combining(c))


# Mots qui n'expriment jamais un produit : liaisons, verbes de demande, et le
# vocabulaire du budget. Sans ce filtre, « un casque audio sans fil pour moins
# de 150 euros » pèse huit termes dont quatre décrivent le prix, et un vrai
# casque Sony n'en retrouve que la moitié — donc se fait rejeter.
# Une demande qui désigne explicitement des vêtements ne peut être satisfaite
# par un objet de sport, un bijou ou un accessoire partageant seulement le nom de
# la pratique. Ces vocabulaires décrivent la nature générique « vêtement » dans
# les langues cibles ; ils ne sont pas des listes propres à un sport ou à une
# catégorie de catalogue.
# Les mots qui désignent une collection d’équipement, quel que soit son
# domaine. Ils activent seulement une préférence de représentativité ; ils ne
# créent ni catégorie ni profil produit.
_CONTEXT_STOPWORDS = frozenset({
    "voor", "van", "the", "of", "for", "with", "met", "avec", "sans",
})

_COLLECTION_REQUEST_TERMS = frozenset({
    "equipment", "gear", "kit", "kits", "uitrusting", "materiaal", "materiel", "matériel",
    "set", "ensemble", "complet", "complete",
})
# Les composants individuels ne représentent pas à eux seuls une demande de kit
# lorsqu’un équipement autonome et correctement observable existe dans le même
# scope. La liste décrit la nature générique de composant, pas un domaine.
_COMPONENT_TERMS = frozenset({
    "piquet", "piquets", "peg", "pegs", "stake", "stakes", "screw", "screws", "vis",
    "spare", "replacement", "rechange", "part", "parts", "piece", "pieces", "component",
    "components", "clip", "clips", "hook", "hooks", "adapter", "adaptor", "cord", "cords",
})


_CLOTHING_REQUEST_TERMS = frozenset({
    "clothing", "clothes", "apparel", "garment", "garments", "kleding", "kledij",
    "vetement", "vetements", "vêtement", "vêtements",
})
_FOOTWEAR_REQUEST_TERMS = frozenset({
    "shoe", "shoes", "schoen", "schoenen", "chaussure", "chaussures",
    "sneaker", "sneakers", "boot", "boots", "botte", "bottes",
})
# Un titre peut contenir une coupe ou un mot de style vestimentaire tout en
# décrivant sans ambiguïté un bijou. La nature d’objet explicite prévaut sur ce
# vocabulaire de style, pour tous les domaines et toutes les langues cibles.
# Le genre ne doit jamais être deviné. Ces marqueurs servent uniquement à ne
# pas opposer au besoin une pièce dont le titre se déclare explicitement pour un
# autre public, et à préserver les articles sans marqueur ou unisexes.
_FEMININE_GENDER_TERMS = frozenset({
    "femme", "femmes", "women", "woman", "female", "dame", "dames", "vrouw", "vrouwen", "girl", "girls", "fille", "filles",
})
_MASCULINE_GENDER_TERMS = frozenset({
    "homme", "hommes", "men", "mens", "male", "heren", "heer", "boy", "boys", "garcon", "garcons",
})
# Comme le genre, le public enfant ne peut pas être déduit d’une demande neutre.
# Ces marqueurs sont linguistiques et transversaux, sans dépendance au rayon.
_CHILD_AUDIENCE_TERMS = frozenset({
    "enfant", "enfants", "child", "children", "kid", "kids", "junior", "toddler",
    "baby", "bebe", "bébé", "kleuter", "peuter", "educatif", "educational",
    "learning", "toy", "jouet", "jouets",
})
_SENIOR_AUDIENCE_TERMS = frozenset({
    "senior", "seniors", "senioren", "elderly", "elder", "bejaarde", "bejaarden",
})


_JEWELLERY_OBJECT_TERMS = frozenset({
    "bracelet", "bracelets", "necklace", "necklaces", "jewelry", "jewellery",
    "earring", "earrings", "pendant", "pendants", "collier", "colliers",
    "bague", "bagues", "bijou", "bijoux", "boucle", "boucles", "choker",
})
_FOOTWEAR_OFFER_TERMS = _FOOTWEAR_REQUEST_TERMS
_HEADPHONE_REQUEST_TERMS = frozenset({"casque", "headphone", "headphones", "koptelefoon"})
_HEADPHONE_EARBUD_TERMS = frozenset({"earbud", "earbuds", "ecouteur", "ecouteurs", "inear", "intra"})
_HEADPHONE_OFFER_TERMS = _HEADPHONE_REQUEST_TERMS
_CLOTHING_OFFER_TERMS = frozenset({
    "tshirt", "shirt", "polo", "top", "jersey", "dress", "skirt", "short", "shorts",
    "trousers", "pants", "legging", "socks", "sock", "jacket", "coat", "sweater", "hoodie",
    "sweatshirt", "maillot", "robe", "jupe", "pantalon", "chaussette", "veste",
    "manteau", "pull", "gilet", "chemise", "tunique", "broek", "jurk", "rok", "sokken",
    "jas", "trui", "vest", "kleding", "kledij",
})


_VIDES = {
    "un", "une", "des", "les", "le", "la", "de", "du", "pour", "avec", "sans",
    "et", "ou", "en", "au", "aux", "dans", "sur", "je", "veux", "cherche",
    "besoin", "bon", "bonne", "meilleur", "meilleure", "euro", "euros", "eur",
    "moins", "plus", "qui", "que", "quoi", "mon", "ma", "mes", "ce", "cette",
    "est", "prix", "budget", "environ", "vers", "sous", "entre", "max", "maxi",
    # Contexte de tenue ou de saison : il ne prouve pas à lui seul une pièce du
    # catalogue et ne doit pas pénaliser une robe de mariage correctement titrée.
    "tenue", "outfit", "look", "ete", "summer", "zomer",
}


def mots(texte: str) -> list[str]:
    """Mots exploitables d'un texte, sans liaisons ni vocabulaire de budget."""
    bruts = re.findall(r"[a-z0-9]{2,}", _plat(texte))
    return [m for m in bruts if m not in _VIDES]


def termes_significatifs(termes: list[str]) -> list[str]:
    """Les termes qui portent l'intention, les plus discriminants d'abord.

    Un mot long est plus spécifique qu'un mot court : « expresso » désigne mieux
    qu'« café ». C'est grossier, mais c'est mesurable et sans dépendance.
    """
    uniques = list(dict.fromkeys(t for t in termes if len(t) >= 3))
    return sorted(uniques, key=len, reverse=True)


def _term_is_present(term: str, offer_words: set[str], normalized_offer_name: str) -> bool:
    """Vérifie un terme ou son équivalent explicite dans le titre marchand."""
    variants = _EQUIVALENCES.get(term, frozenset({term}))
    return any(variant in offer_words or variant in normalized_offer_name for variant in variants)


def request_has_required_features(request: str) -> bool:
    """Indique que la demande contient un attribut fonctionnel à prouver."""
    normalized_request = _plat(request)
    return any(request_pattern.search(normalized_request) for request_pattern, _ in _REQUIRED_FEATURE_PROOFS)


def proves_required_features(request: str, offer_name: str) -> bool:
    """Vérifie chaque attribut fonctionnel explicitement demandé."""
    normalized_request = _plat(request)
    normalized_offer = _plat(offer_name)
    return all(
        not request_pattern.search(normalized_request) or bool(offer_pattern.search(normalized_offer))
        for request_pattern, offer_pattern in _REQUIRED_FEATURE_PROOFS
    )


def explicit_qualifier_terms(terms: tuple[str, ...]) -> tuple[str, ...]:
    """Conserve les qualificatifs explicites, pas les mots composés de contexte.

    Les suffixes néerlandais « kleding » et « uitrusting » décrivent le type de
    demande. Les injecter comme termes obligatoires ferait tomber sous le seuil
    des titres marchands pourtant pertinents (par exemple « tennissokken »).
    """
    return tuple(
        term for term in terms
        if term not in _COLLECTION_REQUEST_TERMS
        and not re.search(r"(?:kleding|kledij|uitrusting|materiaal)$", _plat(term))
    )


def distinct_context_terms(request_terms: tuple[str, ...], scope_terms: tuple[str, ...]) -> tuple[str, ...]:
    """Retourne les mots explicites qui précisent le produit au-delà du scope.

    Le scope « chaise » ne doit pas absorber le qualificatif réellement saisi
    « bureau » ; ce dernier doit être attesté dans le titre marchand. Les mots
    déjà présents dans les synonymes de scope ne sont pas redemandés.
    """
    scope_words = set(mots(" ".join(scope_terms)))
    return tuple(
        term for term in explicit_qualifier_terms(request_terms)
        if len(term) >= 3
        and term not in scope_words
        and term not in _CONTEXT_STOPWORDS
        # Les contraintes de genre et de public disposent déjà de règles
        # compatibles multilingues ; elles ne doivent pas être redemandées sous
        # leur orthographe exacte dans les titres marchands.
        and gender_marker(term) is None
        and audience_marker(term) is None
    )


def proves_context_terms(context_terms: tuple[str, ...], offer_name: str) -> bool:
    """Vérifie tous les qualificatifs distinctifs explicitement demandés."""
    offer_words = set(mots(offer_name))
    normalized_offer = _plat(offer_name)
    return all(_term_is_present(term, offer_words, normalized_offer) for term in context_terms)


def proves_any_product_phrase(scope_terms: tuple[str, ...], offer_name: str) -> bool:
    """Vérifie une expression produit explicite de deux mots ou plus.

    Une phrase telle que « machine à laver » ne peut être satisfaite par la
    seule occurrence de « machine » dans « four à pizza ». Cette preuve n’est
    utilisée que pour empêcher un repli lorsqu’aucun score strict ne subsiste.
    """
    offer_words = set(mots(offer_name))
    normalized_offer = _plat(offer_name)
    for phrase in scope_terms:
        phrase_terms = mots(phrase)
        if len(phrase_terms) >= 2 and all(
            _term_is_present(term, offer_words, normalized_offer)
            for term in phrase_terms
        ):
            return True
    return False


def request_describes_collection(text: str) -> bool:
    """Indique qu’une demande porte sur un kit ou un ensemble d’équipement."""
    normalized = _plat(text)
    return bool(
        set(mots(normalized)) & _COLLECTION_REQUEST_TERMS
        # Le néerlandais compose couramment l’objet et l’ensemble demandé,
        # par exemple « fietsuitrusting ». Ce suffixe est linguistique et ne
        # dépend donc d’aucun domaine de catalogue.
        or re.search(r"[a-z]{3,}(?:uitrusting|materiaal)\b", normalized)
    )


def is_unrequested_component(request: str, nom_offre: str) -> bool:
    """Repère un composant non explicitement demandé dans une demande de kit."""
    request_terms = set(mots(request))
    offer_terms = set(mots(nom_offre))
    return bool(offer_terms & _COMPONENT_TERMS) and not bool(request_terms & _COMPONENT_TERMS)


def request_requires_clothing(text: str) -> bool:
    """Indique que la demande exige un vêtement, quelle que soit sa pratique.

    Le néerlandais soude régulièrement la pratique et le type de besoin
    (« tenniskleding »). Cette terminaison linguistique est traitée sans faire
    intervenir un sport ni une catégorie de produit.
    """
    normalized = _plat(text)
    return bool(
        set(mots(normalized)) & _CLOTHING_REQUEST_TERMS
        or re.search(r"[a-z]{3,}(?:kleding|kledij)\b", normalized)
    )


def request_requires_footwear(text: str) -> bool:
    """Indique qu’une demande exige une chaussure, quel que soit le sport."""
    normalized = _plat(text)
    return bool(
        set(mots(normalized)) & _FOOTWEAR_REQUEST_TERMS
        or re.search(r"[a-z]{3,}(?:schoenen|shoes)\b", normalized)
    )


def has_footwear_proof(nom_offre: str) -> bool:
    """Indique qu’un titre marchand prouve une chaussure plutôt qu’un vêtement."""
    normalized = _plat(nom_offre)
    return bool(
        set(mots(normalized)) & _FOOTWEAR_OFFER_TERMS
        or re.search(r"[a-z]{3,}(?:schoenen|shoes)\b", normalized)
    )


def request_requires_headphones(text: str) -> bool:
    """Indique qu’une demande vise un casque plutôt que des écouteurs."""
    return bool(set(mots(text)) & _HEADPHONE_REQUEST_TERMS)


def has_headphone_proof(nom_offre: str) -> bool:
    """Vérifie qu’un titre désigne un casque et non des écouteurs intra-auriculaires."""
    offer_terms = set(mots(nom_offre))
    if offer_terms & _HEADPHONE_EARBUD_TERMS:
        return False
    return bool(offer_terms & _HEADPHONE_OFFER_TERMS or "circum" in _plat(nom_offre))


def has_clothing_proof(nom_offre: str) -> bool:
    """Indique qu’un titre marchand prouve qu’il vend une pièce vestimentaire."""
    offer_terms = set(mots(nom_offre))
    if offer_terms & _JEWELLERY_OBJECT_TERMS:
        return False
    if offer_terms & _CLOTHING_OFFER_TERMS:
        return True
    # Même mécanisme linguistique que pour la demande : les flux néerlandais
    # concatènent fréquemment la pratique et la pièce (« tennissokken »).
    return bool(re.search(r"[a-z]{3,}(?:sokken|kleding|kledij|trui|broek|jurk)\b", _plat(nom_offre)))


def gender_marker(text: str) -> str | None:
    """Retourne seulement le genre explicitement déclaré par un texte, sinon rien."""
    terms = set(mots(text))
    if terms & _FEMININE_GENDER_TERMS:
        return "female"
    if terms & _MASCULINE_GENDER_TERMS:
        return "male"
    return None


def gender_compatible(request: str, nom_offre: str) -> bool:
    """Évite une hypothèse de genre, sans exclure les articles non marqués."""
    wanted = gender_marker(request)
    declared = gender_marker(nom_offre)
    if wanted is None:
        return declared is None
    return declared is None or declared == wanted


def audience_marker(text: str) -> str | None:
    """Retourne seulement un public d’âge explicitement déclaré, sinon rien."""
    terms = set(mots(text))
    if terms & _CHILD_AUDIENCE_TERMS:
        return "child"
    if terms & _SENIOR_AUDIENCE_TERMS:
        return "senior"
    return None


def targets_children(text: str) -> bool:
    """Indique qu’une demande désigne explicitement un public enfant."""
    return audience_marker(text) == "child"


def age_compatible(request: str, nom_offre: str) -> bool:
    """Évite d’inférer un public enfant ou senior dans une demande neutre."""
    wanted = audience_marker(request)
    declared = audience_marker(nom_offre)
    if wanted is None:
        return declared is None
    return declared is None or declared == wanted


def is_unrequested_satellite(demande_termes: list[str], nom_offre: str) -> bool:
    """Indique qu’un titre décrit un accessoire que la demande ne nomme pas."""
    # Les mots sémantiques peuvent être des expressions (« camera bag ») : ils
    # doivent être re-tokenisés avant comparaison pour ne jamais écarter une
    # composante explicitement demandée.
    demande = set(termes_significatifs(mots(" ".join(demande_termes))))
    offer_words = set(mots(nom_offre))
    satellites_offre = offer_words & _SATELLITES
    normalized_offer = _plat(nom_offre)
    # Les titres néerlandais soudent fréquemment le produit et son accessoire,
    # par exemple « smartwatchbandje ». Cette terminaison renseigne la nature
    # de l’objet sans dépendre d’une famille de produits précise.
    if re.search(r"[a-z]{3,}(?:bandje|band|strap|hoes|case)\b", normalized_offer):
        satellites_offre.add("bandje")
    if re.search(r"[a-z]{3,}(?:tas|tassen|zak|kast|houder)\b", normalized_offer):
        satellites_offre.add("tas")
    if re.search(r"[a-z]{3,}(?:poncho|kussen|coussin|vestje|standaard)\b", normalized_offer):
        satellites_offre.add("poncho")
    satellites_demandes = demande & _INTENTION_SATELLITE
    # Une bandoulière ou une poignée est constitutive d’une sacoche explicitement
    # demandée ; ce n’est pas un second produit. Cette relation est générique aux
    # articles de portage et ne dépend d’aucun rayon de catalogue.
    carrier_terms = {"sac", "bag", "sacoche"}
    if offer_words & carrier_terms and demande & carrier_terms:
        satellites_offre -= {"strap", "bandouliere", "handle", "handgreep"}
    # Une demande de sacoche autorise une sacoche, pas par extension une vitre
    # ou un cadre. La comparaison porte sur la nature précise du satellite.
    return bool(satellites_offre - satellites_demandes)


def score(
    demande_termes: list[str],
    nom_offre: str,
    *,
    offer_kind: str | None = None,
    categorie: str | None = None,
) -> float:
    """Score de 0 à 1. Au-dessous de `SEUIL`, l'offre ne répond pas.

    Le score n'est pas une probabilité : c'est une part de la demande
    réellement retrouvée dans le nom, corrigée par ce qui disqualifie.
    """
    termes = termes_significatifs([_plat(t) for t in demande_termes])
    if not termes:
        return 0.0

    mots_offre = set(mots(nom_offre))
    nom = _plat(nom_offre)

    # Part des termes de la demande réellement présents.
    trouves = sum(1 for t in termes if _term_is_present(t, mots_offre, nom))
    couverture = trouves / len(termes)

    # Le terme le plus discriminant doit être là. Sans lui, la correspondance
    # est accidentelle — c'est le cas « Crazy Machines » pour « machine à café ».
    tete = termes[0]
    if not _term_is_present(tete, mots_offre, nom):
        couverture *= 0.35

    # Une correspondance partielle n'est pas une correspondance. Quand
    # l'utilisateur nomme deux choses — « cafetière Delonghi » — n'en retrouver
    # qu'une désigne un autre produit : la Kitchencraft n'est pas la Delonghi.
    if couverture < 0.6:
        couverture *= 0.6

    s = couverture

    # Un genre d'offre incompatible disqualifie, quelle que soit la couverture.
    if offer_kind in _KINDS_HORS_PRODUIT:
        s *= 0.15

    # Article satellite non demandé : il porte le nom sans être la chose.
    if is_unrequested_satellite(termes, nom_offre):
        s *= 0.25

    return max(0.0, min(1.0, s))


# Sous ce seuil, mieux vaut s'abstenir que répondre à côté. Calé sur les cas
# constatés : « bouchons anti-bruit » pour « casque à réduction de bruit »
# tombe dessous, un vrai casque passe au-dessus.
SEUIL = 0.5
