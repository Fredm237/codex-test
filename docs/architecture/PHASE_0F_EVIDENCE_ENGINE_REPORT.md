# FILON — Rapport P0.5d Evidence Engine shadow

## Verdict

**Moteur de preuve technique local livré. Claims publics et décision : NO-GO.**

Le registre rend explicites les faits utilisables et les prérequis absents.
Il n'est branché à aucun endpoint, carte, classement ou recommandation.

## Livré

- migration expand-only `e8c3f6a0b5d2` et deux tables append-only ;
- quatre claims atomiques sourcés, avec valeur seulement lorsqu'ils sont
  vérifiés et éligibles ;
- sept claims forts toujours inéligibles avec raison explicite en policy v1 ;
- aucune confiance synthétique ;
- échelle `DISCOVERABLE` → `COMPARABLE` → `RANKABLE` →
  `DECISION_ELIGIBLE`, avec plafond v1 à `RANKABLE` ;
- prix décimal et devise explicite, stock tri-state, lien HTTPS public,
  identité exact-GTIN et expiration provisoire à 72 heures ;
- backfill dry-run/apply borné, horodaté explicitement et idempotent ;
- flag off par défaut `EVIDENCE_ENGINE_SHADOW_ENABLED`.

## Preuves locales

- **68/68** tests Evidence/configuration/migration ciblés ;
- **36/36** tests de chaîne Observation/Product/Offer/Merchant/Evidence ;
- **377/377** tests Quality Lab ;
- **2 097 réussis + 2 ignorés** sur le backend complet ;
- une seule tête Alembic `e8c3f6a0b5d2`, sans drift de modèle.

## Commande

```bash
python -m app.evidence_engine.backfill \
  --evaluated-at 2026-08-31T00:00:00+02:00 \
  --after-raw-id 0 \
  --limit 1000
```

Sans `--apply`, aucune écriture n'a lieu. L'apply exige Observation,
Product/Variant Graph, Offer Graph, Merchant Intelligence et Evidence Engine
activés ensemble.

## Limites honnêtes

- Aucun backfill ni lecteur public n'existe en production.
- Le TTL 72 h est provisoire et doit être calibré sur la cadence réelle.
- Pays, shipping, certification, cashback exhaustif et calibration manquent.
- Aucun claim `BUY_NOW`, `WAIT`, superlatif prix ou confiance n'est autorisé.
- Les données humaines Quality restent à zéro ; aucune qualité de décision
  n'est mesurable.
