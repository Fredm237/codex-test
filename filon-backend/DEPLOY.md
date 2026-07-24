# Déployer le backend FILON + brancher l'assistant

L'assistant `/recherche` du site appelle le backend en streaming (SSE) pour
produire un vrai raisonnement LLM et 5 recommandations. Tant que l'URL du
backend n'est pas configurée, le site utilise automatiquement le mock local
(rien ne casse).

## 1. Obtenir une clé LLM (DeepSeek — recommandé)

1. Créer un compte sur https://platform.deepseek.com
2. Générer une clé API (section **API Keys**). Format : `sk-...`
3. DeepSeek est OpenAI-compatible et très peu cher (~0,14 $/million de tokens).

> Alternatives possibles sans changer le code : Kimi (Moonshot) ou GLM (Zhipu).

## 2. Déployer le backend sur Railway

1. Créer un compte sur https://railway.app et **New Project → Deploy from GitHub repo** (`Fredm237/codex-test`).
2. Dans le service, **Settings → Root Directory** = `filon-backend`.
   (Le `Dockerfile` et `railway.json` y sont déjà : build Docker + healthcheck `/health`.)
3. **Variables** (Settings → Variables) :

   ```
   LLM_PROVIDER_DEFAULT=deepseek
   LLM_PROVIDER_REASONING=deepseek
   LLM_PROVIDER_LONG=deepseek
   DEEPSEEK_API_KEY=sk-...        # votre clé
   CORS_ORIGINS=["https://filon.be","https://www.filon.be"]
   ```

   (Laisser `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL` vides : non requis pour l'assistant.)
4. Déployer. Railway fournit une URL publique, ex. `https://filon-backend-production.up.railway.app`.
5. Vérifier : ouvrir `https://<url>/health` → `{"status":"ok"}` attendu, et
   `https://<url>/api/advise/stream?q=un%20pc%20portable%20800€` doit renvoyer un flux SSE.

## 3. Brancher le frontend (Vercel)

1. Vercel → projet `codex-test` → **Settings → Environment Variables** :

   ```
   NEXT_PUBLIC_FILON_API = https://<votre-url-railway>
   ```

   (Environnement : Production. Pas de `/` final.)
2. **Redeploy** le frontend (un nouveau build est nécessaire : la variable est
   injectée au build). Une fois déployé, `/recherche` appelle le vrai backend.

## Comment ça marche

- Frontend : `SearchAssistant.tsx` → `streamAnalyze()` lit `/api/advise/stream`
  (mêmes événements `step` / `step-done` / `results` que le mock).
- Backend : `app/services/recommend.py` → le LLM renvoie un JSON strict (usage +
  5 cartes classées) ; `app/api/routes/stream.py` l'émet en SSE.
- Sans clé LLM, le backend renvoie une synthèse de repli (toujours fonctionnel).

## Données produits réelles (SerpApi — actif si la clé est présente)

Avec une clé **SerpApi**, l'assistant renvoie de **vrais produits** (nom, photo,
prix du jour, marchand, lien cliquable) via Google Shopping, que le LLM classe et
argumente. Sans clé, il reste en mode « LLM estimé ».

Ajouter sur **Railway** (service `web` → Variables) :

```
SERPAPI_API_KEY=votre_clé_serpapi
SERPAPI_GL=be
SERPAPI_HL=fr
```

Obtenir la clé : https://serpapi.com → compte → **Your Account / API Key**
(essai gratuit ~100 recherches/mois). Après ajout, Railway redéploie ; l'assistant
passe automatiquement en données réelles (le bandeau affiche « Prix réels ·
Google Shopping »).

### Étape suivante (monétisation)

Remplacer les liens Google Shopping par des **liens d'affiliation** (Awin/Impact…)
une fois les programmes approuvés — le contrat de carte reste identique.
