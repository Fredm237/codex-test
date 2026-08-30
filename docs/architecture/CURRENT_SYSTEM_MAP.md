# FILON — Current System Map

## 1. Flux réellement en place

```text
Awin API / feeds
      │
      ▼
ingest/awin_catalog + services/awin_catalog
      │
      ├── shadow opt-in ─→ raw_source_records ─→ observations
      │                                      └─→ quarantine_records
      │  legacy v1 : normalisation, EAN, taxonomie et regroupement mêlés
      ▼
PostgreSQL: merchants → offers → catalog_products(EAN)
                         └──────→ price_snapshots
      │
      ├── api/routes/catalog.py ──→ filon-web (canonique)
      │                         ├─→ filon-mobile (client direct)
      │                         └─→ filon-extension (redirige vers filon.be)
      │
      ├── services/search + catalog_search + relevance
      │                         └─→ advise / stream
      │
      └── intelligence/* ─────────→ outfit / faits / relations / traces

filon-mobile possède en parallèle un serveur Express/tRPC et une base MySQL
pour l'identité utilisateur, les alertes, les collections et Recreate.
```

Le Quality Lab forme un circuit de preuve séparé du runtime produit :

```text
cas réels anonymisés
      │
      ├──→ pack aveugle humain A ─┐
      └──→ pack aveugle humain B ─┴→ merge / adjudication humaine
                                      │
                                      ▼
                             cinq golds v0.3 figés
                                      │
run + cinq prédictions + digests ─────┴→ scorecard fail-closed
```

Les `source_pack_fingerprints` engagent les packs complétés, annotations
comprises. Decision transporte en entrée un inventaire de preuves et de
provenance ; le système évalué ne peut pas auto-attester ses claims.

La couche `raw_source → observation → quarantine` existe désormais en shadow,
append-only et derrière `OBSERVATION_SHADOW_ENABLED`. Elle n'a aucun lecteur v1.
Sans activation sur un lot réel, sa couverture production reste à mesurer.

## 2. Cartographie par domaine

