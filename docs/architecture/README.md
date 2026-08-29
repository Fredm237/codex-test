# FILON — dossier d'architecture Phase 0

Statut : **baseline et contrats v1 établis ; exécution du rebuild au-delà de la
Phase 0 non autorisée tant que les gates P0 ouvertes ne sont pas satisfaites**.

Référence auditée : `Fredm237/codex-test`, branche distante `main`, commit
`57724c72e77c50ca54aaf64338f838dda3be2747`, le 28 août 2026. État de travail
documenté : branche locale `codex/filon-phase-0-core`, jusqu'au commit
`45e7768`, le 29 août 2026 ; cette branche n'est pas publiée.

Ce dossier traduit les mandats Product Intelligence Core, Execution Governance et Immersive Experience en décisions vérifiables. Le troisième mandat est volontairement traité comme une bible de production future : ses travaux 3D/cinématiques restent gelés jusqu'à validation du Product Graph, de l'Offer Graph, de la recherche, de l'evidence layer, du decision engine et de la Core UX.

## Décision exécutive

**NO-GO pour le rebuild produit et pour toute extension immersive. GO limité à la Phase 0 : contrats, mesure, gouvernance, observabilité et préparation des migrations.**

Les raisons bloquantes sont factuelles : absence de Product/Variant Graph
canonique et de holdout humain, argent encore stocké en flottants dans le
modèle historique, sources de vérité concurrentes, données Quality de
lancement vides, CI non publiée et branche principale non protégée. Les chemins
de décision durcis localement conservent désormais les inconnus au lieu de les
transformer en avantages favorables ; cela ne vaut pas preuve de production.

Progression : P0.a (audit), P0.d (baseline Alembic/rollback) et P0.e
(RawSource/Observation/Quarantine shadow) sont terminés localement. Les
contrats v1 de P0.b sont figés et deux parcours de décision sont durcis, mais
P0.b reste en cours tant que les fallbacks de devise et confiances heuristiques
des callers historiques ne sont pas supprimés. La taxonomie produit E001–E018 est maintenant canonique et
wire-compatible au commit isolé `7753dff` (29 tests ciblés et 1 304 tests
backend), sans prétendre que les treize codes encore sans producteur couvrent
la production.

La fondation P0.6 d'observabilité, de readiness fail-closed et d'évaluation
locale de cinq alertes provisoires est verte au commit isolé `8b6be85`. Sa front
door pseudonymisée, bornée et anti-spoofing est prouvée au commit isolé
`7cbb81d`. L'export OpenMetrics et un pack Prometheus/Grafana sans cible ni SLO
par défaut sont validés localement. Un compilateur atomique refuse désormais
les inventaires partiels et un vérificateur HTTPS peut produire un reçu sans
hôte ni secret ; aucun reçu de production n’existe encore. P0.6 reste donc
NO-GO faute de CIDR proxy Railway vérifié, WAF, agrégateur réellement déployé,
scrapes, rétention, pager et mesures distribuées.

L'infrastructure P0.c (Quality Lab) applique désormais le contrat v0.3 fermé à
cinq datasets exacts. Elle lie chaque gold aux empreintes des packs humains
complétés, impose la provenance `evidence_ref` → `source_ref` aux décisions et
évalue un run par un scorecard fail-closed. Les supports minimaux sont contrôlés
avant publication. Les gates binomiaux et de couverture utilisent les bornes
prudentes de Wilson à 95 % ; `recall@50`, `NDCG@10` et `ECE` restent ponctuels
et exigent encore une méthode d'intervalle. Les commits `5ee87f2` et `45e7768` portent la preuve locale à
**262/262 tests Quality** ; l'état cumulé avec la vérité offre `f5ae21b` passe
**1 659/1 659 tests backend** sur une archive propre de `45e7768`, avec 7
warnings historiques. Le rapport courant
est intègre mais non prêt (`integrity_valid=true`, `ready=false`) avec **0 cas
humain**. Le gate reste donc rouge et bloque honnêtement le Product/Variant
Graph P0.f.

P0.g (CI) est en cours : le workflow multi-surfaces, migrations incluses, est
prêt localement et configuré pour publier un rapport de readiness lorsqu'il est
exécuté dans GitHub. L'état versionné propre conserve toutefois 5 échecs MegaMenu ; le
succès 17/17 observé dans la copie de travail dépend de modifications utilisateur
protégées et ne peut pas être attribué à la branche. Publication, exécution
distante et protection de `main` restent à réaliser. Le registre
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
- [ADR-001 — baseline Alembic](ADR-001-ALEMBIC-BASELINE.md)
- [Runbook migrations et rollback](DATABASE_MIGRATION_RUNBOOK.md)
- [Rapport P0.e — Observation shadow](PHASE_0E_OBSERVATION_REPORT.md)
- [Rapport P0.c — Quality Lab](PHASE_0C_QUALITY_REPORT.md)
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
