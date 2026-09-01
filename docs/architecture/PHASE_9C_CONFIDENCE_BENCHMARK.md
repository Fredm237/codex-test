# FILON — Phase 9C Confidence Benchmark

- Mode : **AUTONOMOUS_QUALITY_LAB**
- Corpus : **18 000 prédictions synthétiques déterministes**
- Dimensions : **5**
- Verticales/locales : **6 / 3**
- Validation humaine externe : **NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING**
- Statut : **PASS LOCAL ET CI**
- Évaluation locale : `sha256:dd531d9488c81b2cdf0088cbdd1ed13d6b195818d3ab3b333331ba9af22341ea`

## Méthode

Le holdout construit cinq buckets de probabilité (`0.1`, `0.3`, `0.5`, `0.7`,
`0.9`) dont les fréquences positives sont exactement connues, sur quatre seeds.
Il exécute le moteur réel pour chaque dimension et mesure :

- Expected Calibration Error ;
- Brier Score ;
- exactitude par bucket de confiance ;
- support minimum par bucket ;
- provenance des probabilités ;
- promotion interdite d'un unknown ;
- synthèse interdite de Decision Confidence.

Gates ratifiés : ECE `<= 0.001`, Brier `<= 0.171`, support par bucket
`>= 3 500`, zéro unknown promu, zéro confiance décisionnelle synthétique et
provenance complète.

Le corpus est une preuve d'implémentation et de métriques, pas un calibrateur de
production. Ses profils ne sont jamais chargés par le replay production.

## Reçu local

- 18 000 prédictions ;
- 3 600 cas dans chacun des cinq buckets ;
- ECE `0.0` ;
- Brier `0.17` ;
- exactitude par bucket : `0.9`, `0.7`, `0.5`, `0.7`, `0.9` ;
- zéro unknown promu ;
- zéro Decision Confidence synthétique ;
- provenance `1.0` ;
- tous les gates d'ingénierie verts.

## Reçu CI

- run Phase 9 `33539976041` : backend, web, mobile et extension verts ;
- étape dédiée `Exécuter la calibration Confidence ECE Brier et buckets` :
  verte ;
- run correctif catalogue `33541923961` : les quatre jobs sont de nouveau
  terminaux et verts, y compris les régressions et ce benchmark.
