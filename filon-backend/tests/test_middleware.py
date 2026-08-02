"""Limiteur de débit.

Deux défauts corrigés après relecture, tous deux invisibles en test unitaire et
visibles en production :

- le rendu serveur de Vercel sort par quelques adresses partagées, si bien
  qu'une limite par IP comptait toutes les pages régénérées ensemble et nous
  limitait nous-mêmes ;
- le dictionnaire des adresses n'était jamais purgé de ses entrées inactives.
"""

from __future__ import annotations

import time

from app.api.middleware import RateLimitMiddleware


def _limiter(**kw) -> RateLimitMiddleware:
    # L'app n'est pas sollicitée : on teste la mécanique de comptage.
    return RateLimitMiddleware(app=None, **kw)


class TestExemptions:
    def test_le_catalogue_nest_pas_limite(self):
        """Ces lectures sont mises en cache et servent le rendu serveur : les
        limiter revenait à se couper soi-même."""
        limiter = _limiter()
        assert "/api/catalog".startswith(limiter._EXEMPT_PREFIXES) or \
            "/api/catalog/offers".startswith(limiter._EXEMPT_PREFIXES)

    def test_le_health_check_nest_pas_limite(self):
        limiter = _limiter()
        assert "/health".startswith(limiter._EXEMPT_PREFIXES)

    def test_lassistant_reste_limite(self):
        limiter = _limiter()
        assert not "/api/advise/stream".startswith(limiter._EXEMPT_PREFIXES)


class TestComptage:
    def test_bloque_au_dela_de_la_limite(self):
        limiter = _limiter()
        for _ in range(3):
            assert limiter._is_rate_limited("1.2.3.4", limit=3) is False
        assert limiter._is_rate_limited("1.2.3.4", limit=3) is True

    def test_les_adresses_sont_comptees_separement(self):
        limiter = _limiter()
        assert limiter._is_rate_limited("1.1.1.1", limit=1) is False
        # Une autre adresse ne doit pas hériter du compteur de la première.
        assert limiter._is_rate_limited("2.2.2.2", limit=1) is False

    def test_les_relevés_expirent(self):
        limiter = _limiter()
        limiter._requests["9.9.9.9"] = [time.time() - 120]
        # Le relevé date de deux minutes : hors de la fenêtre d'une minute.
        assert limiter._is_rate_limited("9.9.9.9", limit=1) is False


class TestMemoire:
    def test_les_adresses_inactives_sont_purgees(self):
        """Sans purge, une entrée par adresse vue depuis le démarrage restait
        en mémoire — une fuite lente sur un service qui a déjà saturé."""
        limiter = _limiter()
        vieux = time.time() - 3600
        for i in range(limiter._MAX_TRACKED_IPS + 50):
            limiter._requests[f"10.0.{i // 256}.{i % 256}"] = [vieux]

        limiter._is_rate_limited("192.168.1.1", limit=10)

        assert len(limiter._requests) <= limiter._MAX_TRACKED_IPS
        # L'adresse active vient d'être comptée : elle survit à la purge.
        assert "192.168.1.1" in limiter._requests

    def test_la_purge_epargne_les_adresses_actives(self):
        limiter = _limiter()
        maintenant = time.time()
        for i in range(limiter._MAX_TRACKED_IPS + 20):
            limiter._requests[f"10.1.{i // 256}.{i % 256}"] = [maintenant]

        limiter._is_rate_limited("172.16.0.1", limit=10)

        # Toutes récentes : aucune n'est purgée, le plafond n'est qu'un seuil
        # de déclenchement, pas une éviction aveugle.
        assert len(limiter._requests) > limiter._MAX_TRACKED_IPS
