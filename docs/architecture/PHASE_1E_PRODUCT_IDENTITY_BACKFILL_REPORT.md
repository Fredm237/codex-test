# FILON — Phase 1E Product Identity Backfill Report

- Date : **31 août 2026**
- Statut : **QUALIFIÉ EN PRODUCTION — LOT SHADOW BORNÉ**
- Déploiement Railway : `e2a434b4-aedd-47c7-9532-7c6de39cdb67`
- Révision Alembic : `b3e1a7c4d9f2`
- Lecteurs publics : **Core v1 inchangés**
- Portée : **1 feed Awin, 1 000 offres, raws `1..1000`**

## Verdict

Le backfill Product Identity est idempotent sur le premier corpus réel borné.
Le premier passage a persisté les projections shadow ; le second a reconnu
exactement tous les objets existants et n'a créé aucune ligne supplémentaire.
Aucune collision de normalisation Brand, collision d'identifiant scopé,
absence de contexte marchand ou absence de lien vers une Offer n'a été
observée dans ce lot.

Ce verdict qualifie le mécanisme de backfill et sa sécurité de replay. Il ne
mesure pas la couverture de l'intégralité du catalogue Awin et ne promeut
aucun lecteur public vers le Product Graph.

## Constitution du corpus réel

La production ne contenait initialement aucun `RawSourceRecord` ni
`Observation` historique utilisable par le backfill. Un seul cycle Awin a donc
été lancé avec des limites uniquement portées par le processus :

- Observation shadow activée pour ce processus ;
- Product Graph writer désactivé pendant la capture ;
- `AWIN_FEED_LIMIT=1` et `AWIN_MAX_ROWS_PER_FEED=1000` ;
- arrêt coopératif demandé après le checkpoint du feed.

Le run catalogue `20` a terminé honnêtement en `interrupted`, motif
`stop_after_current_feed`, après avoir checkpointé **1 feed**, **1 000 offres**
et **243 marchands**, de `2026-08-31T21:39:43.682931Z` à
`2026-08-31T21:56:24.681650Z`. Aucun second run n'a été lancé. L'exception de
sortie du scheduler traduit son contrat historique qui attend `succeeded` ;
elle n'annule ni le feed checkpointé, ni les raws et observations committés.

## Dry-run réel

| Mesure | Résultat |
|---|---:|
| Sources scannées | 1 000 |
| Variantes résolues par GTIN exact | 330 |
| Sources mises en quarantaine | 670 |
| Assertions projetées | 2 330 |
| Assertions `observed` | 1 000 |
| Assertions `validated` | 1 330 |
| Assertions `quarantine` | 0 |
| Collision Brand normalisée | 0 |
| Collision d'identifiant scopé | 0 |
| Contexte d'identité manquant | 0 |
| Lien Offer manquant | 0 |
| Dernier raw | 1 000 |

La quarantaine Graph correspond aux **670 offres sans GTIN**. Elle est une
abstention conforme au contrat, pas une erreur d'ingestion.

## Application et replay

| Mesure | Premier passage | Replay identique |
|---|---:|---:|
| Sources scannées | 1 000 | 1 000 |
| Résolues / quarantaine | 330 / 670 | 330 / 670 |
| Assertions créées | 2 330 | **0** |
| Assertions reconnues | 0 | **2 330** |
| Liens créés | 1 000 | **0** |
| Liens reconnus | 0 | **1 000** |
| Variantes créées | 321 | **0** |
| Collisions Brand / scoped ID | 0 / 0 | 0 / 0 |
| Contextes / liens Offer manquants | 0 / 0 | 0 / 0 |

Les **330 offres résolues** convergent vers **321 variantes** : plusieurs
offres peuvent légitimement partager le même GTIN global. Le replay à zéro
création prouve que cette convergence n'est pas une duplication accidentelle.

## État PostgreSQL après replay

| Table ou répartition | Total |
|---|---:|
| `raw_source_records` | 1 000 |
| `observations` | 10 000 |
| raws distincts observés | 1 000 |
| `graph_variants` | 321 |
| `graph_identifiers` | 321 |
| `graph_identifier_evidence` | 330 |
| `graph_offer_variant_links` | 1 000 |
| liens `resolved / exact_gtin` | 330 |
| liens `quarantine / missing_gtin` | 670 |
| `graph_identity_assertions` | 2 330 |
| assertions `observed` | 1 000 |
| assertions `validated` | 1 330 |

Les totaux ont été relus directement après le replay, dans une session sans
écriture. La révision de schéma relue dans la même session est
`b3e1a7c4d9f2`.

## Santé et isolement opérationnel

Après le replay :

- `/health/live` : `alive=true` ;
- `/health/ready` : `ready=true`, PostgreSQL `ok`, schéma attendu ;
- `/health` : application `ok`, PostgreSQL `ok`, Redis `ok` ;
- `/api/catalog/pulse` : `live=true`, synchronisation `fresh`, dernier succès
  catalogue inchangé `run 19` ;
- Railway : web, PostgreSQL et Redis `Online`, Cron sans exécution concurrente.

Les flags et limites ont été passés uniquement aux commandes concernées.
Aucune variable Railway persistante n'a été modifiée et aucune ingestion
complète n'a été déclenchée pour cette preuve.

## Limites et suite

- Ce lot porte sur 1 000 offres d'un seul feed, pas sur les quelque 190 feeds.
- L'absence de GTIN conduit volontairement à l'abstention ; Family, Model et
  MPN ne sont toujours pas inventés depuis un titre marchand.
- Le backfill effectue actuellement des vérifications ligne par ligne ; son
  débit doit être optimisé avant un backfill catalogue complet.
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` demeure explicite : seules les propriétés
  déterministes et la provenance sont qualifiées.

P1E est fermé. P1F doit maintenant rejouer les gates exact-product, rapprocher
les mesures du corpus réel avec les seuils ratifiés et vérifier la CI sans
ouvrir les lecteurs v1.
