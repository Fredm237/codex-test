"""Les douze réponses fausses constatées en production, figées en test.

Chaque cas ci-dessous a réellement été rendu par l'assistant le 19 août 2026,
sur le catalogue de production. Aucun n'est inventé pour l'exercice : ce sont
les noms d'offres exacts qui remontaient.
"""

from app.services import relevance


def _termes(phrase: str) -> list[str]:
    return relevance.mots(phrase)


CAS_FAUX = [
    ("un casque audio sans fil pour moins de 150 euros",
     "Carte Cadeau Crypto Voucher à montant variable 10 - 150 Euro", "digital_content"),
    ("casque à réduction de bruit", "Bouchons anti-bruit à usage unique", "physical_product"),
    ("une machine à café expresso",
     "Crazy Machines Elements - Collision Course & Mental Activity DLC", "digital_content"),
    ("un aspirateur robot", "Pixel Robot Hunter Steam CD Key", "digital_content"),
    ("un maillot de bain femme", "La Femme Lipstick - Pink Spice", "physical_product"),
    ("un ordinateur portable pour étudiant sous 900 euros",
     "Häfele Cache IS20 pour vis pour plaques de serrage TORX", "physical_product"),
    ("des chaussures de running homme taille 43",
     "Gartenkraft Slijtstrip Voor Ballastschop - Schepmaat 7", "physical_product"),
    ("casque Sony WH-1000XM5",
     "Lingettes nettoyantes visières et casques Dr Wack S100", "physical_product"),
    ("iPhone", "Adhésif Écran Apple iPhone 7 Plus, Noir, Service Pack", "physical_product"),
    ("Nike", "Nike cadeaubon", "digital_content"),
    ("cafetière Delonghi", "Kitchencraft Koffietimer La Cafetière 20 Cm Staal Zwart", "physical_product"),
    ("des baskets blanches avec un jean",
     "Thermo Ondergoed Dames - Thermo Legging Dames - Zwart", "physical_product"),
]

CAS_JUSTES = [
    ("un casque audio sans fil pour moins de 150 euros",
     "Sony WH-CH720N Casque audio sans fil à réduction de bruit", "physical_product"),
    ("casque à réduction de bruit",
     "Bose QuietComfort 45 casque réduction de bruit active", "physical_product"),
    ("une machine à café expresso",
     "De'Longhi Dedica Style Machine à café expresso EC685", "physical_product"),
    ("un aspirateur robot", "iRobot Roomba 692 aspirateur robot connecté", "physical_product"),
    ("un maillot de bain femme", "Maillot de bain une pièce femme noir", "physical_product"),
    ("des chaussures de running homme taille 43",
     "Asics Gel-Contend 8 chaussures de running homme", "physical_product"),
]


def test_les_douze_reponses_fausses_tombent_sous_le_seuil():
    echecs = []
    for demande, nom, kind in CAS_FAUX:
        s = relevance.score(_termes(demande), nom, offer_kind=kind)
        if s >= relevance.SEUIL:
            echecs.append(f"{s:.2f} — « {demande} » → « {nom} »")
    assert not echecs, "Ces réponses fausses passent encore le seuil :\n" + "\n".join(echecs)


def test_les_bonnes_reponses_passent_le_seuil():
    echecs = []
    for demande, nom, kind in CAS_JUSTES:
        s = relevance.score(_termes(demande), nom, offer_kind=kind)
        if s < relevance.SEUIL:
            echecs.append(f"{s:.2f} — « {demande} » → « {nom} »")
    assert not echecs, "Ces bonnes réponses sont rejetées à tort :\n" + "\n".join(echecs)


def test_une_carte_cadeau_ne_repond_jamais_a_un_objet():
    s = relevance.score(_termes("casque audio"), "Carte cadeau casque audio 150 euros",
                        offer_kind="digital_content")
    assert s < relevance.SEUIL


def test_un_accessoire_reste_valable_si_on_le_demande():
    s = relevance.score(_termes("housse pour iPhone 13"),
                        "Housse silicone pour iPhone 13 noire", offer_kind="physical_product")
    assert s >= relevance.SEUIL


def test_les_accents_ne_separent_pas():
    assert relevance.score(_termes("cafetière"), "Cafetiere italienne inox",
                           offer_kind="physical_product") >= relevance.SEUIL
