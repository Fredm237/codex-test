# FILON — Phase 9 Confidence Final Receipt

- Date : **1er septembre 2026**
- Verdict : **PHASE 9 = GO**
- Contrat : `confidence/v1`
- Migration production : `e2b0d4f6a8c1`
- Merge Phase 9 : `a71ee1e144c443d21d4012ec7028bb3f1cd8f5e8`
- Merge correctif catalogue : `5c667814bcc97d2b02b719113ddb67e94b5f8388`
- CI Phase 9 : run `33539976041`, quatre jobs verts
- CI correctif : run `33541923961`, quatre jobs verts
- Déploiement Phase 9 : `2f71f2d9-62ab-4c78-8f7c-73f07d04c2db`
- Déploiement qualifié final : `efecb8b2-27ea-4ddb-a250-93ea2fc10ae3`
- Lecteurs publics Confidence : **AUCUN**
- Flags persistants : **TOUS OFF**

## Décision

Phase 9 est fermée sur une fondation Confidence séparée par dimension,
empiriquement testable et fail-closed. Retrieval, Entity Match, Attribute,
Offer et Decision Confidence ne reçoivent une probabilité que depuis un profil
calibré avec support et provenance. Evidence Coverage reste un fait distinct.
Une dimension non prouvée reste `UNKNOWN` et aucune valeur `0.5` ou score
additif artificiel n'est synthétisé.

Cette décision qualifie l'ingénierie shadow et non une calibration commerciale
de production. Le replay réel s'est correctement abstenu parce qu'aucun profil
empirique de production n'est encore ratifié.

## Déploiement et schéma

Le déploiement Phase 9 est terminalement réussi et les logs prouvent l'upgrade
PostgreSQL `d1a9c3e5f7b0 -> e2b0d4f6a8c1`. Après le déploiement final :

- `/health/live` : HTTP 200, application vivante ;
- `/health/ready` : HTTP 200, schéma `e2b0d4f6a8c1`, PostgreSQL sain ;
- `/health` : HTTP 200, PostgreSQL et Redis sains ;
- service web : `Online` ;
- Cron catalogue : `Ready`, cadence normale ;
- aucune ingestion concurrente observée au moment du replay.

Les tables `confidence_calibration_runs` et
`confidence_dimension_records` sont additives, append-only et ignorées par les
lecteurs existants.

## Qualification production bornée

Fenêtre fixe :

- `evaluated_at=2026-09-01T18:20:00Z` ;
- `after_offer_optimization_run_id=0` ;
- `limit=1` ;
- source traitée : Offer Optimization run `1` ;
- replay : `confidence-production-replay/v1` ;
- évaluation :
  `sha256:a3cf51e1e17c1b13649dfda635308878e845ab2d5cd11dc2a47728b7cdd55947`.

| Étape | Sources scannées | Runs créés | Runs existants | Dimensions créées | Dimensions existantes | Issue |
|---|---:|---:|---:|---:|---:|---|
| dry-run | 1 | 0 | 0 | 0 | 0 | `ABSTAINED`, 5 `UNKNOWN` |
| apply unique | 1 | 1 | 0 | 5 | 0 | `ABSTAINED`, 5 `UNKNOWN` |
| replay identique | 1 | 0 | 1 | 0 | 5 | `ABSTAINED`, 5 `UNKNOWN` |

Les trois passages ont le même identifiant d'évaluation. Le replay identique
n'a créé aucune ligne. Après l'opération, les onze flags shadow de la chaîne
Observation → Confidence ont été relus à `false`. Les valeurs `true` requises
pour l'apply étaient limitées au processus de maintenance et n'ont jamais été
persistées dans Railway.

## Qualité et calibration autonome

- corpus déterministe : **18 000 prédictions** ;
- support : **3 600 cas par bucket** ;
- ECE : **0.0** ;
- Brier Score : **0.17** ;
- exactitude par bucket : `0.9`, `0.7`, `0.5`, `0.7`, `0.9` ;
- inconnues promues : **0** ;
- Decision Confidence synthétiques : **0** ;
- provenance : **1.0** ;
- tests backend qualifiés : **2 543** ;
- tests ciblés après correctif : **44**, puis **97** régressions catalogue ;
- backend, web, mobile et extension : **verts** sur les deux runs CI.

## Incident catalogue corrigé pendant la qualification

La première qualification du déploiement a révélé un HTTP 500 réel sur
`/api/catalog/highlights`. La cause terminale était un plan PostgreSQL parallèle
épuisant la mémoire partagée du conteneur (`DiskFullError` sur `/dev/shm`), et
non la migration Confidence.

Le correctif PR #407 applique
`SET LOCAL max_parallel_workers_per_gather = 0` à la seule transaction de cet
endpoint. Il ne modifie aucune configuration PostgreSQL globale. Le déploiement
`efecb8b2-27ea-4ddb-a250-93ea2fc10ae3` est terminalement réussi et l'endpoint
répond de nouveau HTTP 200 avec trois sections réelles.

## Limites conservées

- aucun profil empirique de production n'est encore ratifié ;
- les cinq dimensions du replay production restent donc inconnues ;
- le corpus autonome est une preuve d'implémentation, pas une vérité terrain
  humaine indépendante ;
- validation humaine externe :
  `NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` ;
- dimensions subjectives : `NOT_INDEPENDENTLY_VALIDATED` ;
- aucun lecteur public Confidence et aucun flag persistant ne sont activés par
  ce reçu.

Ces limites sont explicites et expliquent l'abstention. Elles ne remettent pas
en cause l'intégrité, le fail-closed, l'idempotence, la récupérabilité ou la
compatibilité nécessaires à la fermeture de Phase 9.

## Passage

**PHASE 9 = GO.**
