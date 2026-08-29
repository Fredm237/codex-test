# FILON — Phase 0 Execution Plan

## Objectif

Rendre le rebuild mesurable, réversible et gouvernable avant de modifier le moteur produit. La Phase 0 n'ajoute aucune fonctionnalité visible et ne lance aucun travail 3D, Fashion, Recreate ou refonte éditoriale.

Progression au 29 août 2026 : **P0.0 audit, P0.1 contrats/unknown, P0.3 migrations, P0.4 Observation shadow et P0.7 CI/gouvernance terminés**. Le registre produit E001–E018 est canonique au commit isolé `7753dff` : Enum, catalogue et schéma sont identiques, les valeurs et clés historiques restent stables, et la couverture réelle est bornée aux cinq codes émis par Awin. La séparation commerciale est couverte localement sur la clé Core et le reranker Assistant : deux barèmes synthétiques inversés conservent le classement, tandis que seuls les liens projetés changent ; cela ne prouve ni des taux réels, ni le panier final, ni une neutralité absolue.

Les commits `f5ae21b`, `996ada4` et `1a167dc` durcissent le Core et l'Assistant : stock, prix, devise, preuve explicite et fraîcheur sont exigés ; le TTL de **72 h est provisoire** ; la devise observée est conservée ; la livraison inconnue ne devient ni zéro ni économie comparative ; le budget EUR est fail-closed et aucun FX n'est inventé. L'Assistant exige maintenant `evidence_current=true` de façon explicite, revalide la preuve avant de conserver une carte et utilise le cache moteur v4 afin de ne pas réutiliser les anciennes cartes insuffisamment qualifiées.

Les commits clients `0c6f674` (web), `55aaf41` puis `a78401a` (mobile) ferment les actions marchandes sur une preuve courante : `evidence_current=true`, `observed_at` valide, non futur et âgé d'au plus 72 h, prix positif, devise supportée, stock positif et URL HTTPS avec nom DNS public qualifié ; les hôtes locaux/réservés et littéraux IP sont refusés. Sur mobile, les paramètres de deep-link ne servent qu'à l'affichage : achat, partage, sauvegarde et alerte exigent une revalidation contre le détail Core, et l'alerte revalide encore la preuve au moment de l'enregistrement. Les historiques futurs, multidevises ou sans `in_stock=true` sont rejetés. Les comparaisons restent mono-devise, l'éligibilité expire dynamiquement sur le web comme sur mobile, les tris/filtres prix sans scope devise ont été retirés et les scores Outfit non calibrés sont neutralisés en « Non mesuré ». `a78401a` ajoute la localisation FR/NL/EN des parcours publics et une réconciliation locale sérialisée, sans transformer un prix ou un statut obsolète en claim public. Le proxy Pulse web partage un TTL de **120 s** pour limiter les divergences entre consommateurs ; ce TTL technique ne qualifie pas la fraîcheur commerciale de l'offre.

Les commits `e152ed0`, `4e5755d` et `56de1cf` ferment ensuite les montants
des cartes, rails et fiches web sans rapprochement courant prix–devise–stock.
Le lot `catalog.py`, SearchAssistant et MegaMenu est intégré dans `4a95a42` et
`90246b2`. La preuve locale finale compte **2 020 réussis + 1 ignoré** côté
backend, web **17/17**, typecheck et build de 42 pages. GitHub Actions #343
confirme **2 021/2 021** backend et les trois clients verts. Cette preuve est
détaillée dans la [post-validation protégée](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md).

**P0.2 Quality Lab reste en cours** : le contrat v0.5 ferme le roster à sept datasets et 27 gates, exécute les moteurs sur une entrée aveugle, lie l'identité du run au manifeste/adaptateurs/sorties, empreinte le contenu exact du holdout et compare deux scorecards sans accepter de roster tronqué. La publication du run est atomique et sans remplacement. Le moteur Decision réel est désormais branché avec une requête fermée, une horloge de benchmark déterministe et des claims sourcés ; cinq adaptateurs applicatifs sont donc disponibles et seuls `variant_resolution` et `offer_attachment` restent fail-closed. Les **359 tests Quality** et la suite backend courante (**2 012 réussis + 1 ignoré**) sont verts. La readiness normale sort avec 0 et la stricte avec 1, mais l'état réel reste `integrity_valid=true`, `ready=false`, `status=not_ready` avec **0 cas humain**. Aucun rapport de régression métier n'est donc mesurable. L'archive propre historique du HEAD `a78401a` compte **1 907 tests backend réussis + 1 ignoré**, 7 warnings, en 370,53 s. Le mobile versionné `a78401a` compte **326 tests réussis + 4 smoke tests ignorés**, un typecheck vert et ESLint à **0 erreur / 17 avertissements** ; la revue finale ne relève aucun P0, P1 ou P2. La même archive passe le typecheck, les gates web contrat/claims/vérité produit et le build de production ; sa suite web complète reste à **12/17**, avec cinq échecs MegaMenu exclusivement liés aux correctifs locaux protégés non intégrés.

