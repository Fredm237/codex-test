"""Le rayon adulte doit être attrapé — et rien d'autre.

Un faux négatif a déjà coûté un partenariat (« Contenu pour adultes »). Un faux
positif coûterait des milliers d'articles légitimes : les deux séries de tests
comptent autant l'une que l'autre.
"""

from app.services.safety import is_adult


def _adult(name: str, category: str | None = None, brand: str | None = None) -> bool:
    return is_adult(name=name, category=category, brand=brand)


class TestArticlesAdultes:
    def test_sex_toys_sous_toutes_leurs_graphies(self):
        assert _adult("Sex Toy rechargeable")
        assert _adult("Sextoy pour couple")
        assert _adult("Sex-toys discount")
        assert _adult("Seksspeeltje voor koppels")

    def test_termes_francais_explicites(self):
        assert _adult("Vibromasseur silicone rechargeable")
        assert _adult("Godemichet réaliste 18 cm")
        assert _adult("Gode ceinture noir")
        assert _adult("Plug anal en verre")
        assert _adult("Masturbateur masculin")
        assert _adult("Œufs vibrants télécommandés")
        assert _adult("Boules de geisha en silicone")
        assert _adult("Lubrifiant intime 100 ml")
        assert _adult("Poupée gonflable taille réelle")

    def test_termes_anglais_et_neerlandais(self):
        assert _adult("Rechargeable vibrator")
        assert _adult("Realistic dildo")
        assert _adult("Butt plug set")
        assert _adult("Crotchless bodysuit")
        assert _adult("Glijmiddel op waterbasis")
        assert _adult("Cock ring silicone")

    def test_lingerie_seulement_quand_elle_est_qualifiee(self):
        assert _adult("Lingerie érotique dentelle noire")
        assert _adult("Erotische lingerie set")
        # « Lingerie » seul est un rayon de mode parfaitement ordinaire.
        assert not _adult("Lingerie coton bio - lot de 3")
        assert not _adult("Ensemble de lingerie sans armatures")

    def test_categorie_marchand_suffit(self):
        assert _adult("Coffret découverte", category="Adult Toys")
        assert _adult("Coffret découverte", category="Sexual Wellness")
        assert _adult("Coffret cadeau", category="Erotiek > Cadeaus")
        assert _adult("Coffret cadeau", category="Boutique érotique")

    def test_marque_erotique_avec_libelle_neutre(self):
        assert _adult("Modèle 3 vitesses", brand="Fetish Collection")


class TestFauxPositifs:
    def test_mots_contenant_sex_par_accident(self):
        assert not _adult("Chemise Oxford coupe Essex")
        assert not _adult("Veste Sussex laine mélangée")
        assert not _adult("T-shirt unisex coton bio")
        assert not _adult("Parfum unisexe 50 ml")

    def test_mots_contenant_anal_par_accident(self):
        assert not _adult("Analyseur de réseau Wi-Fi")
        assert not _adult("Sac de voyage Canal Street")
        assert not _adult("Kit d'analyse d'eau de piscine")

    def test_plug_electrique_et_bricolage(self):
        assert not _adult("Adaptateur plug UK vers EU")
        assert not _adult("Spark plug moteur thermique")
        assert not _adult("Plug and play HDMI switch")

    def test_adulte_au_sens_de_taille(self):
        assert not _adult("Vélo adulte 28 pouces", category="Adult Bikes")
        assert not _adult("Déguisement adulte", category="Adult Costumes")
        assert not _adult("Casque adulte taille L", category="Adult Helmets")

    def test_mode_courante(self):
        assert not _adult("Robe midi plissée", category="Women's Clothing")
        # « godet » est un terme de mode (pan de tissu évasé) : la frontière de
        # mot doit empêcher la règle « gode » de mordre dessus.
        assert not _adult("Jupe à godets taille haute")
        assert not _adult("Godet de peinture céramique")
        assert not _adult("Chaussures de sport homme", category="Men's Shoes")

    def test_champs_absents(self):
        assert not is_adult(name=None)
        assert not is_adult(name="")
        assert not is_adult(name="Produit sans catégorie", category=None, brand=None)
