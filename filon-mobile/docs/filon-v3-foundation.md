# FILON Intelligence Layer — fondation V3

> **Auditer le Core avant toute extension. Ne jamais le modifier ni supposer une donnée qu’il ne fournit pas.**

## Frontière d’interface

| Flux | Contrat | Règle |
|---|---|---|
| Core → Intelligence | `V3CoreOffer` | Identifiant, prix, disponibilité, marchand, image et lien sont copiés comme preuves ; `null` reste inconnu. |
| Intelligence interne | Produit enrichi, style, intention, relation, recommandation, feedback et benchmark. | Toute valeur dérivée porte un statut de preuve, une confiance, une source et une explication. |
| Intelligence → Core | Identifiants d’offre, ordre, raisons, scores et trace. | Le Core conserve catalogue, recherche, prix, commerce, affiliation et alertes. |

## Pipeline normatif

`INTENT → CONSTRAINTS → RETRIEVAL → FILTERING → UNDERSTANDING → COMPOSITION → CRITIC → RANKING → OPTIMIZATION → CONFIDENCE → RESPONSE`

Chaque étape conserve un état `completed`, `skipped` ou `abstained` et un motif. Les offres non disponibles ou à lien non sûr sont exclues avant la composition. Une incertitude de prix, promotion, livraison ou cashback reste inconnue.

## Validation et apprentissage

Les préférences, feedbacks et corrections restent locaux, bornés et réversibles. Les données synthétiques servent uniquement aux tests ; tout entraînement futur exige des données autorisées, des annotations humaines, un versioning et une validation explicite.
