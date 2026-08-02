"""La sonde de santé doit vraiment interroger la base.

Constaté en production sur `/health` : `"status": "degraded"` en permanence,
avec `"error": "module 'app.db.session' has no attribute 'text'"`.

La sonde appelait `db.text("SELECT 1")`, mais `session.py` n'importe `text`
qu'à l'intérieur de `_migrate()` — l'attribut n'existe pas au niveau module.
Le `except Exception` de la sonde attrapait l'`AttributeError` et la rendait
sous la même forme qu'une base injoignable : une faute de code se présentait
comme une panne d'infrastructure, sur chaque appel, sans que rien ne le
signale.

Aucun test n'exécutait la sonde. Ceux-ci le font contre une vraie base, de
sorte que la requête doit réellement partir et aboutir.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import health as health_module
from app.db.base import Base


@pytest.fixture
async def base_vivante(monkeypatch):
    """Substitue une base SQLite réelle à la base de production."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    class _scope:
        async def __aenter__(self):
            self._session = maker()
            return self._session

        async def __aexit__(self, *exc):
            await self._session.close()
            return False

    monkeypatch.setattr(health_module.db, "is_enabled", lambda: True)
    monkeypatch.setattr(health_module.db, "session_scope", _scope)
    yield
    await engine.dispose()


class TestSondeBaseDeDonnees:
    async def test_la_requete_aboutit(self, base_vivante):
        """Le bug : `AttributeError` rendue en `{"status": "error"}`."""
        res = await health_module._check_db()
        assert res["status"] == "ok", res.get("error")

    async def test_aucune_erreur_de_code_ne_passe_pour_une_panne(self, base_vivante):
        res = await health_module._check_db()
        assert "error" not in res

    async def test_le_statut_global_est_ok(self, base_vivante):
        res = await health_module.health()
        assert res["status"] == "ok"
        assert res["dependencies"]["database"]["status"] == "ok"

    async def test_une_base_absente_nest_pas_une_erreur(self, monkeypatch):
        """Sans DATABASE_URL, la persistance est désactivée — pas en panne."""
        monkeypatch.setattr(health_module.db, "is_enabled", lambda: False)
        res = await health_module._check_db()
        assert res["status"] == "disabled"
        assert (await health_module.health())["status"] == "ok"
