"""Le battement du catalogue.

Un catalogue qui ne dit jamais quand il a été relevé se lit comme un fichier
figé. Ces chiffres sont les seuls qui prouvent que quelque chose tourne — ils
doivent donc être mesurés, et faux nulle part.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import pulse as pulse_endpoint
from app.db import models
from app.db.base import Base
from tests.endpoint_call import call


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

        now = datetime.now(UTC).replace(tzinfo=None)
        # Offre 1 : relevée à 120 €, vaut 100 € — une baisse.
        baisse = models.Offer(
            merchant_id=m.id, awin_product_id="1", name="En baisse",
            price=100.0, currency="EUR", in_stock=True,
            image_url="https://e.test/i.jpg",
        )
        # Offre 2 : relevée à 80 €, vaut 80 € — stable.
        stable = models.Offer(
            merchant_id=m.id, awin_product_id="2", name="Stable",
            price=80.0, currency="EUR", in_stock=True,
            image_url="https://e.test/i.jpg",
        )
        s.add_all([baisse, stable])
        await s.flush()

        s.add_all([
            models.PriceSnapshot(offer_id=baisse.id, price=120.0, currency="EUR", in_stock=True, captured_at=now - timedelta(hours=3)),
            models.PriceSnapshot(offer_id=baisse.id, price=100.0, currency="EUR", in_stock=True, captured_at=now - timedelta(minutes=20)),
            models.PriceSnapshot(offer_id=stable.id, price=80.0, currency="EUR", in_stock=True, captured_at=now - timedelta(hours=1)),
            # Hors fenêtre : ne doit compter nulle part.
            models.PriceSnapshot(offer_id=stable.id, price=300.0, currency="EUR", in_stock=True, captured_at=now - timedelta(days=4)),
        ])
        await s.commit()
        yield s
    await engine.dispose()


async def test_compte_les_releves_des_dernieres_24h(session):
    res = await call(pulse_endpoint, session=session)
    assert res["live"] is True
    # Trois relevés dans la fenêtre ; celui d'il y a quatre jours est exclu.
    assert res["readings_24h"] == 3
    # Avant le premier cycle journalisé, le pulse s'appuie explicitement sur les
    # relevés existants au lieu de déclarer le catalogue inconnu ou périmé.
    assert res["sync"]["status"] == "fresh"
    assert res["sync"]["source"] == "price_readings"


async def test_compte_les_baisses_pas_les_stables(session):
    res = await call(pulse_endpoint, session=session)
    assert res["drops_24h"] == 1
    assert res["drops_comparable"] is True


async def test_ne_compare_pas_des_devises_absentes_ou_differentes(session):
    stable = await session.scalar(
        select(models.Offer).where(models.Offer.awin_product_id == "2")
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=stable.id,
                price=800.0,
                currency="GBP",
                in_stock=True,
                captured_at=now - timedelta(minutes=10),
            ),
            models.PriceSnapshot(
                offer_id=stable.id,
                price=900.0,
                currency=None,
                in_stock=True,
                captured_at=now - timedelta(minutes=5),
            ),
        ]
    )
    await session.commit()
    res = await call(pulse_endpoint, session=session)
    assert res["drops_24h"] == 1


async def test_rend_la_date_du_dernier_releve(session):
    res = await call(pulse_endpoint, session=session)
    assert res["last_reading"] is not None
    # Le dernier relevé est celui d'il y a vingt minutes, pas le plus ancien.
    assert datetime.fromisoformat(res["last_reading"]) > datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)


async def test_sans_base_on_ne_pretend_rien():
    """Zéro relevé et « pas de base » ne veulent pas dire la même chose : le
    premier ferait croire à un catalogue mort."""
    res = await call(pulse_endpoint, session=None)
    assert res == {"live": False}
