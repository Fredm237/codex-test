# FILON — Phase 0 Execution Plan

## Objectif

Rendre le rebuild mesurable, réversible et gouvernable avant de modifier le moteur produit. La Phase 0 n'ajoute aucune fonctionnalité visible et ne lance aucun travail 3D, Fashion, Recreate ou refonte éditoriale.

Progression au 31 août 2026 : **P0.0 à P0.7 terminés ; Phase 0 fermée avec verdict GO ; Phase 1 ouverte**. La [décision de timebox](PHASE_0_TIMEBOX_AND_EXIT_DECISION.md) a été exécutée : run 18 interrompu honnêtement, run 19 repris depuis ses checkpoints puis terminé `succeeded`, sondes API/PostgreSQL/Redis/catalogue vertes et moniteur manuel vert. L'absence d'un événement GitHub `schedule` est classée `EXTERNAL_PROVIDER_PENDING / NON_BLOCKING` dans le [reçu final](PHASE_0_FINAL_RECEIPT.md), avec surveillance maintenue. Le reste de l'observabilité avancée reste dans [POST_PHASE_0_HARDENING](POST_PHASE_0_HARDENING.md). Le registre produit E001–E018 est canonique au commit isolé `7753dff` : Enum, catalogue et schéma sont identiques, les valeurs et clés historiques restent stables, et la couverture réelle est bornée aux cinq codes émis par Awin. La séparation commerciale est couverte localement sur la clé Core et le reranker Assistant : deux barèmes synthétiques inversés conservent le classement, tandis que seuls les liens projetés changent ; cela ne prouve ni des taux réels, ni le panier final, ni une neutralité absolue.

Les commits `f5ae21b`, `996ada4` et `1a167dc` durcissent le Core et l'Assistant : stock, prix, devise, preuve explicite et fraîcheur sont exigés ; le TTL de **72 h est provisoire** ; la devise observée est conservée ; la livraison inconnue ne devient ni zéro ni économie comparative ; le budget EUR est fail-closed et aucun FX n'est inventé. L'Assistant exige maintenant `evidence_current=true` de façon explicite, revalide la preuve avant de conserver une carte et utilise le cache moteur v4 afin de ne pas réutiliser les anciennes cartes insuffisamment qualifiées.

Les commits clients `0c6f674` (web), `55aaf41` puis `a78401a` (mobile) ferment les actions marchandes sur une preuve courante : `evidence_current=true`, `observed_at` valide, non futur et âgé d'au plus 72 h, prix positif, devise supportée, stock positif et URL HTTPS avec nom DNS public qualifié ; les hôtes locaux/réservés et littéraux IP sont refusés. Sur mobile, les paramètres de deep-link ne servent qu'à l'affichage : achat, partage, sauvegarde et alerte exigent une revalidation contre le détail Core, et l'alerte revalide encore la preuve au moment de l'enregistrement. Les historiques futurs, multidevises ou sans `in_stock=true` sont rejetés. Les comparaisons restent mono-devise, l'éligibilité expire dynamiquement sur le web comme sur mobile, les tris/filtres prix sans scope devise ont été retirés et les scores Outfit non calibrés sont neutralisés en « Non mesuré ». `a78401a` ajoute la localisation FR/NL/EN des parcours publics et une réconciliation locale sérialisée, sans transformer un prix ou un statut obsolète en claim public. Le proxy Pulse web partage un TTL de **120 s** pour limiter les divergences entre consommateurs ; ce TTL technique ne qualifie pas la fraîcheur commerciale de l'offre.

Les commits `e152ed0`, `4e5755d` et `56de1cf` ferment ensuite les montants
des cartes, rails et fiches web sans rapprochement courant prix–devise–stock.
Le lot `catalog.py`, SearchAssistant et MegaMenu est intégré dans `4a95a42` et
`90246b2`. La preuve locale finale compte **2 020 réussis + 1 ignoré** côté
backend, web **17/17**, typecheck et build de 42 pages. GitHub Actions #343
confirme **2 021/2 021** backend et les trois clients verts. Cette preuve est
détaillée dans la [post-validation protégée](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md).

