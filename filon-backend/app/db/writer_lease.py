"""Sérialisation du démarrage des writers catalogue et V2.

Les deux pipelines possèdent chacun leur lease durable. Ce verrou transactionnel
commun ferme la seule fenêtre restante : deux processus qui vérifieraient les
deux tables exactement au même instant avant d'y créer chacun leur exécution.
"""

from __future__ import annotations

from sqlalchemy import text


# Identité stable, non secrète, limitée à la base FILON.
_PIPELINE_WRITER_START_LOCK = 0x46494C4F4E5632


async def serialize_pipeline_writer_start(session) -> None:
    """Sérialise l'acquisition d'un lease writer sur PostgreSQL.

    SQLite reste un support de tests mono-processus ; son verrou d'écriture
    natif et les index uniques couvrent ce périmètre sans SQL spécifique.
    """

    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_id)"),
        {"lock_id": _PIPELINE_WRITER_START_LOCK},
    )
