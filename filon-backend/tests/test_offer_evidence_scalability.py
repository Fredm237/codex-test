from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db.base import Base
from app.intelligence import catalog_adapter, general_catalog
from app.intelligence.intent_resolution import GeneralIntent, IntentScope
from app.services import catalog_search, taxonomy
from app.services.freshness import offer_observation_is_fresh
from app.services.offer_evidence import OfferEvidence, load_offer_evidence


class _EmptyRows:
    def all(self):
        return []


class _RecordingSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _EmptyRows()


def _bound_ids(statement) -> tuple[int, ...]:
    for value in statement.compile().params.values():
        if (
            isinstance(value, (list, tuple))
            and value
            and all(
                isinstance(item, int) and not isinstance(item, bool) for item in value
            )
        ):
            return tuple(value)
    raise AssertionError("requête sans lot d'identifiants")


@pytest.mark.parametrize("current_only", [False, True])
async def test_grand_scope_decoupe_les_identifiants_sans_in_geant(current_only):
    session = _RecordingSession()
    offers = [
        SimpleNamespace(id=offer_id, price=80.0, currency="EUR", in_stock=True)
        for offer_id in range(1, 1_202)
    ]

    evidence = await load_offer_evidence(
        session,
        offers,
        current_only=current_only,
    )

    assert list(evidence) == list(range(1, 1_202))
    assert [_bound_ids(statement) for statement in session.statements] == [
        tuple(range(1, 501)),
        tuple(range(501, 1_001)),
        tuple(range(1_001, 1_202)),
    ]
    assert all(item.history == () for item in evidence.values())


@pytest.fixture
async def evidence_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session, engine
    await engine.dispose()


async def test_current_only_agrege_une_preuve_par_offre_et_reste_fail_closed(
    evidence_session,
):
    session, engine = evidence_session
    merchant = models.Merchant(awin_mid=9951, name="Preuves", slug="preuves")
    session.add(merchant)
    await session.flush()
    current = models.Offer(
        merchant_id=merchant.id,
        awin_product_id="current",
        name="Offre courante",
        price=80.0,
        currency=" eur ",
        in_stock=True,
    )
    unsupported_currency = models.Offer(
        merchant_id=merchant.id,
        awin_product_id="unsupported",
        name="Devise inconnue",
        price=40.0,
        currency="XXX",
        in_stock=True,
    )
    future = models.Offer(
        merchant_id=merchant.id,
        awin_product_id="future",
        name="Relevé futur",
        price=60.0,
        currency="EUR",
        in_stock=True,
    )
    session.add_all([current, unsupported_currency, future])
    await session.flush()

    now = datetime.now(UTC).replace(microsecond=0)
    matching_observation = now - timedelta(hours=1)
    future_observation = now + timedelta(hours=1)
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=current.id,
                price=100.0 + index,
                currency="EUR",
                in_stock=True,
                captured_at=(now - timedelta(days=10, minutes=index)).replace(
                    tzinfo=None
                ),
            )
            for index in range(200)
        ]
        + [
            models.PriceSnapshot(
                offer_id=current.id,
                price=80.004,
                currency="EUR",
                in_stock=True,
                captured_at=matching_observation.replace(tzinfo=None),
            ),
            # Plus récent, mais ni sa devise ni son stock ne peuvent prouver
            # l'offre EUR achetable.
            models.PriceSnapshot(
                offer_id=current.id,
                price=80.0,
                currency="GBP",
                in_stock=True,
                captured_at=now.replace(tzinfo=None),
            ),
            models.PriceSnapshot(
                offer_id=current.id,
                price=80.0,
                currency="EUR",
                in_stock=False,
                captured_at=now.replace(tzinfo=None),
            ),
            models.PriceSnapshot(
                offer_id=unsupported_currency.id,
                price=40.0,
                currency="XXX",
                in_stock=True,
                captured_at=now.replace(tzinfo=None),
            ),
            models.PriceSnapshot(
                offer_id=future.id,
                price=60.0,
                currency="EUR",
                in_stock=True,
                captured_at=future_observation.replace(tzinfo=None),
            ),
        ]
    )
    await session.commit()

    statements: list[str] = []

    def record_statement(_connection, _cursor, statement, _parameters, _context, _many):
        statements.append(statement.lower())

    event.listen(engine.sync_engine, "before_cursor_execute", record_statement)
    try:
        evidence = await load_offer_evidence(
            session,
            [current, unsupported_currency, future],
            current_only=True,
        )
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record_statement)

    select_statements = [
        statement for statement in statements if statement.lstrip().startswith("select")
    ]
    assert len(select_statements) == 1
    assert "max(price_snapshots.captured_at)" in select_statements[0]
    assert evidence[current.id] == OfferEvidence(
        currency="EUR",
        history=(),
        current_observed_at=matching_observation,
    )
    assert evidence[unsupported_currency.id] == OfferEvidence(
        currency=None,
        history=(),
        current_observed_at=None,
    )
    assert evidence[future.id].history == ()
    assert evidence[future.id].current_observed_at == future_observation
    assert not offer_observation_is_fresh(
        evidence[future.id].current_observed_at,
        now=now,
    )


