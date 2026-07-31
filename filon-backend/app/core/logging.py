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


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"filon.{name}")
