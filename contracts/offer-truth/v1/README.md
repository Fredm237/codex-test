# FILON Offer Truth Contract v1

Statut : `draft_for_shadow` depuis le 1er septembre 2026.

Ce contrat décrit un snapshot interne d'offre sourcé. Il n'altère aucun
endpoint public et n'autorise aucune promotion de lecteur pendant Phase 3.

Règles normatives :

- prix et livraison utilisent une chaîne décimale et une devise ISO explicite,
  toujours atomiques ;
- une valeur absente ou invalide reste `null`, jamais zéro ou gratuite ;
- le stock est `in_stock`, `out_of_stock`, `preorder` ou inconnu ;
- livraison, retours et garantie peuvent rester inconnus sans être inventés ;
- un statut `VERIFIED` exige identité Variant, prix, stock, marchand et
  fraîcheur connus ;
- une observation stale conserve sa valeur pour audit mais n'est jamais une
  vérité courante ;
- chaque claim connu cite raw, source, observation et transformation ;
- aucune confiance numérique n'est exposée tant qu'elle n'est pas calibrée ;
- le marchand est `INDEXED`, `AFFILIATED`, `DIRECT_PARTNER`, `MARKETPLACE` ou
  `UNVERIFIED`, jamais automatiquement « partenaire » ;
- tous les lecteurs publics restent sur Core v1 pendant la qualification.

La politique détaillée est fixée dans
[ADR-008](../../../docs/architecture/ADR-008-OFFER-TRUTH-V1-CONTRACT.md).
