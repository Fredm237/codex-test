# FILON — Phase 7 Product Ranking Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **FONDATION SHADOW EN QUALIFICATION**
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
| P7F — shadow | **TERMINÉ LOCALEMENT** | migration `b9e7a1c3d5f8`, writer OFF, idempotence |
| P7G — replay borné | **TERMINÉ LOCALEMENT** | abstention sans preuve, dry/apply/replay idempotents |
| P7H — préférence humaine | **EN ATTENTE** | au moins 200 jugements externes indépendants |
| P7I — revue de sortie | **À FAIRE** | production shadow et gate humain avant Product Ranking GO |

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

## Séquence restante

1. Publier et faire valider la fondation par la CI complète.
2. Déployer la migration additive avec le writer persistant désactivé.
3. Exécuter un dry-run puis un apply/replay strictement bornés sur la fenêtre Phase 6.
4. Vérifier santé, schéma, idempotence et absence de modification des lecteurs publics.
5. Collecter au moins 200 jugements humains indépendants selon un protocole figé.
6. Comparer le moteur au contrôle et décider Product Ranking GO/NO-GO.
