"""Régression sur la dernière matière textile visible dans Lingerie & Nuit."""

from app.services import taxonomy as t


def test_une_resille_qualifiee_pour_lingerie_est_de_la_mercerie() -> None:
    assert t.classify("Lingerie", "Résille à bord franc pour lingerie - Nude") == t.LOISIRS
    assert t.classify("Lingerie", "Résille à bord franc pour lingerie - Noir") == t.LOISIRS
    assert t.classify("Lingerie", "Satin doux pour lingerie - Noir") == t.LOISIRS


def test_un_vrai_soutien_gorge_nest_pas_un_tissu() -> None:
    assert t.classify("Lingerie", "Soutien-gorge femme en dentelle") == t.MODE_FEMME
