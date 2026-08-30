# FILON — runbook Alembic, adoption, déploiement et rollback

Ce runbook est l'unique procédure autorisée pour activer Alembic sur une base
FILON. Il ne donne jamais l'autorisation de cibler une base dont l'URL, le
projet et l'environnement n'ont pas été confirmés par l'opérateur.

## Topologie de migrations autoritaire

| Rôle | Révision | Effet |
|---|---|---|
| Baseline historique | `b9db07b15986` | Adopte les 14 tables Core/Intelligence historiques |
| Expansion shadow | `d75faf1f6a94` | Ajoute `raw_source_records`, `observations` et `quarantine_records` |
| Devise observée | `3a7f9c2e5b61` | Ajoute `price_snapshots.currency`, nullable et sans backfill inventé |
| Normalisation Core | `f4c81a9d2e70` | Normalise fail-closed les deux drapeaux historiques d'`offers` |
| Tête Graph shadow | `8b2f4c7d9a10` | Ajoute huit tables `graph_*`, sans backfill ni lecteur v2 |
| Offer Graph shadow | `c6a1d4e8f2b3` | Ajoute `graph_offer_observations`, append-only et sans lecteur v2 |
| Merchant Intelligence shadow | `d7b2e5f9a4c1` | Ajoute `merchant_quality_snapshots`, sans score ni lecteur v2 |

La seule tête attendue est `d7b2e5f9a4c1`. La colonne de devise reste
`NULL` pour les relevés antérieurs : la devise d'un montant historique n'est
pas déductible de l'offre courante.

## Invariants non négociables

- Une seule personne ou tâche de déploiement migre à la fois.
- Le service web/release est l'unique propriétaire du pre-deploy Alembic ; les
  workers et Cron valident la révision mais n'exécutent jamais la migration.
- Alembic prend en plus un verrou consultatif PostgreSQL FILON et échoue
  immédiatement si une autre release détient déjà ce verrou.
- Les ingestions et tous les writers sont suspendus pendant sauvegarde,
  adoption, migration et contrôle.
- L'URL de base n'est ni affichée, ni copiée dans un log ou un ticket.
- Snapshot, checksum et exercice de restauration réussi précèdent toute
  adoption ou activation de la configuration Railway.
- Une base existante conforme est **stampée** à sa structure réelle ; elle
  n'est jamais upgradée depuis `base`. La seule variante couverte est celle du
  parcours 3B : elle est prouvée exhaustivement, stampée à la baseline puis
  immédiatement normalisée par la révision fail-closed dédiée.
- Un rollback applicatif ne dégrade pas le schéma. La baseline n'est jamais
  une cible de downgrade en production.

## 1. Choisir la source de configuration Railway

Les trois parcours ci-dessous sont distincts. Ne jamais supposer qu'un fichier
du dépôt pilote un service sans le confirmer dans l'état Railway réel.

### 1A. Service existant déjà opt-in Config as Code

