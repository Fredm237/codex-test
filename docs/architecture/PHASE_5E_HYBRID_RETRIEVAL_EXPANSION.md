# FILON — Phase 5E Structured + Semantic Expansion

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Structured : `hybrid-structured-ontology/v1`
- Semantic : `hybrid-semantic-expand-only/v1`
- Agrégateur : `hybrid-expand-only/v1`
- Lecteur public / writer : **INCHANGÉS / ABSENTS**

## Décision

Les sources structurée et sémantique ferment l'écart `SAFE_INCOMPLETE` de P5D
sur le holdout P5C sans relâcher les gates de sécurité. L'ensemble expand-only
est `QUALIFIED` pour passer à la fusion P5F, mais il n'est ni déployé ni promu
sur un lecteur public.

## Source structurée

La source structurée reçoit une intention observée. Elle :

- s'abstient lorsque le type produit n'est pas résolu ;
- filtre le type, le rôle principal et les contraintes explicites ;
- refuse toute valeur d'attribut contradictoire ;
- ne renvoie que des identités déjà résolues ;
- regroupe les offres par entité ;
- conserve `AMBIGUOUS` pour un scope uniquement générique, même si la fenêtre
  courante ne contient qu'une ligne.

Elle ne transforme donc jamais un rayon, une taxonomie ou un attribut en
identité canonique.

## Source sémantique

L'adaptateur P5E est un proxy déterministe borné utilisé pour qualifier la
politique expand-only, pas une prétention de qualité d'embedding. Il :

- s'abstient en présence d'un identifiant explicite inconnu ;
- ne travaille que sur des préférences et types explicitement observés ;
- conserve l'identité fournie par Entity Resolution, sans la modifier ;
- marque `QUARANTINED` tout hit sans identité ;
- supprime les `offer_ids` d'un hit non résolu ;
- n'a aucun pouvoir de décision ni de promotion.

L'ajout éventuel d'un vrai backend vectoriel devra respecter exactement cette
interface et battre ce proxy sur le même holdout et sur les mesures réelles P5I.

## Agrégation expand-only

`combine_expand_only` produit une union sourcée avant le vrai ranking/fusion :

- regroupement par `entity_ref` déjà prouvée ;
- union des offres et des types de source ;
- aucun score lexical, structuré ou sémantique n'est comparé entre sources ;
- une ambiguïté générique reste ambiguë ;
- un hit semantic-only non résolu donne `AMBIGUOUS` sans candidat éligible ;
- l'absence de toute preuve donne `NO_MATCH`.

P5F reste nécessaire pour versionner la fusion, l'ordre, les rangs source et le
grouping final. P5E ne préjuge pas cette politique.

## Résultats P5C

| Mesure | Expand-only | Gate |
|---|---:|---:|
| Recall@50 | 1,0000 sur 4 612 | ≥ 0,95 |
| NDCG@10 | 1,0000 | ≥ 0,85 |
| top-3, borne Wilson basse | 0,99916777 | ≥ 0,90 |
| no-match, borne Wilson basse | 0,99833692 | ≥ 0,99 |
| ambiguë, borne Wilson basse | 0,99833692 | ≥ 0,95 |
| violations de contraintes | 0 | 0 |
| faux regroupements | 0 | 0 |
| provenance | 9 224 / 9 224 | 100 % |
| fausses résolutions semantic-only | 0 | 0 |

L'évaluation contient zéro mismatch et zéro failure bloquante. Son identité est
`sha256:98b970867cdaeb6d8dbf9c633ca126826e0a4731cf31c80a20b0ca2f21432eb6`.

## Limites et gate

- corpus synthétique, sans vérité humaine externe ;
- proxy sémantique déterministe, sans modèle ni index vectoriel réel ;
- aucune latence ou dérive production encore mesurée ;
- aucune écriture, migration, variable ou activation ;
- `promotion_eligible=true` signifie seulement que l'adaptateur non-oracle
  satisfait P5C, jamais qu'un lecteur public est autorisé.

P5E est terminale. P5F peut figer la fusion réciproque, l'ordre product-first,
les rangs sources et la reproductibilité du digest final.
