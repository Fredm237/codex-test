# FILON — Phase 10B Buy/Wait v2 Baseline

- Date : **1er septembre 2026**
- Verdict v1 : **KEEP AS LEGACY READER / REWRITE DECISION CORE**
- Lecteurs publics : **INCHANGÉS**

## État existant

`app/services/verdict.py` classe le prix courant par rapport au minimum et à la
moyenne d'au moins cinq relevés sur sept jours. Cette logique possède déjà de
bons garde-fous de fraîcheur, stock et devise, mais elle n'a pas de backtest
temporel indépendant et expose donc toujours `confidence=not_calibrated`.

Le verdict v1 ne doit pas être promu comme moteur Phase 10 :

- les seuils `0.95 / 1.05` ne sont pas ratifiés par un backtest ;
- le minimum historique peut sur-réagir à une observation isolée ;
- `attendre` mélange moins cher ailleurs et position de prix historique ;
- aucune identité de politique, trace ou persistance append-only ne permet une
  comparaison shadow reproductible ;
- aucune mesure de fuite temporelle n'est attachée au résultat.

## Sources admissibles v2

- sélection Offer Optimization prouvée ;
- observation de prix courante fraîche, en stock et sourcée ;
- historique de la même offre, même devise, antérieur ou égal à l'instant de
  décision ;
- `DECISION_CONFIDENCE` calibrée par un profil empirique dédié ;
- profil de backtest Buy/Wait versionné.

Toute absence reste une abstention. Phase 10 ne transforme pas le corpus
synthétique autonome en vérité commerciale de production.
