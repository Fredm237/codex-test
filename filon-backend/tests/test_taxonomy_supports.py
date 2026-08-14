"""Le support l'emporte sur le motif.

Constaté en production, et bien plus large que le seul rayon informatique : un
tissu imprimé de souris partait en Informatique, une popeline à motif voitures
en Auto & Moto, un sweat imprimé chiens et chats en Animalerie, un patron de
couture pour peluches en Jeux & Jouets.

Mesuré avant correction sur quinze libellés de mercerie réels : **un seul**
était correctement classé. Le motif imprimé sur un objet piège n'importe quel
classement par mots-clés, dans tous les rayons.

Le principe retenu : c'est le nom de tête qui décide. Un tissu reste un tissu
quel que soit ce qui est imprimé dessus — et symétriquement, un objet fini
fait d'une matière reste un objet fini, « housse de couette en percale » étant
du linge de maison et non de la mercerie.
"""

from app.services.taxonomy import classify

LOISIRS = "Loisirs créatifs"
MAISON = "Maison & Déco"


def _rayon(nom: str) -> str | None:
    return classify(None, nom, None)


class TestLeMotifNeDecidePas:
    """Libellés réellement présents au catalogue, tous mal classés avant."""

    def test_les_tissus_imprimes_restent_de_la_mercerie(self):
        for nom in (
            "Piqué 100% coton milleraies - Souris écolière",
            "Piqué 100% coton milleraies - Hérisson et écureuil",
            "Popeline coton - Petites voitures rouges",
            "Coton cretonne - Ballons de football",
            "Jersey coton - Fleurs et papillons",
            "Sweat molletonné - Chiens et chats",
        ):
            assert _rayon(nom) == LOISIRS, nom

    def test_les_tissus_unis_aussi(self):
        for nom in (
            "Jersey de laine - Gris souris (Coupon de 4.10 m)",
            "Tricotine foulée de laine - Gris souris",
            "Bord côte laine & élasthanne - Gris souris",
            "Tissu tailleur sergé de laine - Gris souris",
            "Viscose unie - Bleu canard",
            "Gabardine coton - Kaki",
        ):
            assert _rayon(nom) == LOISIRS, nom

    def test_les_patrons_de_couture_ne_sont_pas_des_jouets(self):
        assert _rayon("Patron McCall's 8422.OS - Peluches Ours, Lapin") == LOISIRS
        assert _rayon("Patron Burda Carnaval 2791 - Déguisement enfant") == LOISIRS

    def test_un_patron_de_robe_ou_pantalon_n_est_pas_le_vetement_fini(self):
        # Offres observées en production : elles avaient été publiées dans Robes
        # ou Pantalons parce que le libellé nomme le résultat à coudre.
        patrons = (
            "Patron Know Me n°2098 – Robe en tricot avec encolure croisée",
            "Patron Butterick n°7019 – Robe vintage des années 1950",
            "Patron Know Me n°2106 – Pantalon pour hommes",
            "Patron de veste pour femme – modèle n°42",
            "Schnittmuster Kleid Damen 42-50",
            "Patron KnowMe 2129.K5 (36-44) - Bodysuit & Robe",
            "Patron Maison Fauve - Robe et Blouse Pétula",
        )
        for nom in patrons:
            assert _rayon(nom) == LOISIRS, nom

    def test_les_kits_et_toiles_a_patron_restent_des_supports_de_couture(self):
        assert _rayon("Kit de couture pour robe enfant") == LOISIRS
        assert _rayon("Toile à patron 100% coton écru") == LOISIRS

    def test_patronymique_ne_declenche_pas_la_regle_de_couture(self):
        assert _rayon("Bande patronymique lot de 5 simple orange") != LOISIRS


class TestLObjetFiniLemporteSurLaMatiere:
    """Le garde-fou inverse : sans lui, la règle du support aspirait tout
    vêtement ou linge mentionnant sa matière."""

    def test_le_linge_de_maison_reste_de_la_maison(self):
        for nom in (
            "Housse de couette percale de coton 240x220",
            "Drap-housse 160x200 coton",
            "Taie d'oreiller lin lavé",
            "Rideau occultant velours bleu",
        ):
            assert _rayon(nom) == MAISON, nom

    def test_les_vetements_restent_des_vetements(self):
        assert _rayon("Chemise en lin homme manches longues") == "Mode homme"
        assert _rayon("Robe en coton bio femme") == "Mode femme"
        assert _rayon("Pyjama en jersey de coton enfant") == "Mode enfant"
        # « pattern » décrit ici le dessin d’une chemise finie en anglais ; il
        # ne doit jamais être assimilé à un patron de couture.
        assert _rayon("OLYMP Luxor shirt ecru, jacquard pattern") == "Mode"


class TestCestLaTeteQuiDecide:
    """Le garde-fou inverse ne peut pas être un simple veto.

    « S'il y a un nom d'objet fini, on abandonne le support » envoyait
    « Tissu chemise 100% coton » en Mode — un tissu vendu au mètre pour en
    coudre une chemise, chez un marchand qui ne vend que du tissu. Le libellé
    est au catalogue.

    Ce qui départage les deux sens, c'est la position : le premier des deux
    est le nom de tête, le second ne fait que le qualifier.
    """

    def test_un_tissu_a_coudre_reste_un_tissu(self):
        assert _rayon("Tissu chemise 100% coton - Carreaux bleu & vert") == LOISIRS
        assert _rayon("Tissu chemise - Carreaux bleu, rouge & rose") == LOISIRS

    def test_et_l_objet_fini_garde_la_main_quand_il_est_en_tete(self):
        assert _rayon("Housse de couette percale de coton 240x220") == MAISON

    def test_les_autres_rayons_ne_bougent_pas(self):
        attendu = {
            "Acer Souris sans fil ergonomique verticale": "Informatique",
            "Coque téléphone iPhone 15 motif chat": "Téléphonie",
            "Croquettes pour chien 12 kg": "Animalerie",
            "Pneu hiver Michelin 205/55 R16": "Auto & Moto",
            "Casque audio Bluetooth réduction de bruit": "TV & Son",
            "Baskets running homme taille 43": "Chaussures",
            "Parfum femme eau de toilette 50ml": "Beauté & Parfum",
        }
        for nom, rayon in attendu.items():
            assert _rayon(nom) == rayon, nom


class TestSupportsNonTextiles:
    def test_un_livre_sur_les_chiens_est_un_livre(self):
        assert _rayon("Livre sur les chiens de berger") == "Livres & Culture"

    def test_une_affiche_de_voiture_est_de_la_deco(self):
        assert _rayon("Affiche vintage voiture de course 50x70") == MAISON
