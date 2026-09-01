# FILON — Phase 2F Entity Resolution Shadow Replay

- Date locale : **1er septembre 2026**
- Statut : **IMPLÉMENTATION LOCALE QUALIFIÉE — REPLAY PRODUCTION EN ATTENTE**
- Migration : `c4f2b8d5e0a3`
- Extracteur : `awin-entity-signals/v1`
- Resolver : `entity-resolution-shadow-v1`
- Politique : `entity-resolution-policy-v1`
- Promotion publique : **INTERDITE**

## Verdict local

P2F dispose désormais d'une persistance expand-only et d'un replay borné. Les
profils de signaux et les décisions sont append-only par version. Un second
passage identique reconnaît les lignes existantes ; un payload ou une décision
différente sous la même version provoque un échec fermé au lieu d'une mise à
jour silencieuse.

Cette preuve ne remplace pas le replay PostgreSQL réel. Tant que la migration
n'est pas déployée et que les compteurs du corpus production ne sont pas
capturés, P2F reste ouvert au niveau production.

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

## Procédure de qualification production

Le déploiement doit garder le nouveau flag à `false`. Après readiness sur
`c4f2b8d5e0a3` :

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

La qualification attend que les raws sans signaux structurés restent
`UNRESOLVED` ou, au plus, `PROBABLE` sans candidat canonique. Une augmentation
artificielle de couverture, un roster tronqué, un conflit silencieux ou une
divergence d'idempotence est un NO-GO P2F.

## Rollback

Le rollback normal est :

```text
ENTITY_RESOLUTION_SHADOW_ENABLED=false
```

Il n'efface aucune preuve et ne modifie pas les lecteurs v1. Un downgrade ou
une suppression de données n'est pas une procédure de rollback production.
