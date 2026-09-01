# FILON — Phase 5F Hybrid Retrieval Fusion

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Version : `hybrid-rrf-product-first/v1`
- Constante RRF : `k=60`
- Lecteur public / writer : **INCHANGÉS / ABSENTS**

## Décision

La fusion Reciprocal Rank Fusion (RRF) v1 est qualifiée sur le holdout P5C. Elle
combine des rangs propres à chaque source sans comparer leurs scores bruts,
regroupe les offres par identité déjà résolue et conserve toutes les preuves.

## Contrat de fusion

Chaque hit d'entrée contient uniquement :

- `source_type` lexical, structuré ou sémantique ;
- `source_rank` strictement positif ;
- `entity_ref` résolue ou nulle ;
- `offer_ids`, interdits si l'identité est nulle ;
- `evidence_ref` obligatoire.

Il n'existe aucun champ commission, affilié ou marchand dans ce contrat. Ces
signaux ne peuvent donc ni modifier le score RRF ni départager une égalité.

Pour chaque entité, la fusion :

1. conserve le meilleur rang par source ;
2. calcule la somme `1 / (60 + source_rank)` ;
3. réunit les offres et les preuves ;
4. ordonne par score décroissant, nombre de sources décroissant puis
   `entity_ref` stable ;
5. borne la sortie entre 1 et 500 candidats.

Une ambiguïté amont bloque la sélection arbitraire d'un premier candidat. Un
hit semantic-only sans identité augmente le compteur non résolu et produit
`AMBIGUOUS`, jamais un candidat ni une offre.

## Reproductibilité

Le digest SHA-256 engage :

- version de fusion et constante RRF ;
- digest de requête, jamais le texte brut ;
- référence de snapshot ;
- versions d'index triées ;
- garde d'ambiguïté ;
- ordre, rangs, entités, offres et références de preuve de tous les hits.

Deux entrées identiques produisent le même digest. Une modification de rang,
preuve, snapshot ou version produit un autre digest. L'instant d'exécution n'est
pas introduit dans cette identité fonctionnelle.

## Résultats P5C

L'adaptateur `fused` est `QUALIFIED`, `promotion_eligible=true` dans le seul
périmètre du benchmark, avec :

- 9 224 cas, zéro mismatch, zéro failure bloquante ;
- Recall@50, NDCG@10 et top-3 à 1,0 ;
- bornes Wilson basses no-match et ambiguë à 0,99833692 ;
- zéro violation de contrainte sur 1 153 cas ;
- zéro faux regroupement sur 1 153 cas ;
- provenance complète sur 9 224 candidats évalués ;
- zéro fausse résolution semantic-only sur 1 153 cas.

Identité d'évaluation :
`sha256:412ef7ca58cdf7a4acf672ec470be7a3c9c631e9090ecccebb765f234bf9617e`.

## Limites et gate

- le résultat reste synthétique et sans vérité humaine externe ;
- aucun snapshot Hybrid Retrieval n'est encore persisté ;
- aucune latence production ni coût de backend sémantique n'est mesuré ;
- `promotion_eligible` ne modifie pas le lecteur public ;
- la migration, le writer OFF par défaut et le replay idempotent relèvent de
  P5G/P5H.

P5F est terminale. P5G peut ajouter uniquement une persistance append-only
shadow, réversible et désactivée par défaut.
