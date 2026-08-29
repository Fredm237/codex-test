"""Configuration de logs simple et lisible."""

from __future__ import annotations

import logging


def configure_logging(debug: bool = True) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    # Bibliothèques tierces trop bavardes en DEBUG (httpx/httpcore inondent les
    # logs à chaque téléchargement de feed) → on les garde à WARNING.
    for noisy in ("httpx", "httpcore", "hpack", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Le format d'accès Uvicorn inclut la query string. Or le flux Assistant
    # reçoit encore le besoin libre dans ``q=`` : le logger applicatif conserve
    # seulement la route templatisée et doit rester l'unique journal HTTP.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.disabled = True
    access_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"filon.{name}")
