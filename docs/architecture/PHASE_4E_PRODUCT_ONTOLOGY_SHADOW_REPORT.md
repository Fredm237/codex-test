# FILON — Phase 4E Product Ontology Shadow Report

- Date : **1er septembre 2026**
- Statut : **PASS LOCAL ET PRODUCTION — P4F QUALIFIÉE**
- Révision : `e6b4d8f0a2c5`
- Table : `product_ontology_snapshots`
- Writer : `app.product_ontology.replay`
- Flag : `PRODUCT_ONTOLOGY_SHADOW_ENABLED=false` par défaut
- Lecteurs publics : **INCHANGÉS**

## Verdict

P4E ajoute une table append-only et un replay borné, sec par défaut. La
migration est expand-only : elle ne modifie aucune table Core/Graph existante,
n'active aucun writer et ne déclenche aucun replay.

La persistance exige Observation, Product Graph et Entity Resolution. Couper
le flag est le rollback opérationnel ; les assertions et les données Core
restent conservées.

## Schéma et invariants

Chaque ligne conserve :

- digest SHA-256 du snapshot contractuel ;
- raw, offre et Variant nullable ;
- statut `VERIFIED`, `PARTIAL`, `QUARANTINED` ou `INVALID` ;
- classification, rôle, attributs, relations, facettes et mapping legacy JSON ;
- raisons, versions de projection/policy et horloges observée/évaluée.

Les contraintes SQL refusent un digest mal formé, un statut hors roster et
une quarantaine liée à une Variant. L'unicité
raw/version/policy/instant empêche deux vérités concurrentes pour la même
évaluation.

## Idempotence et performance

Le replay exige `--evaluated-at` avec timezone. Même raw + mêmes versions +
même instant doit produire le même digest et retourne `existing`. Toute
divergence échoue fermée ; un nouvel instant crée un nouveau snapshot.

Contrairement au writer P3 initial, P4E précharge en une requête tous les
snapshots existants de la fenêtre et insère le nouveau lot en une transaction.
Cette structure garde la preuve d'idempotence sans imposer une lecture SQL par
raw.

## Preuves locales

| Suite | Résultat |
|---|---:|
| contrat + extracteur + benchmark Product Ontology | 41 PASS |
| configuration + migration + replay | 111 PASS avec recouvrement |
| migration / drift SQLite | PASS |
| suite backend complète | 2 401 PASS, 3 SKIP |

La suite complète a d'abord produit 2 400 PASS, 3 SKIP et un unique échec
d'environnement : le bac à sable local refusait l'ouverture du récepteur OTLP
sur `127.0.0.1`. Le même test de transport, relancé isolément avec l'accès
loopback attendu par sa spécification, a terminé à 1 PASS. Aucun échec produit
ou Product Ontology ne subsiste dans cette qualification locale.

Les tests prouvent : flag off, dépendances de flags, dry-run sans écriture,
fenêtre ≤ 10 000, premier apply, second apply identique, nouvel instant
append-only, refus d'une source modifiée et chargement isolé des modèles.

## Commande de qualification

```bash
python -m app.product_ontology.replay \
  --evaluated-at <UTC_ISO_8601> \
  --after-raw-id 0 \
  --limit 1000
```

Après revue du dry-run, la même commande avec `--apply` est autorisée seulement
dans un processus de maintenance portant les trois flags prérequis et
`PRODUCT_ONTOLOGY_SHADOW_ENABLED=true`. Le timestamp doit rester identique pour
le replay idempotent.

## Décision P4E

P4E et P4F sont qualifiés. La CI PostgreSQL `33493822607`, la révision
production `e6b4d8f0a2c5` et le triplet dry-run / apply / replay idempotent sont
terminaux. Sur 1 000 projections, le premier apply a créé 1 000 snapshots et
le second en a reconnu 1 000 sans création.

Le [reçu final Phase 4](PHASE_4_FINAL_RECEIPT.md) conserve les compteurs,
l'identifiant d'évaluation, les déploiements et les limites de couverture. Les
lecteurs publics et les variables Railway persistantes restent inchangés.
