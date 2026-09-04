# FILON — Baseline de promotion V2

Date du snapshot : **2026-09-04T09:08:36Z** / **11:08:36 CEST**

## Verdict initial

**V2 NOT READY**

Le Core V1 demeure le seul chemin public. La chaîne V2 a une preuve bornée
`dry-run → apply → replay`, mais aucun writer continu, dark reader, canary ou
lecteur public V2 n'est actif. Le run catalogue 25 reste une ingestion réelle,
unique et productive ; aucune écriture V2 ne doit démarrer avant son état
terminal honnête.

Ce document est un snapshot read-only. Il ne vaut ni activation, ni promotion,
ni autorisation de publication.

## Sources contrôlées

- commit et historique Git locaux ;
- GitHub public `Fredm237/codex-test` et GitHub Actions ;
- sondes publiques Railway ;
- Dashboard Railway authentifié ;
- configuration effective lue dans le processus web, limitée aux modes et
  booléens non sensibles ;
- requêtes PostgreSQL strictement `SELECT`, sans payload brut ;
- état des sauvegardes Railway.

Aucune valeur secrète, requête utilisateur, identité ou offre brute n'a été
lue ou enregistrée.

## Code et déploiement

| Élément | État observé |
|---|---|
| branche GitHub par défaut | `main` |
| commit `main` | `e48529bfde73c958f15ae00e1eaff953d382fedc` |
| dernier changement | fusion PR #413, confidentialité P15–P18 et journal P18 |
| service Railway web | `Online`, 1 réplica, EU West |
| déploiement actif | `d444580f-6977-4610-83eb-4797b1ddd087` |
| origine du déploiement | commit `e48529b`, PR #413 |
| `/health/live` | HTTP 200, `alive=true` |
| `/health/ready` | HTTP 200, PostgreSQL `ok` |
| `/health` | HTTP 200, PostgreSQL et Redis `ok` |
| révision Alembic production | `b5d3f7a9c1e4` |
| mode de schéma | `alembic` |

## CI et surveillance

| Preuve | Résultat terminal |
|---|---|
| Core quality gates sur `e48529b` | run `33656618219`, **success** |
| dernier moniteur critique planifié | run `33842173919`, **success** |
| instant du dernier moniteur | `2026-09-04T05:53:23Z` |
| moniteurs précédents sur le même commit | tous verts depuis la fusion |

Une défaillance planifiée antérieure sur `5ac88c1` existe dans l'historique ;
elle n'est pas masquée, mais elle précède le déploiement actuel et les runs
ultérieurs sur `e48529b` sont terminaux et verts.

## Configuration effective

La configuration ci-dessous a été lue depuis l'objet `Settings` du processus
Railway actif. Les champs non présents dans l'environnement prennent leurs
valeurs fail-closed définies par le code déployé.

| Contrôle | Valeur effective |
|---|---:|
| `V2_CHAIN_MODE` | `off` |
| `V2_CANARY_READER_ENABLED` | `false` |
| `V2_PUBLIC_READER_ENABLED` | `false` |
| `OBSERVATION_SHADOW_ENABLED` | `false` |
| `PRODUCT_GRAPH_SHADOW_ENABLED` | `false` |
| `ENTITY_RESOLUTION_SHADOW_ENABLED` | `false` |
| `OFFER_GRAPH_SHADOW_ENABLED` | `false` |
| `OFFER_TRUTH_SHADOW_ENABLED` | `false` |
| `PRODUCT_ONTOLOGY_SHADOW_ENABLED` | `false` |
| `HYBRID_RETRIEVAL_SHADOW_ENABLED` | `false` |
| `CONSTRAINT_ENGINE_SHADOW_ENABLED` | `false` |
| `PRODUCT_RANKING_SHADOW_ENABLED` | `false` |
| `OFFER_OPTIMIZATION_SHADOW_ENABLED` | `false` |
| `CONFIDENCE_SHADOW_ENABLED` | `false` |
| `BUY_WAIT_SHADOW_ENABLED` | `false` |
| `MERCHANT_INTELLIGENCE_SHADOW_ENABLED` | `false` |
| `EVIDENCE_ENGINE_SHADOW_ENABLED` | `false` |
| `PERSONAL_COMMERCE_SHADOW_ENABLED` | `false` |
| `FILON_INTELLIGENCE_ENABLED` | `true` |
| `FASHION_EXPERT_ENABLED` | `true` |
| `OUTFIT_STUDIO_ENABLED` | `true` |

Les trois derniers drapeaux activent le chemin Intelligence historique. Ils ne
constituent ni un writer V2, ni un dark reader, ni un lecteur public V2.

