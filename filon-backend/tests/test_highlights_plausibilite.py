"""Vraisemblance des remises affichées en vitrine.

Ces tests figent un défaut mesuré en production le 4 août 2026. La page
d'accueil affichait deux cartes à « −99 % » :

    LEGO Jurassic World Ultra Pack ...  2,79 € barré 250,00 €   (−98,9 %)
    Bendy and the Dark Revival CD Key  6,74 € barré 560,20 €   (−98,8 %)

L'historique réel de la première offre (id 1134328) :

    250.00 € — 2026-08-01T05:39:42     ← un seul relevé
      2.79 € — 2026-08-01T20:48:17
      2.79 € — 2026-08-02T03:46:08
      2.79 € — 2026-08-03T05:51:53
      2.79 € — 2026-08-03T14:15:30
      2.79 € — 2026-08-03T23:06:43
      2.79 € — 2026-08-04T07:52:57

Le prix de référence venait d'un `max()` brut sur l'historique, sans validation,
et le rail était trié par remise décroissante : plus la donnée était fausse,
plus elle était mise en avant. Le défaut s'auto-sélectionnait.

On teste donc trois propriétés, pas une implémentation :
  1. un pic isolé ne fait pas un prix de référence ;
  2. une remise invraisemblable n'est jamais affichée ;
  3. une vraie promotion, elle, reste affichée.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes.catalog import (
    MAX_PLAUSIBLE_DROP_PCT,
    highlights,
)
from app.db import models
from app.db.base import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _offer(s, merchant, pid, name, price, brand="Marque"):
    o = models.Offer(
        merchant_id=merchant.id, awin_product_id=pid, name=name, brand=brand,
        price=price, currency="EUR", in_stock=True,
        image_url="https://example.test/i.jpg",
    )
    s.add(o)
    await s.flush()
    return o


async def _history(s, offer, prices):
    """Écrit un historique, un relevé par heure, du plus ancien au plus récent."""
    base = _now() - timedelta(hours=len(prices))
    for i, p in enumerate(prices):
        s.add(models.PriceSnapshot(
            offer_id=offer.id, price=p, currency="EUR",
            in_stock=True, captured_at=base + timedelta(hours=i),
        ))
    await s.flush()


async def _rails(s, limit=12):
    data = await highlights(limit=limit, session=s)
    return {sec["key"]: sec["items"] for sec in data["sections"]}


async def _merchants(s, n=6):
    """Plusieurs marchands : les rails entrelacent et exigent de la diversité."""
    out = []
    for i in range(n):
        m = models.Merchant(awin_mid=100 + i, name=f"Boutique {i}", slug=f"boutique-{i}")
        s.add(m)
        out.append(m)
    await s.flush()
    return out


async def _fill_credible(s, merchants, count=10):
    """Fond de rail : des baisses modérées et solidement observées."""
    for i in range(count):
        m = merchants[i % len(merchants)]
        o = await _offer(s, m, f"credible-{i}", f"Article Crédible {i}", 80.0)
        # 100 € observé 5 fois, puis 80 € : baisse de 20 %, référence solide.
        await _history(s, o, [100.0] * 5 + [80.0] * 2)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Le cas LEGO : un pic isolé n'est pas un prix de référence
# ─────────────────────────────────────────────────────────────────────────────

async def test_pic_isole_ne_fait_pas_un_prix_de_reference(session):
    """Reproduction fidèle de l'offre 1134328 vue en production.

    250 € une fois, 2,79 € six fois. Le prix haut n'a jamais été un prix
    pratiqué : c'est une erreur de feed au premier passage.
    """
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    lego = await _offer(
        session, merchants[0], "lego-jurassic",
        "LEGO Jurassic World Ultra Pack Magazinebundel met Minifiguren",
        2.79, brand="Lego",
    )
    await _history(session, lego, [250.0] + [2.79] * 6)
    await session.commit()

    rails = await _rails(session)
    noms = [i["name"] for i in rails.get("drops", [])]
    assert not any("LEGO Jurassic" in n for n in noms), (
        "un prix haut relevé une seule fois sur sept ne doit pas servir de "
        f"référence ; rail obtenu : {noms}"
    )


async def test_aucune_remise_invraisemblable_dans_les_rails(session):
    """Propriété générale : aucune carte ne dépasse le plafond de crédibilité.

    On teste la propriété plutôt qu'un cas, pour attraper aussi les futures
    familles d'erreurs de feed.
    """
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    # Trois familles d'aberrations observées : pic isolé, erreur de devise
    # (prix en centimes lu comme euros), changement de conditionnement.
    aberrations = [
        ("lego", "LEGO Ultra Pack", 2.79, [250.0] + [2.79] * 6),
        ("cdkey", "Bendy and the Dark Revival CD Key", 6.74, [560.20, 560.20, 6.74]),
        ("pneu", "Blizzak LM-32 RFT", 262.48, [952.39] + [262.48] * 4),
    ]
    for i, (pid, name, price, hist) in enumerate(aberrations):
        o = await _offer(session, merchants[i % len(merchants)], pid, name, price)
        await _history(session, o, hist)
    await session.commit()

    rails = await _rails(session)
    for key, items in rails.items():
        for it in items:
            pct = it.get("drop_pct")
            if pct is not None:
                assert pct <= MAX_PLAUSIBLE_DROP_PCT, (
                    f"rail « {key} » : {it['name']} affiche −{pct} %, "
                    f"au-delà du plafond de {MAX_PLAUSIBLE_DROP_PCT} %"
                )
            # Contrôle indépendant du champ calculé : le barré lui-même.
            high, cur = it.get("price_high"), it.get("price")
            if high and cur:
                reel = (high - cur) / high * 100.0
                assert reel <= MAX_PLAUSIBLE_DROP_PCT + 0.5, (
                    f"rail « {key} » : {it['name']} barre {high} € sur {cur} €, "
                    f"soit −{reel:.1f} %"
                )


# ─────────────────────────────────────────────────────────────────────────────
async def test_agregat_historique_ne_melange_jamais_deux_devises(session):
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    offer = await _offer(
        session,
        merchants[0],
        "mixed-currency",
        "Historique Multidevise",
        80.0,
    )
    base = _now() - timedelta(hours=3)
    session.add_all(
        [
            models.PriceSnapshot(
                offer_id=offer.id,
                price=100.0,
                currency="GBP",
                in_stock=True,
                captured_at=base,
            ),
            models.PriceSnapshot(
                offer_id=offer.id,
                price=100.0,
                currency="GBP",
                in_stock=True,
                captured_at=base + timedelta(hours=1),
            ),
            models.PriceSnapshot(
                offer_id=offer.id,
                price=80.0,
                currency="EUR",
                in_stock=True,
                captured_at=base + timedelta(hours=2),
            ),
        ]
    )
    await session.commit()

    rails = await _rails(session)
    names = [item["name"] for item in rails.get("drops", [])]
    assert "Historique Multidevise" not in names


# 2. Ne pas jeter le bébé : les vraies promotions restent
# ─────────────────────────────────────────────────────────────────────────────

async def test_vraie_promotion_reste_affichee(session):
    """Le cas LEBASQ, vu en production : 17,09 € observé 6 fois sur 7, puis 4,29 €.

    C'est une remise forte mais adossée à un prix réellement pratiqué. La
    corriger serait une régression : le rail « baisses » perdrait sa raison
    d'être.
    """
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    o = await _offer(
        session, merchants[1], "lebasq",
        "LEBASQ - The Baker - T-shirt Pitch Black", 12.00,
    )
    # 20 € observé 6 fois, prix courant 12 € : −40 %, crédible et solide.
    await _history(session, o, [20.0] * 6 + [12.0])
    await session.commit()

    rails = await _rails(session)
    noms = [i["name"] for i in rails.get("drops", [])]
    assert any("LEBASQ" in n for n in noms), (
        f"une baisse de 40 % solidement observée doit rester ; obtenu : {noms}"
    )


async def test_prix_haut_frequent_mais_forte_baisse_reste(session):
    """Une baisse de 80 % est plausible si le prix haut est bien établi."""
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    o = await _offer(session, merchants[2], "destock", "Manteau Déstocké", 20.0)
    await _history(session, o, [100.0] * 8 + [20.0])
    await session.commit()

    rails = await _rails(session)
    noms = [i["name"] for i in rails.get("drops", [])]
    assert "Manteau Déstocké" in noms, (
        f"−80 % sur un prix observé 8 fois est crédible ; obtenu : {noms}"
    )


async def test_pic_repete_mais_marginal_est_ecarte(session):
    """Deux relevés hauts sur quarante restent une anomalie.

    Le seuil d'occurrences seul ne suffit pas : il faut aussi que le prix haut
    pèse dans l'historique. C'est la différence entre « 2 fois sur 5 » (un prix
    qui a existé) et « 2 fois sur 40 » (un accident répété).
    """
    merchants = await _merchants(session)
    await _fill_credible(session, merchants)
    o = await _offer(session, merchants[3], "marginal", "Article Pic Marginal", 10.0)
    await _history(session, o, [200.0, 200.0] + [10.0] * 38)
    await session.commit()

    rails = await _rails(session)
    noms = [i["name"] for i in rails.get("drops", [])]
    assert "Article Pic Marginal" not in noms, (
        f"2 relevés hauts sur 40 ne font pas une référence ; obtenu : {noms}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Deux rails, deux questions
# ─────────────────────────────────────────────────────────────────────────────

async def test_drops_et_lowest_ne_sont_pas_identiques(session):
    """Mesuré en production : les deux rails renvoyaient les 12 mêmes produits.

    « Les plus grosses baisses » et « au plus bas historique » répondent à deux
    questions différentes. Trier les deux par une mesure colinéaire les rendait
    interchangeables, et la page paraissait vide de contenu.
    """
    merchants = await _merchants(session)
    # Deux populations distinctes : des offres qui viennent de baisser, et des
    # offres au plancher depuis longtemps.
    for i in range(8):
        m = merchants[i % len(merchants)]
        o = await _offer(session, m, f"baisse-{i}", f"Vient De Baisser {i}", 60.0)
        await _history(session, o, [100.0] * 4 + [60.0])
    for i in range(8):
        m = merchants[i % len(merchants)]
        o = await _offer(session, m, f"plancher-{i}", f"Au Plancher Depuis {i}", 45.0)
        # Historique long, prix courant égal au plus bas observé.
        await _history(session, o, [50.0] * 6 + [45.0] * 20)
    await session.commit()

    rails = await _rails(session)
    drops = [i["id"] for i in rails.get("drops", [])]
    lowest = [i["id"] for i in rails.get("lowest", [])]
    if not drops or not lowest:
        pytest.skip("rails insuffisamment remplis pour comparer")
    assert drops != lowest, (
        "« baisses » et « plus bas » renvoient exactement la même liste dans le "
        "même ordre : deux rangées identiques sur la même page"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Aucune route ne doit interroger une colonne inexistante
# ─────────────────────────────────────────────────────────────────────────────

async def test_aucune_route_ne_reference_de_colonne_absente():
    """`/catalog/featured` répondait 500 sur toutes les requêtes en production.

    Il interrogeait `models.Offer.drop_pct`, colonne jamais définie dans
    `models.py`. Comme aucune page du front ne l'appelait, le défaut est resté
    invisible — tout en polluant les logs en continu.

    Ce test relit les routes et vérifie que chaque attribut de modèle mentionné
    existe réellement. Il attrape la faute de frappe et la colonne supprimée,
    que la couverture fonctionnelle laisserait passer si l'endroit n'est pas
    testé.
    """
    import ast
    import pathlib

    from app.db import models as m

    routes = pathlib.Path("app/api/routes")
    fautes: list[str] = []
    for src in sorted(routes.glob("*.py")):
        tree = ast.parse(src.read_text(), filename=str(src))
        for node in ast.walk(tree):
            # Cible la forme `models.<Classe>.<attribut>`
            if not isinstance(node, ast.Attribute):
                continue
            base = node.value
            if not (
                isinstance(base, ast.Attribute)
                and isinstance(base.value, ast.Name)
                and base.value.id == "models"
            ):
                continue
            cls = getattr(m, base.attr, None)
            if cls is None or not hasattr(cls, "__tablename__"):
                continue
            if not hasattr(cls, node.attr):
                fautes.append(
                    f"{src.name}:{node.lineno} — models.{base.attr}.{node.attr} "
                    f"n'existe pas"
                )

    assert not fautes, "colonnes inexistantes référencées :\n" + "\n".join(fautes)
