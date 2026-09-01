# FILON — Phase 3C Offer Truth Benchmark Report

- Date : **1er septembre 2026**
- Statut : **PASS — BENCHMARK RATIFIÉ**
- Evaluation ID : `sha256:1e55ea592d5dcfe53f9ee290925c0aec0b0f09c41196ffb60201fc3a9c73c654`
- Politique : `offer-truth-contract-oracle/v1`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Promotion publique : **NON AUTORISÉE PAR CE LOT**

## Verdict

Le benchmark adversarial Phase 3 est ratifié avec **14 352 cas**, zéro échec
et zéro fallback dangereux. Les sept claims du contrat sont couverts : prix,
stock, livraison, retours, garantie, marchand et fraîcheur.

Cette gate prouve la cohérence d'un oracle synthétique déterministe et la
capacité à s'abstenir. Elle ne prouve pas qu'un marchand affiche réellement le
bon prix ou le bon stock à un instant donné. La mesure de vérité externe reste
une limitation explicite et ne doit jamais être requalifiée implicitement.

## Corpus et anti-fuite

- quatre seeds indépendants ;
- 256 échantillons par seed ;
- 16 cas de régression lisibles couvrant chaque claim ;
- `development_engine_input=false` ;
- oracle et manifest versionnés ;
- contenu des régressions engagé dans l'identité cryptographique du run ;
- même entrée projetée deux fois pour contrôler le déterminisme ;
- aucune donnée utilisateur ni payload production dans le corpus.

## Résultats

| Gate | Cas | Résultat | Intervalle 95 % | Seuil | Verdict |
|---|---:|---:|---:|---:|---|
| exactitude globale | 14 352 | 100 % | borne basse 99,9732 % | ≥ 99,5 % | PASS |
| claims connus | 5 127 | 100 % | borne basse 99,9251 % | ≥ 99,5 % | PASS |
| abstention sûre | 9 225 | 100 % | borne basse 99,9584 % | ≥ 99,5 % | PASS |
| provenance des claims connus | 5 127 | 100 % | borne basse 99,9251 % | ≥ 99,5 % | PASS |
| fallback dangereux | 9 225 | 0 | borne haute 0,0416 % | ≤ 0,5 % | PASS |
| échecs bloquants | 14 352 | 0 | — | 0 | PASS |

Les intervalles sont des intervalles de Wilson bilatéraux à 95 %.

## Adversaires explicitement couverts

- montant sans devise, devise invalide, prix zéro et prix négatif ;
- stock absent ou valeur hors roster, sans disponibilité par défaut ;
- livraison absente, distincte d'un zéro explicitement observé ;
- retours et garantie absents ou mal formés, sans inférence marketing ;
- relation marchand `AFFILIATED` non embellie en `DIRECT_PARTNER` ;
- observation future ou stale exclue de la vérité courante ;
- claim connu sans preuve interdit ;
- sortie stable sur répétition de la même projection.

## Décision P3C

P3C est fermé. Les targets sont désormais normatives pour P3D et P3E. Le
prochain extracteur et le writer shadow devront passer exactement ces gates,
mais ce PASS n'active aucun writer et ne modifie aucun lecteur public.
