"""Les douze réponses fausses constatées en production, figées en test.

Chaque cas ci-dessous a réellement été rendu par l'assistant le 19 août 2026,
sur le catalogue de production. Aucun n'est inventé pour l'exercice : ce sont
les noms d'offres exacts qui remontaient.
"""

import pytest

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



def test_un_bijou_mentionnant_dress_ne_prouve_pas_un_vetement():
    title = "Yamaler Chic Bracelet Rhinestone Sparkling Dress-up Tennis Bracelet Women Wrist Jewelry"
    assert relevance.has_clothing_proof(title) is False
    assert relevance.has_clothing_proof("T-shirt Tennis Court Femme") is True



def test_demande_de_kit_neerlandais_compose_est_reconnue():
    assert relevance.request_describes_collection("fietsuitrusting onder 500 euro")


def test_satellite_compare_les_natures_dobjet_et_preserve_laccessoire_demande():
    assert relevance.is_unrequested_satellite(
        ["camera", "camera bag"], "Rear camera glass and inner frame service pack"
    )
    assert not relevance.is_unrequested_satellite(
        ["camera", "camera bag"], "Waterproof camera bag with shoulder strap"
    )



def test_anc_exige_un_mot_entier_et_ne_correspond_pas_a_blanc():
    request = "je cherche un casque avec ANC actif"
    assert relevance.proves_required_features(request, "Ecouteurs sans fil Bluetooth TooQ Bender Blanc") is False
    assert relevance.proves_required_features(request, "Casque Bluetooth ANC avec réduction de bruit") is True



def test_neutralite_de_public_ninfere_pas_un_produit_senior():
    assert relevance.age_compatible("smartphone under 400 euros", "Senior mobile phone with 4G") is False
    assert relevance.age_compatible("smartphone under 400 euros", "Senioren mobiele telefoon met 4G") is False
    assert relevance.age_compatible("smartphone for seniors", "Senior mobile phone with 4G") is True



def test_satellites_generiques_observes_dans_l_audit_large_sont_ecartes_hors_demande():
    request = ["smartphone"]
    for title in (
        "Pack embouts USB-C pour ordinateur portable",
        "Graisse silicone pour vélo électrique",
        "Verre de caméra arrière Oppo A79",
        "Bracelet smartwatch Milanese bandje",
        "Chaussettes de compression pour running",
        "Poudre détartrante pour lave-linge",
    ):
        assert relevance.is_unrequested_satellite(request, title) is True


def test_machine_automatique_exige_une_preuve_textuelle_de_l_automatisation():
    request = "automatic coffee machine under 500 euros"

    assert relevance.proves_required_features(request, "Filter coffee machine with glass jug") is False
    assert relevance.proves_required_features(request, "Fully automatic espresso coffee machine") is True



def test_mots_composes_neerlandais_preservent_la_nature_satellite_et_chaussure():
    assert relevance.is_unrequested_satellite(
        ["smartwatch"], "Podec Smartwatchbandje Samsung Galaxy Watch compatibel"
    ) is True
    assert relevance.request_requires_footwear("hardloopschoenen onder 150 euro") is True
    assert relevance.has_footwear_proof("Hardloopvest met LED en telefoonvak") is False
    assert relevance.has_footwear_proof("Hardloopschoenen met demping") is True



def test_satellites_de_maintenance_et_peripheriques_observes_dans_la_revalidation():
    request = ["produit principal"]
    for title in (
        "Robot vacuum accessoireset with HEPA filter and side brush",
        "Lavette mop pour aspirateur robot",
        "Wireless in-ear earbuds with charging case",
        "Chariot de déménagement pour machine à laver",
        "Boîtier de connexion vélo électrique",
        "Poudre détartrante pour lave-linge",
    ):
        assert relevance.is_unrequested_satellite(request, title) is True



def test_preuves_fonctionnelles_4k_et_cafe_automatique_exigent_le_contexte_complet():
    assert relevance.proves_required_features("4K televisie onder 500 euro", "TV-Kast Lowboard voor televisie") is False
    assert relevance.proves_required_features("4K televisie onder 500 euro", "4K UHD Smart TV 50 inch") is True
    assert relevance.proves_required_features(
        "automatic coffee machine under 500 euros", "Automatic electric blender for hot chocolate"
    ) is False
    assert relevance.proves_required_features(
        "automatic coffee machine under 500 euros", "Fully automatic espresso coffee machine"
    ) is True


def test_mots_composes_sac_et_meuble_sont_des_satellites_hors_demande_explicite():
    for title in (
        "Dubbele fietstas voor elektrische fietsen",
        "Schoenen waszak voor wasmachine en droger",
        "TV-kast lowboard voor televisies",
    ):
        assert relevance.is_unrequested_satellite(["fiets"], title) is True



def test_preuves_neerlandaises_automatique_et_reduction_bruit_exigent_un_attribut_explicitement_documente():
    assert relevance.proves_required_features(
        "automatische koffiemachine onder 500 euro", "Koffiezetapparaat met glazen kan en timer"
    ) is False
    assert relevance.proves_required_features(
        "automatische koffiemachine onder 500 euro", "Volautomatische koffiemachine met bonenmaler"
    ) is True
    assert relevance.proves_required_features(
        "koptelefoon met ruisonderdrukking onder 150 euro", "Kinder koptelefoon Bluetooth"
    ) is False
    assert relevance.proves_required_features(
        "koptelefoon met ruisonderdrukking onder 150 euro", "Koptelefoon met actieve ruisonderdrukking"
    ) is True


