# FILON — Phase 8C Offer Optimization Benchmark

- Mode : **AUTONOMOUS_QUALITY_LAB**
- Corpus : **5 760 cas synthétiques déterministes et adversariaux**
- Validation humaine externe : **NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING**
- Statut local : **PASS — RATIFICATION CI RESTANTE**
- Évaluation : `sha256:7fa3254c26e3b700aba213bb2945f966081afdab88886e21c32c6b55e62192b6`

## Couverture

Le holdout v2 couvre six verticales, trois locales, huit seeds et dix
scénarios : objectif exact, livraison inconnue, cashback inconnu, retours
inconnus, devise cashback contradictoire, offre périmée, rupture de stock,
retours refusés, mutation de commission et stabilité des égalités.

Les gates exigent : exactitude avec borne Wilson 95 % supérieure au seuil,
zéro offre inéligible sélectionnée, zéro inconnue sélectionnée, zéro variation
sous mutation de commission et provenance complète.

Le contrôle legacy mélange valeur utilisateur et commission, accepte les
inconnues et ne respecte pas les exclusions. Il doit rester `UNSAFE`.

## Reçu local

- 5 760 sélections exactes sur 5 760 ;
- borne Wilson 95 % : `0.99933352` ;
- 2 304 cas inconnus ou contradictoires ;
- 1 728 cas contenant une offre inéligible ;
- 576 mutations de commission ;
- zéro inconnue ou offre inéligible sélectionnée ;
- zéro variation sous mutation de commission ;
- provenance des sélections : `1.0`.

La preuve est technique et synthétique. Elle ne devient pas une préférence
humaine indépendante : `NOT_INDEPENDENTLY_VALIDATED` reste explicite et non
bloquant.