| Domaine / module | Responsabilité actuelle | Entrées principales | Sorties / appelants | Données et dépendances | Couverture actuelle | Diagnostic | Cible |
|---|---|---|---|---|---|---|---|
| `filon-backend/app/main.py`, `api/routes/*` | Composition FastAPI, santé, chat, advise, catalogue, intelligence | HTTP, configuration | Web, mobile, opérations | PostgreSQL, cache, fournisseurs LLM | Tests routes/santé/catalogue | REFACTOR | API versionnée, routes minces, contrats canoniques |
| `core/observability.py`, `core/local_alerts.py`, `core/distributed_rate_limit.py`, `api/middleware.py`, `api/routes/health.py` | Corrélation HTTP et pipeline, latences, readiness, alertes locales et front door pseudonymisée locale ou Redis atomique opt-in | Requêtes HTTP, scope ASGI ou `X-Real-IP` Railway explicite, sorties decision/recommend, ingestion/observation, DB, Redis, révision Alembic | Logs échantillonnés, headers, 429/503, probes, `/health/metrics` et candidat local sans endpoint d'alerte | HMAC sans adresse brute, plafond local ou registre Redis partagé borné, identité Railway fermée sur en-tête ambigu, aucune requête/IP/identifiant d'offre dans les agrégats | Lot Railway : 180 ciblés ; backend 2 067 réussis + 2 ignorés ; identité edge réelle prouvée, quota production encore local | KEEP + EXTEND | Redis privé activé/testé ou WAF, ordonnanceur, export, propagation, dashboards et pager testés |
| `api/routes/catalog.py` | Lecture catalogue **et** opérations admin/sync/rebuild/purge | Query params, DB, headers admin | Toutes les surfaces catalogue | 2 106 lignes, modèles SQL, taxonomie, sync | Nombreux tests de régression | REWRITE par extraction | Séparer Query API, Admin API et jobs d'ingestion |
| `ingest/*`, `services/awin_catalog.py`, `observations/*`, `core/error_taxonomy.py` | Import Awin v1 + projection shadow raw/observations/quarantaine et registre E001–E018 | Awin API/feeds | Core v1 inchangé ; trois tables shadow | Awin, HTTP, SQLAlchemy, taxonomie produit v1 | Replay, idempotence, unknown, savepoint, migration, valeurs et clés d'erreur stables | KEEP + HARDEN | Activer sur lot borné puis mesurer couverture et rejets ; instrumenter les treize codes sans producteur avant toute revendication exhaustive |
| `services/taxonomy.py` | Classification multilingue par règles | Titres, catégories marchand, marque | Champs taxonomie de l'offre, recherche | 2 360 lignes, listes/règles codées | Beaucoup de tests marchand/cas | REWRITE incrémental | Taxonomy service versionné, règles déclaratives, provenance |
| `services/catalog_grouping.py`, `services/dedup.py` | Regroupement surtout fondé sur l'EAN et déduplication | Offres normalisées | `catalog_products`, liens `offer.product_id` | SQL/heuristiques | Tests grouping/dedup | REWRITE | Entity Resolution séparée : Brand/Family/Model/Variant |
| `services/search.py`, `catalog_search.py`, `relevance.py` | Rappel SQL, intentions et classement heuristique | Requête, budget, pays | Catalogue et recommandation | LIKE/pg_trgm, taxonomie, règles | Tests search/relevance/intents | REFACTOR majeur | Candidate generation → constraints → ranking → evidence → abstention |
| `services/recommend.py`, `services/decision.py`, `services/verdict.py`, `catalog_search.py` | Cartes de résultat, recherche, verdicts et explications historiques | Catalogue, requête, historique | SSE web et autres callers historiques | Cache, catalogue, Awin, LLM | Hors périmètre de `f5ae21b` : `recommend.py` et `catalog_search.py` conservent un fallback de devise vers EUR ; vérité unknown non prouvée de bout en bout | FREEZE + REFACTOR | Retirer les fallbacks favorables, puis converger vers le Decision Engine unique |
| `agents/price_compare.py`, `agents/decision.py` | Comparaison d'offres et construction de la réponse `/advise` | Candidats, requête, budget EUR | `/advise` | Catalogue Awin et orchestration agents | Commit `f5ae21b` : stock, fraîcheur, prix et EUR exigés ; total livré et économie uniquement sur livraison comparable ; budget appliqué au montant calculable | KEEP + HARDEN | Même Decision Engine déterministe ; Money décimal et moteur FX avant toute comparaison multidevise |
| `agents/*` | Orchestration historique de recherche/reviews/décision | État agent et produits | Chat/advise historiques | Services et LLM | Tests partiels | ARCHIVE après callers audit | Aucun moteur métier concurrent ; orchestration fine seulement |
| `intelligence/contracts.py`, `models.py` | Evidence, faits, relations, traces, feedback, benchmark | Offres/produits, analyse | API intelligence, analyse tenue | Tables `intelligence_*` | Tests intelligence | KEEP + HARDEN | Evidence Layer canonique relié aux observations/version des contrats |
| `intelligence/general_*`, `fashion.py`, `catalog_adapter.py` | Second parcours d'intention, décision et tenue | Requête, budget EUR, snapshot offre | API Outfit Studio | Catalogue + tables intelligence | Commit `f5ae21b` : parcours général éligible seulement avec prix/devise/stock/fraîcheur connus et budget EUR fail-closed sans FX ; ses recommandations sont `not_calibrated`, mais son abstention reste `0`/`low` et Fashion conserve un score heuristique | FREEZE + REFACTOR | Client du même retrieval/decision core ; normaliser l'abstention, retirer la confiance Fashion non calibrée et n'exposer aucune confiance avant preuve indépendante |
| `llm/*` | Routage de fournisseurs et provider mock | Prompts, variables d'environnement | Ranking/intention/agents | APIs OpenAI-compatibles | Tests indirects | REFACTOR | LLM hors chemin de vérité ; sorties structurées, versionnées et évaluées |
| `db/models.py`, `db/session.py`, `alembic/*` | Modèles SQL et validation de révision | Déclarations SQLAlchemy/Alembic | Tous les services backend | PostgreSQL ; DDL legacy uniquement en rollback explicite | Upgrade/stamp/drift/downgrade/restauration | KEEP + HARDEN | Alembic obligatoire, expand/shadow/contract |
| `schemas/*`, `contracts/v1`, `contracts/taxonomies/v1` | Contrats Pydantic historiques + baseline inter-clients figée + taxonomie interne des erreurs produit | Routes, JSON Schemas et quarantaine shadow | Web, mobile, extension, producteurs internes et tests | Types Python/JSON | Compatibility suite publique v1 et parité Enum/registre/schéma E001–E018 | KEEP v1 + REWRITE v2 | SDK générés, unknown explicite, Money décimal et lecteurs inter-version sans remap |
| `filon-web` | Interface web canonique Next.js | API backend, contenu éditorial | Utilisateur final, SEO | Vercel, Railway | Copie de travail : 17/17 tests, typecheck et build 42/42, mais grâce à des modifications utilisateur protégées ; état versionné de la branche : 5 échecs MegaMenu | KEEP + REFACTOR client | Client mince du core, états d'incertitude standardisés ; intégrer les correctifs protégés seulement après autorisation et revue |
| `filon-mobile/app`, `hooks`, `lib/filon-api.ts` | Client Expo, catalogue direct, journal et personnalisation locale | API FILON + stockage local | Utilisateur mobile | Railway, Expo, React Query | Tests unitaires de règles locales | KEEP + REFACTOR client | Contrats générés du core, zéro décision produit parallèle |
| `filon-mobile/server`, `drizzle` | Auth, alertes, collections, Recreate via Express/tRPC | App mobile, OAuth, image | Mobile | MySQL, Drizzle, services Forge | Tests partiels | MIGRATE | Identity/Profile service partagé ou BFF sans cerveau produit |
| `filon-extension` | Extension Manifest V3 ; capture contexte et redirection vers `filon.be` | Page marchande | Web FILON | Chrome APIs | Syntaxe seulement | KEEP + HARDEN | Client contextuel du core, contrats et tests d'intégration |
| `filon-site` | Ancien site HTML statique avec séquences simulées | Fichiers statiques | Aucun appelant légitime identifié | Aucune donnée live fiable | Aucun test | ARCHIVE | Sortir du chemin de production, puis supprimer après validation historique |
| Racine `api/`, `core/`, `data/`, `optimization/`, `robustness/`, `strategies/` | SmartWave Quant Lab, produit étranger à FILON | Marchés financiers | Scripts racine | Dépendances Python séparées | Tests/usage non établis dans FILON | ARCHIVE | Dépôt séparé ou archive historique ; jamais dans le runtime FILON |
| `.claude/agent` | Mission persistante et garde-fous locaux | État JSON | Contributeurs/agents | Fichiers versionnés | Validation intégrée au script | KEEP + CLEAN | Mission Phase 0 alignée sur les gates |
| `.github/workflows` | Workflow Phase 0 multi-surfaces prêt localement ; readiness Quality configurée pour devenir un artefact de CI | Push/PR | GitHub checks | Python 3.12, Node 22, pnpm 9.12 | Commit `45e7768` : intégrité invalide = exit 2, validité mais NO-GO = exit 0 ou 1 en strict ; artefact prévu `quality-readiness-*` ; 5 tests MegaMenu rouges dans l'état versionné | IN PROGRESS | Publier le workflow, stabiliser tous les checks puis les rendre requis sur `main` ; aucune de ces protections n'est encore observée à distance |
| `quality/`, `filon-backend/quality_lab` | Contrat v0.3 fermé à cinq datasets, packs aveugles, provenance Decision, readiness et scorecard fail-closed | Candidats anonymisés, deux packs complétés sous identifiants distincts, adjudications, run et cinq fichiers de prédictions séparés | Golds fingerprintés, rapport de readiness et scorecard `pass`/`fail`/`not_measurable` | JSON Schema strict, empreintes canoniques, supports minimaux, Wilson sur gates binomiaux/couverture, golden bootstrap non éligible ; retrieval/NDCG/ECE encore ponctuels | Commits `5ee87f2` et `45e7768` ; Quality **262/262** ; archive propre backend **1 659/1 659**, 7 warnings historiques ; `integrity_valid=true`, `ready=false`, `status=not_ready`, 0 cas humain | IN PROGRESS | Collecter le holdout indépendant stratifié, garantir humainement l'indépendance des annotateurs et ajouter les intervalles manquants avant gate final |

