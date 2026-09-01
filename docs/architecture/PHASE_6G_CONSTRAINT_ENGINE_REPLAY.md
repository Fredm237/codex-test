# FILON — Phase 6G Constraint Engine Replay

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Version : `constraint-engine-production-replay/v1`
- Migration production : `a8d6f0b2c4e7`
- Fenêtre qualifiée : `after_run_id=0`, `limit=1`
- Instant immuable : `2026-09-01T12:52:00Z`

## Exécution bornée

Le dry-run a lu un run Hybrid Retrieval et un candidat, sans écriture. Le
candidat a été classé `ELIGIBLE` ; aucune exclusion ni valeur `UNKNOWN` n'a été
inventée.

Le premier apply a créé un run et une évaluation candidat. Le replay strictement
identique a reconnu ces deux lignes et n'en a créé aucune nouvelle.

| Passage | Runs créés | Runs existants | Candidats créés | Candidats existants |
|---|---:|---:|---:|---:|
| dry-run | 0 | 0 | 0 | 0 |
| apply | 1 | 0 | 1 | 0 |
| replay identique | 0 | 1 | 0 | 1 |

L'identité est restée stable sur les trois passages :
`sha256:1fc80c903ecb90e5a0ce8317d2b5768931f40426208545a81bc029dc36478563`.

## Contrôle physique

- 1 ligne `constraint_evaluation_runs` et 1 `run_key` distinct ;
- 1 ligne `constraint_candidate_evaluations`, statut `ELIGIBLE` ;
- 0 ligne avec `raw_context_retained=true` ;
- aucun score, profil personnel ou payload brut persisté ;
- tous les flags shadow persistants sont restés `false`.

Les flags prérequis ont été activés uniquement dans le processus de maintenance.
Deux tentatives préalables ont été refusées avant écriture par les gardes de
configuration tant que la chaîne shadow complète n'était pas déclarée. Ce
comportement confirme le fail-closed de l'orchestration.

## État production

- déploiement Railway : `03c49999-daf1-4386-aa21-b1ee7e3e758d` ;
- `/health/live` : 200 ;
- `/health/ready` : 200, schéma `a8d6f0b2c4e7` ;
- `/health` : 200, PostgreSQL et Redis `ok`.

Le run catalogue 22 restait historiquement marqué `running`, mais son heartbeat
était périmé et le journal public le classait `recovery_required=true` avec un
état global `interrupted`. Aucun second run catalogue n'a été déclenché ou
modifié pendant P6G.
