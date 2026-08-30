# FILON — Target Architecture

## 1. Principe directeur

La décision est un produit de preuves. Une interface ne peut afficher un produit, un prix, une disponibilité, une livraison, un verdict ou une explication que si le claim est relié à une observation admissible, fraîche et versionnée. L'absence de preuve produit `unknown` ou une abstention, jamais une valeur favorable par défaut.

## 2. Chaîne canonique

```text
Source Registry
  → Raw Source Store (immutable)
  → Observation Store (field-level provenance)
  → Normalization (versioned)
  → Entity Resolution
  → Product Graph → Variant Graph
  → Offer Graph → Merchant Intelligence
  → Evidence Layer + Claim Eligibility
  → Candidate Generation
  → Hard Constraints
  → Ranking + Calibration
  → Decision + Explanation + Abstention
  → versioned API/SDK
  → web / mobile / extension
```

Chaque flèche est observable : version d'entrée, version de sortie, raison d'exclusion, latence, taux d'unknown et identifiant de trace.

## 3. Bounded contexts et ownership

| Contexte | Possède | N'a pas le droit de posséder |
|---|---|---|
| Source Registry | Source, marchand, autorisation, cadence, schéma attendu | Produit canonique ou décision |
| Observation | Payload brut, champ observé, source, horodatage, checksum | Valeur normalisée non sourcée |
| Catalog Core | Brand, Family, Model, Variant, Offer et identités | Profil utilisateur |
| Merchant Intelligence | Fiabilité, couverture, freshness et règles marchand | Altération silencieuse d'une observation |
| Evidence | Faits, statut, confidence, provenance, validity window | Ranking opaque |
| Retrieval | Candidats et raisons de rappel | Verdict final |
| Constraint Engine | Budget, pays, disponibilité, exclusions, compatibilité | Préférence implicite |
| Ranker | Scores composés versionnés et calibration | Invention de facts |
| Decision Engine | Acheter/attendre/abstain, alternatives et explication | Modification du catalogue |
| Profile | Consentement, préférences, historique autorisé | Produit/offre canonique |
| Experience APIs | Projection adaptée au client | Logique métier divergente |

## 4. Modèle minimal du Product Graph

| Entité | Identité | Champs structurants | Règle d'inconnu |
|---|---|---|---|
| `Brand` | `brand_id` stable + aliases sourcés | nom canonique, domaines, ids externes | Pas de marque déduite sans evidence |
| `ProductFamily` | `family_id` | brand, gamme, catégorie | Peut rester absent |
| `ProductModel` | `model_id` | family, model name/code, release facts | Aucun merge sur similarité textuelle seule |
| `Variant` | `variant_id` | model, GTIN/EAN/MPN/SKU, couleur, taille, capacité, bundle | Attributs inconnus restent null/unknown |
| `Offer` | `offer_id` stable par source + external id | merchant, variant nullable, URL, état, observed_at | Une offre non résolue reste en quarantaine consultable |
| `OfferObservation` | id immuable | price Money, stock tri-state, shipping, seller, checksum | Aucun default favorable |

Une offre peut exister avant sa résolution produit. Elle ne devient éligible à une recommandation qu'après validation des claims obligatoires. Les faux merges sont plus graves que les faux splits : le moteur s'abstient de fusionner quand la preuve est insuffisante.

## 5. Contrats fondamentaux

```text
Money              = { amount: DecimalString, currency: ISO-4217 }
Known<T>            = { state: "known", value: T, evidence_ids: [...] }
Unknown             = { state: "unknown", reason_code, observed_at? }
Availability        = known("in_stock" | "out_of_stock" | "preorder") | unknown
Claim               = { subject_id, predicate, value, evidence_ids, policy_version }
Decision            = { outcome, candidates, constraints, claims, confidence, abstention_reason, trace_id }
```

Les contrats sont versionnés, avec compatibilité annoncée et changelog. Les
classes `SOURCE_UNAVAILABLE`, `OBSERVATION_STALE`, `IDENTITY_AMBIGUOUS`,
`CONSTRAINT_UNSATISFIED`, `EVIDENCE_INSUFFICIENT`, `DEPENDENCY_TIMEOUT` et
`INTERNAL_INVARIANT` décrivent des états opérationnels futurs ; elles ne doivent
pas être confondues avec la
[taxonomie E001–E018 des erreurs de qualité produit](ERROR_TAXONOMY.md), dont les
valeurs persistées sont versionnées séparément.

## 6. Retrieval et décision

1. Résoudre l'intention sans ajouter de catégorie absente de la requête.
2. Générer un ensemble large par lexical, identifiants, taxonomie et, après preuve de gain, vecteur.
3. Appliquer les contraintes dures avant le ranking : pays, budget, adult safety, disponibilité prouvée et exclusions.
4. Classer sur des features documentées : pertinence, qualité d'identité, fraîcheur, prix comparable, confiance marchand.
5. Calibrer les scores sur un jeu indépendant.
6. Assembler les claims et supprimer tout candidat qui ne satisfait pas la policy d'éligibilité.
7. Décider, expliquer ou s'abstenir avec un `trace_id`.

Le LLM peut analyser une intention ou formuler une explication à partir de faits fournis. Il ne crée ni produit, ni prix, ni stock, ni score de confiance métier.

## 7. Clients et personnalisation

- `filon-web` est la référence fonctionnelle et SEO.
- Mobile et extension consomment le même SDK et les mêmes décisions ; un BFF ne conserve que les besoins d'expérience, d'auth et de synchronisation.
- Le profil personnel est séparé du graphe produit, soumis au consentement et à l'effacement.
- La personnalisation re-rank des candidats éligibles ; elle ne contourne jamais contraintes, evidence ou safety.
- Fashion/Recreate sont des plug-ins post-core. Ils restent derrière des feature flags jusqu'à validation des gates.

## 8. Migration sans big bang

| Étape | Écriture | Lecture | Validation | Rollback |
|---|---|---|---|---|
| 1. Baseline | Schéma actuel | Schéma actuel | Contrats figés et snapshots | Aucun changement runtime |
| 2. Expand | Nouvelles tables/colonnes nullable | Ancien modèle | Migration Alembic + sauvegarde | Downgrade ou colonnes ignorées |
| 3. Shadow | Double écriture observation/graphe | Ancien modèle | Checksums, drift, false merge/split | Désactiver writer v2 |
| 4. Dual read | Ancien résultat servi, v2 comparé | v1 + shadow v2 | Parity, top-k, latence, eligibility | Flag vers v1 |
| 5. Canary | v2 servi à une fraction contrôlée | v2 avec fallback v1 | SLO et métriques métier | Kill switch immédiat |
| 6. Cutover | v2 autoritaire | v2 | Fenêtre d'observation | Read fallback limité |
| 7. Contract | Arrêt v1 | v2 | Appelants à zéro, ADR | Restaurer tag/migration avant purge |

## 9. ADR à ouvrir avant implémentation

1. Identité Product/Model/Variant et politique de merge :
   [ADR-002 proposé et implémenté en shadow exact-GTIN](ADR-002-PRODUCT-GRAPH-IDENTITY-SHADOW.md).
2. Money, availability, shipping et représentation de `unknown`.
3. Ownership Profile entre backend historique et mobile.
4. Contrat API versionné et génération des SDK.
5. Raw retention, PII, durées de conservation et droit à l'effacement.
6. Stratégie retrieval lexical/hybride et protocole d'évaluation.
7. Policy de claim eligibility et seuils d'abstention.

Ces ADR sont `proposed` tant que les mesures Phase 0 ne permettent pas de les accepter.
