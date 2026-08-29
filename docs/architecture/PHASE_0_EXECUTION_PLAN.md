# FILON — Phase 0 Execution Plan

## Objectif

Rendre le rebuild mesurable, réversible et gouvernable avant de modifier le moteur produit. La Phase 0 n'ajoute aucune fonctionnalité visible et ne lance aucun travail 3D, Fashion, Recreate ou refonte éditoriale.

Progression au 29 août 2026 : **P0.0 audit local, P0.3 migrations et P0.4 Observation shadow terminés ; contrats v1 de P0.1 figés, durcissement des callers encore en cours**. Le registre produit E001–E018 est canonique au commit isolé `7753dff` : Enum, catalogue et schéma sont identiques, les valeurs et clés historiques restent stables, et la couverture réelle est bornée aux cinq codes émis par Awin. La séparation commerciale est couverte localement sur la clé Core et le reranker Assistant : deux barèmes synthétiques inversés conservent le classement, tandis que seuls les liens projetés changent ; cela ne prouve ni des taux réels, ni le panier final, ni une neutralité absolue.

Les commits `f5ae21b`, `996ada4` et `1a167dc` durcissent le Core et l'Assistant : stock, prix, devise, preuve explicite et fraîcheur sont exigés ; le TTL de **72 h est provisoire** ; la devise observée est conservée ; la livraison inconnue ne devient ni zéro ni économie comparative ; le budget EUR est fail-closed et aucun FX n'est inventé. L'Assistant exige maintenant `evidence_current=true` de façon explicite, revalide la preuve avant de conserver une carte et utilise le cache moteur v4 afin de ne pas réutiliser les anciennes cartes insuffisamment qualifiées.

Les commits clients `0c6f674` (web), `55aaf41` puis `a78401a` (mobile) ferment les actions marchandes sur une preuve courante : `evidence_current=true`, `observed_at` valide, non futur et âgé d'au plus 72 h, prix positif, devise supportée, stock positif et URL HTTPS avec nom DNS public qualifié ; les hôtes locaux/réservés et littéraux IP sont refusés. Sur mobile, les paramètres de deep-link ne servent qu'à l'affichage : achat, partage, sauvegarde et alerte exigent une revalidation contre le détail Core, et l'alerte revalide encore la preuve au moment de l'enregistrement. Les historiques futurs, multidevises ou sans `in_stock=true` sont rejetés. Les comparaisons restent mono-devise, l'éligibilité expire dynamiquement sur le web comme sur mobile, les tris/filtres prix sans scope devise ont été retirés et les scores Outfit non calibrés sont neutralisés en « Non mesuré ». `a78401a` ajoute la localisation FR/NL/EN des parcours publics et une réconciliation locale sérialisée, sans transformer un prix ou un statut obsolète en claim public. Le proxy Pulse web partage un TTL de **120 s** pour limiter les divergences entre consommateurs ; ce TTL technique ne qualifie pas la fraîcheur commerciale de l'offre.

Les commits `e152ed0`, `4e5755d` et `56de1cf` ferment ensuite les montants
des cartes, rails et fiches web sans rapprochement courant prix–devise–stock.
Le lot restant dans `catalog.py`, SearchAssistant et MegaMenu a été validé dans
une copie isolée : backend **1 928 réussis + 1 ignoré**, web **17/17**, typecheck
et build de 42 pages verts. Cette preuve est détaillée dans la
[prévalidation protégée](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md) ; elle ne
constitue pas une autorisation d'intégrer les fichiers appartenant déjà à
l'utilisateur.

