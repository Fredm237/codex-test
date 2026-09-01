# FILON — Phase 7G Product Ranking Replay

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Version : `product-ranking-production-replay/v1`
- Migration production : `b9e7a1c3d5f8`
- Fenêtre : `after_constraint_run_id=0`, `limit=1`, verticale `smartphones`
- Instant immuable : `2026-09-01T14:57:52Z`

## Exécution bornée

Le dry-run a lu un run Constraint Engine et un candidat sans écrire. Le candidat
était éligible en entrée, mais aucune des quatre dimensions Product Ranking
n'était prouvée. Le moteur s'est abstenu : 0 candidat classé et 1 candidat
`UNRANKABLE`.

Le premier apply a créé un run et une ligne candidat. Le replay strictement
identique a reconnu les deux lignes et n'a créé aucune donnée supplémentaire.

| Passage | Runs créés | Runs existants | Candidats créés | Candidats existants |
|---|---:|---:|---:|---:|
| dry-run | 0 | 0 | 0 | 0 |
| apply | 1 | 0 | 1 | 0 |
| replay identique | 0 | 1 | 0 | 1 |

Les trois passages ont conservé la même identité d'évaluation :
`sha256:ee50be2ed145bbe499a26904612f1ce06b3b416567e2435fe88357c984904131`.

## Isolation opérationnelle

Les flags Observation, Product Graph, Entity Resolution, Product Ontology,
Hybrid Retrieval, Constraint Engine et Product Ranking ont été fournis seulement
aux deux processus d'apply. Aucun réglage Railway persistant n'a été modifié.
Après le replay, la configuration du processus web a retourné `false` pour les
sept flags.

Les lecteurs publics n'ont pas été raccordés aux tables Product Ranking. Aucun
contexte brut, donnée utilisateur, marchand, commission ou offre gagnante n'a
été introduit dans ce replay.

## État production terminal

- déploiement Railway : `a6ec2c1f-d639-43b8-a2fb-25550231dc1f` ;
- `/health/live` : 200 ;
- `/health/ready` : 200, schéma `b9e7a1c3d5f8` ;
- `/health` : 200, PostgreSQL et Redis `ok` ;
- CI `main` : run `33522393220`, quatre jobs verts.

Le journal catalogue conserve le run 22 périmé, l'état global `interrupted` et
`recovery_required=true`. Aucun run catalogue n'a été lancé, arrêté ou modifié
pendant P7G. Cette dette interdit l'activation persistante de la chaîne shadow,
mais ne bloque pas la qualification du replay borné.
