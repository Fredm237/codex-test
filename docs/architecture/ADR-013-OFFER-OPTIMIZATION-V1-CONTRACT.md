# ADR-013 — Offer Optimization v1

- Date : **1er septembre 2026**
- Statut : **ACCEPTÉ — SHADOW ONLY**

## Décision

Offer Optimization est une étape séparée de Product Ranking. Elle ne reçoit que
le produit classé numéro un et sélectionne au plus une offre `VERIFIED` pour ce
produit exact.

L'objectif est lexicographique : coût total minimal, puis meilleure fiabilité
marchand prouvée, meilleure fraîcheur et identifiant d'offre stable. Aucun poids
caché n'est utilisé. Commission, affiliation, revenu plateforme, sponsorisation
et budget publicitaire sont absents du contrat.

## Fail-closed

- sans produit classé numéro un, le moteur s'abstient ;
- une offre d'un autre produit est inéligible ;
- une offre `PARTIAL`, `STALE`, `INVALID` ou `QUARANTINED` est inéligible ;
- prix, livraison, stock, fiabilité et fraîcheur doivent être connus et sourcés ;
- prix et livraison doivent partager une devise explicite ;
- aucune valeur inconnue n'est remplacée par zéro ou une moyenne.

## Conséquences

Le writer reste append-only et OFF par défaut. Aucun lecteur public ne dépend
des tables Phase 8. L'absence actuelle d'un score de fiabilité marchand prouvé
impose une abstention au replay de production ; elle ne doit pas être masquée.
