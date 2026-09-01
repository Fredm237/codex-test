# FILON — Phase 7 Product Ranking Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **PHASE 7 SHADOW = GO — PHASE 8 OUVERTE**
- Gate d'entrée : Phase 6 Constraint Engine shadow terminale avec verdict GO
- Lecteurs publics : **INCHANGÉS**
- Optimisation d'offre : **HORS PÉRIMÈTRE — PHASE 8**

## Avancement

| Lot | État | Preuve attendue |
|---|---|---|
| P7A — contrat | **TERMINÉ** | ADR-012, schéma v1, manifest et exemples synthétiques |
| P7B — baseline | **TERMINÉ** | fenêtre Constraint Engine réelle bornée, limites explicites |
| P7C — benchmark | **TERMINÉ TECHNIQUEMENT** | 4 608 cas, moteur sûr PASS, contrôle legacy UNSAFE |
| P7D — moteur | **TERMINÉ** | éligibles seuls, quatre dimensions sourcées, poids par verticale |
| P7E — neutralité | **TERMINÉ** | commission et marchand absents du contrat et invariance prouvée |
| P7F — shadow | **TERMINÉ EN PRODUCTION** | migration `b9e7a1c3d5f8`, writer persistant OFF, idempotence |
| P7G — replay borné | **TERMINÉ EN PRODUCTION** | abstention sans preuve, dry/apply/replay idempotents |
| P7H — gouvernance qualité | **TERMINÉ — NON-BLOQUANT** | `AUTONOMOUS_QUALITY_LAB` + `NO_EXTERNAL_HUMAN_GROUND_TRUTH` |
| P7I — revue de sortie | **TERMINÉE — GO SHADOW** | CI, production, migration, santé, neutralité et replay qualifiés |

## Invariants

1. Le ranking ne reçoit que des candidats déclarés `ELIGIBLE` par la Phase 6.
2. `BEST PRODUCT` reste distinct de `BEST OFFER`.
3. Les dimensions sont `need_fit`, `product_quality`, `value` et `evidence`.
4. Une dimension inconnue, invalide, conflictuelle ou sans preuve rend le candidat `UNRANKABLE`.
5. Les poids sont explicites par verticale ; aucune moyenne universelle n'est admise.
6. Commission, marchand et optimisation d'offre n'entrent jamais dans le classement produit.
7. Le contexte brut et les données personnelles ne sont ni reçus ni persistés.
8. Le writer reste OFF et aucun lecteur public ne change avant la revue finale.
9. Un holdout synthétique valide des invariants techniques, pas une préférence humaine.
10. L'absence définitive d'annotation humaine externe reste documentée mais ne
    bloque jamais la progression.

## Décision terminale

La fondation a été fusionnée par la PR `#399`, déployée avec la migration
additive et qualifiée sur une fenêtre réelle d'un run et un candidat. Les trois
passages dry/apply/replay ont produit la même identité ; le replay final a
réutilisé les lignes existantes sans nouvelle écriture.

Phase 7 est **GO en shadow**. Les lecteurs publics et tous les flags shadow
persistants restent désactivés. `NOT_INDEPENDENTLY_VALIDATED` et
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` demeurent explicites. La Phase 8
peut s'ouvrir sans confondre classement produit et optimisation d'offre.