## 3. Sources de vérité actuelles et cibles

| Concept | Source actuelle | Conflits / consommateurs | Verdict | Source cible |
|---|---|---|---|---|
| Marchand | PostgreSQL `merchants` | Profils calculés dans route catalogue ; frontend remappe | KEEP | `Merchant` + `MerchantObservation`, statut et fraîcheur |
| Offre | PostgreSQL `offers` ; `graph_offer_observations` append-only en shadow local | DTO Python, TypeScript web et mobile dupliqués ; aucun lecteur public Graph | KEEP + MIGRATE + SHADOW | `Offer` versionnée, argent décimal, stock tri-state, provenance et fraîcheur |
| Payload source Awin | `raw_source_records` en shadow, flag off | Aucun lecteur public | KEEP SHADOW | Raw immuable, rétention approuvée et replay versionné |
| Observation champ | `observations` en shadow | Aucun lecteur public | KEEP SHADOW | Evidence/claim eligibility après benchmark |
| Anomalie ingestion | `quarantine_records` en shadow + `ProductErrorCode`/`contracts/taxonomies/v1` | Seuls E008, E010 et E016–E018 ont un producteur ; revue interne à construire | KEEP SHADOW | Workflow humain de release/discard, instrumentation des treize codes restants et régression |
| Prix courant | `offers.price` en float, avec devise conservée dans le parcours `/advise` agents | Snapshots et clients en `number` ; budget public en EUR, aucun moteur FX ; certains callers historiques infèrent encore EUR | REWRITE | `Money{amount_decimal,currency}` + observation horodatée ; conversion sourcée avant comparaison multidevise |
| Historique prix | `price_snapshots` | Relief/verdict | KEEP + HARDEN | Série d'observations sourcées et règle d'éligibilité |
| Produit | `catalog_products`, groupé par EAN ; huit tables `graph_*` en shadow local | Ancienne table `products`, logique grouping, DTO mobiles ; aucun lecteur public Graph | REWRITE + SHADOW | Product Graph : Brand → Family → Model → Variant, après qualification indépendante |
| Variante | `graph_variants` en shadow exact-GTIN, flags off | Aucun consommateur v2 ; titre/marque/catégorie interdits comme preuve d'identité | KEEP SHADOW | `Variant` et attributs discriminants avec confiance calibrée ; unknown explicite |
| Taxonomie | `services/taxonomy.py` + colonnes d'offre | Règles et correctifs marchands | REWRITE | Taxonomie versionnée, règles déclaratives, evidence |
| Disponibilité | `offers.in_stock` nullable ; `schemas/advise.py` conserve `None` | `/advise` agents et le planificateur général exigent `in_stock is True` et une fraîcheur de **72 h provisoire** ; couverture des callers historiques encore ouverte | KEEP + HARDEN | `unknown/in_stock/out_of_stock`, provenance et politique de fraîcheur mesurée ; jamais de défaut positif |
| Livraison | Absente des feeds principaux ; `schemas/advise.py` conserve `None` | Dans `/advise` agents, aucun total livré complet, économie moyenne ou écart en euros n'est affirmé sans coût observé ; couverture des autres moteurs encore à prouver | KEEP + HARDEN | Unknown explicite ou observation sourcée ; jamais « gratuit » par défaut et comparabilité fail-closed |
| Preuve | `Evidence` dataclass + `intelligence_product_facts` | Non imposée à tous les verdicts | KEEP + EXTEND | Evidence Store central + claim eligibility |
| Décision | Trois familles de moteurs (`agents`, `services`, `intelligence`) | Web advise, chat, Outfit Studio ; budget EUR et devises sans FX | CONSOLIDATE | Decision Engine unique, règles versionnées et trace ; confiance `not_calibrated` jusqu'à preuve de calibration |
| Vérité d'évaluation | Quality Lab v0.3 : cinq golds humains, provenance et packs complétés fingerprintés | Aucun gold humain présent ; le bootstrap historique n'est pas indépendant | KEEP CONTRACT + COLLECT | Holdout figé, supports minimaux atteints et scorecard fail-closed en CI |
| Profil utilisateur | Backend PostgreSQL historique + mobile MySQL + local storage | Web/mobile divergents | REWRITE | Profile Service commun, consentement, provenance et effacement |
| Contrats API | `contracts/v1` publié ; Pydantic/dataclasses/TS encore manuscrits | Web/mobile/extension | KEEP v1 + REWRITE v2 | Schéma versionné publié et clients générés |
| Configuration | Variables d'environnement, defaults Python/TS | Deux backends et déploiements distincts | HARDEN | Registre de configuration validé, environnements explicites |

