# FILON — Page Product Observation v1

Ce contrat transporte une observation de fiche produit depuis l'extension vers
le Core. Il ne contient ni HTML, ni cookie, ni référent, ni identifiant de
personne. L'envoi exige une action explicite de l'utilisateur.

## Invariants

1. L'URL est limitée à `https://hôte/chemin` : identifiants, requête et fragment
   sont supprimés avant transport.
2. Seuls les champs Product JSON-LD autorisés sont projetés. Le bloc JSON-LD
   brut n'est jamais transmis.
3. Un montant n'est connu qu'avec une valeur positive et une devise ISO 4217
   explicite.
4. Un GTIN doit avoir une longueur normalisée valide et passer son checksum.
5. Une disponibilité non reconnue reste `unknown`.
6. Le Core décide de l'identité et de la comparaison ; l'extension ne contient
   aucun moteur de ranking, BUY/WAIT ou recommandation.
7. Un même payload à la même date d'observation possède une clé de replay
   déterministe et ne crée pas deux preuves.

## Fichiers

- `page-product-observation.schema.json` : requête envoyée au Core ;
- `page-product-observation-result.schema.json` : accusé et résolution ;
- `examples/exact-product.json` : produit à GTIN exact ;
- `examples/partial-product.json` : produit partiel, sans prix inventé.
