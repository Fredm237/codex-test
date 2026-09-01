# FILON — Phase 8F Offer Optimization shadow

- Date : **1er septembre 2026**
- Migration initiale : `c0f8b2d4e6a9`
- Complément v2 : `d1a9c3e5f7b0`
- Parent v2 : `c0f8b2d4e6a9`
- Flag : `OFFER_OPTIMIZATION_SHADOW_ENABLED=false`
- Statut : **V1 DÉPLOYÉE — CORRECTION V2 PASS LOCAL**

## Expansion additive

La migration initiale ajoute `offer_optimization_runs` et
`offer_optimization_candidates`. La migration v2 ajoute `cashback_amount`,
`landed_cost` et `return_period_days`, puis renforce la contrainte de forme.
Les lignes sont append-only, reliées aux runs
Product Ranking et snapshots Offer Truth, et protégées par des identités
uniques. Les contraintes imposent au plus une sélection et interdisent la
rétention de contexte brut.

Le schéma ne possède aucune colonne de commission, taux d'affiliation, revenu
plateforme, sponsorisation ou enchère publicitaire.

Les reçus v1 restent lisibles. Toute nouvelle écriture utilise la politique v2
et exige les faits complets ; aucune ligne historique n'est réécrite.

## Replay borné

Le replay lit au plus 100 runs Product Ranking et 100 offres par run. Il exige
un instant UTC fixe et une borne `after_product_ranking_run_id`. Le dry-run
n'écrit rien ; l'apply exige le flag uniquement dans le processus de
maintenance.

La fenêtre de production initiale est une abstention Product Ranking. Le replay
Phase 8 doit donc créer au plus un reçu `ABSTAINED`, sans candidat et sans offre
sélectionnée. Si une fenêtre future contient un produit classé mais aucune
fiabilité marchand prouvée, les offres restent `UNOPTIMIZABLE`.

## Rollback

Le rollback opérationnel consiste à laisser le flag à `false`. Les lecteurs
existants ignorent les tables Phase 8. Aucun downgrade de production n'est
requis ; la migration reste réversible en environnement jetable.

## Qualification locale

Le writer a prouvé `dry-run -> apply unique -> replay existant` avec le même
`run_key` et le même `evaluation_id`. La propagation d'une abstention Product
Ranking crée un reçu sans candidat ni offre sélectionnée. La chaîne Alembic,
le head runtime et le rollback jetable passent ; le test PostgreSQL réel reste
le gate de la CI avant toute promotion.
