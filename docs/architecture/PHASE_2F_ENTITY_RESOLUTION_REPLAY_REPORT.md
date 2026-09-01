# FILON — Phase 2F Entity Resolution Shadow Replay

- Date locale : **1er septembre 2026**
- Statut : **TERMINÉ — REPLAY PRODUCTION BORNÉ ET IDEMPOTENT**
- Migration : `c4f2b8d5e0a3`
- Extracteur : `awin-entity-signals/v1`
- Resolver : `entity-resolution-shadow-v1`
- Politique : `entity-resolution-policy-v1`
- Promotion publique : **INTERDITE**

## Verdict

P2F dispose d'une persistance expand-only et d'un replay borné. Les
profils de signaux et les décisions sont append-only par version. Un second
passage identique reconnaît les lignes existantes ; un payload ou une décision
différente sous la même version provoque un échec fermé au lieu d'une mise à
jour silencieuse.

La migration `c4f2b8d5e0a3` est appliquée en production. Le même lot réel de
1 000 raws a été exécuté une première fois puis rejoué : le second passage a
retrouvé les 1 000 projections et 1 000 décisions sans créer une seule ligne.
P2F est fermé.

## Reçu production

- commit `main` qualifié : `076a6a2bf83cefa8435fa49cf5c8a52e3c5c4661` ;
- déploiement web : `44a4570c-e939-4de9-b74a-5e4e4b781494` ;
- déploiement Cron : `8a7b3077-35fb-46a0-a35d-d19e7ac282ae` ;
- schéma PostgreSQL : `c4f2b8d5e0a3` ;
- fenêtre : `after_raw_id=0`, `limit=1000` ;
- empreinte stable :
  `sha256:07ef8bd31eb27dd76fc545a69e108b5f8aceb090507a1fd90b305f29c234b4a4`.

| Mesure | Dry-run | Premier apply | Replay |
|---|---:|---:|---:|
| raws scannés / projetés | 1 000 / 1 000 | 1 000 / 1 000 | 1 000 / 1 000 |
| profils candidats | 321 | 321 | 321 |
| `EXACT_VERIFIED` | 330 | 330 | 330 |
| `HIGH_CONFIDENCE` | 0 | 0 | 0 |
| `PROBABLE` | 0 | 0 | 0 |
| `AMBIGUOUS` | 0 | 0 | 0 |
| `UNRESOLVED` | 670 | 670 | 670 |
| liens d'offre manquants | 0 | 0 | 0 |
| projections créées / existantes | 0 / 0 | 1 000 / 0 | 0 / 1 000 |
| décisions créées / existantes | 0 / 0 | 1 000 / 0 | 0 / 1 000 |

Les flags `OBSERVATION_SHADOW_ENABLED`, `PRODUCT_GRAPH_SHADOW_ENABLED` et
`ENTITY_RESOLUTION_SHADOW_ENABLED` ont été activés uniquement dans le processus
des deux commandes `apply`. Une vérification hors commande les retrouve tous à
`false`. Aucun lecteur public Core v1 n'a été modifié.

Le premier essai d'application a échoué avant commit parce que le worker
autonome ne chargeait pas toutes les métadonnées SQLAlchemy. Le correctif
fail-closed a été intégré par la PR `#389`, qualifié par la CI puis déployé ;
aucune ligne partielle n'a été conservée par l'essai échoué.

## Expansion de schéma

| Table | Contenu | Invariant |
|---|---|---|
| `graph_entity_signal_projections` | profil résolveur complet, source, date et version d'extraction | unicité `raw + extractor_version`, SHA-256 et divergence interdite |
| `graph_entity_resolution_decisions` | état, candidat canonique éventuel, roster, raisons, preuves et conflits | unicité `raw + resolver + policy`, SHA-256 et candidat canonique seulement pour `EXACT_VERIFIED`/`HIGH_CONFIDENCE` |

