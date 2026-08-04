"""Un relevé de prix n'est écrit que lorsque le prix change.

Mesuré en production : `price_snapshots` grossissait de **2 413 308 lignes par
jour** alors que seulement **5 447 prix changeaient** sur la même période. Chaque
passage d'ingestion réinsérait le prix de chaque offre, identique ou non — 99,8 %
des écritures ne portaient donc aucune information, pour environ 65 Go par an sur
une base hébergée facturée au gigaoctet.

Ce n'est pas qu'un problème de coût : un historique où 450 lignes sur 451 sont
des doublons ne permet aucune lecture utile. « Ce prix a-t-il déjà été plus
bas ? » devient une requête sur des millions de lignes redondantes.

La correction s'appuie sur une propriété peu connue de PostgreSQL, vérifiée sur
un serveur réel avant d'être retenue : dans la clause `SET` d'un `ON CONFLICT DO
UPDATE`, `offers.price` désigne encore la valeur *avant* écriture. C'est le seul
endroit où l'ancien prix reste lisible — `RETURNING` rend la valeur déjà mise à
jour, et `excluded` y est interdit (`UndefinedTableError`).

Les tests de bout en bout tournent sur un vrai PostgreSQL quand il est
disponible, car c'est précisément le comportement du moteur qui est en jeu :
SQLite ne reproduit pas `ON CONFLICT ... SET col = table.col`.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import models
from app.db.base import Base
from app.services.awin_catalog import _price_changed, _upsert_offer

PG_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://filon:filon@localhost:5432/filontest"
)


# ─────────────────────────────────────────────────────────────────────────────
# La décision elle-même — testable sans base
# ─────────────────────────────────────────────────────────────────────────────


class TestLaDecisionDEcrire:
    def test_un_prix_inchange_nest_pas_reecrit(self):
        """Le cas des 99,8 % : l'ingestion revoit le même prix."""
        assert _price_changed(19.99, 19.99) is False

    def test_une_baisse_est_enregistree(self):
        assert _price_changed(29.99, 24.99) is True

    def test_une_hausse_est_enregistree(self):
        """Une hausse compte autant qu'une baisse : sans elle, « était à X € »
        deviendrait faux et le verdict ne verrait qu'une moitié du marché."""
        assert _price_changed(24.99, 29.99) is True

    def test_le_premier_prix_connu_est_toujours_ecrit(self):
        """`previous_price` est NULL à l'insertion. Sans ce cas, un historique
        n'aurait jamais d'origine et aucune offre neuve ne serait suivie."""
        assert _price_changed(None, 19.99) is True

    def test_un_prix_absent_nest_jamais_ecrit(self):
        """Un relevé sans prix ne dit rien ; `price` est NOT NULL côté modèle."""
        assert _price_changed(19.99, None) is False
        assert _price_changed(None, None) is False

    def test_le_bruit_flottant_ne_compte_pas_comme_un_changement(self):
        """Les prix sont stockés en Float.

        Deux écritures du même 19,99 peuvent différer du dernier bit ; sans
        tolérance, ce bruit recréerait exactement l'hémorragie corrigée.
        """
        assert _price_changed(19.99, 19.990000000000002) is False
        assert _price_changed(0.1 + 0.2, 0.3) is False

    def test_un_centime_reste_un_changement(self):
        """La tolérance ne doit pas avaler de variation réelle : sur un article à
        0,49 €, un centime représente deux pour cent du prix."""
        assert _price_changed(19.99, 19.98) is True
        assert _price_changed(0.49, 0.50) is True


# ─────────────────────────────────────────────────────────────────────────────
# Le comportement réel de l'ingestion, sur PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────


async def _pg_available() -> bool:
    try:
        engine = create_async_engine(PG_URL)
        async with engine.begin():
            pass
        await engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture
