"""Couleurs composées et mots à double sens.

Constaté en production sur filon.be/categorie/informatique/?sub=Claviers%20&%20Souris :
le rayon affichait des coupons de tissu, des patrons de couture Burda, un
puzzle et un panneau de façade. Aucun périphérique.

Deux causes, toutes deux dans la taxonomie :

1. « gris souris » est un nom de couleur français. Le second terme y qualifie
   la teinte, il ne désigne pas l'objet.
2. « souris » seul suffisait à classer en Informatique, alors qu'il désigne
   bien plus souvent un animal, un imprimé de tissu ou une pièce de puzzle.
"""

from app.services.taxonomy import (
    INFORMATIQUE,
    classify,
    classify_subcategory,
    strip_colour_compounds,
)


def _rayon(nom: str) -> str | None:
    return classify(None, nom, None)


class TestCouleursComposees:
    def test_la_teinte_reste_lobjet_disparait(self):
        assert strip_colour_compounds("Tissu Gris souris") == "Tissu Gris"
        assert strip_colour_compounds("Robe bleu marine") == "Robe bleu"
        assert strip_colour_compounds("Coussin gris perle") == "Coussin gris"
        assert strip_colour_compounds("Écharpe bleu canard") == "Écharpe bleu"

    def test_le_trait_dunion_compte_aussi(self):
        assert "souris" not in strip_colour_compounds("Laine gris-souris").lower()

    def test_les_couleurs_simples_sont_intactes(self):
        assert strip_colour_compounds("Pull rouge") == "Pull rouge"
        assert strip_colour_compounds("") == ""

    def test_un_objet_sans_teinte_devant_survit(self):
        """Le garde-fou ne doit pas manger le mot hors contexte de couleur."""
        assert "souris" in strip_colour_compounds("Souris sans fil Logitech").lower()


class TestSourisExigeUnContexte:
    """Les libellés ci-dessous sont ceux réellement affichés à tort."""

    def test_les_tissus_ne_sont_plus_de_linformatique(self):
        for nom in (
            "Tissu tailleur sergé de laine - Gris souris",
            "Tricotine foulée de laine - Gris souris (Coupon de 3 m)",
            "Bord côte laine & élasthanne - Gris souris",
            "Jersey de laine - Gris souris (Coupon de 4.10 m)",
            "Pull tricot col V 100% Yak - Gris souris (Taille M)",
        ):
            assert _rayon(nom) != INFORMATIQUE, nom

    def test_les_imprimes_et_jouets_non_plus(self):
        for nom in (
            "Piqué 100% coton milleraies - Souris écolière",
            "Piqué 100% coton milleraies - Hérisson et souris",
            "Puzzle 100 pièces Souris Dans La Maison Rex London",
        ):
            assert _rayon(nom) != INFORMATIQUE, nom

    def test_les_vrais_peripheriques_restent_classes(self):
        for nom in (
            "Acer Souris sans fil ergonomique verticale",
            "Acer Combo 100 - Clavier et Souris Sans Fil",
            "Logitech MX Master 3S souris bluetooth",
            "Souris optique filaire USB 1600 dpi",
        ):
            assert _rayon(nom) == INFORMATIQUE, nom

    def test_le_sous_rayon_suit_la_meme_regle(self):
        assert classify_subcategory(
            INFORMATIQUE, "Acer Souris sans fil ergonomique verticale"
        ) == "Claviers & Souris"
        # Un tissu forcé dans le rayon ne doit pas hériter du sous-rayon.
        assert classify_subcategory(
            INFORMATIQUE, "Piqué 100% coton milleraies - Souris écolière"
        ) != "Claviers & Souris"

    def test_le_clavier_seul_suffit(self):
        """« clavier » n'a pas de double sens : il n'a pas besoin de contexte."""
        assert _rayon("Clavier mécanique rétroéclairé") == INFORMATIQUE
