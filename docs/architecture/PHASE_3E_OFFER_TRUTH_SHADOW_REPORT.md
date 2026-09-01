# FILON — Phase 3E Offer Truth Shadow Report

- Date : **1er septembre 2026**
- Statut : **PASS LOCAL — PRÊT POUR MIGRATION CONTRÔLÉE**
- Révision : `d5a3c7e9f1b4`
- Table : `offer_truth_snapshots`
- Writer : `app.offer_truth.replay`
- Flag : `OFFER_TRUTH_SHADOW_ENABLED=false` par défaut
- Lecteurs publics : **INCHANGÉS**

## Verdict

P3E ajoute une seule table append-only et un replay borné, sec par défaut. La
migration est expand-only : elle ne modifie aucune table Core/Graph existante,
n'active aucun writer et ne déclenche aucun replay.

La persistance est isolée par un flag dédié qui exige Observation, Product
Graph, Entity Resolution et Offer Graph. Couper ce flag est le rollback
opérationnel ; les snapshots et les données Core restent conservés.

## Contrat d'idempotence temporelle

Le replay exige `--evaluated-at` avec timezone. Ce choix évite deux erreurs :

1. utiliser implicitement l'heure de la machine et produire un snapshot
   différent au second passage ;
2. figer à jamais la fraîcheur sur l'heure d'observation.

Même raw + mêmes versions + même instant d'évaluation doit produire le même
digest et retourne `existing`. Toute divergence échoue fermée. Un autre instant
crée volontairement un nouveau snapshot append-only, ce qui permet d'observer
le passage de fresh à stale sans réécrire l'histoire.

## Schéma

Chaque ligne conserve :

- digest SHA-256 du snapshot contractuel ;
- raw, offre, Variant nullable et marchand ;
- statut `VERIFIED`, `PARTIAL`, `STALE`, `INVALID` ou `QUARANTINED` ;
- claims et raisons JSON sous contrat v1 ;
- versions de projection et policy ;
- horodatages d'observation et d'évaluation.

Les contraintes SQL interdisent notamment une quarantaine avec Variant ou un
statut non quarantiné sans Variant. Les index restent dédiés au shadow.

## Preuves locales

| Suite | Résultat |
|---|---:|
| contrat + benchmark + extracteurs Offer Truth | 63 PASS |
| replay + configuration | 62 PASS |
| migration, backup/restore et drift SQLite | 13 PASS |

Les tests prouvent : dry-run sans écriture, fenêtre ≤ 10 000, premier apply,
second apply identique, nouveau snapshot à un autre instant, refus d'une
source modifiée au même instant, flag off par défaut et rollback sans perte.

## Commande de qualification

```bash
python -m app.offer_truth.replay \
  --evaluated-at <UTC_ISO_8601> \
  --after-raw-id 0 \
  --limit 1000
```

Après revue du dry-run, la même commande avec `--apply` est autorisée seulement
dans un processus de maintenance portant tous les flags requis. Le timestamp
doit être strictement identique pour le second passage idempotent.

## Décision P3E

P3E est qualifié localement. P3F reste ouvert tant que la migration n'est pas
appliquée en production et que le triplet dry-run / apply / replay idempotent
n'a pas atteint des états terminaux prouvés.
