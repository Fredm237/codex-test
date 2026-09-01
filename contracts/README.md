# FILON Contract Registry

Ce répertoire est la source versionnée des formes échangées entre le core et ses clients. Il ne remplace pas encore la génération des SDK ; il fige la baseline nécessaire pour l'introduire sans casser les surfaces existantes.

Règles :

- une modification compatible ajoute un champ facultatif ou élargit explicitement un état inconnu ;
- retirer, renommer, rendre obligatoire ou changer la sémantique d'un champ exige une nouvelle version majeure ;
- `null` signifie « non observé ou non fourni », jamais zéro, gratuit ou disponible ;
- les exemples font partie de la compatibility suite ;
- les montants restent des nombres dans v1 pour décrire l'existant. Le passage à `Money` décimal appartient à v2 et nécessitera un adaptateur.

Versions actives :

- contrats clients publics : [`v1`](v1/README.md) ;
- contrats internes Product Identity shadow :
  [`product-identity/v1`](product-identity/v1/README.md) ;
- contrats internes Entity Resolution shadow :
  [`entity-resolution/v1`](entity-resolution/v1/README.md) ;
- contrats internes Offer Truth shadow :
  [`offer-truth/v1`](offer-truth/v1/README.md) ;
- taxonomie d'erreurs produit interne :
  [`taxonomies/v1`](taxonomies/v1/README.md).
