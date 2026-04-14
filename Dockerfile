FROM python:3.11-slim

# Dépendances système pour numba/numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le dossier uploads (volume persistant en prod)
RUN mkdir -p /app/uploads

# Port dynamique Railway
ENV PORT=8001
EXPOSE $PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/v1/health')" || exit 1

# Démarrage
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1
