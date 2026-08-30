# FILON — Rapport P0.5 Product/Variant Graph shadow

Date : 30 août 2026

## Décision

**GO technique pour le schéma expand, le resolver exact-GTIN, le writer
shadow, le backfill borné et les adaptateurs Quality. NO-GO pour toute lecture
publique, tout cutover et toute revendication de qualité produit.**

Le lot avance malgré l'absence de données humaines, sans modifier le verdict
du gate. Les sept datasets conservent zéro cas, `integrity_valid=true`,
`ready=false` et `status=not_ready`.

## Périmètre livré

- révision Alembic `8b2f4c7d9a10`, strictement expand-only ;
- tables parallèles Brand, alias, Family, Model, Variant, identifiants,
  provenance et liens Offer→Variant ;
- résolution pure `exact-gtin-shadow-v1` : un seul GTIN valide résout une
  variante ; conflit, absence et identifiant invalide s'abstiennent ;
- aucune fusion par titre, marque, catégorie ou similarité ;
- double écriture Awin dans un savepoint propre au Graph, après la preuve
  RawSource/Observation et sans annuler le Core v1 en cas d'échec ;
- flags imbriqués, faux par défaut ;
- backfill ordonné, paginable, limité à 10 000 raws et dry-run par défaut ;
- adaptateurs réels pour les sept datasets Quality, tous non calibrés.

## Invariants

1. Une résolution `resolved` possède un `variant_id`; une quarantaine ou un
   rejet n'en possède jamais.
2. Un identifiant global normalisé appartient à une seule variante.
3. Chaque preuve d'identifiant cite un raw immuable et une date d'observation.
4. Un même raw et une même version ne créent jamais deux liens.
5. Deux GTIN différents ne prouvent pas deux produits différents.
6. Aucun endpoint ni lecteur Core ne consulte les tables `graph_*`.

## Activation contrôlée future

1. sauvegarder et restaurer la base selon le runbook ;
2. appliquer la migration, laisser les deux flags à `false` et vérifier le
   Core ;
3. exécuter un dry-run borné :

   ```bash
   python -m app.product_graph.backfill --after-raw-id 0 --limit 1000
   ```

4. activer les deux flags sur le seul worker d'ingestion shadow ;
5. exécuter le même lot avec `--apply`, conserver uniquement les compteurs
   agrégés et reprendre au `last_raw_source_id` ;
6. comparer résolus, quarantaines et erreurs ; ne lancer aucun lecteur v2 ;
7. en rollback, remettre `PRODUCT_GRAPH_SHADOW_ENABLED=false` sans downgrade.

## Limites

- Brand, Family et Model ne sont pas encore alimentés : Awin ne fournit pas
  dans le contrat actuel une preuve forte suffisante pour ces merges.
- Un GTIN exact identifie une variante, pas à lui seul sa famille ou son
  modèle.
- Aucun backfill de production, benchmark humain, faux-merge/faux-split ou
  attachement réel n'est encore mesuré.
- L'Offer Graph complet, les politiques marchands et les lecteurs dual-read
  restent des lots ultérieurs soumis aux gates.
