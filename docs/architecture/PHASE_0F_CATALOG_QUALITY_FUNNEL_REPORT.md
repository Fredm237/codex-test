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
| `RESOLVED_PRODUCT` → `DECISION_ELIGIBLE` | `blocked` | La chaîne stricte ne franchit pas une classification non mesurable |

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
- suite backend complète : **2 118 réussis, 2 ignorés** en 164,98 s ;
- replay identique à entrée et instant identiques ;
- cas vide, fenêtre invalide, timestamp interne ambigu, offre obsolète,
  rupture de stock, identité manquante et observation remplacée couverts.

La qualification distante doit encore être consignée après publication de la
branche.

## Limites et sortie du NO-GO

Ce rapport ne mesure ni la justesse de taxonomie, ni les faux merges/splits, ni
la qualité d'attachement, ni le coût rendu, ni la qualité d'une décision. La
sortie exige les datasets humains indépendants du Quality Lab, leur adjudication
et les sources manquantes de livraison/taxes/destination. Tant que ces preuves
n'existent pas, le funnel strict reste volontairement interrompu à
`CORRECTLY_CLASSIFIED`.
