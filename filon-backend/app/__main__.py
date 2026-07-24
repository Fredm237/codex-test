"""Point d'entrée robuste : `python -m app`.

Lit le port depuis la variable d'environnement PORT (fournie par Railway et la
plupart des PaaS) directement en Python — aucune dépendance à l'expansion `$PORT`
par un shell, qui échouait sur Railway ("'$PORT' is not a valid integer").
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
