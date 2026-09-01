# FILON — Phase 6H Constraint Engine Comparison

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Limitation principale : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Lecteurs publics : **INCHANGÉS**

## Comparaison sur le holdout immuable

| Mesure | Constraint Engine fail-closed | Simulateur preference-first |
|---|---:|---:|
| cas | 4 608 | 4 608 |
| exactitude statut | 100 % | 68,75 % |
| faux éligibles | 0 | 1 440 |
| unknowns satisfaits | 0 | 720 |
| exclusions réintroduites | 0 | 720 |
| provenance complète | 100 % | 0 % |
| verdict | **PASS** | **UNSAFE** |

Le moteur sûr atteint 4 608 / 4 608 avec une borne basse Wilson de
99,916704 %. Son évaluation est
`sha256:bcc0a9eaaec561163e19a8395b53ccb44eb934e7f27d563a9657358bfc3c5921`.

## Comparaison production bornée

La production ne contient qu'un run Hybrid Retrieval qualifiable et un
candidat attaché à une offre. Cette fenêtre prouve le câblage, la persistance
et l'idempotence, pas la couverture métier générale.

Trente dry-runs identiques ont été exécutés sur cette fenêtre :

| Mesure | Résultat |
|---|---:|
| P50 | 259,595 ms |
| P95 | 265,493 ms |
| P99 | 962,904 ms |
| maximum | 962,904 ms |
| runs mesurés | 30 |

Ces chiffres qualifient uniquement la mécanique shadow sur un candidat ; ils
ne constituent pas un SLO de trafic public.

## Limites conservées

- `SINGLE_HYBRID_CANDIDATE_SHADOW_SAMPLE` ;
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` ;
- `NO_PUBLIC_TRAFFIC_SLO` ;
- `CATALOG_CRON_RECOVERY_PENDING` : le run catalogue 22 doit être récupéré par
  le mécanisme opérationnel avant toute activation persistante du Constraint
  Engine.

Ces limites interdisent une promotion du lecteur ou une activation persistante.
Elles ne bloquent pas l'ouverture de Phase 7 en shadow, qui doit consommer les
statuts et motifs sans les réécrire.