**P0.2 Quality Lab est terminé sous le nouveau mandat autonome** : la décision fondateur du 31 août 2026 remplace le gate humain bloquant par `AUTONOMOUS_QUALITY_LAB + NO_EXTERNAL_HUMAN_GROUND_TRUTH`. Le contrat externe v0.5, ses sept datasets et son reçu `ready=false` restent dans l'historique et ne sont pas présentés comme satisfaits. La gate active exécute **571 contrôles objectifs** : golden set `REGRESSION_GROUND_TRUTH`, holdout adversarial multi-seed, checksum et identité GTIN/EAN, non-fusion, rattachement, prix, devise, stock, fraîcheur, budget, abstention et concordance multi-source. Les **571/571** passent, avec un conflit correctement `UNRESOLVED`. Les dimensions subjectives restent `PROVISIONAL` ou `NOT_INDEPENDENTLY_VALIDATED` et ne bloquent pas la progression.

**P0.5 Product/Variant, Offer Graph, Merchant Intelligence, Evidence Engine et Catalog Quality Funnel sont terminés en shadows techniques autonomes** : douze tables d'expansion, quatre migrations expand-only, des writers isolés et des backfills bornés/idempotents sont disponibles derrière cinq flags désactivés par défaut. L'identité utilise uniquement `exact-gtin-shadow-v1`. L'Offer Graph conserve argent décimal, devise, stock tri-state et lien HTTPS public. Merchant Intelligence expose des compteurs à dénominateur explicite et ne fabrique aucun score. Evidence enregistre les faits atomiques et refuse les claims forts non prouvés. Le funnel v2 traverse désormais les étapes objectivement mesurables ; `CORRECTLY_CLASSIFIED` reste `provisional`, puis la chaîne s'arrête sur les vrais manques `COMPLETE_LANDED_COST=not_supported` et `confidence_not_independently_calibrated`. Ces limites interdisent les claims correspondants, pas la progression de phase. Les lectures v1 et les flags off restent inchangés.

**P0.6 Observabilité est terminé** : corrélation HTTP, readiness fail-closed, Redis privé, export OpenMetrics, sauvegardes, capacité Railway, Cron mono-exécution, heartbeat, checkpoints et reprise réelle sont acquis. Le run 19 a repris trois checkpoints du run 18, sauté un feed déjà terminé et atteint `succeeded`; le moniteur manuel `33404840701` est vert. Le workflow planifié est présent, valide et actif ; l'absence d'occurrence créée par GitHub reste surveillée comme limitation fournisseur non bloquante. Prometheus/Grafana avancés, backend OTLP, rétention, pager secondaire, trafic représentatif et SLO sont reportés. **P0.7 CI est terminé et intégré** : PR #385 fusionnée dans `main`, run `33404710182` vert sur quatre jobs.

La requalification courante est Actions **#366** (`33337020943`) :
web, mobile, extension, Alembic, les **2 132** régressions backend et la
readiness normale sont verts. Le gate strict reste rouge uniquement parce que
les sept datasets humains sont vides. L'artefact Quality `9739367304`, digest
`sha256:c8e3e9a3d725fc5efe1123e4247f801252b9b2af8674dbf42574f4602328e9d3`,
a été publié.

## Correspondance avec le registre de missions

| Lot du plan | Mission persistante |
|---|---|
| P0.0 | `p0_a` |
| P0.1 | `p0_b` |
| P0.2 | `p0_c` |
| P0.3 | `p0_d` |
| P0.4 | `p0_e` |
| P0.5 | `p0_f` |
| P0.6 | `p0_i` |
| P0.7 | `p0_g` |
| Revue d'entrée Phase 1 | `p0_h` |

## Séquence d'exécution

