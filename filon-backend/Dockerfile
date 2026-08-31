FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system filon \
    && useradd --system --gid filon --home-dir /nonexistent --shell /usr/sbin/nologin filon

COPY --chown=filon:filon alembic.ini ./alembic.ini
COPY --chown=filon:filon alembic ./alembic
COPY --chown=filon:filon app ./app

USER filon

EXPOSE 8000

# Le port est lu depuis PORT en Python (voir app/__main__.py) — pas d'expansion
# shell, donc robuste quel que soit la façon dont la plateforme lance le conteneur.
CMD ["python", "-m", "app"]
