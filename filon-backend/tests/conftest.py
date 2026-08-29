"""Environnement hermétique commun aux tests backend."""

from __future__ import annotations

import os


# La configuration runtime exige désormais un environnement explicite. Les
# tests utilisent une valeur fermée avant l'import des modules applicatifs.
os.environ.setdefault("ENV", "test")
