# FILON — reçu de déploiement Railway Phase 0 Core

- Fenêtre d'exécution : **29 août 2026, 13:50–13:59 UTC**
- Environnement : `production`
- Projet Railway : `feisty-rejoicing`
- Identifiant projet Railway : `d5f2a738-67b2-4634-ae5f-efb9f540c283`
- Identifiant environnement Railway : `b843980b-13e3-414b-8568-890a953310ed`
- Service applicatif : `web`
- Identifiant service applicatif : `db05c3f5-e8d3-4034-ba9e-a96c3eb6b391`
- Service PostgreSQL : `d68db2c1-3ff8-45ca-a329-c89b4e81fab9`
- Volume PostgreSQL : `e4ebe095-06e2-492a-99b5-06ddf79d5065`
- Référence locale déployée : `6717b39eb922d1dab3fc42242ecf17fc784b2e26`
- Référence distante de même arbre : `7896c6dd3922386e5f1ee7ea4d8e9911820ccc93`
- Arbre applicatif commun : `04560737a72825928612ae00fb52eef4eb7e009f`
- Déploiement Railway qualifié : `c832d1c8-e50f-4fac-94b3-8b59bb6cfff1`
- Décision : **GO pour le backend Core et l'adoption Alembic ; NO-GO Phase 1**

Ce reçu ne contient ni jeton, ni mot de passe, ni chaîne de connexion, ni
valeur de variable protégée.

Les identifiants Railway ci-dessus sont publiés comme repères d'exploitation,
avec autorisation explicite du propriétaire le 30 août 2026. Ils ne sont pas
des secrets et ne donnent aucun accès sans authentification Railway.

## Sauvegarde et restauration prouvée

Avant toute migration, une sauvegarde native Railway nommée
`FILON pre-core-deploy 2026-08-29` a été créée sous l'identifiant
`d5a5aaf4-c5f1-4ca1-ae50-7e25e5c125a5`. Elle ne déclare pas de date
d'expiration.

Un dump logique PostgreSQL custom de **396 811 802 octets** a aussi été créé,
protégé localement en mode `0600`, avec l'empreinte :

`sha256:51f159590ff439dbbb2277c825f51729806e912e0fd1f42ba6bf43572af5e008`.

Ce dump a été restauré dans PostgreSQL 18 hors production. `pg_amcheck`, les
tables, la structure et les compteurs ont été vérifiés. Le restore drill
reproduisait exactement l'état sauvegardé :

| Table | Lignes restaurées |
|---|---:|
| `offers` | 2 007 401 |
| `catalog_products` | 596 211 |
| `merchants` | 241 |
| `price_snapshots` | 20 412 530 |

Aucune restauration d'essai complète n'a été exécutée dans le cluster de
production. Une base jetable amorcée par erreur sur ce volume a été arrêtée à
environ 231 Mio puis supprimée, sans résidu, afin de ne pas compromettre
l'espace disponible.

## Fenêtre sans écrivain applicatif

Railway réinterprétait une dernière région à zéro comme un retour au minimum
implicite d'un réplica. Le déploiement actif n'a donc pas été supprimé. Un
conteneur de maintenance statique, sans code FILON et sans accès PostgreSQL, a
été qualifié localement puis déployé sous l'identifiant
`677dd242-4bdc-404a-8d89-37fb3f2b20b6`.

Railway a confirmé un seul processus `RUNNING`, avec la commande `httpd`, la
healthcheck `/health` et aucune pré-migration. L'historique des déploiements
antérieurs a été conservé ; aucune commande de suppression de déploiement n'a
été exécutée.

## Adoption Alembic en production

Après activation du mode maintenance, les préconditions ont donné :

| Contrôle | Valeur avant migration |
|---|---:|
| `offers` | 2 007 415 |
| `catalog_products` | 596 211 |
| `merchants` | 251 |
| `price_snapshots` | 20 413 730 |
| `offers.is_canonical IS NULL` | 0 |
| `offers.is_adult IS NULL` | 0 |
| table `alembic_version` | absente |
| tables shadow | absentes |

La baseline existante a été adoptée par `stamp b9db07b15986`, puis la chaîne a
été appliquée jusqu'à `f4c81a9d2e70` :

1. `d75faf1f6a94` — tables shadow de provenance, observation et quarantaine ;
2. `3a7f9c2e5b61` — devise source nullable sur les instantanés de prix ;
3. `f4c81a9d2e70` — drapeaux d'offre stricts sans valeur inventée.

`alembic current` a retourné `f4c81a9d2e70 (head)` et `alembic check` a
retourné `No new upgrade operations detected`.

Les quatre compteurs métier après migration et après remise en service sont
restés strictement identiques aux compteurs juste avant migration. Les trois
tables shadow contiennent chacune **0 ligne**, `price_snapshots.currency`
contient **0 valeur non nulle**, les deux drapeaux contiennent **0 NULL** et
les deux colonnes sont `NOT NULL` sans default serveur.

## Déploiement qualifié et remise en service

Le backend a été envoyé depuis un export propre du commit qualifié, séparé des
modifications locales protégées. Railway a appliqué :

