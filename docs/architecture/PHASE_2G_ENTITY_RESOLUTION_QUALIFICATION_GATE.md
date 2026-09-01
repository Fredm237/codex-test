# FILON — Phase 2G Entity Resolution Qualification Gate

- Date locale : **1er septembre 2026**
- Statut : **GATE LOCALE PRÊTE — REÇUS PRODUCTION ABSENTS**
- Manifest : `quality/entity-resolution-production-gate.json`
- Receipt : `entity-resolution-production-gate-receipt/v1`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Objet

P2G ne peut pas se contenter d'un journal relu manuellement. Le vérificateur
`quality_lab.entity_resolution_replay` exige deux reçus complets du même lot :

1. le premier `apply`, qui doit créer exactement une projection et une décision
   par raw éligible ;
2. le replay, qui doit produire la même vérité et ne créer aucune ligne.

Le vérificateur ne contacte aucun service et ne peut donc pas inventer une
preuve de production. Des fichiers absents, incomplets, enrichis d'une clé
inconnue ou portant un total incohérent rendent le reçu `INVALID`.

## Baseline ratifiée

Le manifest fige les mesures réelles déjà acquises en Phase 1/P2B :

| Mesure | Attendu |
|---|---:|
| fenêtre raw | `after_raw_id=0`, `limit=1000` |
| raws scannés/projetés | 1 000 / 1 000 |
| dernier raw | 1 000 |
| variantes candidates | 321 |
| exact-GTIN préservés | 330 |
| liens d'offre manquants | 0 |
| `HIGH_CONFIDENCE` non-GTIN | 0 |

`PROBABLE`, `AMBIGUOUS` et `UNRESOLVED` restent des abstentions sans candidat
canonique. Le corpus actuel ne contient aucune preuve structurée permettant
un `HIGH_CONFIDENCE`; en produire un serait un échec, même si le score était
élevé.

## Gates automatiques

- fenêtre bornée identique ;
- corpus et dernier raw préservés ;
- provenance offre complète ;
- 321 profils candidats et 330 exacts préservés ;
- aucune promotion canonique non prouvée ;
- premier apply complet et sans ligne préexistante ;
- mêmes versions, états, compteurs et `evaluation_id` au replay ;
- zéro création au replay et 1 000 projections/décisions reconnues.

Le reçu dérivé contient seulement les résultats des gates et les empreintes
des deux rapports. Il ne recopie ni payload, ni preuve brute, ni donnée
utilisateur.

## Preuve locale

La suite teste le PASS nominal et refuse :

- un lien d'offre manquant ;
- la perte d'un exact-GTIN ;
- un `HIGH_CONFIDENCE` artificiel ;
- une empreinte différente entre les deux passages ;
- une création pendant le replay ;
- une clé inconnue, un total d'états faux ou un manifest relâché.

P2G reste ouvert tant que les deux reçus PostgreSQL réels et la CI distante ne
sont pas terminaux. Le présent document prouve la capacité de qualification,
pas son résultat production.