## Writers, readers et tâches planifiées

| Composant | État actuel |
|---|---|
| writers V2 P0/P1–P10 | **OFF** |
| writer Personal Commerce P18 | **OFF** |
| dark reader V2 | absent du déploiement et **OFF** |
| lecteur canary V2 | absent du déploiement et **OFF** |
| lecteur public V2 | absent du déploiement et **OFF** |
| lecteur public réellement servi | Core V1 |
| Cron catalogue | un service privé, cadence normale, exécution active |
| Cron V2 continu | **absent** |

## Run catalogue 25

Lecture PostgreSQL à `2026-09-04T09:08Z` :

| Champ | Valeur |
|---|---:|
| run | `25` |
| filiation | `resumed_from_run_id=24` |
| état | `running` |
| début | `2026-09-02T18:03:39.170399Z` |
| dernier heartbeat observé | `2026-09-04T09:08:12.380406Z` |
| feeds terminés | `126` |
| feed actif | `1` |
| lignes commit des feeds terminés | `1 074 857` |
| lignes du feed courant au snapshot | `4 600` |

Le Dashboard Railway confirme une seule exécution Cron catalogue en cours. Le
heartbeat et la progression rendent une interruption accélératrice interdite.

## Volumes shadow réellement persistés

| Périmètre | Tables | Records |
|---|---|---:|
| P0 Observation | `raw_source_records` / `observations` / `quarantine_records` | `1 000 / 10 000 / 0` |
| P0 Product Graph | brands / aliases / families / models / variants | `0 / 0 / 0 / 0 / 321` |
| P0 Product Graph | identifiers / evidence / offer links | `321 / 330 / 1 000` |
| P0 Offer Graph | `graph_offer_observations` | `10` |
| P0 Merchant Intelligence | `merchant_quality_snapshots` | `1` |
| P0 Evidence | claims / eligibility | `110 / 10` |
| P1 Product Identity | `graph_identity_assertions` | `2 330` |
| P2 Entity Resolution | projections / decisions | `1 000 / 1 000` |
| P3 Offer Truth | `offer_truth_snapshots` | `1 010` |
| P4 Product Ontology | `product_ontology_snapshots` | `1 010` |
| P5 Hybrid Retrieval | runs / candidates | `9 / 1` |
| P6 Constraint Engine | runs / candidates | `9 / 1` |
| P7 Product Ranking | runs / candidates | `9 / 1` |
| P8 Offer Optimization | runs / candidates | `10 / 0` |
| P9 Confidence | runs / dimensions | `9 / 45` |
| P10 BUY/WAIT | `buy_wait_decision_runs` | `9` |
| chaîne V2 bornée | `v2_chain_executions` | `3` |
| P18 Personal Commerce | decisions / erasure receipts | `1 / 0` |

Ces volumes sont historiques et n'augmentent pas actuellement : les writers
correspondants sont OFF.

## Dernière qualification V2 en production

Trois journaux existent, tous pour la verticale `smartphones`, la fenêtre
`after_raw_id=0`, `row_limit=10`, et les treize étapes P1–P10 :

| id | mode | état | plage | identité |
|---:|---|---|---|---|
| 1 | `dry_run` | `succeeded` | `0 → 10` | `sha256:6d442…` |
| 2 | `apply` | `succeeded` | `0 → 10` | `sha256:99e25…` |
| 3 | `apply` replay | `succeeded` | `0 → 10` | `sha256:99e25…` |

L'identité partagée par les runs 2 et 3 prouve le replay borné idempotent. Elle
ne prouve ni le shadow continu, ni 30 fenêtres distinctes, ni le dark read.

## Migrations locales non publiées

La branche locale `codex/filon-v2-continuous-shadow` est propre et contient
**15 commits** au-dessus de `origin/main`, tête
`9e8aaacbe1397e30ce7e5316f35bd25d011b9995`. Elle n'existe pas sur GitHub au
snapshot. Trois migrations additives restent locales :

1. `c6f4a8b0d2e5` — observations dark reader ;
2. `d7a5b9c1e3f6` — observations canary ;
3. `e8b6c0d2f4a7` — reçus de promotion.

Le delta complet représente 61 fichiers et environ 9 348 insertions. Aucun des
trois fichiers protégés n'est modifié.

## Inventaire des 15 commits à auditer

