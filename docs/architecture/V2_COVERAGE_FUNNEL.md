# V2 Coverage Funnel

Statut : **PENDING — aucune fenêtre Phase 19.5 n'a encore été lancée en production.**

Ce document est volontairement incomplet tant que le run catalogue 25 reste
actif et que les 30 fenêtres réelles, distinctes, terminales et contiguës ne
sont pas persistées. Aucun compteur historique P1→P10 n'est recyclé comme
preuve de cette campagne.

Le générateur `app.v2_chain.coverage_funnel` agrège sans sélection favorable
les seules exécutions `progression` ou `recovery` ; un `replay` est visible
dans le nombre de lignes auditées mais ne compte jamais comme fenêtre ou
volume supplémentaire :

`RAW → IDENTIFIED → RESOLVED → VERIFIED OFFER → ONTOLOGY VERIFIED → RETRIEVED → ELIGIBLE → RANKABLE → OPTIMIZABLE → CALIBRATED → ACTIONABLE`.

Il conserve également le nombre d'exécutions actives, échouées et
interrompues. Le verdict ne peut devenir `READY` que si au moins 30 fenêtres
valides sont présentes, qu'aucune n'est active, que les curseurs sont contigus
et que les comptages restent monotones.

Le tableau chiffré et son identité d'évaluation seront remplacés ici depuis le
journal de la campagne réelle. Jusqu'alors, le verdict demeure :

`V2 NOT READY`.
