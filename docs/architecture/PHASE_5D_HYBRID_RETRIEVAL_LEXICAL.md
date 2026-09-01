# FILON — Phase 5D Hybrid Retrieval Lexical

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — SAFE_INCOMPLETE**
- Version : `hybrid-lexical-pgtrgm/v1`
- Lecteur public : **INCHANGÉ**
- Migration / index nouveau : **AUCUN**
- Activation production : **AUCUNE**

## Décision

L'adaptateur lexical product-first est qualifié pour la sécurité, le rappel et
la provenance sur le holdout P5C. Il reste volontairement incomplet sur les cas
où seul un signal sémantique peut expliquer l'ambiguïté. Cette abstention est
préférable à une fausse résolution et sera mesurée par P5E.

## Implémentation

`app/hybrid_retrieval/lexical.py` fournit deux surfaces séparées :

1. un moteur pur et déterministe pour le Quality Lab ;
2. un builder SQLAlchemy PostgreSQL qui produit `ILIKE` sur `offers.name` et
   `offers.brand`, sans envelopper les colonnes dans `lower(...)`.

La requête SQL est bornée à 500 candidats, exige une entité produit reliée et
conserve les filtres canonical/adulte. Elle est compatible avec les index GIN
`pg_trgm` déjà présents ; aucun DDL supplémentaire n'est requis à ce stade.

Le moteur pur :

- normalise accents, casse, stopwords et alias FR/NL/EN ;
- borne la requête à douze termes ;
- utilise les contraintes d'attribut explicitement observées ;
- refuse un rôle accessoire connu lorsque la requête ne demande pas un
  accessoire ;
- ignore les matches sans identité résolue ;
- fusionne les offres d'une même entité avant de produire le rang source ;
- répond `AMBIGUOUS` lorsqu'un type générique ne départage pas les entités ;
- publie score, sémantique de score, rang et champs de preuve.

## Résultats P5C

| Mesure | Résultat lexical | Gate |
|---|---:|---:|
| Recall@50 | 1,0000 sur 4 612 | ≥ 0,95 |
| NDCG@10 | 1,0000 | ≥ 0,85 |
| top-3, borne Wilson basse | 0,99916777 | ≥ 0,90 |
| no-match, borne Wilson basse | 0,99833692 sur 2 306 | ≥ 0,99 |
| ambiguë, borne Wilson basse | 0,47960954 | ≥ 0,95 |
| violations de contraintes | 0 sur 1 153 | 0 |
| faux regroupements | 0 sur 1 153 | 0 |
| provenance complète | 9 224 / 9 224 | 100 % |
| fausses résolutions semantic-only | 0 sur 1 153 | 0 |

Les 1 153 mismatches sont exclusivement les scénarios
`semantic_only_unresolved` : la voie lexicale retourne `NO_MATCH`, tandis que le
contrat hybride final attend `AMBIGUOUS` après observation d'un candidat
sémantique non résolu. L'identité de cette évaluation est
`sha256:8e1165bcd4108096ce2e1df77bad7e138644162107d8a40e6d59a0af6f81c2db`.

## Preuve PostgreSQL associée

La baseline P5B a démontré sur un non-match synthétique :

- `lower(name) LIKE` : scan séquentiel complet, 572,366 ms et 145 448 blocs lus ;
- `name ILIKE` : bitmap index scan `ix_offers_name_trgm`, 9,137 ms et 622 blocs.

Cette observation ponctuelle prouve la compatibilité index, pas encore un SLO.
P5I devra mesurer P50/P95/P99 sur un replay borné et une fenêtre comparable.

## Limites et gate

- le holdout est synthétique et sans préférence humaine externe ;
- aucun accès réel n'est encore branché sur ce builder ;
- les attributs et rôles structurés restent des garde-fous observés, pas des
  inférences lexicales ;
- les candidats semantic-only ne sont jamais promus par cet adaptateur ;
- aucun lecteur public ne peut utiliser P5D avant P5G à P5J.

P5D est terminale `SAFE_INCOMPLETE`. P5E peut ajouter les sources structurée et
sémantique expand-only sur le même corpus, sans relâcher les tolérances zéro.