- builder `DOCKERFILE` et `Dockerfile` du backend ;
- pré-déploiement `alembic upgrade head` ;
- démarrage `python -m app` ;
- healthcheck `/health/ready`, délai 120 secondes.

Le déploiement `c832d1c8-e50f-4fac-94b3-8b59bb6cfff1` est `SUCCESS` avec un
seul réplica `RUNNING`. Les vérifications publiques ont retourné :

- `GET /health/live` : HTTP 200, `alive=true` ;
- `GET /health/ready` : HTTP 200, `ready=true`, base `ok`, révision
  `f4c81a9d2e70`.

Les journaux confirment `env=production`, la validation de la révision et des
requêtes catalogue HTTP 200. Aucun log de build de niveau erreur n'a été
retourné.

Les propriétés de configuration ont été contrôlées sans afficher leurs
valeurs : environnement production, debug désactivé, mode Alembic, shadow
désactivé, URL PostgreSQL privée, deux origines CORS HTTPS sans wildcard,
confiance proxy limitée à la boucle locale et token métriques de 64 caractères
hexadécimaux.

## Activation de l'identité Railway — 30 août 2026

La branche de production est désormais `codex/filon-phase-0-core`, dans la
région `EU West (Amsterdam, Netherlands)`, avec un réplica. La configuration a
activé `RATE_LIMIT_IDENTITY_SOURCE=railway` tout en conservant
`RATE_LIMIT_BACKEND=local` : cette étape qualifie la frontière d'identité sans
revendiquer une coordination Redis encore absente.

Le premier essai `f63024eb-e6d9-48ff-a59b-6aa78454c657` a correctement échoué
au healthcheck : les sondes internes Railway n'empruntent pas le proxy HTTP
public et n'ont donc pas de `X-Real-IP`. L'ancien déploiement est resté actif.
Le correctif borne l'exemption aux seuls `GET`/`HEAD /health/live` et
`/health/ready` ; `/health`, les métriques, les lookalikes et toutes les routes
métier restent soumis à l'identité et au quota.

Le commit distant `2725a464e046c3790ed20eb0533068760922a524`, arbre
`de9cc8944e82f42ae28361f43f5fa49791d6b1e1` byte-identique au commit local
`04fe05bc7cc841e54b23341ef5208d4f0f61518e`, a produit le déploiement
`03be13dc-e20f-4f62-8119-c27d84176b47`, désormais `ACTIVE` et `SUCCESS`.
Les journaux montrent le pré-déploiement Alembic, le démarrage Python 3.12.14,
la validation de la révision et `GET /health/ready → 200`.

Les contrôles publics datés ont ensuite établi :

- `GET /health/ready` : HTTP 200, base `ok`, révision `f4c81a9d2e70` ;
- `GET /health/live` : HTTP 200 ;
- `GET /health` : HTTP 200 alors que cette route n'est pas exemptée ;
- le même `GET /health` avec un `X-Real-IP` client invalide, puis deux valeurs
  forgées dupliquées : HTTP 200 dans les deux cas. Comme FILON répondrait 503
  à une valeur absente, invalide ou dupliquée, l'edge a remplacé/normalisé ces
  entrées avant de livrer exactement une adresse canonique à l'application.

Le correctif passe **180 tests ciblés** et la suite backend complète
**2 067 réussis + 2 ignorés** sous Python 3.12. GitHub Actions #352 confirme
Alembic, les régressions backend, Web, Mobile et Extension ; son unique échec
est le gate humain strict volontairement rouge sur les sept datasets vides.
L'artefact Quality associé est `9736128514`.

## Redéploiement automatique qualifié — 30 août 2026

Railway a ensuite redéployé automatiquement la correction finale du Catalog
Quality Funnel depuis la même branche publique. Le déploiement
`cd88cf30-354d-4be0-8206-493a829432f9` est affiché **Deployment successful**,
en `EU West`, avec un réplica. Il remplace le déploiement actif précédent sans
supprimer son historique de rollback.

La référence distante `9d8ade3ad671afe98f28be9c6f1fd5bf69fae414`
et la référence locale `594f51fc91651eb6e067dc9497b0b4337d0e57bc`
portent exactement l'arbre
`9534214815bc6af2630bbf523fffb5c76f64980c`. La qualification GitHub Actions
#358 (`33332958611`) a validé Web, Mobile, Extension, Alembic, les **2 118**
régressions backend et la readiness normale. Le seul échec est le gate humain
strict attendu sur les sept datasets vides. Son artefact `9738202431`, nommé
`quality-readiness-417c4f5db118a1e9445f56539cc492f5342a6cbc`, porte le digest
`sha256:b2bdbd23cd83f6c7372e81987af4af3619f2aeae56215b8b79eefe73b951b50a`.

Les sondes publiques du backend Railway
`https://web-production-c6842.up.railway.app` ont répondu après ce
redéploiement :

- `GET /health/ready` : HTTP 200, `ready=true`, PostgreSQL `ok`, révision
  `e8c3f6a0b5d2` ;
- `GET /health/live` : HTTP 200, `alive=true`.

