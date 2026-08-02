"""Appeler un endpoint FastAPI directement, sans passer par HTTP.

Hors requête, FastAPI ne résout pas les valeurs par défaut : un paramètre
déclaré `Query(default=None)` arrive comme un objet `Query`, qui est *vrai* au
sens booléen. Un test qui ne passe pas explicitement ce paramètre active donc
silencieusement le filtre correspondant.

Les harnais énuméraient les paramètres à la main, si bien que chaque nouveau
paramètre d'endpoint cassait des tests sans rapport — c'est arrivé en ajoutant
`department`. Cette aide lit la signature et substitue les vraies valeurs par
défaut : un ajout d'argument ne casse plus rien.
"""

from __future__ import annotations

import inspect
from typing import Any


def defaults_of(endpoint) -> dict[str, Any]:
    """Valeurs par défaut réelles d'un endpoint, sentinelles FastAPI résolues."""
    out: dict[str, Any] = {}
    for name, parameter in inspect.signature(endpoint).parameters.items():
        default = parameter.default
        if default is inspect.Parameter.empty:
            continue
        # Query/Path/Header/Depends exposent la valeur voulue sous `.default`.
        inner = getattr(default, "default", None)
        if inner is not None and default.__class__.__module__.startswith("fastapi"):
            out[name] = inner
        elif default.__class__.__module__.startswith("fastapi"):
            out[name] = None
        else:
            out[name] = default
    return out


async def call(endpoint, **overrides):
    """Invoque l'endpoint avec ses défauts réels, surchargés par `overrides`."""
    params = defaults_of(endpoint)
    params.update(overrides)
    return await endpoint(**params)
