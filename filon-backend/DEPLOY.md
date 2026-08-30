# Déployer le backend FILON + brancher l'assistant

L'assistant `/recherche` du site appelle le backend en streaming (SSE). Une
carte ou un prix n'est publié que lorsque le Core apporte une preuve courante
et réconciliée. Si le backend, la base ou cette preuve manque, le client doit
s'abstenir explicitement ; un mock local n'est jamais une source de vérité.

## 1. Obtenir une clé LLM (DeepSeek — recommandé)

1. Créer un compte sur https://platform.deepseek.com
2. Générer une clé API (section **API Keys**). Format : `sk-...`
3. DeepSeek est OpenAI-compatible et très peu cher (~0,14 $/million de tokens).

> Alternatives possibles sans changer le code : Kimi (Moonshot) ou GLM (Zhipu).

## 2. Déployer le backend sur Railway

### Nouveau service : configuration Dashboard obligatoire

[Config as Code](https://docs.railway.com/config-as-code) est déprécié et un
nouveau service ne peut plus l'activer. Pour ce nouveau service,
`railway.json` n'est pas sa source de configuration.

1. Créer un compte sur https://railway.app et **New Project → Deploy from
   GitHub repo** (`Fredm237/codex-test`).
2. Dans **Settings**, définir **Root Directory** sur `filon-backend`. Railway
   auto-détecte alors le `Dockerfile` présent dans cette racine. Ne rien
   renseigner comme **Railway Config File**.
3. Configurer explicitement dans le Dashboard :

   - **Pre-Deploy Command** : `alembic upgrade head` ;
   - **Start Command** : `python -m app` ;
   - **Healthcheck Path** : `/health/ready` ;
   - **Healthcheck Timeout** : `120` secondes.

   Le `Dockerfile` embarque l'application, `alembic.ini` et les migrations,
   puis exécute le runtime sous l'utilisateur non privilégié `filon`. La
   commande de pre-deploy s'exécute dans cette image et un exit non nul arrête
   la livraison.
4. Configurer les **Variables** :

   ```
   LLM_PROVIDER_DEFAULT=deepseek
   LLM_PROVIDER_REASONING=deepseek
   LLM_PROVIDER_LONG=deepseek
   DEEPSEEK_API_KEY=sk-...        # votre clé
   ENV=production
   DEBUG=false
   DATABASE_URL=<référence privée vers le service PostgreSQL Railway>
   DATABASE_SCHEMA_MODE=alembic
   OBSERVATION_SHADOW_ENABLED=false
   PRODUCT_GRAPH_SHADOW_ENABLED=false
   OFFER_GRAPH_SHADOW_ENABLED=false
   MERCHANT_INTELLIGENCE_SHADOW_ENABLED=false
   CORS_ORIGINS=["https://filon.be","https://www.filon.be"]
   FORWARDED_ALLOW_IPS=<IP/CIDR exacts et vérifiés du proxy Railway>
   METRICS_EXPORT_TOKEN=<secret aléatoire distinct, 32-256 caractères ASCII>
   RATE_LIMIT_BACKEND=local
   ```

   `DATABASE_URL` est obligatoire : le pre-deploy doit pouvoir migrer la base
   et `/health/ready` doit en vérifier la connexion et la révision. `REDIS_URL`
   et `QDRANT_URL` restent optionnelles.
   `FORWARDED_ALLOW_IPS` est un gate de sécurité : ne jamais utiliser `*`, `/0`
   ou des réseaux dont l'union couvre tout Internet. Tant que les pairs réels
   du proxy ne sont pas identifiés et vérifiés, le déploiement reste NO-GO.
   `METRICS_EXPORT_TOKEN` active uniquement l'export standard authentifié ; il
   ne doit être ni réutilisé comme jeton admin, ni ajouté à une URL.

   Le quota distribué est un opt-in séparé. Après avoir créé un Redis privé et
   vérifié sa disponibilité depuis le service web, remplacer la dernière ligne
   par :

   ```
   REDIS_URL=<référence privée vers Redis Railway>
   RATE_LIMIT_BACKEND=redis
   RATE_LIMIT_IDENTITY_SOURCE=railway
   RATE_LIMIT_IDENTITY_SECRET=<secret partagé distinct, 32-256 caractères ASCII>
   RATE_LIMIT_REDIS_TIMEOUT_SECONDS=0.25
   ```

   Tous les réplicas doivent recevoir le même secret afin de produire le même
   pseudonyme réseau sans stocker l'adresse brute. Railway injecte
   `RAILWAY_ENVIRONMENT_ID` et `RAILWAY_SERVICE_ID` ; FILON exige leurs UUID
   canoniques avant d'accepter la source `railway`, puis lit exactement un
   `X-Real-IP` canonique conformément aux
   [spécifications réseau Railway](https://docs.railway.com/networking/public-networking/specs-and-limits).
   Un en-tête absent, dupliqué ou invalide ferme la requête avec `503` sans
   atteindre la route. En mode `redis`, une erreur, un timeout ou une décision
   illisible produit le même refus ; FILON ne retombe jamais sur un compteur
   local qui rouvrirait le quota. Les seuls `GET`/`HEAD /health/live` et
   `/health/ready` restent exempts : Railway appelle sa sonde directement dans
   le conteneur, sans le `X-Real-IP` de son proxy HTTP public. Les métriques,
   `/health`, les lookalikes et toutes les routes métier restent protégés.
   Conserver `local` tant que Redis n'est pas créé et qualifié ; la présence du
   code seule ne prouve pas une protection distribuée en production.
5. Avant de déployer, exécuter intégralement le
   [runbook d'adoption et de rollback](../docs/architecture/DATABASE_MIGRATION_RUNBOOK.md) :
   sauvegarde, restauration test et adoption Alembic précèdent la migration
   automatique.
6. Déployer. Un exit non nul de `alembic upgrade head` arrête la livraison.
   Railway fournit ensuite une URL publique, par exemple
   `https://filon-backend-production.up.railway.app`.
7. Vérifier : ouvrir `https://<url>/health/ready` → HTTP 200 avec la révision
   `e8c3f6a0b5d2` attendue. Railway exige ce 200 avant de basculer le trafic.
   `/health/live` reste un diagnostic de processus et `/health` un diagnostic
   détaillé des dépendances. Enfin,
   `https://<url>/api/advise/stream?q=un%20pc%20portable%20800€` doit renvoyer un flux SSE.

### Export OpenMetrics

L'endpoint de collecte est `GET /health/metrics/openmetrics`. Il répond `503`
tant que `METRICS_EXPORT_TOKEN` n'est pas configuré, puis exige exactement :

```
Authorization: Bearer <METRICS_EXPORT_TOKEN>
```

Configurer ce secret dans le gestionnaire de secrets du collecteur, jamais
dans une cible contenant le token en query string. Le format est OpenMetrics
1.0, le cache est interdit et l'export ne contient que les dimensions fermées
du contrat d'observabilité. Une erreur de snapshot répond `503` sans détail.

Avant tout GO, raccorder cet endpoint à l'agrégateur approuvé, vérifier les
scrapes de chaque replica, la rétention, les doublons après redémarrage et
l'absence de labels libres. L'endpoint exporte des compteurs locaux à chaque
processus : l'agrégateur est responsable de la somme multi-replica et ne doit
jamais interpréter un reset comme une guérison.

Un pack Prometheus/Grafana fail-closed est versionné dans
[`observability/`](observability/README.md). Il fournit le scrape authentifié
par fichier secret, un service discovery vide par défaut, 11 rollups testés et
un dashboard descriptif sans SLO ni règle de pager. Il doit être importé dans
la plateforme approuvée avec l'inventaire réel de chaque réplica ; sa présence
dans le dépôt ne prouve ni le déploiement, ni la rétention, ni le trafic.

Ne pas écrire directement l’inventaire actif. Le compiler avec
`python -m observability.tools.target_inventory`, en passant le nombre exact
de réplicas annoncé par la plateforme. Après activation, exécuter
`python -m observability.tools.verify_prometheus` contre l’API HTTPS protégée
du collecteur et archiver son reçu expurgé. La procédure, les arguments et les
limites de cette preuve sont détaillés dans le README du pack. Un reçu absent,
un compte différent ou une seule des 11 séries manquantes maintient le NO-GO.

### Job catalogue séparé du processus web

Le serveur FastAPI ne lance aucune boucle d'ingestion. Créer un second service
Railway, sans domaine public, depuis le même dépôt et la même racine
`filon-backend`, puis configurer :

- **Start Command** : `python -m app.ingest.scheduler` ;
- **Cron Schedule** : `0 */6 * * *` (UTC) ;
- **Pre-Deploy Command** : aucune ; le service web/release reste l'unique
  propriétaire de `alembic upgrade head`, et le job refuse un schéma en retard ;
- variables de production identiques pour la base et la sécurité, plus
  `AWIN_AUTO_SYNC_HOURS=6`, `AWIN_FEED_API_KEY` et `AWIN_API_TOKEN` ;
- bornes obligatoires : `AWIN_MAX_ROWS_PER_FEED=100000`,
  `AWIN_MAX_DOWNLOAD_BYTES=268435456` et
  `AWIN_MAX_DECOMPRESSED_BYTES=536870912`. Une valeur lignes à `0` utilise le
  plafond dur interne de 250 000 ; elle ne rend jamais le feed illimité.

Le job consulte le journal persistant, exécute au plus un cycle dû, puis se
termine. Une valeur `AWIN_AUTO_SYNC_HOURS=0`, un identifiant absent, un schéma
en retard, une collecte vide ou dégradée et toute erreur rendent un code non
nul. Un run encore actif empêche déjà un doublon au niveau base ; Railway saute
aussi une occurrence si l'exécution Cron précédente n'est pas terminée.
Le téléchargement quitte la mémoire après 8 MiB et utilise un spool local ; un
dépassement du corps reçu ou du contenu décompressé interrompt le feed avant
parsing. Dimensionner l'espace temporaire du service au moins à la borne
compressée et ne relever aucun plafond sans mesure de mémoire et de disque.
L'activation de ce service reste un changement externe séparé, après adoption
de la base.

Avant d'activer la cadence, lancer une occurrence manuelle avec la commande
`python -m app.ingest.scheduler --check`. Ce préflight est strictement
non-écrivant : il valide les identifiants sans les afficher, les plafonds, la
connexion, la révision Alembic et l'état du catalogue, puis émet un unique reçu
JSON expurgé. Un code `0` et `"status":"ready"` autorisent uniquement
l'activation de la cadence ; ils ne prouvent pas qu'une synchronisation réelle
a réussi. Toute autre sortie maintient le service Cron désactivé.

### Product/Variant et Offer Graph shadows

Les migrations créent les tables `graph_*` sans backfill et sans lecteur public.
Le writer Graph ne peut être activé seul : il exige simultanément
`OBSERVATION_SHADOW_ENABLED=true` et `PRODUCT_GRAPH_SHADOW_ENABLED=true` sur le
worker d'ingestion. Le service web conserve les cinq flags shadow à `false`.

Avant toute écriture, exécuter un lot en lecture seule :

```bash
python -m app.product_graph.backfill --after-raw-id 0 --limit 1000
```

La commande n'écrit rien sans `--apply`, refuse plus de 10 000 raws par lot et
retourne uniquement des compteurs ainsi que `last_raw_source_id`. Après revue
du dry-run et activation des deux flags, rejouer exactement la commande avec
`--apply`, puis reprendre au dernier identifiant. Aucun titre, marque ou
similarité ne remplace un GTIN exact. Une identité absente, invalide ou
contradictoire reste en quarantaine.

`OFFER_GRAPH_SHADOW_ENABLED=true` exige également
`OBSERVATION_SHADOW_ENABLED=true`. Il projette chaque raw Awin vers un relevé
append-only : argent décimal, devise explicite, stock tri-state, lien marchand
HTTPS public et éligibilité motivée. Sans lien de variante résolu, le relevé
est quarantiné ; prix, devise, stock ou lien insuffisant produisent
`unknown`/`ineligible`, jamais un claim favorable. Ce shadow n'est pas lu par
les endpoints v1.

Qualifier ensuite l'Offer Graph en lecture seule, après le lot Product Graph :

```bash
python -m app.offer_graph.backfill --after-raw-id 0 --limit 1000
```

L'option `--apply` exige les flags Observation et Offer Graph. Reprendre au
`last_raw_source_id` et ne jamais confondre les compteurs techniques avec une
mesure Quality Lab.

Mesurer ensuite un lot Merchant Intelligence avec une horloge explicite :

```bash
python -m app.merchant_intelligence.backfill \
  --evaluated-at 2026-08-31T00:00:00+02:00 \
  --after-raw-id 0 --limit 1000
```

Cette commande ne produit aucun score et laisse livraison, retours, garantie,
support, paiement, shipping et exactitude prix comme non mesurables. Son
`--apply` exige les quatre flags shadow ; le service web les conserve off.

Construire ensuite le registre Evidence en lecture seule :

```bash
python -m app.evidence_engine.backfill \
  --evaluated-at 2026-08-31T00:00:00+02:00 \
  --after-raw-id 0 --limit 1000
```

Les claims forts et toute décision restent inéligibles sans leurs prérequis.
L'option `--apply` exige les cinq flags shadow et n'active aucun lecteur public.

### Service existant déjà opt-in Config as Code

Le `railway.json` du dépôt reste le contrat legacy exact d'un service dont les
détails de déploiement prouvent déjà qu'il utilise ce fichier. Il porte les
mêmes valeurs que le Dashboard ci-dessus. Seuls ces services existants
continuent à lire Config as Code jusqu'au **hard cutoff du 1er décembre 2026**.
La date ISO est `2026-12-01`. Ne jamais rattacher un nouveau service à ce
fichier.

### Migration vers Infrastructure as Code

[Infrastructure as Code](https://docs.railway.com/infrastructure-as-code) et
`.railway/railway.ts` remplacent Config as Code. Aucun fichier IaC n'est ajouté
ici sans import du projet live : inventer le graphe pourrait planifier la
suppression de ressources omises.

Après obtention d'un accès externe autorisé, exécuter `railway login` et
`railway link`, puis choisir un seul chemin :

- service legacy : `railway config migrate`, revue de la prévisualisation,
  `railway config migrate --apply`, `railway config plan`, puis
  `railway config apply` ;
- projet géré dans le Dashboard : `railway config pull`, revue du fichier
  importé, `railway config plan`, puis `railway config apply`.

Ne jamais utiliser `--include-variables` pour cet import : il pourrait écrire
des secrets déchiffrés dans le dépôt. Le plan doit être relu et ne montrer
aucune suppression inattendue avant l'apply. L'ajout de `.railway/` et le
retrait ultérieur du contrat legacy seront un changement séparé, fondé sur cet
import live.

En cas de régression, remettre la version applicative précédente,
`PRODUCT_GRAPH_SHADOW_ENABLED=false` et
`OFFER_GRAPH_SHADOW_ENABLED=false`,
`MERCHANT_INTELLIGENCE_SHADOW_ENABLED=false`,
`EVIDENCE_ENGINE_SHADOW_ENABLED=false`,
`OBSERVATION_SHADOW_ENABLED=false`, tout en conservant le schéma à la tête
`e8c3f6a0b5d2`.
Ne jamais downgrader vers la baseline. Le downgrade technique
`3a7f9c2e5b61` → `d75faf1f6a94` supprime la colonne de devise et les valeurs
qu'elle contient ; une suppression structurelle exige une migration
compensatoire forward ou, si les données sont corrompues, la restauration du
snapshot testé vers une nouvelle base.

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
- Backend : `app/services/recommend.py` → le LLM renvoie un JSON strict ; seules
  les cartes dont la preuve Core est explicite et courante sont émises par
  `app/api/routes/stream.py`.
- Sans clé LLM ou sans preuve produit courante, le backend produit une réponse
  contrôlée ou s'abstient ; il n'invente ni produit, ni prix, ni verdict.

## Données produits réelles (SerpApi — actif si la clé est présente)

Avec une clé **SerpApi**, l'assistant peut collecter des candidats externes
(nom, photo, prix observé, marchand et lien). Ces candidats ne deviennent pas
des preuves par eux-mêmes : une carte transactionnelle exige toujours la
réconciliation avec le Core et une preuve courante explicite. Sans clé ou sans
réconciliation, l'assistant s'abstient au lieu d'estimer un prix.

Ajouter sur **Railway** (service `web` → Variables) :

```
SERPAPI_API_KEY=votre_clé_serpapi
SERPAPI_GL=be
SERPAPI_HL=fr
```

Obtenir la clé : https://serpapi.com → compte → **Your Account / API Key**
(essai gratuit ~100 recherches/mois). Après ajout, Railway redéploie ; valider
la réconciliation et la fraîcheur des preuves avant d'afficher une carte ou un
qualificatif de prix réel.

### Étape suivante (monétisation)

Remplacer les liens Google Shopping par des **liens d'affiliation** (Awin/Impact…)
une fois les programmes approuvés — le contrat de carte reste identique.
