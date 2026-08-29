# FILON — reçu de déploiement Railway Phase 0 Core

- Fenêtre d'exécution : **29 août 2026, 13:50–13:59 UTC**
- Environnement : `production`
- Projet Railway : `feisty-rejoicing`
- Service applicatif : `web`
- Référence locale déployée : `6717b39eb922d1dab3fc42242ecf17fc784b2e26`
- Référence distante de même arbre : `7896c6dd3922386e5f1ee7ea4d8e9911820ccc93`
- Arbre applicatif commun : `04560737a72825928612ae00fb52eef4eb7e009f`
- Déploiement Railway qualifié : `c832d1c8-e50f-4fac-94b3-8b59bb6cfff1`
- Décision : **GO pour le backend Core et l'adoption Alembic ; NO-GO Phase 1**

Ce reçu ne contient ni jeton, ni mot de passe, ni chaîne de connexion, ni
valeur de variable protégée.

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
