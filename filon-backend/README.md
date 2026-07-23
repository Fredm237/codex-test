# FILON AI — Backend

Le cerveau de FILON : un **agent IA d'achat** qui comprend un besoin, compare
le marché (prix, cashback, promos, historique, avis) et recommande la
meilleure décision — quoi acheter, où, et quand.

> Le frontend (`../filon-web`) est l'interface. Ce backend est le produit.

## Architecture

```
Frontend  ──API──▶  Backend (FastAPI)  ──▶  Orchestrateur (LangGraph)
                                              │
        ┌─────────────────────────────────────┼───────────────────────────┐
        ▼                                      ▼                           ▼
  Agents spécialisés (compréhension, recherche, comparaison, cashback,
  promos, historique, avis, décision)  ──▶  Sources externes (APIs marchands,
                                              affiliation) — Phase 2
```

- **API** : FastAPI (`app/main.py`) — `/api/advise`, `/api/chat`, `/health`.
- **Agents** : `app/agents/` — 8 agents + orchestrateur LangGraph.
- **LLM** : couche d'abstraction `app/llm/` — routeur multi-fournisseurs
  (DeepSeek / Kimi / GLM), repli automatique sur un mock déterministe.
- **Mémoire** : PostgreSQL (classique) + Qdrant (IA) — optionnels au runtime.
- **Cache** : Redis — optionnel.

## Démarrage rapide

### Sans rien installer d'autre (mode mock, sans clé)

```bash
cd filon-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Puis :

```bash
curl -s localhost:8000/api/advise \
  -H 'content-type: application/json' \
  -d '{"query":"Je cherche un ordinateur portable pour étudiant à moins de 900€"}' | jq
```

Vous obtenez une recommandation argumentée (meilleur choix, prix réel après
cashback + promo, signal d'achat, alternatives).

### Avec l'infrastructure complète (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Démarre le backend + PostgreSQL + Redis + Qdrant. Voir `/health` pour l'état
des dépendances.

## Activer un vrai LLM

Dans `.env`, renseignez une clé et pointez la tâche voulue dessus :

```
LLM_PROVIDER_DEFAULT=deepseek
DEEPSEEK_API_KEY=sk-...
```

Tâches : `default` (conversation, orchestration), `reasoning` (décision),
`long` (analyses longues, ex. Kimi).

## Tests

```bash
pytest
```

Le test de bout en bout valide le scénario cible « portable étudiant < 900 € »
entièrement en mock (aucun réseau requis).

## Roadmap

- **Phase 1 (ici)** : API, agents, orchestrateur, couche LLM, mémoire, Docker.
- **Phase 2** : connecteurs marchands/affiliation réels (Awin, Impact, CJ,
  Rakuten ; Amazon, Fnac, Back Market…), base produit propriétaire.
- **Phase 3** : cashback/coupons/historique en temps réel, alertes.
- **Phase 4** : extension navigateur (analyse automatique des pages marchandes).
- **Phase 5** : reprise et connexion du frontend.