## 4. Tables persistées observées

### Backend PostgreSQL

- Héritage : `users`, `products`, `search_logs`, `alerts`.
- Catalogue : `merchants`, `catalog_sync_runs`, `catalog_products`, `offers`, `price_snapshots`.
- Intelligence : `intelligence_product_facts`, `intelligence_relations`, `intelligence_traces`, `intelligence_feedback`, `intelligence_benchmarks`.
- Observation shadow : `raw_source_records`, `observations`, `quarantine_records`.
- Product/Variant Graph shadow : `graph_brands`, `graph_brand_aliases`,
  `graph_product_families`, `graph_product_models`, `graph_variants`,
  `graph_identifiers`, `graph_identifier_evidence`,
  `graph_offer_variant_links`.
- Offer Graph shadow : `graph_offer_observations`.

### Mobile MySQL

- `users`, `price_alerts`, `push_devices`, `saved_collections`, `saved_collection_members`.

Cette double persistance utilisateur est une frontière à formaliser, pas à fusionner brutalement. Toute migration devra définir propriétaire, double écriture temporaire, réconciliation et rollback.

## 5. Dépendances externes

| Système | Usage | Risque actuel | Contrat cible |
|---|---|---|---|
| Awin | Marchands, feeds, liens affiliés | Schéma/qualité variables ; ingestion directe | Adaptateur versionné, raw retention, replay, quota et freshness |
| PostgreSQL | Catalogue et intelligence | Migrations ad hoc au démarrage | Alembic, sauvegarde, réplica de lecture, SLO |
| Redis / cache mémoire | Cache recommandation | Sémantique de cache peu visible | Clés versionnées, TTL par domaine, invalidation mesurée |
| Qdrant | Prévu pour retrieval | Usage canonique non démontré | Option après baseline lexical/hybride, jamais source de vérité |
| LLM providers | Intention/ranking/analyse | Provider mock et repli implicite possibles | Enrichissement non autoritaire, budget, trace et évaluation |
| SerpAPI | Code de fallback recherche | Source non partenaire incompatible avec le parcours de confiance | Retirer du chemin commercial ; conserver seulement si usage séparé approuvé |
| Railway | API backend publique | Build web tolère son indisponibilité | Health/SLO et tests contractuels hors build statique |
| Vercel | Web canonique | Check déploiement seul sur certains commits | Preview + tests contractuels requis |
| Expo / services Forge | Mobile, OAuth, média/LLM | Second backend et dépendance fournisseur | BFF borné, consentement et erreurs explicites |

## 6. Points de contrôle immédiats

1. Aucun chantier visuel, Fashion ou Recreate ne peut devenir P0.
2. `filon-web` reste la surface canonique ; `filon-site` doit être archivé, pas maintenu.
3. `catalog_products` ne doit pas être renommé « Product Graph » : le modèle manque Brand/Family/Model/Variant et des identités alternatives.
4. Les tables `intelligence_*`, l'EAN validé, les sync runs et les snapshots sont des fondations utiles, à migrer avec compatibilité.
5. Les clients ne doivent plus définir séparément les valeurs par défaut et la signification de `unknown`.
6. Les métriques et cinq règles locales ne constituent pas un SLO : aucun
   seuil P95/P99, d'erreur, d'abstention ou de couverture ne peut être déclaré
   atteint avant mesure distribuée sur trafic représentatif.
7. Un score Quality Lab n'est publiable que si le roster exact, les digests, le
   holdout, les supports minimaux et tous les gates sont valides. Les gates
   binomiaux et de couverture utilisent les bornes prudentes de Wilson à 95 % ;
   `recall@50`, `NDCG@10` et `ECE` restent ponctuels et doivent recevoir une
   méthode d'intervalle avant le gate final.
