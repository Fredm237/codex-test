# FILON — Phase 10 Buy/Wait v2 Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **QUALIFIÉ LOCAL — PUBLICATION ET PRODUCTION EN ATTENTE**
- Gate d'entrée : **Phase 9 = GO**
- Lecteurs publics : **INCHANGÉS**
- Activation persistante : **OFF**

## Objectif

Remplacer le verdict historique heuristique par une décision versionnée
`BUY_NOW | WAIT | ABSTAIN`, qualifiée par backtest temporel et incapable de
lire des observations futures.

## Lots

| Lot | État | Preuve attendue |
|---|---|---|
| P10A — baseline | ACQUIS LOCAL | inventaire du verdict v1 et des historiques exploitables |
| P10B — contrat | ACQUIS LOCAL | résultat, claims, traces, inconnues et abstention versionnés |
| P10C — politique v2 | ACQUIS LOCAL | moteur déterministe fail-closed sans prévision inventée |
| P10D — backtest | ACQUIS LOCAL | 7 200 cas, 3 600 actionnables, Wilson 0,99893407, fuite 0 |
| P10E — shadow | ACQUIS LOCAL | migration additive, writer append-only, flag OFF |
| P10F — replay | ACQUIS LOCAL | dry/apply/replay borné et idempotent sur base isolée |
| P10G — sortie | À FAIRE | reçu terminal et limites explicites |

## Invariants

1. Une décision ne consulte aucune observation postérieure à `evaluated_at`.
2. `WAIT` n'est jamais une promesse de baisse future.
3. `BUY_NOW` et `WAIT` exigent une confiance de décision calibrée et un profil
   de backtest versionné.
4. Devise, fraîcheur, stock, provenance ou historique inconnus produisent
   `ABSTAIN`.
5. Le moteur ne publie ni prix futur, ni date de baisse, ni économie garantie.
6. Le backtest sépare strictement le préfixe de décision de l'horizon futur.
7. Aucun lecteur public ou flag persistant ne change pendant la qualification.
