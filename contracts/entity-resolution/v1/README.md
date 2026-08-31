# FILON Entity Resolution Contracts v1

Statut : `draft_for_shadow` depuis le 1er septembre 2026.

Ce contrat décrit une décision interne entre des observations et un candidat
ProductModel ou Variant. Il ne modifie aucun endpoint public et ne permet
aucune promotion automatique pendant Phase 2.

| Artefact | Rôle |
|---|---|
| `entity-resolution-decision` | décision, confiance, preuves, candidats et conflits |

Règles normatives :

- `EXACT_VERIFIED` exige un GTIN exact, valide et non contradictoire ;
- `HIGH_CONFIDENCE` exige au moins deux preuves structurées fortes et aucun
  conflit ;
- `PROBABLE` ne porte jamais de `canonical_id` et reste candidat shadow ;
- `AMBIGUOUS` conserve plusieurs candidats et au moins un conflit explicite ;
- `UNRESOLVED` ne porte ni candidat favorable ni identité canonique ;
- un `canonical_id` doit appartenir à `candidate_ids` ;
- titre, image et similarité sémantique restent faibles et ne peuvent servir
  que de corroboration ou de génération de candidats ;
- seul le GTIN global peut porter `strength=exact` dans cette version ;
- un score numérique n'est jamais une preuve et ne peut pas lever un veto ;
- toute preuve cite le raw, la source, l'observation et sa transformation ;
- tous les lecteurs publics restent sur Core v1 pendant la qualification.

La politique détaillée est fixée dans
[ADR-007](../../../docs/architecture/ADR-007-ENTITY-RESOLUTION-DECISION-CONTRACT.md).