**P0.2 Quality Lab reste en cours** : le contrat v0.5 ferme le roster à sept datasets et 27 gates, exécute les moteurs sur une entrée aveugle, lie l'identité du run au manifeste/adaptateurs/sorties, empreinte le contenu exact du holdout et compare deux scorecards sans accepter de roster tronqué. La publication du run est atomique et sans remplacement. Le moteur Decision réel est désormais branché avec une requête fermée, une horloge de benchmark déterministe et des claims sourcés ; cinq adaptateurs applicatifs sont donc disponibles et seuls `variant_resolution` et `offer_attachment` restent fail-closed. Les **359 tests Quality** et la suite backend courante (**2 012 réussis + 1 ignoré**) sont verts. La readiness normale sort avec 0 et la stricte avec 1, mais l'état réel reste `integrity_valid=true`, `ready=false`, `status=not_ready` avec **0 cas humain**. Aucun rapport de régression métier n'est donc mesurable. L'archive propre historique du HEAD `a78401a` compte **1 907 tests backend réussis + 1 ignoré**, 7 warnings, en 370,53 s. Le mobile versionné `a78401a` compte **326 tests réussis + 4 smoke tests ignorés**, un typecheck vert et ESLint à **0 erreur / 17 avertissements** ; la revue finale ne relève aucun P0, P1 ou P2. La même archive passe le typecheck, les gates web contrat/claims/vérité produit et le build de production ; sa suite web complète reste à **12/17**, avec cinq échecs MegaMenu exclusivement liés aux correctifs locaux protégés non intégrés.

