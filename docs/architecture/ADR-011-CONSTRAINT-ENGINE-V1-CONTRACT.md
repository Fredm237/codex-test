# ADR-011 — Constraint Engine v1, filtres durs avant préférences

- Statut : **accepté pour shadow**
- Date : **1er septembre 2026**
- Portée : Phase 6 Constraint Engine
- Contrat : `contracts/constraint-engine/v1`
- Lecteurs publics : **inchangés**

## Contexte

Hybrid Retrieval fournit un ensemble de candidats sourcés. Il ne doit ni
interpréter un budget, ni supposer une disponibilité, ni résoudre une
compatibilité, ni appliquer une préférence personnelle. Ces décisions doivent
être observables avant le futur ranking.

## Décision

1. Les contraintes dures sont évaluées avant toute préférence.
2. `UNSATISFIED` produit une exclusion explicite et sourcée.
3. `UNKNOWN` sur une contrainte requise produit une abstention, jamais une
   compatibilité favorable.
4. Seuls les candidats dont toutes les contraintes sont `SATISFIED` ou
   `NOT_APPLICABLE` sont éligibles au futur ranker.
5. Les préférences sont évaluées séparément, sans score ni ordre.
6. Une préférence ne peut jamais réintroduire un candidat exclu ou unknown.
7. Les montants sont atomiques : montant décimal et devise doivent être connus
   et identiques pour comparer un budget.
8. Aucun contexte brut ni profil utilisateur n'est persisté. Le shadow conserve
   un digest, les résultats, leurs motifs et leurs références de preuve.
9. La commission et la relation affiliée sont absentes de l'entrée et du
   résultat.
10. Le composant reste shadow-only jusqu'au benchmark, au replay et à la revue
    de sortie Phase 6.

## Rollback

Le writer est OFF par défaut. La migration est expand-only ; désactiver le flag
retire immédiatement le composant du chemin de maintenance sans modifier
Hybrid Retrieval, le catalogue ou les lecteurs publics.
