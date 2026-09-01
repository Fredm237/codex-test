# ADR-010 — Hybrid Retrieval v1, candidats product-first et sourcés

- Statut : **accepté pour shadow**
- Date : **1er septembre 2026**
- Portée : Phase 5 Hybrid Retrieval
- Contrat : `contracts/hybrid-retrieval/v1`
- Lecteurs publics : **inchangés**

## Contexte

Le retrieval historique mélange SQL `LIKE`, heuristiques de termes, filtres de
rayon, exclusion d'accessoires et ordre de pertinence. Ces garde-fous protègent
des parcours existants mais ne permettent pas de mesurer séparément rappel,
fusion, grouping, précision du ranking ou respect des contraintes.

## Décision

1. Candidate generation et ranking deviennent deux composants distincts.
2. Le retrieval combine lexical, structured et semantic derrière des
   adaptateurs versionnés et mesurés sur le même corpus.
3. Les scores bruts restent accompagnés de leur sémantique et ne sont jamais
   comparés directement entre sources.
4. La fusion produit un rang de candidat, pas une note de qualité ou un
   verdict.
5. Le grouping utilise seulement les entités prouvées par Entity Resolution.
6. Un hit sémantique seul ne peut résoudre ni Product, ni Model, ni Variant.
7. Une entité non résolue reste quarantainée et non promouvable.
8. Plusieurs offres du même produit sont attachées à un seul candidat.
9. La requête brute n'est pas persistée ; le run conserve un digest et une
   référence opaque.
10. Affiliation, commission et relation commerciale ne participent jamais au
    retrieval produit.
11. Hard constraints et soft preferences sont séparées, mais leur enforcement
    appartient à Phase 6.
12. Le contrat reste shadow-only jusqu'aux benchmarks et au replay P5.

## Invariants

- rang de retrieval ≠ score produit ;
- similarité vectorielle ≠ identité canonique ;
- titre marchand ≠ vérité ontologique ;
- plusieurs offres ≠ plusieurs produits ;
- `NO_MATCH` ≠ candidat synthétique ;
- unknown ≠ contrainte satisfaite ;
- commission ≠ pertinence.

## Rollback

P5A n'active ni index, ni writer, ni lecteur. Les futurs index et snapshots
seront expand-only, désactivés par défaut et supprimables du chemin runtime par
feature flag sans modifier Product Graph, Offer Truth ou Product Ontology.
