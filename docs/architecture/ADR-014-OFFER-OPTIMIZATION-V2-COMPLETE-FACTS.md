# ADR-014 — Offer Optimization v2, faits complets

- Date : **1er septembre 2026**
- Statut : **ACCEPTÉ — SHADOW ONLY**
- Remplace comme politique active : `offer-optimization-policy/v1`

## Décision

La politique v2 optimise une offre uniquement pour le produit classé numéro un
et exige six dimensions opérationnelles sourcées : prix, livraison, cashback,
retours, fiabilité marchand et fraîcheur. La disponibilité reste une condition
d'éligibilité explicite.

Le coût livré est calculé exactement par `prix + livraison - cashback`. Les
trois montants doivent partager la même devise. Le cashback ne peut pas excéder
le coût brut. L'objectif lexicographique est : coût livré minimal, meilleure
fiabilité, plus longue fenêtre de retour, meilleure fraîcheur, puis identifiant
d'offre stable.

## Fail-closed

- cashback inconnu ou non sourcé : `UNOPTIMIZABLE`, jamais zéro implicite ;
- retours refusés : `INELIGIBLE` ;
- retours acceptés sans période sourcée : `UNOPTIMIZABLE` ;
- conflit de devise ou cashback supérieur au coût brut : `UNOPTIMIZABLE` ;
- commission, affiliation et revenu plateforme restent hors contrat.

## Compatibilité

Les artefacts v1 et leurs éventuels reçus historiques sont conservés. La
migration `d1a9c3e5f7b0` ajoute uniquement les colonnes nécessaires au writer
v2 et renforce la contrainte de forme. Aucun lecteur public ne consomme ces
tables et tous les flags persistants restent OFF.