| Lot | Livrable | Actions | Critère de sortie | Risque / rollback |
|---|---|---|---|---|
| P0.0 — Freeze et ownership — **AUDIT LOCAL TERMINÉ** | Registre de propriétaires et règles de merge | CODEOWNERS et template de preuve livrés ; protéger `main`, geler les features, classifier PR #384 et PR #96 | Aucune fusion sans checks requis ; owner par contexte | Checks d'abord non bloquants si faux positifs |
| P0.1 — Contrats actuels — **TERMINÉ** | Snapshots v1, contract catalog et taxonomie produit v1 | Payloads sentinelles web/mobile/extension, unknown explicite, callers recensés ; E001–E018 versionnés ; Core, catalogue, Assistant, web et mobile durcis ; preuve explicite, expiration 72 h, revalidation Core, mono-devise, stock explicite et liens HTTPS publics sûrs ; horodatages HTTP UTC explicites et URL Assistant/catalogue canonique | Local courant : backend **2 119 + 2 ignorés**, web **17/17**, typecheck et build 42 routes ; aucun caller couvert ne transforme un unknown, une preuve expirée ou une date ambiguë en fait favorable | Adaptateurs v1 et stockage SQL conservés ; TTL 72 h provisoire à recalibrer |
| P0.2 — Quality Lab — **TERMINÉ EN MODE AUTONOME** | Manifeste autonome v1 + historique externe v0.5 conservé | Oracles déterministes, golden set de régression, holdout adversarial multi-seed, concordance/conflit multi-source, statuts de qualité et rapport SHA-256 livrés | **571/571** checks, **7/7** tests, 0 échec bloquant, 1 conflit correctement `UNRESOLVED` | `NO_EXTERNAL_HUMAN_GROUND_TRUTH` permanent ; subjectif provisoire et non bloquant ; aucun claim de précision humaine |
| P0.3 — Migrations — **TERMINÉ** | Alembic baseline `b9db07b15986` et runbook | Schéma photographié ; mode normal sans DDL runtime ; upgrade, stamp, drift, downgrade et restauration testés | Base éphémère reconstruite sans drift et restauration avec donnée sentinelle | Snapshot restauré ; `legacy` seulement pour rollback initial |
| P0.4 — Observation — **TERMINÉ EN SHADOW** | RawSource/Observation/Quarantine + ADR + codes E001–E018 | Payload/checksum/provenance, projection Awin, savepoint et replay versionnés ; producteurs stricts, lecteurs inter-version sans perte ; lectures v1 inchangées | Commit `7753dff` isolé : 29 tests taxonomie/observation/contrats et backend 1 304/1 304 | Flag off par défaut ; valeurs/clés historiques inchangées ; downgrade vers `b9db07b15986` conserve le Core |
| P0.5 — Product/Variant + Offer Graph + Merchant Intelligence + Evidence + Funnel shadows — **TERMINÉ EN SHADOW AUTONOME** | Brand/Family/Model/Variant/Offer/Merchant/Claim v0 et funnel v2 | Douze tables expand-only, backfills contrôlés, exact-GTIN, preuves offre décimales, compteurs sans score, claims fail-closed et funnel autonome livrés | Invariants, adversarial, shadow, intégrité et protections faux-merge verts ; **80/80** sur le lot ciblé courant | Flags off ; coût rendu et confiance non supportés ; aucun claim fort ni backfill implicite ; ces limites n'annulent pas la sortie P0.5 |
| P0.6 — Observabilité — **TERMINÉ** | Minimum critique : API, DB, Redis, catalogue, 5xx et capacité | Sondes + moniteur GitHub 15 min fail-closed ; Cron, heartbeat, checkpoints et reprise réelle | Run 19 `succeeded` ; moniteur manuel `33404840701` vert ; workflow planifié actif ; premier événement `schedule` classé `EXTERNAL_PROVIDER_PENDING / NON_BLOCKING` | Le reste est dans `POST_PHASE_0_HARDENING` et ne bloque pas Product Identity |
| P0.7 — CI complète — **TERMINÉ ET INTÉGRÉ** | Matrice de qualité multi-surfaces | Ruleset `21798272`, PR #385 fusionnée et quatre jobs requis sans bypass | Run `33404710182` : quatre jobs verts sur `main` | Aucun bypass ; intégrité ou régression autonome bloquante ; zéro cas humain non bloquant |

## Gates proposées à ratifier