def test_batteries_tapis_et_velos_exercice_sont_des_satellites_ou_objets_connexes_hors_demande():
    for title in (
        "Batterie vélo électrique tige de selle",
        "Anti trillingsmat wasmachine en droger",
        "Mini vélo d exercice électrique avec résistance",
    ):
        assert relevance.is_unrequested_satellite(["produit principal"], title) is True


def test_casque_exige_un_format_casque_et_ecarte_les_ecouteurs_intra_auriculaires():
    assert relevance.request_requires_headphones("casque avec réduction de bruit") is True
    assert relevance.has_headphone_proof("Wireless in-ear earbuds noise cancelling") is False
    assert relevance.has_headphone_proof("Casque circum-aural avec réduction de bruit") is True



def test_peripheriques_portes_affichage_et_confort_observes_sont_des_satellites_hors_demande():
    for title in (
        "Regenponcho fiets waterdicht unisex",
        "Compteur vélo électrique connectique 6 pins",
        "Elektrisch warmtekussen wasmachine heating pad",
    ):
        assert relevance.is_unrequested_satellite(["produit principal"], title) is True



def test_vetements_de_securite_et_kits_de_superposition_sont_des_satellites_hors_demande():
    for title in (
        "Veiligheidsvestje fluojas fietsen hardlopen",
        "Tussenstuk wasmachine droger stapelkit universeel",
    ):
        assert relevance.is_unrequested_satellite(["produit principal"], title) is True



def test_bequilles_et_stands_de_velo_sont_des_satellites_hors_demande():
    for title in (
        "Bicycle Gear Fietsstandaard Achterwiel verstelbaar",
        "Kickstand stand for electric bicycle",
    ):
        assert relevance.is_unrequested_satellite(["velo electrique"], title) is True



def test_velo_electrique_exige_une_preuve_du_qualificatif_fonctionnel():
    request = "elektrische fiets onder 1200 euro"

    assert relevance.proves_required_features(request, "Tuinberging voor fietsen en gereedschap") is False
    assert relevance.proves_required_features(request, "Elektrische fiets met 500 Wh accu") is True


@pytest.mark.parametrize(
    ("query", "offer_name"),
    [
        ("ordinateur portable sous 700 euros", "Pochette pour ordinateur portable"),
        ("aspirateur robot sous 300 euros", "Lot de chiffons de nettoyage pour aspirateur robot"),
        ("wireless printer under 200 euros", "Rail de guidage pour imprimantes 3D"),
        ("lave-vaisselle sous 700 euros", "Bac gastronorme lavable au lave-vaisselle"),
        ("camping tent under 300 euros", "Tent cloth canopy tarp"),
        ("sac de couchage sous 150 euros", "Doublure sac de couchage"),
        ("chaise de bureau sous 300 euros", "Housses de chaise anthracite"),
    ],
)
def test_exclut_les_satellites_de_produit_principal_observes_en_production(query, offer_name):
    assert relevance.is_unrequested_satellite(relevance.mots(query), offer_name) is True


@pytest.mark.parametrize(
    ("query", "offer_name"),
    [
        ("ordinateur portable sous 700 euros", "Set d'enceintes PC pour ordinateur portable"),
        ("camping tent under 300 euros", "Piquets d'ancrage au sol pour tentes camping"),
    ],
)
def test_exclut_les_peripheriques_audio_et_ancrages_de_tente_non_demandes(query, offer_name):
    assert relevance.is_unrequested_satellite(relevance.mots(query), offer_name) is True



def test_exclut_une_table_pour_ordinateur_d_une_demande_d_ordinateur_portable():
    assert relevance.is_unrequested_satellite(
        relevance.mots("ordinateur portable sous 700 euros"),
        "Table pour ordinateur portable en bambou avec trous d'aération",
    ) is True


@pytest.mark.parametrize(
    "offer_name",
    [
        "CHUWI Clavier magnétique pour ordinateur portable Hi10 Max",
        "Souris sans fil pour ordinateur portable",
        "Dock USB-C pour ordinateur portable",
    ],
)
def test_exclut_les_peripheriques_informatiques_d_une_demande_d_ordinateur_portable(offer_name):
    assert relevance.is_unrequested_satellite(
        relevance.mots("ordinateur portable sous 700 euros"), offer_name
    ) is True



def test_exclut_un_moniteur_portable_d_une_demande_d_ordinateur_portable():
    assert relevance.is_unrequested_satellite(
        relevance.mots("ordinateur portable sous 700 euros"),
        "Extension d'écran Moniteur Portable pour Ordinateur Portable",
    ) is True


@pytest.mark.parametrize(
    ("query", "offer_name"),
    [
        ("laptop onder 700 euro", "Wouf Studio Laptop Hoes 13-14 inch Laptopsleeve"),
        ("smartwatch under 200 euros", "Vervangende Armbanden Set voor Smartwatch"),
        ("wireless printer under 200 euros", "Canon Cartouche d'encre jaune"),
        ("lave-vaisselle sous 700 euros", "Ménagère couverts couteau fourchette cuillère"),
        ("kampeertent onder 300 euro", "Moustiquaire pour Tente"),
        ("sleeping bag under 150 euros", "Clip ceinture Garmin"),
        ("chaise de bureau sous 300 euros", "Coussins pour chaise"),
        ("washing machine under 600 euros", "VEVOR Countertop for washing machine and dryer"),
    ],
)
def test_exclut_les_satellites_multilingues_releves_dans_outfit(query, offer_name):
    assert relevance.is_unrequested_satellite(relevance.mots(query), offer_name) is True
