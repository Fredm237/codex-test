# FILON — Phase 6C Constraint Engine Benchmark

- Date : **1er septembre 2026**
- Périmètre : **holdout synthétique autonome**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Évaluation sûre : `sha256:bcc0a9eaaec561163e19a8395b53ccb44eb934e7f27d563a9657358bfc3c5921`
- Contrôle négatif : `sha256:94210417524d3ec4d69032cb54012b7b1aef2f93af35db53aab7562c6bf42a39`

## Corpus

Le générateur indépendant produit 4 608 cas déterministes sur six verticales,
trois langues et six scénarios. Le corpus contient 1 584 éligibles, 2 304
exclusions, 720 unknowns requis et 720 cas centrés sur les préférences.

## Résultats

| Mesure | Constraint Engine | Simulateur préférence-first |
|---|---:|---:|
| exactitude statut | 100 % | 68,75 % |
| borne basse Wilson 95 % | 99,916704 % | 67,396549 % |
| faux éligibles | 0 | 1 440 |
| unknowns déclarés satisfaits | 0 | 720 |
| exclusions réintroduites par préférence | 0 | 720 |
| provenance complète | 100 % | 0 % |
| verdict | **PASS** | **UNSAFE** |

Le benchmark prouve sa puissance en rejetant le simulateur qui considère les
unknowns favorables et laisse une préférence réintroduire un candidat. L'oracle
n'est pas promu en vérité humaine ; il ratifie uniquement les invariants du
contrat v1.
