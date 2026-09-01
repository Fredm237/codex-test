# FILON — Phase 5 Hybrid Retrieval Final Receipt

- Date : **1er septembre 2026**
- Verdict : **PHASE 5 = GO — OUVERTURE PHASE 6 CONSTRAINT ENGINE**
- Périmètre : **SHADOW UNIQUEMENT**
- Lecteurs publics : **INCHANGÉS**
- Migration active : `f7c5e9a1b3d6`
- Feature flag persistant : `HYBRID_RETRIEVAL_SHADOW_ENABLED=false`

## Décision

Hybrid Retrieval v1 est qualifié comme générateur de candidats product-first,
expand-only, sourcé et fail-closed. Il sépare explicitement retrieval, ranking,
sélection d'offre et décision. Cette décision ouvre Phase 6 Constraint Engine ;
elle ne promeut aucun ranking, endpoint ou lecteur public.

## Gates terminales

| Gate | Preuve | Verdict |
|---|---|---:|
| contrat | schéma v1, exemples synthétiques, requête brute interdite | **GO** |
| benchmark | 9 224 cas ; fusion : 0 mismatch, 0 failure bloquante | **GO** |
| hard negatives | legacy : 5 765 mismatches, 4 612 failures | **GO** |
| sécurité | 0 violation de contrainte, 0 faux grouping, 0 promotion semantic-only | **GO** |
| provenance | 100 % sur le holdout final | **GO** |
| migration | tête unique et production `f7c5e9a1b3d6` | **GO** |
| CI | run `33502628802`, quatre jobs verts ; Vercel vert | **GO** |
| replay | dry → create → existing, même identité | **GO** |
| données sensibles | 0 requête brute persistée ; 0 donnée utilisateur | **GO** |
| performance shadow | P50 434,591 ms ; P95 519,885 ms sur 30 dry-runs | **GO LIMITÉ** |

## Publication et production

- PR GitHub : `#395` ;
- commit `main` : `8857f16c74dfd1311f5fa3ce9f188d7085118cc4` ;
- déploiement Railway : `3c0f71a6-dc0e-4454-b05d-5e75cf798211` ;
- branche Railway canonique : `main` ;
- PostgreSQL : `ok` ; Redis : `ok` ; readiness : `true` ;
- ancienne version Phase 4 conservée comme déploiement retiré pour rollback.

La première CI a correctement détecté que l'environnement Alembic ne chargeait
pas encore les modèles Hybrid Retrieval. La fusion a été bloquée, l'import
manquant ajouté, puis la seconde exécution PostgreSQL est devenue verte. Cette
détection est une preuve du gate de dérive, pas une réussite rétroactive du run
échoué.

## Replay P5H

Fenêtre qualifiée : snapshot 184, `after_snapshot_id=183`, `limit=1`, instant
`2026-09-01T18:00:00Z`.

1. dry-run : 1 candidat, top-1 cible, 0 écriture ;
2. premier apply : 1 run et 1 candidat créés ;
3. replay identique : 1 run et 1 candidat existants, 0 création ;
4. identité inchangée :
   `sha256:6b7526f54012e7288ee1037c7969e472fe48e760197cc968972091e5ff3beb10` ;
5. contrôle physique : 1 `run_key` unique, 1 candidat, 0
   `raw_query_retained` ;
6. activation uniquement process-local ; flag persistant revenu à `false`.

## Qualification logicielle

- suite backend locale : 2 450 tests réussis, 3 ignorés ;
- suite Phase 5 ciblée : 114 tests réussis ;
- CI GitHub : backend/PostgreSQL/Quality Lab, web, mobile et extension verts ;
- arbre public initial identique bit pour bit à l'arbre local qualifié.

## Limites conservées

- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` ;
- `SINGLE_PRIMARY_PRODUCT_SHADOW_SAMPLE` : 1 seul `PRIMARY_PRODUCT` sur 330
  snapshots Variant résolus ;
- `NO_REAL_VECTOR_BACKEND` : le semantic est un proxy déterministe ;
- `NO_PUBLIC_TRAFFIC_SLO` : les latences mesurent un replay shadow de taille 1 ;
- aucune promotion du lecteur, du ranking, d'une offre ou d'un verdict.

Ces limites deviennent des axes de couverture ultérieurs. Elles ne bloquent pas
Phase 6, car Constraint Engine doit précisément conserver `UNKNOWN`, exclure les
incompatibilités prouvées et s'abstenir lorsque la vérité manque.

## Ouverture Phase 6

Phase 6 peut figer les contraintes dures, incompatibilités, préférences souples
et motifs d'exclusion. Elle doit consommer uniquement les candidats sourcés de
Phase 5, sans transformer une absence de preuve en compatibilité et sans
introduire le ranking de Phase 7.
