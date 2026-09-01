# FILON Product Ontology Contract v1

Statut : `draft_for_shadow` depuis le 1er septembre 2026.

Ce contrat remplace progressivement la taxonomie plate comme cerveau produit,
sans supprimer son utilité de fallback. Il décrit la catégorie, la
sous-catégorie, le type produit, les attributs, le rôle, les relations et les
facettes métier d'une Variant.

Règles normatives :

- le rôle appartient au roster fermé `PRIMARY_PRODUCT`, `ACCESSORY`,
  `REPLACEMENT_PART`, `CONSUMABLE`, `SERVICE`, `DIGITAL_CONTENT`,
  `ACCOMMODATION`, `BUNDLE`, `UNKNOWN` ;
- une cible textuelle observée conserve `target_state=observed_text` et ne peut
  porter aucun `target_variant_id` ;
- une relation canonique exige une Variant résolue et ne conserve pas un texte
  comme substitut d'identité ;
- catégorie, sous-catégorie et type produit sont des concepts identifiés par
  une clé stable sous un contrat versionné, pas
  des libellés marchands libres ;
- les attributs sont typés et sourcés ; une valeur invalide ou contradictoire
  reste `null` ;
- use case, audience, compatibilité, style, matière, saison, occasion et
  fonction sont des facettes explicites ; une liste vide vaut unknown ;
- la taxonomie legacy déclare son état de migration et ne devient jamais une
  preuve plus forte qu'une observation structurée ;
- `VERIFIED` exige une Variant, une catégorie, un type produit et un rôle
  connus ;
- aucun lecteur public n'est modifié pendant Phase 4.

La politique détaillée est fixée par
[ADR-009](../../../docs/architecture/ADR-009-PRODUCT-ONTOLOGY-V1-CONTRACT.md).
