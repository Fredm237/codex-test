"""Mémoire IA (Qdrant) — préférences, contexte, connaissances produit.

Optionnelle : sans QDRANT_URL, les fonctions deviennent des no-op. Le socle
d'intégration est posé pour la Phase 2.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("vectorstore")

COLLECTION = "filon_memory"


class VectorStore:
    def __init__(self) -> None:
        self._client = None
        url = get_settings().qdrant_url
        if url:
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(url=url)
            except Exception as exc:  # pragma: no cover
                log.warning("Qdrant indisponible (%s) → mémoire IA désactivée", exc)

    @property
    def enabled(self) -> bool:
        return self._client is not None


_store: VectorStore | None = None


def get_vectorstore() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
