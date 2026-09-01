# FILON — Phase 5 Hybrid Retrieval Execution Plan

- Préparation locale : **1er septembre 2026**
- Ouverture : **1er septembre 2026**
- Statut : **TERMINÉE — PHASE 5 = GO**
- Gate d'entrée : Phase 4 Product Ontology terminale avec verdict GO
- Gate de sortie : **Precision / Recall / NDCG targets**
- Lecteurs publics : **INCHANGÉS**
- Ranking, contraintes et personnalisation : **HORS PÉRIMÈTRE DE PROMOTION**

## Avancement

| Lot | État | Preuve |
|---|---|---|
| P5A — contrat | **TERMINÉ** | contrat v1, manifestes, exemples synthétiques et 12 tests verts |
| P5B — baseline réelle | **TERMINÉ** | agrégats production, audit SQL/index et plans synthétiques |
| P5C — benchmark | **TERMINÉ** | 9 224 cas, oracle ratifié, legacy offer-first détecté `UNSAFE` |
| P5D — lexical | **TERMINÉ** | `SAFE_INCOMPLETE`, index-compatible, zéro failure bloquante |
| P5E — structured + semantic | **TERMINÉ** | expand-only qualifié, zéro promotion semantic-only |
| P5F — fusion et grouping | **TERMINÉ** | RRF product-first, digest et invariance affiliée structurelle |
| P5G — shadow | **TERMINÉ** | migration production `f7c5e9a1b3d6`, writer OFF et idempotence |
| P5H — replay réel | **TERMINÉ** | dry/apply/replay borné ; 1 create puis 1 existing |
| P5I — comparaison | **TERMINÉ** | matrice qualité, couverture, latence, coût et limites publiée |
| P5J — revue de sortie | **TERMINÉ** | Phase 5 = GO ; Phase 6 ouverte ; lecteur public inchangé |

## Objectif

Construire un générateur de candidats produit unique, product-first et à haut
rappel, combinant signaux lexicaux, sémantiques et structurés sans confondre
retrieval et ranking. Une même entité produit ne doit pas apparaître comme
plusieurs recommandations parce que plusieurs marchands la vendent.

Le pipeline cible est :

```text
query observée
  -> intention structurée
  -> contraintes et préférences observées
  -> lexical + semantic + structured retrieval
  -> fusion sourcée
  -> entity grouping
  -> candidats produit
```

Phase 5 produit des candidats et leurs preuves de récupération. Elle ne décide
ni du meilleur produit, ni de la meilleure offre, ni d'un verdict Buy/Wait.

## Invariants non négociables

1. Le retrieval favorise le rappel ; le ranking reste un composant séparé.
2. Aucun candidat n'est inventé lorsqu'une source ou une représentation manque.
3. Un signal lexical, vectoriel ou marchand n'est jamais une identité canonique.
4. Le regroupement réutilise uniquement les identités et abstentions qualifiées
   par Product Identity, Entity Resolution et Product Ontology.
5. Les champs absents restent `UNKNOWN` ; aucun budget, pays, langue, attribut
   ou compatibilité favorable n'est supposé.
6. Les candidats restent product-first ; les offres sont attachées après le
   regroupement, sans dupliquer les produits.
7. Les commissions et relations affiliées ne participent jamais au score de
   récupération produit.
8. Le writer et le dual-read restent désactivés par défaut ; aucun endpoint
   public ne change avant la revue de sortie.

## Décisions à mesurer, pas à présumer

PostgreSQL FTS, `pg_trgm`, recherche vectorielle, Qdrant et un moteur de
recherche dédié sont des candidats techniques. Aucun n'est déclaré canonique
avant comparaison sur le même corpus selon : qualité, latence, coût,
complexité opérationnelle, fraîcheur, rollback et capacité fail-closed.

La recherche sémantique ne peut qu'ajouter des candidats sourcés. Elle ne peut
ni créer une identité, ni rendre répondable une requête dont les contraintes
ou la vérité produit restent inconnues.

## Gates mesurables

| Gate | Seuil ou exigence |
|---|---|
| Recall@50 répondable | ≥ 0,95 |
| NDCG@10 | ≥ 0,85 |
| pertinence top-3 | ≥ 0,90 |
| exactitude `no_match` | ≥ 0,99 |
| exactitude ambiguë | ≥ 0,95 |
| violation de contrainte top-10 | 0 |
| faux regroupement produit | 0 sur le corpus de promotion |
| provenance | 100 % des candidats et signaux traçables |
| reproductibilité | mêmes versions + même instant = même digest |
| performance | P95 ≤ 750 ms hors dépendance tierce froide |

Ces seuils sont évalués séparément par langue, verticale et scénario. Une
moyenne globale ne peut pas masquer une strate en échec. La limitation
`NO_EXTERNAL_HUMAN_GROUND_TRUTH` reste publiée tant qu'aucun corpus externe
indépendant n'existe ; elle n'autorise aucune prétention de préférence humaine.

## Séquence

1. **P5A — contrat** : figer Query, Intent, RetrievalCandidate,
   RetrievalEvidence et RetrievalRun, avec versions et `UNKNOWN` explicite.
2. **P5B — baseline réelle** : mesurer requêtes SQL actuelles, duplication par
   offre, couverture des attributs, latences et tailles de fenêtres sur un lot
   borné sans payload public.
3. **P5C — benchmark** : construire un holdout autonome, adversarial,
   multilingue et multi-vertical couvrant exact product, no-match, ambiguïtés,
   accessoires, contradictions et hard negatives.
4. **P5D — lexical** : qualifier un adaptateur PostgreSQL FTS/`pg_trgm` à haut
   rappel, borné et reproductible.
5. **P5E — structured + semantic** : ajouter les attributs ontologiques puis
   comparer un adaptateur sémantique optionnel sans lui déléguer l'identité.
6. **P5F — fusion et grouping** : fusionner les listes avec une méthode
   versionnée, dédupliquer par entité prouvée et conserver les abstentions.
7. **P5G — shadow expand-only** : ajouter, si nécessaire, index et snapshots
   append-only via migration réversible, writer sec par défaut et flags OFF.
8. **P5H — replay réel** : exécuter un lot production borné puis le rejouer à
   instant identique pour prouver idempotence et absence de double écriture.
9. **P5I — comparaison** : publier qualité, couverture, latence, coût,
   complexité, drift, erreurs, abstentions et gain marginal de chaque stage.
10. **P5J — revue de sortie** : décider GO/NO-GO vers Phase 6 Constraint Engine,
    sans promouvoir le Product Ranking de Phase 7.

## Preuves de sortie obligatoires

- contrats et manifestes versionnés avec exemples synthétiques ;
- corpus déterministe, hashes et mutations adversariales ;
- baseline réelle agrégée et non réidentifiante ;
- matrice lexical / structured / semantic / fusion sur le même holdout ;
- tests de non-invention, non-duplication, provenance et abstention ;
- migration upgrade/downgrade/restauration si le schéma change ;
- CI PostgreSQL et quatre surfaces terminales vertes ;
- replay production borné, idempotent et sans lecteur public ;
- mesures P50/P95/P99, coût et limites connues ;
- reçu final P5 et décision explicite vers Constraint Engine.

## État de sortie

P5A à P5J sont terminales avec le verdict Phase 5 = GO. La migration et le
replay shadow sont qualifiés ; le writer reste OFF et aucun lecteur public ne
change. Phase 6 Constraint Engine est ouverte sans promouvoir le ranking de
Phase 7 ni prétendre disposer d'une vérité humaine externe.
