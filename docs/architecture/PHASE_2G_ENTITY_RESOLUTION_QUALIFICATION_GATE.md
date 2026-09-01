# FILON — Phase 2G Entity Resolution Qualification Gate

- Date locale : **1er septembre 2026**
- Statut : **TERMINÉ — PASS PRODUCTION**
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

## Reçu terminal

- statut : **PASS** ;
- reçu P2G :
  `sha256:15ab40f37a93a274b7ff73a76c913536a3826fc3be826f385f153d182b086ec4` ;
- premier apply :
  `sha256:07ef8bd31eb27dd76fc545a69e108b5f8aceb090507a1fd90b305f29c234b4a4` ;
- replay idempotent : même empreinte ;
- source baseline : `phase1-awin-shadow-2026-08-31` ;
- limitation conservée : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`.

| Gate | Verdict |
|---|---|
| `bounded_window` | PASS |
| `corpus_preserved` | PASS |
| `offer_provenance_complete` | PASS |
| `candidate_baseline_preserved` | PASS |
| `exact_gtin_preserved` | PASS |
| `no_unproved_canonical_promotion` | PASS |
| `first_apply_complete` | PASS |
| `same_replay_truth` | PASS |
| `idempotent_replay` | PASS |

L'image d'exécution web minimale n'embarque volontairement ni `quality_lab`
ni le manifest. Les deux reçus expurgés produits dans le conteneur ont donc été
vérifiés hors conteneur par le vérificateur et le manifest versionnés du même
commit qualifié. L'absence du laboratoire dans l'image n'a entraîné aucune
écriture et n'affaiblit aucune gate : le vérificateur ne contacte ni base ni
service et compare uniquement les deux reçus complets.

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

Les deux reçus PostgreSQL réels sont terminaux. La CI distante du run
`33454869610` est verte sur ses quatre jobs, migrations PostgreSQL et benchmark
Entity Resolution inclus. P2G est fermé avec le verdict **PASS**.
