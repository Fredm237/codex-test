# ADR-015 — Confidence v1 par calibration empirique

- Décision : **ACCEPTÉE**
- Date : **2 septembre 2026**
- Portée : **Phase 9 shadow uniquement**

## Décision

FILON représente séparément cinq probabilités : Retrieval, Entity Match,
Attribute, Offer et Decision Confidence. Une probabilité est disponible
uniquement lorsqu'un score source prouvé rencontre un bucket d'un profil
empirique dédié, dont la fréquence observée, le support, ECE, Brier et la
provenance sont conservés.

Evidence Coverage est un ratio `observé / requis`. Ce ratio mesure la
complétude des preuves ; il ne prédit pas la justesse et ne peut jamais devenir
une confiance de décision.

## Conséquences fail-closed

- aucun profil : `UNKNOWN`, probabilité `null` ;
- provenance absente : `INVALID`, probabilité `null` ;
- support du bucket insuffisant : `INSUFFICIENT_SUPPORT`, probabilité `null` ;
- bucket absent : `INVALID`, probabilité `null` ;
- Decision Confidence absente : elle n'est jamais déduite des quatre autres ;
- aucune somme, moyenne, pondération arbitraire ou valeur `0.5` par défaut.

Les profils du benchmark synthétique servent à tester le mécanisme. Ils ne
sont pas des profils de production et ne sont jamais promus par le replay.

## Gouvernance

Le Quality Lab autonome est un gate d'ingénierie, sous la limitation
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING`. La qualité subjective reste
`NOT_INDEPENDENTLY_VALIDATED`. Aucun lecteur public n'est ajouté.
