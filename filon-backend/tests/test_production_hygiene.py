"""Ce que le service doit taire en production.

La production tournait avec `ENV=dev`, donc `/docs`, `/openapi.json` et un
`/health` bavard servis publiquement. Les endpoints sensibles étaient eux
correctement fermés — vérifié en direct : `/catalog/debug/feeds` et
`/catalog/admin/merchant-profiles` répondent bien 403 sans `ADMIN_SYNC_TOKEN`.

Le défaut n'était donc pas une porte ouverte, mais un plan du bâtiment affiché à
l'entrée : le schéma OpenAPI énumérait les onze routes d'administration, dont
`purge-offers` et `reset-price-history`, avec leurs paramètres et le nom de
l'en-tête d'authentification attendu.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import pytest

from app.core.config import Settings


@contextmanager
def _client_pour(env: str):
    """Une application bâtie avec `ENV=env`, en ignorant tout `.env` local.

    Gestionnaire de contexte, et non simple fonction : `create_app()` lit les
    réglages au démarrage, mais `/health` les relit à *chaque* requête. Rendre le
    client puis restaurer aussitôt l'environnement laissait donc l'application
    construite en production répondre avec les réglages de développement — le
    test passait sur `/docs` et échouait sur `/health`, ce qui a d'abord ressemblé
    à un défaut du code vérifié. L'environnement doit rester en place aussi
    longtemps que le client est utilisé.

    `env_file` est neutralisé : un `.env` local définissant `ENV` prendrait sinon
    le pas sur la valeur testée, et le test passerait sans rien vérifier.
    """
    from fastapi.testclient import TestClient

    from app.core import config
    from app.main import create_app

    fichier_env = config.Settings.model_config.get("env_file")
    env_precedent = os.environ.get("ENV")
    config.Settings.model_config["env_file"] = None
    os.environ["ENV"] = env
    config.get_settings.cache_clear()
    try:
        yield TestClient(create_app())
    finally:
        config.Settings.model_config["env_file"] = fichier_env
        if env_precedent is None:
            os.environ.pop("ENV", None)
        else:
            os.environ["ENV"] = env_precedent
        config.get_settings.cache_clear()


class TestLaDetectionDeLaProduction:
    """`is_production` doit se tromper du bon côté.

    Les hébergeurs n'écrivent pas tous la même valeur dans `ENV`. Plutôt que
    d'énumérer ce qui doit être protégé, on énumère ce qui ne l'est pas : une
    faute de frappe rend alors le service plus prudent, jamais moins.
    """

    @pytest.mark.parametrize(
        "valeur", ["dev", "development", "local", "test", "DEV", " Dev "]
    )
    def test_les_environnements_de_developpement_sont_reconnus(self, valeur):
        assert Settings(env=valeur).is_production is False

    @pytest.mark.parametrize(
        "valeur", ["production", "prod", "PRODUCTION", "staging", "preprod"]
    )
    def test_tout_le_reste_est_traite_comme_de_la_production(self, valeur):
        assert Settings(env=valeur).is_production is True

    def test_une_valeur_inattendue_protege_par_defaut(self):
        """Le cas qui compte : `ENV=prodution` ne doit pas ouvrir la doc."""
        assert Settings(env="prodution").is_production is True
        assert Settings(env="").is_production is True


class TestLaDocumentationPubliqueEnProduction:
    def test_la_doc_est_fermee_en_production(self):
        with _client_pour("production") as client:
            assert client.get("/openapi.json").status_code == 404
            assert client.get("/docs").status_code == 404
            assert client.get("/redoc").status_code == 404

    def test_la_racine_n_annonce_pas_une_doc_absente(self):
        with _client_pour("production") as client:
            assert "docs" not in client.get("/").json()

    def test_la_doc_reste_disponible_en_developpement(self):
        """L'outil de travail ne doit pas disparaître pour autant."""
        with _client_pour("dev") as client:
            assert client.get("/openapi.json").status_code == 200
            assert client.get("/docs").status_code == 200
            assert client.get("/").json().get("docs") == "/docs"

    def test_les_routes_d_administration_restent_absentes_du_schema(self):
        """Le cœur du correctif : ne plus publier la carte des opérations."""
        with _client_pour("dev") as client:
            chemins = client.get("/openapi.json").json()["paths"]
        # En développement le schéma les liste, c'est son rôle.
        assert any("/admin/" in c for c in chemins)
        # En production, aucun schéma n'est servi : rien à énumérer.
        with _client_pour("production") as client:
            assert client.get("/openapi.json").status_code == 404


class TestCeQueHealthRevele:
    def _corps(self, env: str) -> dict:
        with _client_pour(env) as client:
            return client.get("/health").json()

    def test_l_essentiel_reste_public(self):
        """Une sonde et un humain doivent pouvoir constater que le service vit."""
        corps = self._corps("production")
        assert corps["status"] in {"ok", "degraded"}
        assert "version" in corps
        assert "uptime_seconds" in corps
        assert "dependencies" in corps

    def test_l_inventaire_technique_est_tu_en_production(self):
        corps = self._corps("production")
        for champ in ("python", "platform", "env", "llm"):
            assert champ not in corps, f"{champ} ne doit pas être public"

    def test_aucun_message_d_erreur_brut_de_la_base(self):
        """Une trace SQLAlchemy peut révéler un hôte ou un nom de base.

        Chaque dépendance ne doit rendre qu'un mot d'état, sans latence ni
        message : de quoi distinguer une panne d'un ralentissement, pas de quoi
        cartographier l'infrastructure.
        """
        dependances = self._corps("production")["dependencies"]
        assert all(isinstance(v, str) for v in dependances.values())
        assert dependances["database"] in {"ok", "slow", "error", "disabled"}

    def test_le_detail_reste_disponible_en_developpement(self):
        """Le diagnostic local ne doit rien perdre."""
        corps = self._corps("dev")
        assert corps["env"] == "dev"
        assert "python" in corps
        assert "llm" in corps
        assert isinstance(corps["dependencies"]["database"], dict)
