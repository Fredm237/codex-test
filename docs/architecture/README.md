# FILON — dossier d'architecture Phase 0

Statut : **PHASES 0 À 4 = GO ; PHASE 5 — HYBRID RETRIEVAL OUVERTE ; premier
événement GitHub `schedule` classé `EXTERNAL_PROVIDER_PENDING /
NON_BLOCKING` ; Immersive reste NO-GO**.

Référence de baseline : `Fredm237/codex-test`, branche distante `main`, commit
`57724c72e77c50ca54aaf64338f838dda3be2747`, le 28 août 2026. État de travail
qualifié : branche publique `codex/filon-phase-0-core`, référence applicative
locale `8594bd8`, référence distante consolidée `5ab3c3c`, arbre commun
`e2124704b30d405f5d7215f4acc95bc5246dc570`, le 30 août 2026.

Ce dossier traduit les mandats Product Intelligence Core, Execution Governance et Immersive Experience en décisions vérifiables. Le troisième mandat est volontairement traité comme une bible de production future : ses travaux 3D/cinématiques restent gelés jusqu'à validation du Product Graph, de l'Offer Graph, de la recherche, de l'evidence layer, du decision engine et de la Core UX.

## Décision exécutive

**PHASES 0 À 4 = GO ; Phase 5 ouverte ; NO-GO Immersive inchangé. Aucun blocker
humain : le Quality Lab autonome reste la gate active.**

Le cycle catalogue réel, la migration heartbeat, les checkpoints de reprise,
la CI et l'alerting critique minimum sont désormais prouvés. Le workflow
GitHub planifié est présent, valide et actif ; l'absence actuelle d'une
occurrence créée par GitHub reste surveillée comme limitation fournisseur non
bloquante. Collecteur OTLP, agrégateur, rétention, dashboards avancés, pager
secondaire et trafic représentatif sont des travaux post-Phase 0 non
bloquants. Les chemins
de décision durcis localement conservent désormais les inconnus au lieu de les
transformer en avantages favorables ; cela ne vaut pas preuve de production.
La branche principale est protégée ; backup, restore drill, Redis privé, Cron
et readiness Railway sont acquis dans leurs périmètres.

Progression : P0.a (audit), P0.b (contrats/unknown), P0.d
(baseline Alembic/rollback) et P0.e
(RawSource/Observation/Quarantine shadow) sont terminés localement. Les
contrats v1 de P0.b sont figés ; les chemins catalogue, Assistant, clients et
agrégats sont fail-closed sur la preuve courante, la devise et le stock. La
taxonomie produit E001–E018 est maintenant canonique et
wire-compatible au commit isolé `7753dff` (29 tests ciblés et 1 304 tests
backend), sans prétendre que les treize codes encore sans producteur couvrent
la production.

La fondation P0.6 d'observabilité, de readiness fail-closed et d'évaluation
locale de cinq alertes provisoires est verte au commit isolé `8b6be85`. Sa front
door pseudonymisée, bornée et anti-spoofing est prouvée au commit isolé
`7cbb81d`. Un mode Redis atomique opt-in, pseudonymisé, borné et sans fallback
local et lié à `X-Real-IP` Railway passe 180 tests ciblés ; la suite backend
compte 2 067 réussis et 2 ignorés. Le déploiement `03be13dc…` actif en EU West
prouve l'identité edge et les sondes réelles, tandis que le quota reste local.
L'export OpenMetrics et un pack
Prometheus/Grafana sans cible ni SLO
par défaut sont validés localement. Un compilateur atomique refuse les
inventaires partiels et un vérificateur HTTPS produit des preuves expurgées.
P0.6 est fermé : Redis privé, Cron, run 18 interrompu honnêtement, run 19 repris
et réussi, heartbeat/checkpoints et moniteur manuel sont qualifiés. Les scrapes,
rétentions et visualisations supplémentaires ne bloquent plus Phase 1.

P0.c applique désormais `AUTONOMOUS_QUALITY_LAB` avec la limitation permanente
`NO_EXTERNAL_HUMAN_GROUND_TRUTH`. Le contrat humain v0.5 et son reçu
`ready=false` restent historiques, sans être présentés comme satisfaits. La
gate active exécute 571 oracles déterministes et adversariaux sur golden set,
GTIN/EAN, rattachement, prix, devise, stock, fraîcheur, budget, abstention et
conflits multi-source. Les 571 passent ; un conflit reste correctement
`UNRESOLVED`. Subjectif et confiance restent `PROVISIONAL` ou
`NOT_INDEPENDENTLY_VALIDATED`, sans bloquer la progression.