[Config as Code](https://docs.railway.com/config-as-code) est déprécié. Seuls
les services qui utilisent **déjà** `railway.json` ou `railway.toml` continuent
à le faire jusqu'au **hard cutoff du 1er décembre 2026 (`2026-12-01`)**. Un
nouveau service ne peut plus activer Config as Code.

Le `railway.json` versionné reste uniquement le contrat legacy exact d'un
service existant dont les détails de déploiement prouvent déjà la provenance
fichier. Il utilise le schéma officiel
`https://railway.com/railway.schema.json` et décrit :

- Pre-Deploy Command : `alembic upgrade head` ;
- Start Command : `python -m app` ;
- Healthcheck Path : `/health/ready` ;
- Healthcheck Timeout : `120` secondes ;
- build par le `Dockerfile` de `filon-backend`.

Si Railway ne montre pas que ce service est déjà piloté par ce fichier, ne pas
l'y rattacher et appliquer le parcours 1B.

### 1B. Nouveau service : configuration Dashboard obligatoire

Pour un nouveau service, `railway.json` n'est pas sa source de configuration.
Dans le Dashboard Railway :

1. définir **Root Directory** sur `filon-backend` et laisser Railway
   auto-détecter le `Dockerfile` qui s'y trouve ;
2. ne rien renseigner comme **Railway Config File** ;
3. définir **Pre-Deploy Command** sur `alembic upgrade head` ;
4. définir **Start Command** sur `python -m app` ;
5. définir **Healthcheck Path** sur `/health/ready` ;
6. définir **Healthcheck Timeout** sur `120` secondes.

La commande de pre-deploy s'exécute **dans l'image construite**. Le Dockerfile
embarque donc `alembic.ini` et tout le répertoire `alembic/`. Un exit non nul de
la migration arrête le déploiement. Après démarrage, Railway ne bascule le
trafic que lorsque `/health/ready` répond HTTP 200 ; cette readiness vérifie
aussi la connexion et la révision de schéma.

### 1C. Remplacement par Infrastructure as Code

[Infrastructure as Code](https://docs.railway.com/infrastructure-as-code), avec
un fichier projet `.railway/railway.ts`, remplace Config as Code. Aucun fichier
IaC n'est ajouté dans ce lot : le graphe du projet, les services et les valeurs
`preserve()` doivent provenir d'un import Railway live authentifié. Un fichier
inventé serait dangereux, car une ressource omise du graphe IaC peut devenir
une suppression au plan.

Après obtention d'un accès externe autorisé, authentifier et lier le projet :

```bash
railway login
railway link
```

Pour migrer un service legacy déjà opt-in, prévisualiser d'abord la conversion,
puis seulement après revue écrire la configuration et retirer la source legacy :

```bash
railway config migrate
railway config migrate --apply
railway config plan
railway config apply
```

Pour importer un projet actuellement géré dans le Dashboard, partir de l'état
live, sans inclure les valeurs de secrets dans les fichiers :

```bash
railway config pull
railway config plan
railway config apply
```

Le plan doit être relu et ne montrer aucune suppression inattendue avant
`apply`. Railway refuse qu'un même service soit piloté simultanément par
Config as Code et IaC. La suppression de `railway.json` et l'ajout du répertoire
`.railway/` feront donc l'objet d'un changement ultérieur, fondé sur l'import
live et sa preuve, pas de ce lot hors ligne.

## 2. Préflight et sauvegarde obligatoires

Depuis `filon-backend` :

```bash
python -m pip install -r requirements.txt
alembic heads
```

Résultat attendu : une seule tête, `d7b2e5f9a4c1`. Confirmer ensuite hors log
le projet, l'environnement et l'hôte visés. Pour PostgreSQL, `pg_dump` et
`pg_restore` reçoivent une URL native `postgresql://`, pas le suffixe
SQLAlchemy `+asyncpg`.

Créer un snapshot custom, calculer son checksum, puis le restaurer vers une
base jetable **distincte** :

```bash
pg_dump "$PG_DUMP_URL" --format=custom --no-owner --no-acl --file=filon-before-alembic.dump
sha256sum filon-before-alembic.dump
pg_restore --clean --if-exists --no-owner --no-acl --dbname="$RESTORE_DRILL_URL" filon-before-alembic.dump
```

Comparer sur la restauration les comptes des tables critiques (`offers`,
`catalog_products`, `merchants`, `price_snapshots`) et contrôler plusieurs
lignes, dont les devises connues et inconnues. Si la restauration, le checksum
ou les comptes divergent, arrêter la procédure.

## 3. Choisir exactement un chemin d'adoption

### 3A. Base neuve

Une base neuve ne contient aucune table applicative :

```bash
alembic upgrade head
alembic current
alembic check
```

La révision courante doit être `d7b2e5f9a4c1 (head)` et le check doit afficher
`No new upgrade operations detected.`.

### 3B. Base existante à la baseline ou variante legacy couverte

Vérifier les 14 tables attendues et les colonnes historiques de `offers` :
`product_id`, `filon_category`, `filon_subcategory`, `offer_kind`, `dedup_key`,
`is_canonical`, `is_adult`. Vérifier aussi `pg_trgm`,
`ix_offers_name_trgm` et `ix_offers_brand_trgm`.

Deux formes seulement sont admises pour `offers.is_canonical` et
`offers.is_adult` :

- baseline stricte : `NOT NULL`, sans default serveur ;
- variante legacy couverte : colonnes nullables, respectivement defaults
  `TRUE` et `FALSE`, avec **zéro** valeur `NULL` dans les deux colonnes.

La révision `f4c81a9d2e70` refuse toute colonne absente, tout default différent
ou toute valeur `NULL`. Elle valide les contraintes avant de poser `NOT NULL`,
puis retire les defaults sans modifier les valeurs existantes.

Ce chemin n'est valide que si les trois tables shadow et
`price_snapshots.currency` sont encore absentes. Après preuve :

```bash
alembic stamp b9db07b15986
alembic upgrade head
alembic current
alembic check
```

L'upgrade ajoute les trois tables Observation, la colonne de devise, normalise
les deux drapeaux couverts puis crée les huit tables Product Graph, la table
Offer Graph et la table Merchant Intelligence. Il ne modifie aucune valeur
historique, ne fabrique aucune devise et ne lance aucun backfill.

### 3C. Base existante exactement identique à la tête

Si les 27 tables, contraintes, index et colonnes correspondent déjà
exactement aux modèles et aux migrations de tête, une adoption directe est
possible après la même sauvegarde et une comparaison exhaustive :

```bash
alembic stamp d7b2e5f9a4c1
alembic current
alembic check
```

### 3D. Schéma partiel ou divergent

Ne pas stamp et ne pas lancer `upgrade head`. Une base qui possède, par
exemple, `price_snapshots.currency` sans les tables shadow n'est ni la baseline
ni la tête. Produire une migration d'adoption/rattrapage distincte et testée,
puis reprendre ce runbook. Le stamp ne doit jamais servir à mentir au registre
de version.

## 4. Activation contrôlée

Avant tout premier déploiement avec migration automatique :

1. prouver le snapshot et sa restauration ;
2. terminer le chemin d'adoption correspondant ;
3. configurer `ENV=production`, `DATABASE_SCHEMA_MODE=alembic` et une
   `DATABASE_URL` confirmée ;
4. garder `OBSERVATION_SHADOW_ENABLED=false` et
   `PRODUCT_GRAPH_SHADOW_ENABLED=false` et
   `OFFER_GRAPH_SHADOW_ENABLED=false` et
   `MERCHANT_INTELLIGENCE_SHADOW_ENABLED=false` ;
5. obtenir `d7b2e5f9a4c1 (head)` avec `alembic current` et un `alembic check`
   sans drift ;
6. pour un nouveau service, enregistrer dans le Dashboard les six valeurs du
   parcours 1B et confirmer leur présence dans les détails de déploiement ;
7. pour un service legacy, utiliser `railway.json` uniquement si son opt-in
   antérieur est prouvé, puis planifier sa migration IaC avant le hard cutoff ;
8. laisser le pre-deploy rejouer l'upgrade idempotent vers `head`.

Après bascule :

- `/health/ready` répond HTTP 200 et annonce la révision
  `d7b2e5f9a4c1` ;
- les comptes catalogue correspondent aux comptes avant migration ;
- une ingestion limitée termine sans DDL implicite ni erreur de schéma ;
- les latences, comptes et identifiants de preuve sont annexés à la livraison ;
- le snapshot est conservé selon la politique de rétention approuvée.

## 5. Rollback sans perte

### Régression du shadow

Le rollback opérationnel est le feature flag :

```text
OBSERVATION_SHADOW_ENABLED=false
PRODUCT_GRAPH_SHADOW_ENABLED=false
OFFER_GRAPH_SHADOW_ENABLED=false
MERCHANT_INTELLIGENCE_SHADOW_ENABLED=false
```

Redéployer avec ce flag désactivé. Les tables shadow restent en place et les
données Core, shadow et de devise sont conservées. **Ne pas downgrader vers la
baseline.**

### Régression applicative

Remettre la version applicative précédente, conserver le schéma à
`d7b2e5f9a4c1` et garder les quatre shadows désactivés. Les structures d'expansion sont
compatibles avec l'ancien lecteur, qui les ignore. Un rollback applicatif ne
justifie ni un downgrade ni `DATABASE_SCHEMA_MODE=legacy`.

### Avertissement explicite sur la devise

Le downgrade technique de `3a7f9c2e5b61` vers `d75faf1f6a94` supprime la
colonne `price_snapshots.currency` **et perd toutes les devises qui y ont été
écrites**. Il n'est donc pas un rollback de production. Choisir l'une de ces
deux voies :

- rollback applicatif sans downgrade, schéma conservé à la tête ;
- restauration du snapshot testé vers une nouvelle base, puis bascule contrôlée
  de la connexion si des données ont été corrompues.

### Suppression structurelle ultérieure

Si une structure doit réellement disparaître, créer une **migration
compensatoire forward** depuis la tête : exporter ou transformer les données,
valider la restauration, puis appliquer une nouvelle révision avec
`alembic upgrade head`. Ne jamais utiliser la baseline comme cible de
downgrade en production.

## 6. Preuve CI reproductible

```bash
python -m pytest -q tests/test_migrations.py tests/test_middleware.py \
  tests/test_observation_shadow.py::test_feed_ingestion_writes_shadow_only_when_enabled
```

La suite prouve notamment : tête unique et garde-fou runtime alignés, upgrade
sans drift, présence nullable de `price_snapshots.currency`, absence de
backfill inventé pendant l'adoption, restauration d'un snapshot vers une base
distincte, rollback shadow par flag sans downgrade, contenu Alembic dans
l'image, contrat legacy exact, configuration Dashboard obligatoire des nouveaux
services, pre-deploy bloquant et readiness Railway sur `/health/ready`.