La migration ne lance aucun backfill et ne modifie aucune table Core. Le
downgrade technique ne supprime que ces deux tables shadow ; le rollback
opérationnel normal conserve le schéma et coupe le flag.

## Replay borné

La commande `python -m app.product_graph.entity_replay` :

1. lit au plus `--limit` raws Awin en ordre primaire stable ;
2. retrouve l'offre Core par les observations déjà sourcées ;
3. extrait les 16 signaux versionnés ;
4. construit un roster uniquement depuis les variantes Graph déjà résolues ;
5. utilise d'abord l'identifiant global, ensuite les signaux structurés, puis
   le titre ou l'image exacts uniquement comme génération de candidats ;
6. refuse un roster supérieur à 100 plutôt que de tronquer une ambiguïté ;
7. calcule les cinq états du contrat ;
8. reste en dry-run par défaut ;
9. exige `ENTITY_RESOLUTION_SHADOW_ENABLED=true` pour `--apply` ;
10. ne modifie aucun lecteur catalogue v1.

`brand` et `taxonomy` peuvent corroborer une décision mais ne génèrent jamais
seuls un candidat. Un GTIN fourni mais invalide conserve le veto du resolver et
ne peut pas bénéficier d'un fallback.

## Preuves locales

- **125/125** tests ciblés : contrats, extracteurs, resolver, configuration,
  migration, rollback et replay ;
- **2 271** tests backend passés, **3** tests PostgreSQL ignorés hors service ;
- l'unique test de transport OTLP empêché par le sandbox réseau local a été
  rejoué séparément avec loopback autorisé : **1/1 vert** ;
- migration `upgrade head`, `alembic check`, restauration et downgrade Graph
  validés par la suite ;
- fixture replay : 3 raws donnent `EXACT_VERIFIED=1`,
  `HIGH_CONFIDENCE=1`, `UNRESOLVED=1` ; le second apply donne 3 projections et
  3 décisions existantes, aucune création ;
- mutation de la source sous la même version : `signal replay divergence`,
  transaction refusée.

## Procédure de qualification production exécutée

Le déploiement a gardé le nouveau flag à `false`. Après readiness sur
`c4f2b8d5e0a3`, la procédure suivante a été exécutée :

1. confirmer snapshot/restauration, CI terminale et absence d'ingestion
   concurrente ;
2. exécuter un dry-run borné sur les 1 000 raws audités ;
3. comparer `scanned`, `projected`, `missing_offer_links`, les cinq états et
   `candidate_profiles` avec P2B et Phase 1 ;
4. activer le flag uniquement pour l'exécution de maintenance ;
5. exécuter exactement un apply borné ;
6. rejouer le même lot et exiger `created=0`, `existing=projected` et le même
   `evaluation_id` ;
7. contrôler en lecture seule les deux tables, les clés de version et l'absence
   de mutation Core ;
8. remettre le flag à `false` ;
9. publier les totaux expurgés dans ce rapport et ouvrir P2G.

La qualification confirme que les raws sans signaux structurés restent
`UNRESOLVED` ou, au plus, `PROBABLE` sans candidat canonique. Une augmentation
artificielle de couverture, un roster tronqué, un conflit silencieux ou une
divergence d'idempotence est un NO-GO P2F.

À l'issue du replay, `/health/live`, `/health/ready` et `/health` sont verts,
PostgreSQL et Redis sont `ok`, et le service catalogue Cron est au repos. Le
run catalogue `21` reste déclaré `running` dans le journal avec heartbeat stale
et `recovery_required=true`, mais aucune exécution Railway correspondante n'est
active ; le mécanisme fail-closed l'expose comme `interrupted`.

## Rollback

Le rollback normal est :

```text
ENTITY_RESOLUTION_SHADOW_ENABLED=false
```

Il n'efface aucune preuve et ne modifie pas les lecteurs v1. Un downgrade ou
une suppression de données n'est pas une procédure de rollback production.
