# FILON — Phase 7B Product Ranking Baseline

- Observation source : **1er septembre 2026**
- Mode : **agrégats et reçus Phase 6 uniquement**
- Schéma de production qualifié : `a8d6f0b2c4e7`
- Payload brut publié : **aucun**

## Surface Constraint Engine disponible

La fenêtre Phase 6 qualifiée contient un run Constraint Engine, un candidat et
un statut `ELIGIBLE`. Cette surface suffit à tester le câblage, l'abstention,
la persistance append-only et l'idempotence de Phase 7. Elle ne fournit aucune
des quatre dimensions de préférence et ne permet donc aucun classement produit
honnête.

| Mesure | Valeur |
|---|---:|
| runs Constraint Engine qualifiés | 1 |
| candidats persistés | 1 |
| candidats `ELIGIBLE` | 1 |
| dimensions Product Ranking prouvées | 0 / 4 |
| labels humains externes | 0 |

Le résultat attendu du replay initial est `ABSTAINED`, avec le candidat
`UNRANKABLE`. Produire un score à partir du seul prix, statut, stock ou taux de
commission serait une invention et doit échouer fermée.

Par décision fondateur, l'absence de labels humains est définitive et non
bloquante. Elle impose `NO_EXTERNAL_HUMAN_GROUND_TRUTH` et
`NOT_INDEPENDENTLY_VALIDATED`, jamais une attente de collecte future.

## Limites héritées

- `SINGLE_CONSTRAINT_CANDIDATE_SHADOW_SAMPLE` ;
- `NO_PRODUCT_RANKING_EVIDENCE_IN_PRODUCTION` ;
- `NO_EXTERNAL_HUMAN_PREFERENCE_GROUND_TRUTH` ;
- `CATALOG_CRON_RECOVERY_PENDING` pour le run catalogue 22 historique.

La dette Cron interdit une activation persistante de la chaîne shadow. Elle ne
bloque ni la conception locale du moteur, ni la migration additive, ni un
replay de maintenance strictement borné après qualification opérationnelle.
