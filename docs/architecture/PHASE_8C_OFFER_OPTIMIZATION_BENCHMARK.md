# FILON — Phase 8C Offer Optimization Benchmark

- Mode : **AUTONOMOUS_QUALITY_LAB**
- Corpus : **4 608 cas synthétiques déterministes et adversariaux**
- Validation humaine externe : **NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING**
- Statut local : **PASS — RATIFICATION CI RESTANTE**
- Évaluation : `sha256:bdf9c048e9c8d082cf9ffb987411a2d9af3bce9fbdfc987db48c588fd935ca99`

## Couverture

Le holdout couvre six verticales, trois locales, huit seeds et six scénarios :
objectif exact, livraison inconnue, offre périmée, rupture de stock, mutation de
commission et stabilité des égalités.

Les gates exigent : exactitude avec borne Wilson 95 % supérieure au seuil,
zéro offre inéligible sélectionnée, zéro inconnue sélectionnée, zéro variation
sous mutation de commission et provenance complète.

Le contrôle legacy mélange valeur utilisateur et commission, accepte les
inconnues et ne respecte pas les exclusions. Il doit rester `UNSAFE`.

## Reçu local

- 4 608 sélections exactes sur 4 608 ;
- borne Wilson 95 % : `0.99916704` ;
- 864 cas avec livraison inconnue ;
- 1 440 cas contenant une offre inéligible ;
- 720 mutations de commission ;
- zéro inconnue ou offre inéligible sélectionnée ;
- zéro variation sous mutation de commission ;
- provenance des sélections : `1.0`.

La preuve est technique et synthétique. Elle ne devient pas une préférence
humaine indépendante : `NOT_INDEPENDENTLY_VALIDATED` reste explicite et non
bloquant.
