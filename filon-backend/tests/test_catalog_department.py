"""Filtrer par département.

Régression constatée en production : cliquer sur « Beauté & Santé » dans le
catalogue affichait des pneus. Le département n'est pas une colonne — c'est un
regroupement de rayons — et l'endpoint n'en tenait aucun compte : la sélection
n'envoyait donc aucun critère et la page rendait le catalogue entier.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import offers as offers_endpoint
from app.db import models
from app.db.base import Base
from app.services import taxonomy
from tests.endpoint_call import call

# Rayons réels, pris dans la taxonomie plutôt qu'écrits en dur : si un rayon
# change de département, le test doit suivre le code, pas le contredire.
BEAUTE = taxonomy.categories_of_department("Beauté & Santé")[0]
AUTO = taxonomy.categories_of_department("Famille & Quotidien")[-1]


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        m = models.Merchant(awin_mid=1, name="Boutique", slug="b")
        s.add(m)
        await s.flush()

        def offer(pid, name, category):
            return models.Offer(
                merchant_id=m.id, awin_product_id=pid, name=name, price=10.0,
                currency="EUR", image_url="https://example.test/i.jpg",
                is_canonical=True, filon_category=category,
            )

        s.add(offer("1", "Parfum Nina Ricci Nina", BEAUTE))
        s.add(offer("2", "Crème hydratante visage", BEAUTE))
        s.add(offer("3", "Pneu hiver Kenda 205/55 R16", AUTO))
        s.add(offer("4", "Pneu été Austone 195/65 R15", AUTO))
        await s.commit()
        yield s
    await engine.dispose()


async def test_le_departement_filtre_vraiment(session):
    """Le bug : « Beauté & Santé » renvoyait aussi les pneus."""
    res = await call(offers_endpoint, department="Beauté & Santé", session=session)
    assert res["total"] == 2
    assert all("Pneu" not in item["name"] for item in res["items"])


async def test_le_slug_marche_comme_le_nom(session):
    """L'URL porte le slug ; l'API doit accepter les deux."""
    par_slug = await call(
        offers_endpoint, department=taxonomy.slug_of("Beauté & Santé"), session=session
    )
    par_nom = await call(offers_endpoint, department="Beauté & Santé", session=session)
    assert par_slug["total"] == par_nom["total"] == 2


async def test_un_departement_inconnu_ne_rend_rien(session):
    """Mieux vaut zéro résultat qu'un filtre silencieusement ignoré : c'est
    exactement ce qui faisait passer le bug inaperçu."""
    res = await call(offers_endpoint, department="Rayon Inexistant", session=session)
    assert res["total"] == 0


async def test_sans_departement_tout_reste_visible(session):
    res = await call(offers_endpoint, session=session)
    assert res["total"] == 4


async def test_le_rayon_reste_prioritaire(session):
    """Rayon et département ensemble : le rayon, plus précis, doit primer."""
    res = await call(
        offers_endpoint, department="Beauté & Santé", category=BEAUTE, session=session
    )
    assert res["total"] == 2
