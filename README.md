# SmartWave Quant Lab — Backend API

FastAPI backend pour le Quant Lab SaaS.

## Déploiement sur Railway (recommandé)

1. Créer un compte sur [railway.app](https://railway.app)
2. Cliquer "New Project" → "Deploy from GitHub repo"
3. Connecter ce dossier (ou uploader via CLI)
4. Railway détecte automatiquement Python et installe les dépendances
5. Copier l'URL générée (ex: `https://smartwave-quant-backend.up.railway.app`)
6. Copier l'URL Railway (ex: `https://smartwave-quant-backend.up.railway.app`) et la renseigner dans :
   - **Manus → Paramètres → Secrets → `QUANT_API_URL`** = `https://smartwave-quant-backend.up.railway.app`
   - **Manus → Paramètres → Secrets → `VITE_QUANT_DIRECT_URL`** = `https://smartwave-quant-backend.up.railway.app`

## Déploiement sur Render

1. Créer un compte sur [render.com](https://render.com)
2. "New Web Service" → connecter le repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

## Endpoints disponibles

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/v1/health` | Health check (Railway healthcheck) |
| GET | `/api/strategies` | Liste des stratégies |
| GET | `/api/data/symbols` | Liste des symboles |
| POST | `/api/backtest` | Lancer un backtest |
| POST | `/api/optimize` | Optimisation Bayésienne |
| POST | `/api/montecarlo` | Analyse Monte Carlo |

## Test local

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
# Ouvrir http://localhost:8000/docs
```
