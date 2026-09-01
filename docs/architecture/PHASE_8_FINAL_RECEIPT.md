# FILON — Phase 8 Offer Optimization Final Receipt

- Date : **1er septembre 2026**
- Verdict : **PHASE 8 = GO**
- Politique active : `offer-optimization-policy/v2`
- Migration production : `d1a9c3e5f7b0`
- Merge `main` : `7b66d2c2439d990cf78e678b526f4343a726ca4b`
- Déploiement Railway : `202d9162-515c-49c6-8c3a-1f292b87657e`
- CI PR : run `33534826059`, quatre jobs verts
- Lecteurs publics : **INCHANGÉS**
- Flags persistants : **TOUS OFF**

## Décision

Phase 8 est fermée avec un contrat v2 complet sur les dimensions exigées :
prix, livraison, cashback, retours, fiabilité marchand et fraîcheur. Le coût
livré est exact et auditable. Les inconnues restent inoptimisables ; commission,
affiliation et revenu plateforme restent hors contrat.

Le déploiement est terminalement réussi. Les logs prouvent l'upgrade PostgreSQL
`c0f8b2d4e6a9 -> d1a9c3e5f7b0`. Les sondes publiques prouvent application,
PostgreSQL, Redis et schéma sains.

## Qualification production bornée

Fenêtre fixe :

- `evaluated_at=2026-09-01T17:05:00Z` ;
- `after_product_ranking_run_id=0` ;
- `limit=1` ;
- replay : `offer-optimization-production-replay/v2` ;
- évaluation : `sha256:16f14486eb145a0ac8a814b4016e8fade53543dee4d281627fe7ba2bcd2b450e`.

Résultats :

| Étape | Runs scannés | Offres | Créés | Existants | Issue |
|---|---:|---:|---:|---:|---|
| dry-run | 1 | 0 | 0 | 0 | `ABSTAINED` |
| apply unique | 1 | 0 | 1 | 0 | `ABSTAINED` |
| replay identique | 1 | 0 | 0 | 1 | `ABSTAINED` |

Les deux premières tentatives d'apply ont été refusées avant toute écriture par
la validation de configuration, car les dépendances shadow n'étaient pas toutes
activées dans le processus de maintenance. L'apply qualifié a ensuite activé la
chaîne complète uniquement pour son processus. La lecture postérieure sans ces
variables confirme les dix flags persistants à `false`.

## Qualité

- benchmark autonome v2 : **5 760 / 5 760** ;
- borne Wilson 95 % : `0.99933352` ;
- inconnue ou offre inéligible sélectionnée : **0** ;
- variation sous mutation de commission : **0** ;
- provenance : **1.0** ;
- tests backend qualifiés : **2 528**, trois intégrations PostgreSQL exécutées
  et vertes en CI ;
- web, mobile et extension : **verts**.

La validation humaine externe reste
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING`. La preuve est autonome et
technique ; les dimensions subjectives restent `NOT_INDEPENDENTLY_VALIDATED`.

## Limites conservées

- la fenêtre Product Ranking initiale ne contient aucun produit classé ;
- aucun score marchand, cashback ou retour réel n'est assez prouvé pour une
  sélection d'offre réelle ;
- le run catalogue 22 demeure une dette historique de récupération ;
- aucune activation publique n'est autorisée par ce reçu.

Ces limites justifient l'abstention observée, mais ne remettent pas en cause
l'intégrité, le fail-closed, l'idempotence ou la récupérabilité de Phase 8.

## Passage

**PHASE 8 = GO. PHASE 9 — CONFIDENCE EST OUVERTE.**
