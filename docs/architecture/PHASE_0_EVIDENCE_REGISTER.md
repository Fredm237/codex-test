# FILON — Registre canonique des preuves de Phase 0

- Date de coupure : **31 août 2026**
- Branche locale : `codex/filon-phase-0-core`
- Référence applicative locale qualifiée : `8594bd8`
- Référence applicative distante qualifiée : `5ab3c3c`, arbre commun `e2124704b30d405f5d7215f4acc95bc5246dc570`
- Référence Quality versionnée : artefact Actions `9738761749`

Décision globale : **PHASE 0 = GO ; ingestion timeboxée, reprise, heartbeat,
CI `main`, moniteur manuel et deux exécutions planifiées réelles sont prouvés.
Phase 1 est ouverte.**

Ce registre relie les lots du plan aux identifiants de la
[mission courante](../../.claude/agent/missions/courante.json), aux preuves
rejouables et aux conditions de sortie encore ouvertes. Un test logiciel prouve
un contrat technique dans le périmètre testé ; il ne devient ni une annotation
humaine indépendante, ni une preuve de production. La décision fondateur du
31 août 2026 remplace définitivement l'ancien gate humain bloquant par
`AUTONOMOUS_QUALITY_LAB + NO_EXTERNAL_HUMAN_GROUND_TRUTH`. Les zéro cas
externes restent documentés, mais ne bloquent plus P0.2, P0.5, Phase 0 ou
Phase 1.

## Registre

