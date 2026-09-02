# Solution Composer v1

Le composeur Phase 17 assemble une solution structurée de type `outfit`,
`setup`, `kit` ou `routine`. Chaque rôle obligatoire reçoit exactement un
composant prouvé.

## Invariants

- un élément possédé éligible est choisi avant une offre du même rôle ;
- son coût marginal est toujours nul ;
- une offre exige les gates contraintes `ELIGIBLE`, Offer Truth `VERIFIED`, une
  preuve de non-duplication et une devise comparable ;
- une offre partielle, périmée, inconnue ou dupliquée ne complète jamais une
  solution ;
- tous les rôles obligatoires doivent être couverts ;
- le coût total doit respecter un budget explicite dans une devise unique ;
- aucune solution partielle n'est renvoyée en cas d'abstention ;
- aucun score d'utilité n'est fabriqué.

Le moteur est pur : aucune donnée personnelle brute n'est retenue, aucune table,
écriture, exposition publique ou tâche planifiée n'est ajoutée.