**P0.6 Observabilité est verte localement mais incomplète en production** : corrélation HTTP, huit jalons décisionnels, spans PostgreSQL/Redis/Awin/SerpAPI/LLM, propagation W3C vers les dépendances HTTP, téléchargement Awin réellement streamé avec bornes compressée/décompressée/lignes, percentiles, readiness fail-closed, moteur local de cinq règles, front door anti-spoofing/bornée, limite Redis atomique opt-in et export OpenMetrics 1.0 authentifié sont testés. Un pack Prometheus/Grafana fail-closed ajoute une configuration sans cible par défaut, 11 rollups multi-réplica testés et un dashboard descriptif sans SLO. Son activation est fermée par un compilateur d’inventaire atomique et un vérificateur HTTPS qui produit un reçu sans hôte ni secret ; aucun reçu n’est fabriqué sans infrastructure. Le lot Redis et identité `X-Real-IP` passe **138 tests ciblés** et la suite backend finale (**2 065 réussis + 2 ignorés**). Backend de traces, preuve Railway réelle, activation Redis ou WAF, agrégateur effectivement déployé, scrapes/rétention, pager et trafic représentatif manquent encore. **P0.7 CI est terminé** : branche publique byte-identique, Actions #343, artefact Quality, preview Vercel et ruleset `21798272` active sur `main` sans bypass sont prouvés dans le [rapport distant](PHASE_0_REMOTE_QUALIFICATION_REPORT.md). P0.5 Product Graph reste **NO-GO** jusqu'aux annotations indépendantes exigées par P0.2.

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
| P0.1 — Contrats actuels — **TERMINÉ** | Snapshots v1, contract catalog et taxonomie produit v1 | Payloads sentinelles web/mobile/extension, unknown explicite, callers recensés ; E001–E018 versionnés ; Core, catalogue, Assistant, web et mobile durcis ; preuve explicite, expiration 72 h, revalidation Core, mono-devise, stock explicite et liens HTTPS publics sûrs ; lots protégés intégrés | Local : backend 2 020 + 1 ignoré, web 17/17, typecheck/build ; Actions #343 : backend 2 021/2 021 et clients verts ; aucun caller couvert ne transforme un unknown ou une preuve expirée en fait favorable | Adaptateurs v1 conservés ; TTL 72 h provisoire à recalibrer ; UTC naïf et URL canonique restent des limites suivies |
| P0.2 — Quality Lab — **EN COURS** | Sept datasets v0.5 : taxonomy, entity, variant, attachment, offer truth, retrieval, decision | Formats, schémas, packs aveugles, accord humain, anti-fuite, métriques, runner réel, identité/provenance, scorecard et comparateur livrés ; Decision réel branché ; collecter/doubler les annotations réelles puis mesurer | Quality **359/359** ; 7 datasets/27 gates ; `integrity_valid=true`, `ready=false`, `status=not_ready`, 0 cas humain ; deux adaptateurs Graph encore absents ; sortie seulement après volumes minimums et comparaison mesurable | Aucune donnée synthétique admise dans le holdout ou le gate de lancement ; le bootstrap historique reste non éligible ; toute entrée incomplète reste `not_measurable` et le mode strict bloque le NO-GO intègre |
| P0.3 — Migrations — **TERMINÉ** | Alembic baseline `b9db07b15986` et runbook | Schéma photographié ; mode normal sans DDL runtime ; upgrade, stamp, drift, downgrade et restauration testés | Base éphémère reconstruite sans drift et restauration avec donnée sentinelle | Snapshot restauré ; `legacy` seulement pour rollback initial |
| P0.4 — Observation — **TERMINÉ EN SHADOW** | RawSource/Observation/Quarantine + ADR + codes E001–E018 | Payload/checksum/provenance, projection Awin, savepoint et replay versionnés ; producteurs stricts, lecteurs inter-version sans perte ; lectures v1 inchangées | Commit `7753dff` isolé : 29 tests taxonomie/observation/contrats et backend 1 304/1 304 | Flag off par défaut ; valeurs/clés historiques inchangées ; downgrade vers `b9db07b15986` conserve le Core |
| P0.5 — Product Graph shadow | Brand/Family/Model/Variant v0 | Backfill contrôlé, résolution conservative, file de revue | Seuils entity/variant atteints sur test indépendant | Aucun consommateur v2 ; drop logique seulement |
| P0.6 — Observabilité — **EN COURS** | Corrélation, readiness, front door, export standard, traces de bout en bout et dashboards | Request ID, latences P50/P95/P99, huit jalons décisionnels, spans et `traceparent`, compteurs bornés, évaluateur local, front door stricte, mode Redis atomique sans fallback et identité `X-Real-IP` fermée, OpenMetrics authentifié, pack Prometheus/Grafana, compilateur et reçu v1 livrés | Export désactivé sans secret ; Redis production exige URL + secret + identité Railway et ferme en 503 sur panne/en-tête ambigu ; cibles vides, 11 rollups et reçu expurgé validés ; sortie après traces, preuve Railway, activation Redis/WAF, scrapes/rétention, dashboard et notifications testés | Production encore locale ; config Redis/export/proxy/collecte fail-closed et rollback sans migration ; aucune réception de trace ni reçu Prometheus sans infrastructure réelle |
| P0.7 — CI complète — **TERMINÉ** | Matrice de qualité multi-surfaces | Workflow publié ; readiness téléversée ; branche byte-identique ; run #343 exécuté ; preview Vercel construite ; ruleset `21798272` active sur `main`, PR et quatre jobs requis sans bypass | Migrations 12/12, backend 2 021/2 021, web/mobile/extension verts ; artefact `9713798390` inspectable ; gate strict rouge uniquement sur le NO-GO humain attendu | L'intégrité invalide et le `not_ready` sur changement moteur restent bloquants ; aucun bypass administrateur |

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

P0.1 à P0.7 terminés, datasets indépendants disponibles, migrations et rollback testés, Product Graph shadow au-dessus des gates, contrat `unknown` adopté par les trois clients, backend catalogue qualifié et intégré, infrastructure de production observée, CI requise sur une branche principale protégée. Avant cela, et notamment tant que P0.2 conserve 0 cas humain, le statut reste **NO-GO**.