| Lot | Mission | Statut au 29-08-2026 | Commit ou preuve locale connue | Commande ou mesure principale | Artefact canonique | Condition de sortie / blocage |
|---|---|---|---|---|---|---|
| P0.0 — Freeze, ownership et baseline | `p0_a` | **AUDIT TERMINÉ** (`p0_a` fait) ; règles de livraison actives | Audit local et GitHub consigné ; run Actions #343 exécuté ; ruleset `21798272` active sur `main` sans bypass | Suites complètes de chaque surface et contrôles distants | [Current System Map](CURRENT_SYSTEM_MAP.md), [baseline qualité](BASELINE_QUALITY_REPORT.md), [qualification distante](PHASE_0_REMOTE_QUALIFICATION_REPORT.md) | La baseline, la CI distante et la protection de `main` sont acquises ; le gel reste applicable jusqu'au GO métier/production |
| P0.1 — Contrats v1 et `unknown` | `p0_b` | **TERMINÉ** (`p0_b` fait) | Catalogue, agrégats, Assistant et MegaMenu fail-closed ; UTC explicite sur toutes les dates catalogue publiques et constructeur d'URL unique ; local courant : backend **2 119 + 2 ignorés**, web **17/17**, typecheck et build 42 routes | Suites de compatibilité backend/web/mobile/extension ; preuve explicite, `observed_at` valide ≤ 72 h, devise, stock, prix, URL sûre, horodatage RFC 3339 et revalidation Core exigés avant action | [durcissement final du contrat](PHASE_0B_CATALOG_CONTRACT_HARDENING_REPORT.md), [post-validation protégée](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md), [registre `contracts/v1`](../../contracts/v1/README.md), [claims non supportés](UNSUPPORTED_CLAIMS_REGISTER.md), [preuve d'invariance](AFFILIATE_INVARIANCE_REPORT.md) | Contrat acquis ; le TTL 72 h reste provisoire et devra être recalibré sur cadence/dérive réelles |
| P0.2 — Quality Lab | `p0_c` | **TERMINÉ — AUTONOMOUS QUALITY LAB** ; limitation externe non bloquante | Manifeste autonome v1, golden set `REGRESSION_GROUND_TRUTH`, holdout adversarial multi-seed, exact-GTIN, prix/devise/stock/fraîcheur/budget, conflits multi-source et abstention ; **571/571 contrôles objectifs**, 1 conflit correctement `UNRESOLVED`, **7/7 tests du laboratoire** ; backend **2 142 + 3 ignorés localement** | `python -m quality_lab.autonomous --strict` : exit 0 ; identité SHA-256 stable ; l'ancien reçu externe reste `ready=false` sans être une gate | [contrat autonome](../../quality/AUTONOMOUS_QUALITY_LAB.md), [manifeste autonome](../../quality/autonomous-manifest.json), [rapport de décision fondateur](PHASE_0C_AUTONOMOUS_QUALITY_REPORT.md), [historique externe v0.5](../../quality/manifest.json) | Acquis pour Phase 0 ; ne jamais présenter les dimensions subjectives comme indépendamment validées ; tout futur juge modèle reste auxiliaire et audité |
| P0.3 — Migrations | `p0_d` | **TERMINÉ ET ACTIVÉ EN PRODUCTION** | Baseline `b9db07b15986`, production `e8c3f6a0b5d2`, heartbeat `f9a4c7d1e2b3`, checkpoints `a2d7e9f4c1b6` ; restore drill PostgreSQL 18, stamp, upgrade, drift et invariance prouvés ; reprise du même run, checkpoints par feed et replay idempotent qualifiés ; suite backend courante **2 158 réussis + 3 ignorés**, test OTLP isolé **1/1** | `alembic current`, `alembic check`, tests SQLite/PostgreSQL, reprise de journal et non-duplication d'un feed partiel | [ADR baseline](ADR-001-ALEMBIC-BASELINE.md), [runbook](DATABASE_MIGRATION_RUNBOOK.md), [reçu Railway](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md) | Acquis ; conserver backup, rollback et fenêtre sans écrivain pour toute future migration |
| P0.4 — Observation shadow | `p0_e` | **TERMINÉ EN SHADOW** (`fait`) | `7753dff` ; **29 tests ciblés** et backend **1 304/1 304** ; taxonomie E001–E018, replay et compatibilité v1 prouvés | Suites taxonomie/Observation/contrats et replay idempotent, flag shadow désactivé par défaut | [rapport P0.e](PHASE_0E_OBSERVATION_REPORT.md), [taxonomie d'erreurs](ERROR_TAXONOMY.md) | Garder le shadow opt-in et les lectures v1 inchangées tant que le Product Graph n'a pas passé ses gates |
| P0.5 — Product/Variant + Offer Graph + Merchant Intelligence + Evidence + Funnel shadows | `p0_f` | **TERMINÉ EN SHADOW AUTONOME** ; aucune promotion publique implicite | Douze tables d'expansion, quatre migrations, resolver `exact-gtin-shadow-v1`, argent décimal, stock tri-state, compteurs sans score, 11 claims et funnel `catalog-quality-funnel-autonomous-v2` ; faux merges, GTIN invalides/contradictoires, rattachement, devise, stock et budget qualifiés adversarialement | Funnel poursuit les étapes déterministes avec classification `provisional`, puis s'arrête sur les vraies limites `COMPLETE_LANDED_COST=not_supported` et confiance non calibrée ; lot ciblé cumulé **80/80** | [ADR Product Graph](ADR-002-PRODUCT-GRAPH-IDENTITY-SHADOW.md), [ADR Offer Graph](ADR-003-OFFER-GRAPH-EVIDENCE-SHADOW.md), [ADR Merchant Intelligence](ADR-004-MERCHANT-INTELLIGENCE-MEASUREMENT-SHADOW.md), [ADR Evidence](ADR-005-EVIDENCE-CLAIM-ELIGIBILITY-SHADOW.md), [funnel autonome](PHASE_0F_CATALOG_QUALITY_FUNNEL_REPORT.md) | Lot P0.5 acquis en shadow ; coût rendu, confiance subjective et sources après clic/achat restent non supportés et interdisent seulement les claims correspondants, pas la progression de phase |
| P0.6 — Observabilité et front door | `p0_i` | **TERMINÉ** ; socle, probes, Redis, Cron, capacité, heartbeat et reprise réels verts | Run 18 terminal `interrupted`, run 19 terminal `succeeded`, trois checkpoints repris, feed terminé sauté sans réingestion ; moniteur manuel `33404840701` vert ; runs planifiés `33578462794` et `33596363980` verts | Pulse `fresh`, PostgreSQL/Redis/schéma `ok`, exécution Railway `5fa66804-f096-4522-9aad-91afdcb2ab75`, restauration `7d707084-7d3f-4ae1-a1b5-1799ab59ca47` | [reçu final](PHASE_0_FINAL_RECEIPT.md), [activation Redis/Cron](PHASE_06_REDIS_CRON_ACTIVATION_REPORT.md), [backlog post-Phase 0](POST_PHASE_0_HARDENING.md) | Moniteur planifié prouvé sur `main`; OTLP, Prometheus/Grafana avancés, rétention, pager secondaire et trafic représentatif sont non bloquants |
| P0.7 — CI multi-surfaces et protection | `p0_g` | **TERMINÉ ET INTÉGRÉ SUR MAIN** | PR #385 fusionnée au commit `50a04b85944e6a5363092692572859fbeb00c5a0` ; ruleset `21798272` sans bypass ; run `33404710182` | Quatre jobs GitHub Actions terminaux `success`, Quality autonome strict bloquant sur régressions objectives | [qualification distante](PHASE_0_REMOTE_QUALIFICATION_REPORT.md), [workflow Phase 0](../../.github/workflows/backend-catalog-quality.yml) | Acquis ; zéro cas humain explicitement non bloquant |
| Revue de passage Phase 1 | `p0_h` | **TERMINÉ — PHASE 0 GO** | Intégrité, récupérabilité, migration, CI et production prouvées ; moniteur manuel vert ; attente fournisseur non bloquante | Revue exclusive des risques d'intégrité/récupérabilité | Ce registre, le [plan](PHASE_0_EXECUTION_PLAN.md) et le [reçu final](PHASE_0_FINAL_RECEIPT.md) | Phase 1 ouverte ; Immersive reste séparément NO-GO |

## Preuves transversales à ne pas surinterpréter

- `e152ed0`, `4e5755d` et `56de1cf` ajoutent les primitives de vérité prix ;
  `4a95a42` et `90246b2` achèvent leur intégration dans catalogue,
  SearchAssistant et MegaMenu. La preuve est désormais locale et distante :
  **2 020 tests backend + 1 ignoré** localement, **2 021/2 021** dans Actions,
  web **17/17**, typecheck et build. Elle reste une preuve technique, jamais
  une mesure humaine.

- `f5ae21b` ferme `/advise` agents et le planificateur général sur la vérité des
  offres : prix, devise, disponibilité, livraison et comparaison inconnus ne
  produisent plus d'avantage favorable ; les recommandations générales
  n'inventent plus de confiance. Cette preuve n'englobe pas les callers legacy
  recensés ci-dessus. L'état cumulé `f5ae21b` + `45e7768` est vert à
  **1 659/1 659** tests backend. Cette preuve renforce P0.1 et les garde-fous
  offre/décision pré-Graph, sans mesurer P0.2 ni la qualité du Product Graph sur
  des offres réelles annotées.
- `1a167dc` ferme l'Assistant sur une preuve explicitement courante : le marqueur
  `evidence_current=true` est obligatoire, la carte est revalidée et le cache
  moteur v4 empêche de reprendre une ancienne carte insuffisamment qualifiée.
  Une archive propre de ce commit passe **1 795 tests**, avec **7 warnings**, en
  **120,91 s**. Cette preuve ne qualifie pas le backend catalogue protégé.
- `0c6f674` et `a78401a` — qui inclut le socle mobile `55aaf41` — ferment les
  parcours produit web/mobile sur une preuve
  explicitement courante :
  `evidence_current=true`, `observed_at` strict, non futur et âgé d'au plus
  72 h, prix positif, devise supportée, stock positif et lien marchand HTTPS
  avec nom DNS public qualifié. Une URL contenant des identifiants, un hôte
  local/réservé ou un littéral IP n'est pas actionnable. L'expiration est
  recalculée dynamiquement ; un rendu ouvert ne transforme donc pas une preuve
  expirée en preuve courante. Le proxy Pulse web partage un TTL de **120 s**,
  distinct du TTL de preuve marchande.
- Sur mobile, les paramètres de deep-link sont display-only. Achat, partage,
  sauvegarde et alerte exigent une concordance avec le détail Core ; l'alerte
  revalide encore au submit. Un historique futur, multidevise ou dépourvu de
  `in_stock=true` explicite est rejeté.
- Les comparaisons produit sont mono-devise et chaque point d'historique porte
  sa propre devise ainsi qu'un `in_stock=true` explicite. Les tris/filtres prix ont été retirés lorsque l'API ne
  fournit aucun scope devise. Les scores Outfit non calibrés n'affichent plus
  de valeur synthétique et deviennent « Non mesuré ». Ces garde-fous
  techniques ne mesurent ni la qualité d'une tenue ni celle du futur Graph.
- L'archive propre du HEAD `a78401a` passe le typecheck, les gates web contrat
  v1, claims et vérité produit, ainsi que le build de production. La suite web complète
  passe **12 tests sur 17** ; ses cinq seuls échecs concernent MegaMenu. Les
  correctifs locaux protégés du composant et du script de test ne sont pas
  intégrés à l'archive. Cette limite n'est
  pas transformée en faux vert. Le mobile `a78401a` passe **326 tests**, avec
  **4 smoke tests ignorés**, son typecheck et ESLint à **0 erreur / 17
  avertissements** ; la revue indépendante ne relève aucun P0, P1 ou P2.
- `6e12386` prouve le roster v0.5 fermé à sept datasets, les 27 gates, le runner
  aveugle, l'identité du run, l'empreinte de contenu du holdout, la publication
  atomique sans remplacement et la comparaison fail-closed. Il ne rend pas le
  laboratoire prêt lorsque les fichiers humains sont absents. Le lot courant
  ajoute le moteur Decision réel ; variante et attachement restent les deux
  surfaces volontairement refusées.
- La readiness distingue une entrée valide mais incomplète d'une entrée dont
  l'intégrité est invalide. Le
  [rapport du 29-08-2026](../../quality/reports/readiness-2026-08-29.json) reste
  l'autorité datée : `integrity_valid: true`, `ready: false`,
  `status: not_ready`, fingerprint
  `sha256:e949de01a819a5b5ef4fb0b53b5efd15241bc514b71831d32c7b1146b491262f`
  et zéro cas dans chacun des sept datasets.

Les zéros du laboratoire externe interdisent toujours les claims de précision
humaine, de rappel humain ou de calibration subjective. Ils ne bloquent plus la
progression. Le backend Core de production, le heartbeat, les checkpoints, la
reprise bornée, la CI `main` et les moniteurs manuel et planifié sont qualifiés.
Le verdict est **PHASE 0 = GO**. Les runs planifiés `33578462794` et
`33596363980` ont levé la limitation fournisseur historique. Il n'existe plus
de NO-GO humain ni de gate d'observabilité parfaite.
