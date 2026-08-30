# FILON — Catalog Quality Funnel shadow

- Date : **30 août 2026**
- Statut : **livré en lecture interne ; NO-GO pour toute promotion produit**
- Politique : `catalog-quality-funnel-shadow-v1`
- Unité : lot borné de `raw_source_records` Awin, puis dernière
  `graph_offer_observation` par offre dans ce lot

## Objet

Ce lot rend visible le funnel exigé par l'article 27 du mandat sans inventer
une formule universelle ni transformer des signaux techniques en qualité
métier. Il s'agit d'un rapport interne, déterministe et en lecture seule. Il
n'ajoute aucun endpoint, aucun score, aucune migration et aucun consommateur
public.

## Funnel strict

| Étape | Statut actuellement calculable | Règle |
|---|---|---|
| `RAW_OFFERS` | `measured` | Lignes Awin du lot borné |
| `ACTIVE_OFFERS` | `measured` | Dernière observation de l'offre, non future, ≤ 72 h et `in_stock` |
| `VALID_PRICE` | `measured` | Montant décimal positif et devise explicite valide |
| `VALID_MERCHANT` | `measured` | Marchand joint et lien public HTTPS déjà validé par l'Offer Graph |
| `CORRECTLY_CLASSIFIED` | `not_measurable` | Aucun gold humain indépendant n'est joint au rapport |
| `RESOLVED_PRODUCT` → `HIGH_CONFIDENCE_DECISION` | `blocked` | La chaîne stricte ne franchit pas une classification non mesurable ; une confiance non calibrée n'est jamais qualifiée de haute |

Chaque étape porte son numérateur, son dénominateur et un code de raison.
Après la frontière humaine, numérateur et dénominateur restent `null` : un
zéro aurait faussement signifié une mesure.

## Signaux techniques séparés

Le rapport publie parallèlement des compteurs descriptifs pour :

- la présence des observations Offer Graph et de leur version courante ;
- la présence des champs de classification, explicitement distincte de leur
  justesse ;
- les liens exact-GTIN vers variante et modèle produit ;
- les variantes comparables chez au moins deux marchands joints dans une même
  devise ;
- un relevé historique de même devise datant d'au moins 30 jours ;
- l'existence d'un enregistrement d'éligibilité conforme à la politique
  Evidence courante.

Ces compteurs ont le statut `technical_signal_only`. Ils ne remplissent aucune
étape bloquée du funnel et ne peuvent servir de gate de lancement. Le coût
rendu complet reste `not_supported`, car livraison, taxes et destination ne
sont pas modélisées ensemble.

## Garde-fous

- lecture seule, refus du mode DDL `legacy` et aucune exposition API ;
- lot limité à 10 000 lignes, curseur explicite et ordre stable ;
- horodatage d'évaluation explicite, normalisé en UTC ;
- observations futures ou âgées de plus de 72 h non actives ;
- devise absente ou invalide et prix non positif exclus ;
- concordance obligatoire entre observation, offre, raw record et lien de
  variante ;
- empreinte SHA-256 canonique du rapport ;
- `launch_gate_eligible=false` constant en v1.

## Preuves locales

- tests ciblés du funnel : **12/12** ;
- tests combinés Funnel, Product Graph, Offer Graph, Evidence Engine et
  vérité devise : **67/67** ;
- suite backend complète : **2 118 réussis, 2 ignorés** en 64,33 s ;
- replay identique à entrée et instant identiques ;
- cas vide, fenêtre invalide, timestamp interne ambigu, offre obsolète,
  rupture de stock, identité manquante et observation remplacée couverts.

La publication distante associe le commit local `34a4f856c47b73220950134271a3e904b29a67f8`
au commit GitHub `7a39348804e4a9106bbd0d31317c756d56dc623b` par leur arbre
commun `1706a0be2418173a6fb68782c01ae38b2e1f12d2`. Actions #356
(`33332272585`) confirme les trois clients, Alembic, les régressions backend et
la readiness normale. Seul le gate strict humain échoue comme attendu.

La correction finale rend explicite la douzième étape
`HIGH_CONFIDENCE_DECISION`, toujours strictement bloquée et sans score de
confiance fabriqué. Le commit local
`594f51fc91651eb6e067dc9497b0b4337d0e57bc` et le commit distant
`9d8ade3ad671afe98f28be9c6f1fd5bf69fae414` partagent l'arbre
`9534214815bc6af2630bbf523fffb5c76f64980c`. Actions #358
(`33332958611`) a requalifié les quatre surfaces et publié l'artefact
`9738202431`; seul le gate humain strict reste rouge comme prévu.

## Limites et sortie du NO-GO

Ce rapport ne mesure ni la justesse de taxonomie, ni les faux merges/splits, ni
la qualité d'attachement, ni le coût rendu, ni la qualité d'une décision. La
sortie exige les datasets humains indépendants du Quality Lab, leur adjudication
et les sources manquantes de livraison/taxes/destination. Tant que ces preuves
n'existent pas, le funnel strict reste volontairement interrompu à
`CORRECTLY_CLASSIFIED`.
