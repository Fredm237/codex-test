# FILON — Phase 8B Offer Optimization Baseline

- Observation source : **1er septembre 2026**
- Schéma de production qualifié : `b9e7a1c3d5f8`
- Product Ranking : **1 run, 1 candidat `UNRANKABLE`**
- Offre brute publiée : **aucune**

## Surface disponible

La fenêtre Phase 7 qualifiée ne contient aucun produit classé : elle s'est
abstenue honnêtement faute de dimensions Product Ranking prouvées. Phase 8 doit
propager cette abstention et ne peut donc sélectionner aucune offre réelle sur
la fenêtre initiale.

Offer Truth expose prix, stock, livraison et fraîcheur sous forme de claims
sourcés. Merchant Intelligence conserve des compteurs bruts, mais aucun score
de fiabilité marchand. Phase 8 ne transforme pas ces compteurs en score
synthétique : `merchant_reliability` reste inconnu tant qu'un contrat dédié ne
le prouve pas.

## Limites

- `NO_RANKED_PRODUCT_IN_PRODUCTION_SHADOW_SAMPLE` ;
- `NO_PROVEN_MERCHANT_RELIABILITY_SCORE` ;
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` ;
- `CATALOG_CRON_RECOVERY_PENDING` pour le run catalogue 22 historique.

Ces limites empêchent une sélection d'offre réelle et toute activation
persistante. Elles n'empêchent pas de qualifier le contrat, le moteur, la
persistance et un replay borné qui s'abstient.
