# ADR-012 — Product Ranking v1, produit avant offre

- Statut : **accepté pour shadow**
- Date : **1er septembre 2026**
- Portée : Phase 7 Product Ranking
- Contrat : `contracts/product-ranking/v1`
- Lecteurs publics : **inchangés**

## Contexte

Hybrid Retrieval génère des candidats et Constraint Engine décide de leur
éligibilité. Le ranking doit améliorer la précision sans refaire ces décisions,
dupliquer un produit par marchand ou laisser une commission influer sur la
pertinence.

## Décision

1. Seul un candidat `ELIGIBLE` peut être classé.
2. `EXCLUDED` et `UNKNOWN` restent hors ranking, quelles que soient les préférences.
3. Need Fit, Product Quality, Value et Evidence sont des dimensions distinctes.
4. Chaque dimension doit être connue, bornée entre 0 et 1 et sourcée.
5. Une dimension absente, invalide ou conflictuelle produit `UNRANKABLE`.
6. Les poids sont figés par verticale ; aucune formule universelle n'est utilisée.
7. Le classement porte sur l'identité produit, jamais sur une ligne marchand.
8. Commission, affiliation, cashback et sélection d'offre sont hors contrat.
9. Les égalités sont déterministes et aucun contexte brut n'est persisté.
10. La gate Phase 7 reste ouverte tant qu'un benchmark humain externe n'existe pas.

## Rollback

Le writer est OFF par défaut. La migration est expand-only et l'ancien lecteur
ignore les nouvelles tables. Désactiver le flag retire immédiatement le replay
du chemin de maintenance sans modifier Constraint Engine ni le catalogue.
