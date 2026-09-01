# FILON — Phase 6D/E Constraint Engine déterministe

- Date : **1er septembre 2026**
- Mode : **shadow-only**
- Version : `constraint-engine-policy/v1`
- Lecteurs publics : **inchangés**

## Surface implémentée

Le moteur évalue séparément :

- budget maximal avec montant décimal et devise atomiques ;
- pays autorisé ;
- disponibilité requise ;
- égalité d'attribut / compatibilité ;
- exclusion du contenu adulte ;
- liste d'exclusion explicite ;
- préférences factuelles sans score.

Une contrainte non satisfaite produit `EXCLUDED`. Une contrainte requise dont
la vérité est absente, invalide, conflictuelle ou non comparable produit
`UNKNOWN`. Seul un candidat dont toutes les contraintes dures sont satisfaites
devient `ELIGIBLE`.

## Séparation des responsabilités

Les préférences sont évaluées après les contraintes dures et stockées dans un
tableau distinct. Elles n'ont aucun poids, score ou rang. Même satisfaite, une
préférence ne change jamais le statut `EXCLUDED` ou `UNKNOWN` d'un candidat.
Le module ne choisit ni produit gagnant, ni offre, ni verdict Buy/Wait.

## Qualification locale

- 4 608 / 4 608 cas du holdout conformes ;
- 0 faux éligible ;
- 0 unknown favorable ;
- 0 réintroduction par préférence ;
- 100 % de provenance sur les résultats connus ;
- tests ciblés contrat, moteur, benchmark, config, migration, persistance et
  replay : **93 réussis, 3 PostgreSQL ignorés localement**.