async def pg_session():
    if not await _pg_available():
        pytest.skip("PostgreSQL indisponible — ce test vérifie le moteur lui-même")
    engine = create_async_engine(PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        marchand = models.Merchant(awin_mid=1, name="Boutique", slug="boutique")
        s.add(marchand)
        await s.commit()
        # Exposé aux tests : `scalar()` sur un select de table rend la première
        # colonne (l'id), pas l'objet — source de confusion à l'usage.
        s.info["merchant_id"] = marchand.id
        yield s
    await engine.dispose()


def feed_row(price: str, *, pid: str = "p1", name: str = "Cafetière Expresso"):
    """Une ligne de feed Awin telle que `_upsert_offer` la reçoit."""
    return {
        "aw_product_id": pid,
        "product_name": name,
        "search_price": price,
        "currency": "EUR",
        "in_stock": "1",
        "merchant_image_url": "https://example.test/i.jpg",
        "aw_deep_link": "https://example.test/go",
        "ean": "4006381333931",
        "brand_name": "Delonghi",
        "merchant_category": "Electromenager",
    }


async def _count_snapshots(session) -> int:
    from sqlalchemy import func, select

    return int(await session.scalar(select(func.count()).select_from(models.PriceSnapshot)) or 0)


@pytest.mark.usefixtures("pg_session")
class TestLIngestionNEcritQueLesChangements:
    async def test_le_premier_passage_cree_un_releve(self, pg_session):
        mid = pg_session.info["merchant_id"]
        await _upsert_offer(pg_session, mid, feed_row("19.99"))
        await pg_session.commit()
        assert await _count_snapshots(pg_session) == 1

    async def test_dix_passages_au_meme_prix_ne_creent_quun_releve(self, pg_session):
        """Le cœur du correctif.

        Auparavant : dix passages, dix lignes. C'est la mécanique qui produisait
        2,4 millions de lignes quotidiennes.
        """
        mid = pg_session.info["merchant_id"]
        for _ in range(10):
            await _upsert_offer(pg_session, mid, feed_row("19.99"))
            await pg_session.commit()
        assert await _count_snapshots(pg_session) == 1

    async def test_un_changement_de_prix_est_capture(self, pg_session):
        mid = pg_session.info["merchant_id"]
        for prix in ("19.99", "19.99", "17.49", "17.49", "22.00"):
            await _upsert_offer(pg_session, mid, feed_row(prix))
            await pg_session.commit()
        # Trois prix distincts dans la séquence → trois relevés.
        assert await _count_snapshots(pg_session) == 3

    async def test_l_historique_conserve_les_valeurs_exactes(self, pg_session):
        """Réduire le volume ne doit rien retirer à l'information conservée."""
        from sqlalchemy import select

        mid = pg_session.info["merchant_id"]
        for prix in ("29.99", "29.99", "24.99", "24.99", "24.99", "31.50"):
            await _upsert_offer(pg_session, mid, feed_row(prix))
            await pg_session.commit()
        releves = (
            await pg_session.execute(
                select(models.PriceSnapshot.price).order_by(models.PriceSnapshot.id)
            )
        ).scalars().all()
        assert releves == [29.99, 24.99, 31.50]

    async def test_previous_price_suit_le_prix_precedent(self, pg_session):
        """La colonne technique doit rester juste : elle sert aussi d'affichage
        « était à X € » sans requêter l'historique."""
        from sqlalchemy import select

        mid = pg_session.info["merchant_id"]
        await _upsert_offer(pg_session, mid, feed_row("50.00"))
        await pg_session.commit()
        await _upsert_offer(pg_session, mid, feed_row("40.00"))
        await pg_session.commit()
        offre = await pg_session.scalar(select(models.Offer))
        assert offre.price == 40.00
        assert offre.previous_price == 50.00

    async def test_plusieurs_offres_restent_independantes(self, pg_session):
        """Un changement chez une offre ne doit pas déclencher d'écriture chez
        les autres — sans quoi le gain disparaîtrait à l'échelle du catalogue."""
        mid = pg_session.info["merchant_id"]
        for pid in ("p1", "p2", "p3"):
            await _upsert_offer(pg_session, mid, feed_row("10.00", pid=pid))
        await pg_session.commit()
        assert await _count_snapshots(pg_session) == 3

        # Second passage : seul p2 bouge.
        await _upsert_offer(pg_session, mid, feed_row("10.00", pid="p1"))
        await _upsert_offer(pg_session, mid, feed_row("8.50", pid="p2"))
        await _upsert_offer(pg_session, mid, feed_row("10.00", pid="p3"))
        await pg_session.commit()
        assert await _count_snapshots(pg_session) == 4

    async def test_la_proportion_dcritures_evitees(self, pg_session):
        """Reproduit la proportion observée en production, en miniature.

        450 offres stables pour une seule qui bouge : c'est l'ordre de grandeur
        mesuré (2 413 308 écritures pour 5 447 changements).
        """
        mid = pg_session.info["merchant_id"]
        for i in range(50):
            await _upsert_offer(pg_session, mid, feed_row("10.00", pid=f"s{i}"))
        await pg_session.commit()
        base = await _count_snapshots(pg_session)
        assert base == 50  # amorçage de l'historique

        # Cinq passages d'ingestion. L'offre s0 baisse au troisième, puis remonte
        # au quatrième : deux mouvements réels, donc deux relevés.
        for tour in range(5):
            for i in range(50):
                prix = "9.00" if (i == 0 and tour == 2) else "10.00"
                await _upsert_offer(pg_session, mid, feed_row(prix, pid=f"s{i}"))
            await pg_session.commit()

        # Ancien comportement : 50 + 5 x 50 = 300 lignes.
        # Désormais : 50 d'amorçage + la baisse + le retour = 52.
        # Les 249 écritures restantes, toutes redondantes, ne sont plus faites.
        assert await _count_snapshots(pg_session) == 52


# ─────────────────────────────────────────────────────────────────────────────
# Les migrations elles-mêmes doivent rester sûres au démarrage
# ─────────────────────────────────────────────────────────────────────────────


class TestLesMigrationsNeBloquentPasLeDemarrage:
    """`_migrate()` s'exécute au démarrage de l'application.

    Deux défauts y ont été introduits puis corrigés pendant ce chantier, tous
    deux invisibles en test SQLite et destinés à ne se manifester qu'en
    production. Ces vérifications lisent le texte des migrations : elles gardent
    la trace de ce qui ne doit pas revenir.
    """

    def _sources(self) -> str:
        from pathlib import Path

        import app.db.session as session_module

        return Path(session_module.__file__).read_text(encoding="utf-8")

    def _sql_execute(self) -> str:
        """Le SQL réellement exécuté, commentaires Python exclus.

        Les commentaires décrivent légitimement les instructions à ne pas écrire ;
        seule compte ici la substance exécutée.
        """
        lignes = [
            ligne
            for ligne in self._sources().splitlines()
            if not ligne.lstrip().startswith("#")
        ]
        return "\n".join(lignes)

    def test_aucun_drop_trigger_au_demarrage(self):
        """`DROP TRIGGER` exige un ACCESS EXCLUSIVE sur `price_snapshots`.

        Une lecture encore ouverte suffit à le bloquer. Au démarrage, cela
        suspend l'application, fait expirer le healthcheck et met le déploiement
        en échec répété — la table étant sollicitée en continu par l'ingestion.
        Observé sur PostgreSQL 16 : le script de vérification s'est figé, et
        `pg_stat_activity` montrait le DROP en attente derrière un simple
        `SELECT count(*)`.
        """
        assert "DROP TRIGGER" not in self._sql_execute().upper()

    def test_les_migrations_renoncent_plutot_que_dattendre(self):
        """Un `lock_timeout` borne chaque migration.

        Sans lui, toute instruction réclamant un verrou déjà tenu attend
        indéfiniment et retient le démarrage avec elle.
        """
        assert "lock_timeout" in self._sql_execute()

    def test_le_trigger_est_cree_conditionnellement(self):
        """Sa création doit être idempotente sans passer par une suppression."""
        source = self._sql_execute()
        assert "trg_skip_unchanged_snapshot" in source
        assert "pg_trigger" in source

    def test_l_ingestion_n_ecrit_pas_les_releves_via_l_orm(self):
        """`session.add()` sur `PriceSnapshot` est incompatible avec le trigger.

        L'ORM attend un `RETURNING id` ; quand le trigger écarte la ligne, aucun
        identifiant ne revient et SQLAlchemy lève `FlushError`, ce qui
        interromprait le cycle d'ingestion entier. L'insertion doit passer par
        Core, qui tolère zéro ligne affectée.
        """
        from pathlib import Path

        import app.services.awin_catalog as awin_module

        source = Path(awin_module.__file__).read_text(encoding="utf-8")
        assert "session.add(models.PriceSnapshot" not in source
        assert "sa_insert(models.PriceSnapshot)" in source
