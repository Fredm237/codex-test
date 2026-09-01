# FILON — Phase 5G Hybrid Retrieval Shadow

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — LOCAL QUALIFIED / PRODUCTION OFF**
- Migration : `f7c5e9a1b3d6`
- Writer : `hybrid-retrieval-shadow-writer/v1`
- Flag : `HYBRID_RETRIEVAL_SHADOW_ENABLED=false` par défaut
- Lecteur public : **INCHANGÉ**

## Décision

La persistance Hybrid Retrieval est une expansion append-only et réversible.
Elle ne remplace aucune table Core, ne stocke jamais le texte brut d'une
requête et n'active aucun writer ou lecteur au déploiement.

## Schéma

### `hybrid_retrieval_runs`

Chaque run immuable conserve :

- une clé SHA-256 et un digest de requête ;
- une référence opaque de requête avec `raw_query_retained=false` ;
- locale et pays observés ;
- intention, sources, versions d'index et raisons sous contrat JSON ;
- outcome, versions retrieval/fusion, snapshot et digest de résultat ;
- instant d'évaluation.

L'unicité engage requête, versions, snapshot et instant. Les checks SQL
interdisent la conservation du texte brut, les locales hors roster et les
outcomes hors contrat.

### `hybrid_retrieval_candidates`

Chaque candidat conserve :

- rang unique dans le run ;
- statut shadow, type et référence d'entité ;
- group key product-first ;
- score RRF sérialisé sans arrondi implicite ;
- offres groupées et preuves source.

Une entité ne peut apparaître qu'une fois par run. La table dépend du run avec
suppression en cascade uniquement pour permettre un downgrade/restauration
contrôlé ; l'application ne fournit aucune mutation destructive.

## Writer et idempotence

`persist_fusion_result` ne reçoit aucun champ de requête brute. Il calcule la
clé du run sur l'enveloppe complète et :

- en dry-run, ne crée aucune ligne ;
- au premier apply, crée un run et ses candidats ;
- au replay strictement identique, reconnaît le run et les candidats existants ;
- refuse un replay dont le digest ou le nombre de candidats diverge ;
- refuse un candidat dont le préfixe d'entité n'est pas Product, Model ou
  Variant.

Le test SQLite prouve `0 → 1 → 1` run et candidat entre dry-run, apply et replay.

## Configuration fail-closed

Le flag reste OFF par défaut et exige simultanément :

- Observation shadow ;
- Product Graph shadow ;
- Entity Resolution shadow ;
- Product Ontology shadow.

Une activation sans cette chaîne est rejetée au chargement de configuration.
Le flag n'est modifié dans aucun environnement par P5G.

## Migration et rollback

La migration crée uniquement les deux tables, contraintes et index. Son
downgrade les supprime dans l'ordre candidat puis run et ne touche aucune table
catalogue, observation, graph, offre ou ontologie. Le rollback opérationnel
reste le flag OFF avec le schéma conservé à la tête.

## Qualification locale

- tests Hybrid Retrieval, configuration et migration SQLite : verts ;
- tête unique et garde runtime : `f7c5e9a1b3d6` ;
- `alembic check` couvert par la suite de migration ;
- aucun fichier protégé modifié par ce lot ;
- aucune écriture ou migration production exécutée.

P5G est terminale localement. P5H doit encore publier, migrer avec sauvegarde,
exécuter un replay réel borné puis son replay identique avant toute conclusion
production.
