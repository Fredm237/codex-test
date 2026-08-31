# FILON — rapport de phase P0.e Observation shadow

## Phase et statut

**P0.e — RawSource, Observation et Quarantine : GO pour shadow local ; NO-GO
pour tout lecteur v2 ou activation production générale.**

## Current state

Avant P0.e, une ligne Awin devenait directement une `Offer`. Sa valeur brute,
la transformation et le motif d'un rejet n'étaient pas conservés de manière
rejouable. Le Core v1 reste aujourd'hui la seule lecture publique.

## Evidence et root causes

- Le parsing prix/stock et l'upsert vivaient dans `services/awin_catalog.py`.
- Une disponibilité textuelle non reconnue devenait auparavant `False` au lieu
  de `unknown`.
- Les lignes sans identifiant/nom étaient ignorées sans trace durable.
- `offers` ne pouvait pas expliquer quelle valeur source avait produit un champ.

## Architecture livrée

```text
Awin row
  ├─→ legacy upsert v1 (inchangé)
  └─→ savepoint shadow, si flag actif
       ├─→ raw_source_records (payload + checksum + contexte)
       ├─→ observations (verified / inferred / unknown)
       └─→ quarantine_records (erreur structurée + raw)
```

La clé de replay dépend de la source, du record, du checksum et de la date
d'observation. Une nouvelle version de transformation produit une nouvelle
projection attachée au même raw, sans le modifier.

## Files affected

- `filon-backend/app/observations/` : modèles et projection/replay Awin.
- `filon-backend/app/services/source_normalization.py` : parsing partagé.
- `filon-backend/app/services/awin_catalog.py` : double écriture opt-in.
- `filon-backend/alembic/versions/d75faf1f6a94_*.py` : expansion réversible.
- `filon-backend/tests/test_observation_shadow.py` et `test_migrations.py`.
- `docs/adr/ADR-002-RAW-OBSERVATION-QUARANTINE.md`.

## Data migration et rollback

- La migration n'ajoute que trois tables et leurs index.
- Aucun backfill n'est lancé automatiquement.
- Le writer est désactivé par défaut avec
  `OBSERVATION_SHADOW_ENABLED=false`.
- Rollback fonctionnel : remettre le flag à `false`.
- Rollback schéma : `alembic downgrade b9db07b15986`, après export des raws ;
  toutes les tables et données de la baseline sont conservées.

## Tests et benchmarks

- Tests ciblés observation/Awin/migrations : **28/28**.
- Suite backend : **1216/1216**, avec 4 avertissements de date préexistants.
- Migration : upgrade, adoption baseline, `alembic check`, rollback shadow,
  downgrade complet et restauration verts.
- Fixture valide : 1 raw, 10 observations, 0 quarantaine.
- Fixture invalide : champs prix/stock/GTIN inconnus, 4 anomalies conservées ;
  aucune valeur favorable inventée.
- Replay même version : 0 doublon ; nouvelle version : 10 nouvelles
  observations sur le raw existant.
- Mutation de l'offre v1 par le shadow : **0** dans le test sentinelle.

Ces chiffres prouvent l'infrastructure et non la qualité d'un feed réel. Il
n'existe encore aucun benchmark production du taux d'unknown ou de quarantaine.

## Before / after

| Mesure structurelle | Avant | Après local |
|---|---:|---:|
| Payload Awin rejouable | 0 | 1 par événement capturé quand le flag est actif |
| Provenance champ-par-champ | 0 | 10 champs v1 projetés sur la fixture |
| Anomalie reliée au raw | 0 | 4/4 sur la fixture invalide |
| Valeur stock non reconnue convertie en `False` | oui | non, `unknown` |
| Lecteur v1 modifié | n/a | 0 |

## Latency et cost

La latence et le volume de stockage n'ont pas encore été mesurés sur un lot
Awin réel. L'activation globale reste donc interdite. Le savepoint par ligne est
sûr mais peut être trop coûteux ; la prochaine preuve opérationnelle doit mesurer
P50/P95, lignes/seconde et octets/raw sur un lot borné.

Le durcissement postérieur de l'ingestion garantit désormais que « borné »
n'est pas seulement une consigne opératoire : le corps Awin est lu par morceaux
dans un spool qui quitte la mémoire après 8 MiB, puis les volumes compressé et
décompressé ainsi que le nombre de lignes sont plafonnés. Une valeur de lignes
à zéro active encore le plafond dur de 250 000. Les dépassements échouent par
types d'erreur fermés avant l'upsert et ne journalisent ni URL ni clé de feed.
Cette protection mémoire ne remplace toujours pas une mesure de débit réelle.

## Known limitations et risques production

- aucune activation sur données Awin réelles ;
- aucune politique de rétention/légal approuvée ;
- immutabilité imposée par l'API et contrôlée au replay, pas encore par trigger DB ;
- aucun workflow humain de release/discard de quarantaine ;
- aucune reprise batch ou backfill chunké ;
- les lecteurs et le Product Graph restent volontairement absents.

## Next gate

Activer le shadow sur un lot réel borné, mesurer sa couverture et ses rejets,
puis compléter les datasets indépendants P0.c. Le Product/Variant Graph P0.f
reste **NO-GO** tant que le Quality Lab ne possède pas les annotations humaines
indépendantes requises.
