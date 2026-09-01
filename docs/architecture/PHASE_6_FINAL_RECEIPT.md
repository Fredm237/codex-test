# FILON — Phase 6 Constraint Engine Final Receipt

- Date : **1er septembre 2026**
- Verdict : **PHASE 6 SHADOW = GO — OUVERTURE PHASE 7 PRODUCT RANKING**
- Lecteurs publics : **INCHANGÉS**
- Activation persistante : **OFF**
- Migration active : `a8d6f0b2c4e7`

## Décision

Constraint Engine v1 est qualifié en shadow comme barrière fail-closed entre
retrieval et ranking. Il sépare contraintes dures et préférences, conserve
`UNKNOWN`, ne produit aucun score et ne réintroduit jamais un candidat exclu.

Cette décision ouvre Phase 7 Product Ranking en shadow. Elle n'autorise ni
activation persistante, ni changement de lecteur public, ni sélection d'offre,
ni verdict Buy/Wait.

## Gates terminales

| Gate | Preuve | Verdict |
|---|---|---:|
| contrat | schéma v1, ADR-011, trois exemples synthétiques | **GO** |
| benchmark | 4 608 / 4 608 ; borne Wilson 99,916704 % | **GO** |
| sécurité | 0 faux éligible, 0 unknown satisfait, 0 réintroduction | **GO** |
| provenance | 100 % sur les résultats connus | **GO** |
| migration | production `a8d6f0b2c4e7`, readiness verte | **GO** |
| CI | run `33509297177`, quatre jobs verts | **GO** |
| replay | dry → create → existing, identité stable | **GO** |
| données sensibles | 0 contexte brut, 0 donnée utilisateur | **GO** |
| performance shadow | P50 259,595 ms ; P95 265,493 ms sur 30 dry-runs | **GO LIMITÉ** |
| Cron catalogue | run 22 périmé, récupération requise | **NON-BLOQUANT SHADOW** |

## Publication et production

- PR GitHub : `#397` ;
- commit `main` : `f5c7e94b6a4a16b37e439a73d020e3035eb93689` ;
- CI GitHub : `33509297177`, Web, Backend, Extension et Mobile verts ;
- déploiement Railway : `03c49999-daf1-4386-aa21-b1ee7e3e758d` ;
- PostgreSQL : `ok` ; Redis : `ok` ; readiness : `true` ;
- flags Observation, Product Graph, Entity Resolution, Product Ontology,
  Hybrid Retrieval et Constraint Engine persistants : `false`.

## Replay P6G

Fenêtre : run Hybrid Retrieval 1, `after_run_id=0`, `limit=1`, instant
`2026-09-01T12:52:00Z`.

1. dry-run : 1 candidat `ELIGIBLE`, 0 écriture ;
2. apply : 1 run et 1 candidat créés ;
3. replay identique : 1 run et 1 candidat existants, 0 création ;
4. identité inchangée :
   `sha256:1fc80c903ecb90e5a0ce8317d2b5768931f40426208545a81bc029dc36478563` ;
5. contrôle physique : 1 run unique, 1 candidat, 0 contexte brut retenu.

## Limites et dette opérationnelle

Le run catalogue 22 est périmé et signalé `recovery_required=true`. Cette dette
reste `CATALOG_CRON_RECOVERY_PENDING` et bloque toute activation persistante du
Constraint Engine. Elle ne remet pas en cause la migration, le writer borné ou
l'ouverture de Phase 7 en shadow ; aucun nouveau run catalogue n'a été lancé
pendant la qualification.

Les limites `SINGLE_HYBRID_CANDIDATE_SHADOW_SAMPLE`,
`NO_EXTERNAL_HUMAN_GROUND_TRUTH` et `NO_PUBLIC_TRAFFIC_SLO` restent explicites.

## Ouverture Phase 7

Phase 7 peut construire un Product Ranking séparé qui consomme uniquement les
candidats `ELIGIBLE` et les motifs sourcés. Il doit conserver `EXCLUDED` et
`UNKNOWN` hors classement, ne jamais convertir une préférence en contrainte et
rester sans promotion publique jusqu'à sa propre revue terminale.