Les valeurs suivantes sont des seuils de lancement, pas des résultats actuels. Elles doivent être confirmées après constitution des datasets et accompagnées d'un intervalle de confiance.

| Gate | Seuil de passage proposé | Raison |
|---|---:|---|
| Faux merges Product/Variant | ≤ 0,5 % global et aucun segment critique > 1 % | Un faux merge contamine offres, prix et décisions |
| Faux splits | ≤ 2 % | Coût inférieur au faux merge mais nuit à la comparaison |
| Attachement offre → bonne variante | ≥ 98 % sur offres éligibles | Base de comparaison fiable |
| Claims prix/stock/livraison sans `evidence_current=true` et `observed_at` valide ≤ 72 h | 0 | Invariant de confiance ; le TTL reste provisoire |
| Contraintes dures violées dans top-10 | 0 | Budget, pays, safety et stock ne sont pas négociables |
| Recall@50 retrieval | ≥ 95 % sur requêtes répondables | Le ranker ne peut récupérer un candidat absent |
| NDCG@10 | ≥ 0,85 sur test indépendant | Qualité d'ordre utile |
| Calibration, ECE | ≤ 0,05 | La confiance affichée doit correspondre aux erreurs observées |
| Couverture d'explication sourcée | ≥ 99 % des décisions non abstention | Une décision doit être vérifiable |
| P95 API catalogue/retrieval | ≤ 750 ms hors dépendance tierce froide | Cible expérience ; mesurer aussi P50/P99 |
| P95 décision complète | ≤ 2,5 s | Interaction utile sans masquer l'attente |
| Build/tests requis | 100 % verts | Hygiène minimale, jamais preuve métier suffisante |

## Dataset minimal avant Product Graph

- Au moins 2 000 paires positives/négatives d'identité, stratifiées par catégorie, langue, marchand et qualité de titre.
- Au moins 500 familles comportant plusieurs variantes réellement ambiguës.
- Des hard negatives : même modèle/capacité différente, bundle, reconditionné, accessoire compatible, couleur/taille, homonymes de marque.
- Un jeu test figé et aveugle ; aucun correctif de règle ne peut être validé sur le seul cas qui l'a déclenché.
- Double annotation des cas ambigus, désaccord et niveau de certitude conservés.

Ces volumes sont un minimum de démarrage et pourront augmenter après analyse des intervalles de confiance.

## Ordre des premières pull requests

1. `governance/phase-0-baseline` : ce dossier, CODEOWNERS proposé, template ADR et inventaire des contrats ; aucun runtime change.
2. `contracts/v1-snapshots` : fixtures des réponses actuelles et compatibility tests, sans changer les clients.
3. `migrations/alembic-baseline` : baseline du schéma et runbook, sans nouvelle table métier.
4. `quality/entity-datasets` : format d'annotation, premiers jeux indépendants et rapport vide mais exécutable.
5. `observations/schema-shadow` : tables expand-only et writer Awin désactivé par défaut.

Chaque PR annonce : owner, contrats touchés, tables, callers, métriques avant/après, migration, rollback, risques et gates.

## Décisions en attente de preuve

- Fusion ou séparation du service Profile mobile.
- Usage de Qdrant : uniquement si le benchmark démontre un gain par rapport au lexical.
- Conservation de SerpAPI dans un contexte non commercial séparé.
- Seuils finaux de latence et de calibration après trafic et dataset représentatifs.
- Calendrier d'archive de `filon-site`, SmartWave et des agents historiques.

## Condition d'entrée dans la Phase 1

Phase 1 est ouverte par le [reçu final Phase 0](PHASE_0_FINAL_RECEIPT.md). Le
cycle long, heartbeat/reprise, checkpoints, CI/production, migrations,
rollback, backup/restore, Quality autonome, shadows sûrs et protection de
branche sont acquis. Le workflow GitHub est présent sur `main`, actif et
correctement planifié ; l'absence d'une occurrence générée par son fournisseur
reste `EXTERNAL_PROVIDER_PENDING / NON_BLOCKING` et continue d'être surveillée.
Les zéro cas externes et le backlog d'observabilité avancé demeurent
documentés, jamais bloquants.
