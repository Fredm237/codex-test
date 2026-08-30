# FILON — dossier d'architecture Phase 0

Statut : **baseline et contrats v1 établis ; exécution du rebuild au-delà de la
Phase 0 non autorisée tant que les gates P0 ouvertes ne sont pas satisfaites**.

Référence de baseline : `Fredm237/codex-test`, branche distante `main`, commit
`57724c72e77c50ca54aaf64338f838dda3be2747`, le 28 août 2026. État de travail
qualifié : branche publique `codex/filon-phase-0-core`, référence applicative
locale `b1a18f2`, référence distante consolidée `6a793ac`, arbre commun
`2a377adf6808bd5e7eafb6756d8949c2ce0b1e30`, le 30 août 2026.

Ce dossier traduit les mandats Product Intelligence Core, Execution Governance et Immersive Experience en décisions vérifiables. Le troisième mandat est volontairement traité comme une bible de production future : ses travaux 3D/cinématiques restent gelés jusqu'à validation du Product Graph, de l'Offer Graph, de la recherche, de l'evidence layer, du decision engine et de la Core UX.

## Décision exécutive

**NO-GO pour le rebuild produit et pour toute extension immersive. GO limité à la Phase 0 : contrats, mesure, gouvernance, observabilité et préparation des migrations.**

Les raisons bloquantes sont factuelles : Product/Variant, Offer Graph,
Merchant Intelligence et Evidence Engine existent seulement en shadows locaux
non qualifiés, le holdout humain est absent,
l'argent reste stocké en flottants dans le modèle historique, les sources de
vérité restent concurrentes et les données Quality de lancement ne contiennent
aucun cas humain.
La CI distante existe désormais et ferme volontairement la promotion tant que
ces données humaines sont absentes. Les chemins
de décision durcis localement conservent désormais les inconnus au lieu de les
transformer en avantages favorables ; cela ne vaut pas preuve de production.
La branche principale est désormais protégée ; l'accès Railway est confirmé en
lecture, mais aucun déploiement n'est autorisé avant backup et restore drill.

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
inventaires partiels et un vérificateur HTTPS peut produire un reçu sans hôte
ni secret ; aucun reçu de production n’existe encore. P0.6 reste donc NO-GO
faute d'activation Redis ou WAF, agrégateur
réellement déployé, scrapes, rétention, pager et mesures distribuées réelles.

L'infrastructure P0.c (Quality Lab) applique le contrat v0.5 fermé à sept
datasets et 27 gates. Elle lie chaque gold aux packs humains complétés, impose
provenance, identité de run, empreinte exacte du holdout et publication
atomique, puis compare les scorecards fail-closed. Wilson, Bernstein empirique
et bootstrap déterministe bornent les métriques. Les sept adaptateurs
applicatifs sont désormais branchés, dont variante et attachement exact-GTIN.
Leur confiance reste non calibrée. Product/Variant, Offer Graph, Merchant
Intelligence et Evidence Engine demeurent shadows, avec argent décimal, stock
tri-state, quarantaine fail-closed, claims forts inéligibles et aucune note
marchand synthétique. Le rapport reste
`integrity_valid=true`, `ready=false`,
`status=not_ready` avec **0 cas humain**. Le gate strict bloque donc honnêtement
son cutover. Un inventaire public de 1 000 candidats sans label est maintenant
figé pour démarrer la curation. Un workflow séparé, lié à l'inventaire et
fail-closed, permet désormais à un humain de produire des candidats Taxonomy et
Variant encore sans gold ; il ne modifie pas la readiness.

P0.g (CI) est terminé : la branche publique est byte-identique au HEAD local,
le run GitHub Actions #354 prouve les migrations, les régressions backend, le web,
le mobile et l'extension. Le seul échec est le gate strict attendu sur les sept
datasets humains vides ; l'artefact Quality a été publié. Vercel a construit la
preview. La ruleset GitHub `21798272` est active sur `main`, sans bypass, avec
les quatre jobs requis, PR obligatoire et branche à jour. Le registre
[`contracts/v1`](../../contracts/v1/README.md) fige les formes catalogue, advise
et extension.

## Documents vivants

- [Cartographie du système actuel](CURRENT_SYSTEM_MAP.md)
- [Matrice KEEP / REFACTOR / REWRITE / ARCHIVE](KEEP_REFACTOR_REWRITE_DELETE.md)
- [Baseline qualité et gates](BASELINE_QUALITY_REPORT.md)
- [Architecture cible et stratégie de migration](TARGET_ARCHITECTURE.md)
- [Plan d'exécution Phase 0](PHASE_0_EXECUTION_PLAN.md)
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
- [Rapport P0.c — Quality Lab](PHASE_0C_QUALITY_REPORT.md)
- [Rapport P0.c.1 — workflow de curation humaine](PHASE_0C_CURATION_WORKFLOW_REPORT.md)
- [Rapport P0.6 — Observabilité](PHASE_06_OBSERVABILITY_REPORT.md)
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