async def test_retrievers_general_et_fashion_demandent_current_only(
    evidence_session,
    monkeypatch,
):
    session, _engine = evidence_session
    merchant = models.Merchant(awin_mid=9952, name="Mode", slug="mode")
    session.add(merchant)
    await session.flush()
    dress = models.Offer(
        merchant_id=merchant.id,
        awin_product_id="dress",
        name="Robe de soirée",
        filon_category=taxonomy.MODE_FEMME,
        filon_subcategory="Robes",
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        is_canonical=True,
        is_adult=False,
        price=90.0,
        currency="EUR",
        in_stock=True,
        image_url="https://example.test/dress.jpg",
    )
    session.add(dress)
    await session.commit()

    calls: list[bool] = []

    async def evidence_loader(_session, offers, *, current_only=False):
        calls.append(current_only)
        return {
            offer.offer_id: OfferEvidence("EUR", (), datetime.now(UTC))
            for offer in offers
        }

    monkeypatch.setattr(general_catalog, "load_offer_evidence", evidence_loader)
    monkeypatch.setattr(catalog_adapter, "load_offer_evidence", evidence_loader)
    intent = GeneralIntent(
        raw_request="robe",
        locale="fr",
        scopes=(
            IntentScope(
                taxonomy.MODE_FEMME,
                "Robes",
                "robe",
                ("robe",),
            ),
        ),
        terms=("robe",),
        required_title_phrases=(),
        budget_eur=None,
    )

    general = await general_catalog.retrieve_general_offers(session, intent)
    fashion = await catalog_adapter.retrieve_fashion_offers(session, query="robe")

    assert [item.offer_id for item in general] == [dress.id]
    assert [item.offer_id for item in fashion] == [dress.id]
    assert calls == [True, True]


async def test_historique_complet_reserve_aux_offres_finales(monkeypatch):
    final_offer = SimpleNamespace(
        id=1,
        product_id=10,
        merchant_id=100,
        name="Produit final",
        category="Produit",
        brand=None,
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        is_canonical=True,
        is_adult=False,
        price=80.0,
        currency="EUR",
        in_stock=True,
        updated_at=datetime.now(UTC),
    )
    grouped_offer = SimpleNamespace(
        id=2,
        product_id=10,
        merchant_id=200,
        name="Produit comparable",
        category="Produit",
        brand=None,
        offer_kind=taxonomy.PHYSICAL_PRODUCT,
        is_canonical=True,
        is_adult=False,
        price=75.0,
        currency="EUR",
        in_stock=True,
        updated_at=datetime.now(UTC),
    )

    class _GroupedRows:
        def scalars(self):
            return self

        def all(self):
            return [final_offer, grouped_offer]

    class _Session:
        async def execute(self, _statement):
            return _GroupedRows()

    calls: list[tuple[list[int], bool]] = []

    async def evidence_loader(_session, offers, *, current_only=False):
        calls.append(([offer.id for offer in offers], current_only))
        now = datetime.now(UTC)
        return {
            offer.id: OfferEvidence(
                currency="EUR",
                history=() if current_only else ((float(offer.price), now),),
                current_observed_at=now,
            )
            for offer in offers
        }

    monkeypatch.setattr(catalog_search, "load_offer_evidence", evidence_loader)
    monkeypatch.setattr(
        catalog_search.decision,
        "compute_decision",
        lambda **values: values,
    )

    decisions = await catalog_search._decisions_for_offers(_Session(), [final_offer])

    assert final_offer.id in decisions
    assert calls == [([1, 2], True), ([1], False)]