**P0.6 Observabilité est verte localement mais incomplète en production** : corrélation HTTP, huit jalons décisionnels, spans PostgreSQL/Redis/Awin/SerpAPI/LLM, propagation W3C vers les dépendances HTTP, téléchargement Awin réellement streamé avec bornes compressée/décompressée/lignes, percentiles, readiness fail-closed, moteur local de cinq règles, front door anti-spoofing/bornée et export OpenMetrics 1.0 authentifié sont testés. Un pack Prometheus/Grafana fail-closed ajoute une configuration sans cible par défaut, 11 rollups multi-réplica testés et un dashboard descriptif sans SLO. Son activation est fermée par un compilateur d’inventaire atomique et un vérificateur HTTPS qui produit un reçu sans hôte ni secret ; aucun reçu n’est fabriqué sans infrastructure. Promtool 3.13.2 LTS, les **11 nouveaux tests ciblés de sûreté Awin** et la suite backend courante (**2 012 réussis + 1 ignoré**) sont verts. Backend de traces, CIDR Railway réel, WAF, agrégateur effectivement déployé, scrapes/rétention, pager et trafic représentatif manquent encore. **P0.7 CI est en cours** : le workflow multi-surfaces produit un artefact de readiness et distingue les exits 0/1/2, mais il n'est ni publié ni requis sur une branche protégée. Les intégrations protégées `catalog.py`, `SearchAssistant.tsx` et le lot MegaMenu sont désormais autorisées mais pas encore versionnées dans cette preuve. Les surfaces versionnées s'abstiennent au lieu d'inventer une preuve. P0.5 Product Graph reste **NO-GO** jusqu'aux annotations indépendantes exigées par P0.2.

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
| P0.1 — Contrats actuels — **EN COURS** | Snapshots v1, contract catalog et taxonomie produit v1 | Payloads sentinelles web/mobile/extension, unknown explicite, callers recensés ; E001–E018 versionnés ; Core et Assistant durcis jusqu'à `1a167dc`, web `0c6f674`, mobile jusqu'à `a78401a` ; preuve explicite, cache Assistant v4, expiration 72 h, deep-links display-only puis revalidation Core, mono-devise, devise et stock explicites par point d'historique et liens marchands HTTPS sur DNS public qualifié ; scores Outfit neutralisés ; parcours publics FR/NL/EN et synchronisation locale sérialisée ; intégrer les fichiers protégés restants | Compatibility suite exécutable sur chaque client ; parité Enum/registre/schéma ; aucun caller ne transforme un unknown, une preuve expirée ou une devise incompatible en fait favorable | Adaptateurs v1 conservés ; codes inconnus préservés sans remap ; TTL 72 h provisoire à recalibrer ; surfaces masquées tant que le backend ne fournit pas la preuve ; UTC naïf et URL canonique restent à résoudre |
| P0.2 — Quality Lab — **EN COURS** | Sept datasets v0.5 : taxonomy, entity, variant, attachment, offer truth, retrieval, decision | Formats, schémas, packs aveugles, accord humain, anti-fuite, métriques, runner réel, identité/provenance, scorecard et comparateur livrés ; Decision réel branché ; collecter/doubler les annotations réelles puis mesurer | Quality **359/359** ; 7 datasets/27 gates ; `integrity_valid=true`, `ready=false`, `status=not_ready`, 0 cas humain ; deux adaptateurs Graph encore absents ; sortie seulement après volumes minimums et comparaison mesurable | Aucune donnée synthétique admise dans le holdout ou le gate de lancement ; le bootstrap historique reste non éligible ; toute entrée incomplète reste `not_measurable` et le mode strict bloque le NO-GO intègre |
| P0.3 — Migrations — **TERMINÉ** | Alembic baseline `b9db07b15986` et runbook | Schéma photographié ; mode normal sans DDL runtime ; upgrade, stamp, drift, downgrade et restauration testés | Base éphémère reconstruite sans drift et restauration avec donnée sentinelle | Snapshot restauré ; `legacy` seulement pour rollback initial |
| P0.4 — Observation — **TERMINÉ EN SHADOW** | RawSource/Observation/Quarantine + ADR + codes E001–E018 | Payload/checksum/provenance, projection Awin, savepoint et replay versionnés ; producteurs stricts, lecteurs inter-version sans perte ; lectures v1 inchangées | Commit `7753dff` isolé : 29 tests taxonomie/observation/contrats et backend 1 304/1 304 | Flag off par défaut ; valeurs/clés historiques inchangées ; downgrade vers `b9db07b15986` conserve le Core |
| P0.5 — Product Graph shadow | Brand/Family/Model/Variant v0 | Backfill contrôlé, résolution conservative, file de revue | Seuils entity/variant atteints sur test indépendant | Aucun consommateur v2 ; drop logique seulement |
| P0.6 — Observabilité — **EN COURS** | Corrélation, readiness, front door, export standard, traces de bout en bout et dashboards | Request ID, latences P50/P95/P99, cinq étapes, huit jalons décisionnels, spans de dépendance et `traceparent` HTTP, compteurs bornés, évaluateur local, front door stricte, OpenMetrics authentifié, pack Prometheus/Grafana, compilateur atomique et reçu v1 livrés ; déployer collecte/traces/WAF/canal ensuite | Export désactivé sans secret ; champs de trace fermés sans payload ; cibles vides, compte attendu obligatoire, 11 rollups, dashboard sans SLO et reçu expurgé validés ; sortie après backend de traces, CIDR proxy, scrapes/rétention, dashboard et notifications testés sur trafic représentatif | Compteurs locaux par processus ; config export/proxy/collecte fail-closed et rollback sans migration ; aucune réception de trace ni reçu Prometheus sans infrastructure réelle |
| P0.7 — CI complète — **EN COURS** | Matrice de qualité multi-surfaces | Workflow backend/web/mobile/extension/contracts/quality livré et configuré pour écrire/téléverser la readiness ; normal `not_ready` intègre = exit 0, strict = exit 1, intégrité invalide = exit 2 ; archive `a78401a` : backend 1 907 réussis + 1 ignoré, mobile 326 réussis + 4 ignorés, typecheck/gates/build web et extension verts ; intégrer sous autorisation `catalog.py` et `SearchAssistant.tsx`, publier, observer puis protéger `main` | Checks requis stables et artefacts inspectables sur `main` protégée ; aucune preuve distante actuelle | Retour temporaire du gate de lancement en mode normal documenté ; l'invalidité reste toujours bloquante ; la suite web complète de l'archive reste à 12/17 tant que le lot MegaMenu protégé n'est pas intégré |

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
