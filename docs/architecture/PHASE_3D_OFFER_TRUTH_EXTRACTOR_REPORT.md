# FILON — Phase 3D Offer Truth Extractor Report

- Date : **1er septembre 2026**
- Statut : **PASS — EXTRACTEURS QUALIFIÉS LOCALEMENT**
- Version : `awin-offer-truth-extractor/v1`
- Policy : `offer-truth-policy/v1`
- Freshness : `offer-truth-freshness-72h/v1`
- Evaluation ID réel : `sha256:1be811d152a49d1485ca8a3af3279783a319e86b6d1b0060d8a6422bf125b409`
- Lecteurs et writers publics : **INCHANGÉS**

## Verdict

Les extracteurs purs Offer Truth produisent un snapshot v1 valide pour les
sept claims. L'implémentation réelle passe les **14 352 cas** du benchmark
ratifié avec zéro échec, zéro fallback dangereux et une sortie déterministe.

La projection n'effectue aucune écriture. Elle peut donc être utilisée par le
futur writer shadow P3E sans modifier le catalogue Core ni ses endpoints.

## Règles implémentées

- prix positif exact sous forme de chaîne décimale et devise du roster fermé ;
- prix sans devise `unknown`, devise explicitement invalide `invalid` ;
- stock fermé sur `in_stock`, `out_of_stock`, `preorder`, sinon abstention ;
- coût de livraison connu uniquement avec sa propre devise explicite ;
- zéro livraison accepté uniquement lorsqu'il est effectivement présent ;
- retours et garantie construits seulement depuis des champs structurés ;
- relation marchand issue du Registry et jamais promue implicitement ;
- observation future invalide, observation au-delà du TTL stale ;
- valeur stale conservée uniquement pour audit ;
- preuve versionnée attachée à chaque claim connu ;
- Variant absente = quarantaine, sans destruction des faits observés.

## Gates

| Gate | Résultat |
|---|---:|
| cas évalués | 14 352 |
| exactitude globale | 100 % |
| exactitude claims connus | 100 % |
| abstention sûre | 100 % |
| provenance | 100 % |
| fallbacks dangereux | 0 |
| tests Offer Truth contrat + benchmark + extracteurs | 63 PASS |

## Limites maintenues

- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` ;
- TTL 72 h provisoire et versionné ;
- aucun champ shipping/retours/garantie n'existe dans le feed production
  audité, ils resteront donc `unknown` lors du premier replay ;
- aucun claim n'est encore persisté ni servi publiquement.

## Décision P3D

P3D est fermé. P3E peut ajouter une migration expand-only et un writer shadow
désactivé par défaut. Toute promotion publique reste interdite avant P3G/P3H.
