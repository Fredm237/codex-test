# FILON Hybrid Retrieval Contract v1

Statut : `draft_for_shadow` depuis le 1er septembre 2026.

Ce contrat sépare le générateur de candidats du ranking, de l'optimisation
d'offre et de la décision. Il décrit une requête pseudonymisée, son intention
structurée, les sources lexicales/structurées/sémantiques, la fusion et le
regroupement product-first.

Règles normatives :

- la requête brute n'est jamais persistée dans un run ; seul un digest et une
  référence opaque sont conservés ;
- les hard constraints et soft preferences restent séparées ;
- lexical, structured et semantic publient leurs rangs, versions et latences
  sans rendre leurs scores directement comparables ;
- une entité `RESOLVED` exige une preuve `ENTITY_RESOLUTION` ; un hit
  sémantique seul reste insuffisant ;
- une entité non résolue reste `QUARANTINED` et ne devient pas un candidat
  public ;
- un `group_key` produit ne peut apparaître qu'une fois après fusion ;
- plusieurs offres d'un même produit restent attachées au même candidat ;
- le rang de retrieval ne représente ni qualité produit, ni valeur, ni
  confiance, ni verdict ;
- commissions, affiliation et relation commerciale ne participent jamais au
  retrieval produit ;
- `NO_MATCH` et `ERROR` n'inventent aucun candidat ;
- aucun lecteur public n'est modifié pendant P5A.

La politique détaillée est fixée par
[ADR-010](../../../docs/architecture/ADR-010-HYBRID-RETRIEVAL-V1-CONTRACT.md).