L'environnement contient actuellement les seuls services `web` et
`Postgres`. Aucun service Redis, agrégateur Prometheus ou backend de traces
n'est présent. Le quota distribué reste donc non activé et aucune preuve
multi-réplica n'est revendiquée.

## Préflight scheduler dans l'image web — 30 août 2026

Le lot applicatif scheduler a été publié sur la branche de production sous la
référence distante
`5ab3c3c0da28c2df6433d773d897f1a29e6f12ec`, arbre
`e2124704b30d405f5d7215f4acc95bc5246dc570` identique à l'arbre local du
commit `8594bd84fd4e60166dc852637807f130da752213`.

Le déploiement web automatique
`d1e17b10-fce8-4f16-90d9-68aadbac4747` est affiché **Deployment successful**,
en EU West avec un réplica. Les sondes publiques ont confirmé `alive=true`,
`ready=true`, PostgreSQL `ok` et la révision `e8c3f6a0b5d2`.

Actions #362 (`33334944805`) a validé les trois clients, Alembic, les
régressions backend et la readiness normale. Le seul échec reste le gate
humain strict attendu. Son artefact Quality `9738761749` porte le digest
`sha256:751ccb0860009fcad22a12c2fddae8b6dc1fc36b2c58ac2f51df4456f10298a9`.

La commande `python -m app.ingest.scheduler --check` est donc présente dans
l'image qualifiée, mais aucun troisième service Railway n'a été créé : la
topologie reste strictement `web` + `Postgres`. Aucune exécution scheduler,
cadence Cron ou ingestion Awin n'est revendiquée par ce reçu.

## Exporteur OTLP désactivé dans l'image web — 30 août 2026

Le lot applicatif OTLP et son transport loopback ont été publiés sous la
référence distante `160d89fe8cdec295e61c2e32a3bc7c70d7931192`, arbre
`f653c8c975e30c1e1ae3383c2202a3fdc2b6e8af` identique à celui du commit
local `1b2541cfafce32e0d0a78b75e2b934d106d6e73f`.

Le déploiement automatique
`6eb242cc-efca-46f4-987f-ab4e503e3459` est affiché
**Deployment successful**, en EU West avec un réplica. Les sondes publiques
ont confirmé `alive=true`, `ready=true`, PostgreSQL `ok` et la révision
`e8c3f6a0b5d2`. Actions #366 (`33337020943`) valide les trois clients,
Alembic, les **2 132** régressions backend et la readiness normale ; seul le
gate humain strict échoue comme attendu. L'artefact Quality est `9739367304`,
digest
`sha256:c8e3e9a3d725fc5efe1123e4247f801252b9b2af8674dbf42574f4602328e9d3`.

L'exporteur est présent mais `TRACE_EXPORT_BACKEND=disabled`. Aucun endpoint
ni jeton OTLP n'a été ajouté, aucun span n'est envoyé et aucun collecteur n'a
été créé. La topologie Railway reste `web` + `Postgres`.

## Capacité, rollback et risques résiduels

Le volume PostgreSQL est `READY` à **7 855,56 Mio sur 20 000 Mio**, soit
**39,28 %**. Les logs historiques du 28 août 2026 contiennent cependant des
échecs `No space left on device` sur des fichiers temporaires PostgreSQL. Un
audit API ultérieur a d'abord confirmé zéro planning, deux sauvegardes manuelles
sans expiration et aucun dashboard/moniteur Railway dans l'environnement.
Après autorisation explicite, les plannings `DAILY`, `WEEKLY` et `MONTHLY` ont
été activés et relus ; le volume est resté `READY` au même taux d'occupation.
Deux blocs Railway Observability ciblant exclusivement le volume ont ensuite
été créés : avertissement au-dessus de 14 GB et critique au-dessus de 17 GB,
avec notifications natives. L'API confirme `DISK_USAGE_GB`, les deux seuils et
aucune alerte active au niveau courant. L'export OpenMetrics direct de
production a également passé son contrat d'authentification, de format et de
cardinalité. Les mesures expurgées figurent dans le
[reçu observabilité et résilience](PHASE_06_PRODUCTION_OBSERVABILITY_RECEIPT.md).

Le rollback opérationnel reste applicatif : les déploiements précédents sont
conservés dans l'historique, la nouvelle structure est compatible avec
l'ancien runtime et la migration des drapeaux ne réintroduit volontairement ni
nullable ni default en downgrade. La sauvegarde native et le dump restauré
restent les recours de restauration de données en cas d'incident explicite.

La production Core ne lève pas les autres gates : l'endpoint OpenMetrics direct
est qualifié, mais agrégateur, rétention, backend de traces, WAF ou limite
distribuée, pager, trafic représentatif et SLO restent non prouvés. Les sept
datasets humains Quality Lab restent vides ; Product Graph, Phase 1 et
Immersive demeurent donc **NO-GO**.

## Nettoyage des accès temporaires

Après vérification, le tunnel SSH a été fermé, la clé éphémère retirée du
compte Railway et supprimée localement, le script de migration temporaire a été
supprimé et la session CLI a été déconnectée. La sauvegarde native et le dump
logique ont été conservés ; aucun secret n'est versionné dans ce reçu.
