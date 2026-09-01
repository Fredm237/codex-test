# FILON — Phase 9 Confidence Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **EN EXÉCUTION — CONTRAT, BASELINE ET SHADOW IMPLÉMENTÉS**
- Gate d'entrée : **Phase 8 = GO**
- Lecteurs publics : **INCHANGÉS**
- Activation persistante : **OFF**

## Objectif

Calibrer séparément, sans score artificiel additif :

- Retrieval Confidence ;
- Entity Match Confidence ;
- Attribute Confidence ;
- Offer Confidence ;
- Decision Confidence ;
- Evidence Coverage.

## Lots

| Lot | État | Preuve attendue |
|---|---|---|
| P9A — contrat | IMPLÉMENTÉ | dimensions, états unknown et invariants versionnés |
| P9B — baseline | ÉTABLIE | inventaire des signaux réellement mesurables |
| P9C — corpus | IMPLÉMENTÉ | holdout autonome, stratifié et sans fuite |
| P9D — calibration | IMPLÉMENTÉ | ECE, Brier Score, accuracy par bucket |
| P9E — abstention | IMPLÉMENTÉ | confiance insuffisante sans fallback numérique |
| P9F — shadow | IMPLÉMENTÉ | migration additive, writer append-only, flag OFF |
| P9G — replay | QUALIFIÉ LOCAL | dry/apply/replay borné et idempotent |
| P9H — sortie | À FAIRE | reçu terminal et limites explicites |

## Invariants initiaux

1. Aucune confiance ne naît d'une somme arbitraire `55 + 20 + 15 + 10`.
2. Une probabilité n'est publiée que si elle est empiriquement calibrée.
3. Une dimension inconnue reste inconnue et ne reçoit pas `0.5` par défaut.
4. Evidence Coverage reste distincte de la confiance de décision.
5. Les métriques sont stratifiées par verticale, locale et classe de décision.
6. Le benchmark autonome ne devient pas une ground truth humaine externe.
7. Aucun lecteur public ou flag persistant ne change avant le reçu final.
