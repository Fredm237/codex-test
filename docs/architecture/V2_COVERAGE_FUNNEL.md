# FILON — Funnel de couverture V2 réel (Belgique)

- Campagne : `sha256:d4160cb9a4e0aa08a9b7e3e61385fc7c31ada5f6f650a5d14b8d6fabc7109b8a`
- Extraction : **2026-09-08T19:54:54Z**, base privée Railway en lecture seule
- Portée : `BE / fr-BE / smartphones / purchase_advice`
- Fenêtres réelles : **30 `progression` réussies** (`70` à `99`)
- Replay audité mais exclu du volume : **exécution `100`, source `70`**
- Lignes de campagne auditées : **31**
- Curseur : **1277 → 1777**, monotone, contigu et sans chevauchement
- Exécutions actives, échouées ou interrompues : **0**

## Funnel agrégé sans sélection favorable

| Étape | Records | Part de RAW |
|---|---:|---:|
| RAW | 500 | 100,00 % |
| IDENTIFIED | 0 | 0,00 % |
| RESOLVED | 0 | 0,00 % |
| VERIFIED OFFER | 0 | 0,00 % |
| ONTOLOGY VERIFIED | 0 | 0,00 % |
| RETRIEVED | 0 | 0,00 % |
| ELIGIBLE | 0 | 0,00 % |
| RANKABLE | 0 | 0,00 % |
| OPTIMIZABLE | 0 | 0,00 % |
| CALIBRATED | 0 | 0,00 % |
| ACTIONABLE | 0 | 0,00 % |

Compteurs complémentaires : **500 scannés, 500 quarantaines, 0 erreur**.
Les comptes ont été relus
directement depuis `v2_chain_executions.window_metrics_json` pour la campagne
exacte. Aucun compteur d'une autre campagne n'est inclus.

## Conclusion objective

Le gate mécanique est **READY** : 30 fenêtres terminales, mono-exécution,
curseur valide, replay exact et aucune erreur. Le p95 writer de **82 325 ms**
ne respecte pas l'ancien plafond de 30 000 ms ; il respecte le plafond
background explicite de **90 000 ms**. Cette borne ne remplace pas le SLO du
lecteur : les 30 observations DARK ont un p95 V2 de **1 291 477 µs**.

La couverture fonctionnelle est **ABSTAIN_ONLY**. Le canary peut donc être
fermé au seul type `ABSTAIN`, avec Core V1 comme repli intégral. `BUY_NOW`,
`WAIT` et `FACTUAL_OPTIONS` restent bloqués jusqu'à leurs propres preuves.
