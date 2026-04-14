FROM python:3.11-slim

# Dépendances système pour numba/numpy (compilateur C requis)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python en premier (cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le dossier uploads (volume persistant recommandé en prod)
RUN mkdir -p /app/uploads

# Railway injecte PORT automatiquement (par défaut 8080)
ENV PORT=8080
EXPOSE $PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen(f'http://localhost:{__import__(\"os\").environ.get(\"PORT\",\"8080\")}/api/v1/health')" || exit 1

# Démarrage — Railway fournit $PORT automatiquement
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1