| Commit | Objet | Statut avant audit |
|---|---|---|
| `1ca0a47` | scheduler shadow continu | REVIEW REQUIRED |
| `ca68143` | dark reader agrégé | REVIEW REQUIRED |
| `9f4c90d` | garde canary atomique | REVIEW REQUIRED |
| `ceaa13b` | lecteur canary borné à ABSTAIN | REVIEW REQUIRED |
| `9e70861` | journal de qualification canary | REVIEW REQUIRED |
| `e17f08b` | gate canary dérivé des preuves | REVIEW REQUIRED |
| `fe3990b` | gate public dérivé du canary | REVIEW REQUIRED |
| `8994e07` | reçus de promotion append-only | REVIEW REQUIRED |
| `cac4c83` | verrouillage runtime par reçu | REVIEW REQUIRED |
| `d73d352` | commande privée de promotion | REVIEW REQUIRED |
| `e943d9d` | récupération bornée des leases stale | REVIEW REQUIRED |
| `9d6e44a` | état du lease shadow | REVIEW REQUIRED |
| `f04c2d8` | tests du reçu de lease | REVIEW REQUIRED |
| `2fbeeb9` | reprise exacte des checkpoints | REVIEW REQUIRED |
| `9e8aaac` | constat run catalogue | REVIEW REQUIRED |

## Sauvegardes et restauration

| Contrôle | État |
|---|---|
| sauvegardes volume PostgreSQL | planifiées et présentes |
| dernière sauvegarde | quotidienne, environ 19 h avant le snapshot, 6,89 Go |
| sauvegardes quotidiennes antérieures | présentes et restaurables |
| sauvegarde mensuelle | présente et restaurable |
| sauvegarde manuelle pré-Core | présente et restaurable |
| prochaine sauvegarde | planifiée dans environ 4 h |
| PITR | **OFF** |
| test de restauration Phase 19.5 | non encore exécuté |

L'absence de PITR n'est pas masquée. Une restauration testée et un reçu
restent obligatoires avant canary ; activer PITR n'est pas implicitement requis
si la stratégie de restauration retenue satisfait les gates de récupérabilité.

## Kill switches

| Risque | Contrôle disponible | État observé |
|---|---|---|
| toutes écritures V2 | `V2_CHAIN_MODE=off` | actif et effectif |
| lecture canary | `V2_CANARY_READER_ENABLED=false` | actif et effectif |
| lecture publique V2 | `V2_PUBLIC_READER_ENABLED=false` | actif et effectif |
| writer P18 | `PERSONAL_COMMERCE_SHADOW_ENABLED=false` | actif et effectif |
| service V2 continu | absence de Cron V2 | effectif |
| retour public | Core V1 reste seul chemin | effectif, exercice à produire |

## État P11–P18 dans cette promotion

- P11 Web sert encore les lecteurs publics V1.
- P12 Extension conserve son transport réseau OFF.
- P13 Mobile lit le catalogue/Core V1 et garde ses gates appareil.
- P14 Fashion et les surfaces P15–P18 sont construites contre les contrats V2,
  mais ne disposent d'aucune promotion publique par ce mandat.
- P15 Wardrobe reste local appareil.
- P16 Stylist et P17 Composer n'ont pas de lecteur public V2 activé.
- P18 possède une qualification shadow bornée, un writer OFF et aucun canary.

## Blockers objectifs immédiats

1. run catalogue 25 non terminal ;
2. audit des 15 commits non terminé ;
3. branche locale non publiée et CI de ce lot inexistante ;
4. migrations dark/canary/reçus absentes de production ;
5. zéro fenêtre shadow continue sur le scheduler local ;
6. zéro observation dark réelle ;
7. zéro exercice de rollback Phase 19.5 ;
8. zéro canary ;
9. SLO publics non mesurés et non ratifiés.

Le travail sûr autorisé pendant le run 25 est l'audit, la correction locale,
les tests, la revue des migrations, l'observabilité, le rollback outillé et la
documentation. Aucune écriture production n'est nécessaire pour ces étapes.

## Addendum local après correction

Le snapshot production ci-dessus reste inchangé. Depuis sa capture, l'écart
local a ajouté une quatrième migration additive, `f9c7d1e3a5b8`, qui porte la
campagne/filiation des fenêtres, le funnel, le dual-read réel, l'éligibilité
canary et le registre append-only des preuves externes. Les gates résolvent
maintenant chaque digest vers une preuve `VERIFIED` de la portée exacte ; un
hash arbitraire ne peut plus être traité comme vert.

Qualification locale terminale : **2 770 tests backend passent, 3 sont
ignorés**, et les **3 tests PostgreSQL 16** passent. Aucun changement n'a été
publié ou appliqué à Railway ; le run catalogue 25 demeure le blocker externe
de la première fenêtre shadow.
