# ADR-003 — Offer Graph evidence shadow

- Statut : **proposed / implémenté en shadow local**
- Date : 30 août 2026
- Révision expand : `c6a1d4e8f2b3`
- Projection : `awin-offer-graph-v1`

## Contexte

Le Core v1 stocke l'offre courante et ses relevés de prix, tandis que le store
Observation conserve déjà la provenance champ par champ. Il manquait une
projection append-only qui relie explicitement identité, argent, stock et lien
marchand sans rendre une valeur inconnue favorable.

## Décision

1. `graph_offer_observations` est ajoutée sans modifier `offers`,
   `price_snapshots` ni les endpoints v1.
2. Un relevé est unique par raw source et version de projection. Le replay
   n'écrase jamais une preuve antérieure.
3. L'argent est un couple atomique `Numeric(20,6)` + devise normalisée. Si un
   membre manque ou est invalide, les deux colonnes restent `NULL`.
4. La disponibilité est `in_stock`, `out_of_stock` ou `unknown` ; aucun défaut
   positif n'existe.
5. Un lien marchand connu doit être HTTPS, sans credentials, port exotique,
   littéral IP ni hôte local/réservé.
6. Une identité variante non résolue place d'abord l'offre en `quarantine`.
   Une identité résolue reste `unknown` ou `ineligible` si prix, devise, stock
   ou lien sont insuffisants.
7. `OFFER_GRAPH_SHADOW_ENABLED=true` exige
   `OBSERVATION_SHADOW_ENABLED=true`. Le writer possède son savepoint et son
   échec ne peut annuler ni Core v1, ni Observation, ni Product Graph.
8. Le backfill est dry-run par défaut, borné à 10 000 raws, ordonné par ID et
   idempotent. Aucun backfill n'est lancé par Alembic.

## Conséquences

- Le shadow peut mesurer la couverture des preuves sans devenir une nouvelle
  source publique.
- Shipping reste `unknown` en v1 : aucune gratuité ni total livré n'est
  déduit.
- L'éligibilité technique n'est ni une recommandation, ni une calibration,
  ni un GO. Le holdout humain et la policy de claim eligibility restent requis.

## Rollback

Couper `OFFER_GRAPH_SHADOW_ENABLED`. Conserver le schéma et les observations.
Le downgrade structurel est réservé aux bases éphémères ou à une restauration
explicitement sauvegardée.