Le Catalog Quality Funnel v2 est exécutable en lecture interne. Il traverse les
étapes déterministes, marque `CORRECTLY_CLASSIFIED` `provisional`, mesure les
résolutions Graph, la comparabilité et l'historique, puis s'arrête sur les vrais
manques : coût rendu complet et confiance non calibrée. P0.5 est terminé en
shadow ; `launch_gate_eligible` reste faux pour toute promotion publique.

P0.g (CI) est acquis : la ruleset GitHub `21798272` est active sur `main`, sans
bypass, avec les quatre jobs requis, PR obligatoire et branche à jour. La PR
#385 est fusionnée, le run `33404710182` est vert sur quatre jobs et le
moniteur manuel `33404840701` est vert. Le registre
[`contracts/v1`](../../contracts/v1/README.md) fige les formes catalogue, advise
et extension.

## Documents vivants

- [Cartographie du système actuel](CURRENT_SYSTEM_MAP.md)
- [Matrice KEEP / REFACTOR / REWRITE / ARCHIVE](KEEP_REFACTOR_REWRITE_DELETE.md)
- [Baseline qualité et gates](BASELINE_QUALITY_REPORT.md)
- [Architecture cible et stratégie de migration](TARGET_ARCHITECTURE.md)
- [Plan d'exécution Phase 0](PHASE_0_EXECUTION_PLAN.md)
- [Reçu final Phase 0](PHASE_0_FINAL_RECEIPT.md)
- [Plan d'exécution Phase 1](PHASE_1_EXECUTION_PLAN.md)
- [Baseline Product Identity Phase 1A](PHASE_1A_PRODUCT_IDENTITY_BASELINE.md)
- [ADR-006 — frontières Product Identity v1](ADR-006-PRODUCT-IDENTITY-V1-BOUNDARIES.md)
- [Rapport Phase 1C — benchmark exact-product](PHASE_1C_EXACT_PRODUCT_BENCHMARK_REPORT.md)
- [Rapport Phase 1D — assertions Product Identity shadow](PHASE_1D_PRODUCT_IDENTITY_SHADOW_REPORT.md)
- [Rapport Phase 1E — backfill réel borné et idempotence](PHASE_1E_PRODUCT_IDENTITY_BACKFILL_REPORT.md)
- [Rapport Phase 1F — qualification Product Identity](PHASE_1F_PRODUCT_IDENTITY_QUALIFICATION_REPORT.md)
- [Reçu final Phase 1](PHASE_1_FINAL_RECEIPT.md)
- [Plan d'exécution Phase 2 — Entity Resolution](PHASE_2_EXECUTION_PLAN.md)
- [ADR-007 — contrat de décision Entity Resolution v1](ADR-007-ENTITY-RESOLUTION-DECISION-CONTRACT.md)
- [Rapport Phase 2B — audit des signaux Entity Resolution](PHASE_2B_ENTITY_RESOLUTION_SIGNAL_AUDIT.md)
- [Rapport Phase 2C — benchmark Entity Resolution](PHASE_2C_ENTITY_RESOLUTION_BENCHMARK_REPORT.md)
- [Rapport Phase 2D — extracteurs de signaux Entity Resolution](PHASE_2D_ENTITY_SIGNAL_EXTRACTORS_REPORT.md)
- [Rapport Phase 2E — resolver Entity Resolution multi-signal](PHASE_2E_MULTI_SIGNAL_RESOLVER_REPORT.md)
- [Rapport Phase 2F — persistance et replay Entity Resolution shadow](PHASE_2F_ENTITY_RESOLUTION_REPLAY_REPORT.md)
- [Gate Phase 2G — qualification automatique des deux reçus production](PHASE_2G_ENTITY_RESOLUTION_QUALIFICATION_GATE.md)
- [Reçu final Phase 2](PHASE_2_FINAL_RECEIPT.md)
- [Plan d'exécution Phase 3 — Offer Truth](PHASE_3_EXECUTION_PLAN.md)
- [Reçu final Phase 3](PHASE_3_FINAL_RECEIPT.md)
- [Plan d'exécution Phase 4 — Product Ontology](PHASE_4_EXECUTION_PLAN.md)
- [Baseline Product Ontology Phase 4B](PHASE_4B_PRODUCT_ONTOLOGY_BASELINE.md)
- [Benchmark Product Ontology Phase 4C](PHASE_4C_PRODUCT_ONTOLOGY_BENCHMARK.md)
- [Extracteur Product Ontology Phase 4D](PHASE_4D_PRODUCT_ONTOLOGY_EXTRACTOR_REPORT.md)
- [Persistance Product Ontology Phase 4E](PHASE_4E_PRODUCT_ONTOLOGY_SHADOW_REPORT.md)
- [Reçu final Phase 4](PHASE_4_FINAL_RECEIPT.md)
- [Plan d'exécution Phase 5 — Hybrid Retrieval](PHASE_5_EXECUTION_PLAN.md)
- [Décision de timebox et sortie de Phase 0](PHASE_0_TIMEBOX_AND_EXIT_DECISION.md)
- [Backlog de durcissement post-Phase 0](POST_PHASE_0_HARDENING.md)
- [Durcissement final du contrat catalogue v1](PHASE_0B_CATALOG_CONTRACT_HARDENING_REPORT.md)
- [Registre canonique des preuves Phase 0](PHASE_0_EVIDENCE_REGISTER.md)
- [Audit canonique de complétude des trois mandats](MANDATE_COMPLETION_AUDIT.md)
- [Qualification distante Phase 0](PHASE_0_REMOTE_QUALIFICATION_REPORT.md)
- [Préflight Railway de production](PHASE_0_RAILWAY_PREFLIGHT.md)
- [ADR-001 — baseline Alembic](ADR-001-ALEMBIC-BASELINE.md)
- [ADR-002 — identité Product/Variant Graph shadow](ADR-002-PRODUCT-GRAPH-IDENTITY-SHADOW.md)
- [ADR-003 — preuves Offer Graph shadow](ADR-003-OFFER-GRAPH-EVIDENCE-SHADOW.md)
- [ADR-004 — mesure Merchant Intelligence shadow](ADR-004-MERCHANT-INTELLIGENCE-MEASUREMENT-SHADOW.md)
- [ADR-005 — Evidence Engine et Claim Eligibility shadow](ADR-005-EVIDENCE-CLAIM-ELIGIBILITY-SHADOW.md)
- [Runbook migrations et rollback](DATABASE_MIGRATION_RUNBOOK.md)
- [Rapport P0.e — Observation shadow](PHASE_0E_OBSERVATION_REPORT.md)
- [Rapport P0.f — Product/Variant Graph shadow](PHASE_0F_PRODUCT_GRAPH_SHADOW_REPORT.md)
- [Rapport P0.f.b — Offer Graph shadow](PHASE_0F_OFFER_GRAPH_SHADOW_REPORT.md)
- [Rapport P0.f.c — Merchant Intelligence shadow](PHASE_0F_MERCHANT_INTELLIGENCE_REPORT.md)
- [Rapport P0.f.d — Evidence Engine shadow](PHASE_0F_EVIDENCE_ENGINE_REPORT.md)
- [Rapport P0.f.e — Catalog Quality Funnel shadow](PHASE_0F_CATALOG_QUALITY_FUNNEL_REPORT.md)
- [Rapport P0.c — Quality Lab](PHASE_0C_QUALITY_REPORT.md)
- [Rapport P0.c autonome — décision fondatrice](PHASE_0C_AUTONOMOUS_QUALITY_REPORT.md)
- [Rapport P0.c.1 — workflow de curation humaine](PHASE_0C_CURATION_WORKFLOW_REPORT.md)
- [Rapport P0.6 — Observabilité](PHASE_06_OBSERVABILITY_REPORT.md)
- [Export de traces OTLP/HTTP fail-closed](PHASE_06_OTLP_TRACE_EXPORT_REPORT.md)
- [Qualification du préflight scheduler](PHASE_06_SCHEDULER_PREFLIGHT_REPORT.md)
- [Politique de sécurité de la front door](FRONT_DOOR_SECURITY_POLICY.md)
- [Contrat des métriques locales](OBSERVABILITY_METRICS_CONTRACT.md)
- [Politique locale provisoire d'alertes](LOCAL_ALERT_POLICY.md)
- [Runbook local d'incident observabilité](OBSERVABILITY_INCIDENT_RUNBOOK.md)
- [Preuve isolée de l'évaluateur local](LOCAL_ALERT_EVALUATION_REPORT.md)
- [Preuve bornée d'invariance du classement affilié](AFFILIATE_INVARIANCE_REPORT.md)
- [Politique provisoire de fraîcheur des offres](OFFER_FRESHNESS_POLICY.md)
- [Taxonomie canonique des erreurs produit](ERROR_TAXONOMY.md)
- [Registre des claims non supportés](UNSUPPORTED_CLAIMS_REGISTER.md)
- [Registre des ADR](../adr/README.md)
- [Registre des contrats v1](../../contracts/v1/README.md)
- [Registre de taxonomie produit v1](../../contracts/taxonomies/v1/README.md)
- [Quality Lab](../../quality/README.md)
- [Rapport de readiness du Quality Lab](../../quality/reports/readiness-2026-08-29.json)

## Règles d'actualisation

Toute modification d'un contrat, d'une table canonique, d'un propriétaire de données ou d'une frontière de module doit mettre à jour ce dossier dans la même pull request. Les chiffres de qualité doivent toujours indiquer le jeu de données, la version du contrat, le commit et la date. Un test vert ne remplace pas une mesure métier.
