# FILON — Rapport P0.2 Autonomous Quality Lab

- Date : **31 août 2026**
- Décision : **P0.2 terminé**
- Statut : `AUTONOMOUS_QUALITY_LAB`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Immersive : **gate inchangée, toujours NO-GO**

## Décision fondatrice et historique

Le prérequis v0.5 de deux annotateurs humains et d'une adjudication externe est
remplacé par décision fondateur. Il n'est pas déclaré satisfait et son reçu
historique conserve `ready=false` avec zéro cas. Cette limite n'est désormais
plus une condition de progression.

La gate active mesure ce qui possède un oracle autonome et laisse le reste
explicitement provisoire ou non résolu. Elle ne contient aucune étiquette
présentée comme validée humainement.

## Preuves livrées

- manifeste `autonomous-quality-manifest/v1` ;
- holdout adversarial `filon-adversarial-holdout/v1`, trois seeds et 24
  échantillons par seed ;
- golden set historique conservé comme `REGRESSION_GROUND_TRUTH` ;
- checksums GTIN/EAN, identité exacte, rattachement exact, non-fusion de
  variantes stockage/couleur, identifiants invalides ou contradictoires ;
- prix, devise, stock tri-state, fraîcheur, budget et livraison inconnue ;
- concordance multi-source avec `SOURCE_COUNT`, `SOURCE_AGREEMENT` et
  `SOURCE_CONFLICT` ;
- conflit explicitement `UNRESOLVED` ;
- juge modèle désactivé car aucun check bloquant n'en dépend ;
- rapport atomique avec identité SHA-256 stable.

## Résultat local courant

| Mesure | Résultat |
|---|---:|
| Contrôles autonomes | **571/571** |
| Échecs bloquants | **0** |
| Conflits correctement non résolus | **1** |
| Tests du laboratoire autonome | **7/7** |
| Lot ciblé heartbeat + migrations + funnel + Quality | **80/80** |
| Suite backend complète | **2 142 réussis + 3 ignorés localement** |
| Transport OTLP loopback isolé hors sandbox | **1/1** |
| Verdict P0.2 | **PASS** |

Identité de l'évaluation autonome courante :
`sha256:d0d58f2073109852d0e7d6e2a976a9ea72cc4cf7458c229307a4114aecd1f7c2`.

Les dimensions de pertinence perçue, style et goût portent `PROVISIONAL` et
`NOT_INDEPENDENTLY_VALIDATED`. Elles ne fournissent aucune précision humaine et
ne bloquent pas Phase 0.

## Gate CI

GitHub Actions conserve deux artefacts :

1. le reçu historique externe, non bloquant et toujours non prêt ;
2. le rapport autonome strict, bloquant sur toute régression objective ou
   intégrité invalide.

Une requalification distante est encore requise avant de déclarer P0.7 vert
sur ce nouveau contrat. P0.2 est néanmoins techniquement fermé localement ;
aucun annotateur ne sera redemandé.
