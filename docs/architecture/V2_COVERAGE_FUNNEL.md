# FILON — Funnel de couverture V2 réel

- Campagne : `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d`
- Extraction : **2026-09-05T22:15:46Z**, interface privée Railway en lecture seule
- Fenêtres réelles : **30 `progression` réussies** (`4`, puis `6` à `34`)
- Replay audité mais exclu du volume : **exécution `5`, source `4`**
- Lignes de campagne auditées : **31**
- Curseur : **0 → 129**, monotone, contigu et sans chevauchement
- Exécutions actives, échouées ou interrompues dans la campagne : **0**

## Funnel agrégé sans sélection favorable

| Étape | Records | Part de RAW |
|---|---:|---:|
| RAW | 129 | 100,00 % |
| IDENTIFIED | 81 | 62,79 % |
| RESOLVED | 81 | 62,79 % |
| VERIFIED OFFER | 0 | 0,00 % |
| ONTOLOGY VERIFIED | 0 | 0,00 % |
| RETRIEVED | 0 | 0,00 % |
| ELIGIBLE | 0 | 0,00 % |
| RANKABLE | 0 | 0,00 % |
| OPTIMIZABLE | 0 | 0,00 % |
| CALIBRATED | 0 | 0,00 % |
| ACTIONABLE | 0 | 0,00 % |

Compteurs complémentaires : **129 scannés, 81 acceptés, 48 non résolus,
48 mis en quarantaine, 0 erreur et 81 `ABSTAIN`**. Les comptes ont été relus
directement depuis `v2_chain_executions.window_metrics_json` pour la campagne
exacte. Aucun compteur historique d'une autre campagne n'est inclus.

## Conclusion objective

Le gate mécanique de campagne est **READY** : 30 fenêtres terminales,
mono-exécution, curseur valide, replay dédupliqué et aucune erreur. La
couverture fonctionnelle est en revanche **ABSTAIN_ONLY**. Cette campagne
prouve le comportement fail-closed, pas la capacité à servir `BUY_NOW` ou
`WAIT`.

La seule promotion compatible avec cette preuve est donc un canary fermé au
type `ABSTAIN`, avec Core V1 comme bloc de repli intégral. `BUY_NOW`, `WAIT` et
une exposition publique V2 restent hors périmètre tant que leurs propres
sorties réelles n'ont pas franchi les gates ratifiées.

Évaluation déterministe :
`sha256:cda5325612b208960927d6f351d7e47aa12e6122661f115b87c0902d029f7fab`.
