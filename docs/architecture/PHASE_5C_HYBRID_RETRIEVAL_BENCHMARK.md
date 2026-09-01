# FILON — Phase 5C Hybrid Retrieval Benchmark

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — HOLDOUT RATIFIÉ**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Entrée moteur de développement : **INTERDITE**
- Promotion de l'oracle : **INTERDITE**

## Objectif

Ratifier avant les adaptateurs un holdout autonome qui mesure le retrieval
product-first, les abstentions et les hard negatives avec les gates Phase 5.
Le corpus ne contient que des marques, modèles, attributs, offres et requêtes
synthétiques.

## Couverture

Le générateur croise six verticales, trois langues et huit scénarios : exact
product, alias multilingue, no-match, intention ambiguë, accessoire piège,
contrainte contradictoire, offres dupliquées et candidat uniquement sémantique
sans identité résolue.

Trois graines et 64 échantillons par verticale produisent 9 216 cas générés,
auxquels s'ajoutent huit régressions explicites, soit **9 224 cas**. Le même
corpus mesure :

- Recall@50, NDCG@10 et pertinence top-3 ;
- exactitude no-match et ambiguë ;
- violations de contraintes en top-10 ;
- faux regroupements produit ;
- complétude de provenance ;
- promotion illégitime d'un signal semantic-only.

## Contrôle de puissance

L'oracle de contrat doit satisfaire toutes les gates mais reste non promouvable.
Un simulateur legacy offer-first est évalué sur le même corpus. Il doit être
classé `UNSAFE` et échouer sur no-match, ambiguïtés, contraintes, duplication et
semantic-only. Si le simulateur passait, le benchmark serait trop faible pour
qualifier P5D à P5F.

## Résultats terminaux

| Mesure | Oracle de contrat | Gate |
|---|---:|---:|
| Recall@50 | 1,0000 sur 4 612 | ≥ 0,95 |
| NDCG@10 | 1,0000 sur 4 612 | ≥ 0,85 |
| pertinence top-3, borne Wilson basse | 0,99916777 | ≥ 0,90 |
| no-match, borne Wilson basse | 0,99833692 sur 2 306 | ≥ 0,99 |
| ambiguë, borne Wilson basse | 0,99833692 sur 2 306 | ≥ 0,95 |
| violations de contraintes | 0 sur 1 153 | 0 |
| faux regroupements produit | 0 sur 1 153 | 0 |
| provenance complète | 8 071 / 8 071 | 100 % |
| fausses résolutions semantic-only | 0 sur 1 153 | 0 |

L'oracle termine `QUALIFIED`, avec zéro mismatch et zéro failure bloquante,
mais `promotion_eligible=false` par construction. Son identité est :

- corpus : `sha256:f92eb735007fe1a0521dd27b5fbb6ea5410417c26352c6dc6d979fa2901c3d28` ;
- régressions : `sha256:3c19a3afdde6e61529471ec11b66b7413c0562025dbd98d87340a5a84de5252f` ;
- évaluation : `sha256:5471183336d2e2b35866724d97d7ffed674dbc242c5ed7acc8c3efd7e6830cb8`.

Le simulateur offer-first conserve artificiellement un rappel de 1,0, ce qui
montre pourquoi le rappel seul est insuffisant. Il échoue néanmoins sur les
2 306 no-match, les 2 306 cas ambigus, les 1 153 scénarios de contraintes, les
1 153 regroupements dupliqués et les 1 153 semantic-only. Il produit 5 765
mismatches et 4 612 failures bloquantes : le benchmark détecte donc bien les
risques de sécurité recherchés.

## Gate

P5C est terminale après 11 tests verts, publication des digests, métriques et
strates. Aucun score de cet oracle synthétique n'est présenté comme préférence
humaine ou qualité production. P5D peut maintenant implémenter les adaptateurs
lexicaux contre ce corpus immuable.
