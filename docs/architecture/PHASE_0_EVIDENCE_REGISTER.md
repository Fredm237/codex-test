# FILON — Registre canonique des preuves de Phase 0

- Date de coupure : **29 août 2026**
- Branche locale : `codex/filon-phase-0-core`
- Référence applicative locale qualifiée : `6717b39`
- Référence applicative distante qualifiée : `7896c6d`, arbre commun `04560737a72825928612ae00fb52eef4eb7e009f`
- Référence Quality versionnée : artefact Actions `9715609325`

Décision globale : **NO-GO vers la Phase 1**

Ce registre relie les lots du plan aux identifiants de la
[mission courante](../../.claude/agent/missions/courante.json), aux preuves
rejouables et aux conditions de sortie encore ouvertes. Un test logiciel prouve
un contrat technique dans le périmètre testé ; il ne devient ni une annotation
humaine indépendante, ni une mesure de qualité métier, ni une preuve de
production. En particulier, les **359 tests Quality Lab verts** ne remplacent
pas les **0 cas humains** actuellement disponibles.

## Registre

| Lot | Mission | Statut au 29-08-2026 | Commit ou preuve locale connue | Commande ou mesure principale | Artefact canonique | Condition de sortie / blocage |
|---|---|---|---|---|---|---|
| P0.0 — Freeze, ownership et baseline | `p0_a` | **AUDIT TERMINÉ** (`p0_a` fait) ; règles de livraison actives | Audit local et GitHub consigné ; run Actions #343 exécuté ; ruleset `21798272` active sur `main` sans bypass | Suites complètes de chaque surface et contrôles distants | [Current System Map](CURRENT_SYSTEM_MAP.md), [baseline qualité](BASELINE_QUALITY_REPORT.md), [qualification distante](PHASE_0_REMOTE_QUALIFICATION_REPORT.md) | La baseline, la CI distante et la protection de `main` sont acquises ; le gel reste applicable jusqu'au GO métier/production |
| P0.1 — Contrats v1 et `unknown` | `p0_b` | **TERMINÉ** (`p0_b` fait) | `4a95a42` ferme catalogue, agrégats et Assistant ; `90246b2` intègre MegaMenu et sa couverture. Local : backend **2 020 + 1 ignoré**, web **17/17**, typecheck et build 42 pages ; Actions #343 : backend **2 021/2 021** et clients verts | Suites de compatibilité backend/web/mobile/extension ; gates vérité produit ; preuve explicite, `observed_at` valide ≤ 72 h, devise compatible, stock, prix, URL sûre et revalidation Core exigés avant action | [post-validation protégée](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md), [registre `contracts/v1`](../../contracts/v1/README.md), [claims non supportés](UNSUPPORTED_CLAIMS_REGISTER.md), [preuve d'invariance](AFFILIATE_INVARIANCE_REPORT.md) | Contrat acquis ; le TTL 72 h reste provisoire et devra être recalibré sur cadence/dérive réelles |
| P0.2 — Quality Lab | `p0_c` | **EN COURS** ; infrastructure v0.5 locale et distante verte, données **NO-GO** | Le roster reste fermé à 7 datasets/27 gates ; 5 moteurs réels sont branchés, dont Decision déterministe et sourcé ; inventaire public immuable de **1 000 candidats** sans label, empreinte `sha256:dee650…31c8`, **15 tests ciblés**, Quality cœur **257/257** et backend courant **2 035 + 1 ignoré** ; Actions #344 **2 036/2 036** ; rapport `integrity_valid: true`, `ready: false` | Vérification de l'inventaire et suites Quality ; readiness normale exit 0 et stricte exit 1 ; artefact distant `9714475518` | [inventaire réel](../../quality/candidates/README.md), [manifeste v0.5](../../quality/manifest.json), [rapport de readiness daté](../../quality/reports/readiness-2026-08-29.json), [rapport P0.c](PHASE_0C_QUALITY_REPORT.md) | Curer humainement les candidats, collecter les sept jeux réellement indépendants avec adjudication, provenance, volumes et supports minimaux ; brancher les 2 adaptateurs Graph encore absents ; aujourd'hui : **0 cas humains** et aucune régression métier mesurable |
| P0.3 — Migrations | `p0_d` | **TERMINÉ ET ACTIVÉ EN PRODUCTION** | Baseline `b9db07b15986`, head `f4c81a9d2e70` ; backend local **2 035 réussis + 2 ignorés** ; restore drill PostgreSQL 18, stamp, upgrade, drift et invariance des quatre compteurs prouvés en production | `alembic current`, `alembic check`, compteurs avant/après, shadow vide et readiness de révision | [ADR baseline](ADR-001-ALEMBIC-BASELINE.md), [runbook](DATABASE_MIGRATION_RUNBOOK.md), [reçu Railway](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md) | Acquis pour le Core ; le rollback reste applicatif et les sauvegardes planifiées restent à configurer |
| P0.4 — Observation shadow | `p0_e` | **TERMINÉ EN SHADOW** (`fait`) | `7753dff` ; **29 tests ciblés** et backend **1 304/1 304** ; taxonomie E001–E018, replay et compatibilité v1 prouvés | Suites taxonomie/Observation/contrats et replay idempotent, flag shadow désactivé par défaut | [rapport P0.e](PHASE_0E_OBSERVATION_REPORT.md), [taxonomie d'erreurs](ERROR_TAXONOMY.md) | Garder le shadow opt-in et les lectures v1 inchangées tant que le Product Graph n'a pas passé ses gates |
| P0.5 — Product/Variant Graph shadow | `p0_f` | **À FAIRE — BLOQUÉ** | Aucun scorecard métier éligible et aucun lot Graph revendiqué | Mesurer faux merges/splits, relations de variantes et attachement d'offres sur le holdout indépendant | Aucun artefact Graph validé ; exigences dans le [plan d'exécution](PHASE_0_EXECUTION_PLAN.md) | Dépend de P0.2 : datasets humains v0.5, supports minimaux et les 27 gates du scorecard conformes |
| P0.6 — Observabilité et front door | `p0_i` | **EN COURS** ; backend Core et probes production verts, agrégation externe encore NO-GO | Déploiement Railway `c832d1c8…` : Dockerfile, preDeploy Alembic, `env=production`, `/health/live` et `/health/ready` HTTP 200, révision `f4c81a9d2e70`, un réplica `RUNNING` ; shadow désactivé | Readiness publique, logs de démarrage, variables contrôlées sans valeur, compteurs et capacité volume | [rapport P0.6](PHASE_06_OBSERVABILITY_REPORT.md), [reçu Railway](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md), [pack agrégateur](../../filon-backend/observability/README.md) | Déployer backend de traces et agrégateur, produire le reçu de scrapes, vérifier rétention/resets ; WAF/limite distribuée, canal/pager, capacité disque et trafic représentatif restent ouverts |
| P0.7 — CI multi-surfaces et protection | `p0_g` | **TERMINÉ** (`p0_g` fait) | Référence distante `7896c6d`, arbre `045607…` identique au commit local `6717b39` ; PR #385 ; Actions #345 : web/mobile/extension verts, migrations et régressions backend vertes ; seul le gate strict Quality échoue comme attendu sur les datasets humains vides ; artefact `9715609325` | Workflow backend/contrats/migrations/Quality, web, mobile et extension ; GitHub Actions réel et protection de `main` | [qualification distante](PHASE_0_REMOTE_QUALIFICATION_REPORT.md), [workflow Phase 0](../../.github/workflows/backend-catalog-quality.yml), [reçu Railway](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md) | Lot acquis ; la conclusion globale reste NO-GO parce que le check backend ferme correctement sur les datasets humains vides |
| Revue de passage Phase 1 | `p0_h` | **À FAIRE — NO-GO** | Aucune décision GO approuvée | Revue conjointe des gates, risques, ADR, preuves de rollback et conditions de production | Ce registre et le [plan Phase 0](PHASE_0_EXECUTION_PLAN.md) | P0.1, P0.2, P0.5, P0.6 et P0.7 doivent atteindre leurs sorties ; les risques résiduels doivent être explicitement acceptés |

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

Tant que ces zéros persistent, aucune précision, aucun rappel, aucun taux de
faux merge/split, aucune calibration et aucun claim de qualité produit ne peut
être déduit des suites techniques. Le backend Core de production est qualifié,
mais le verdict reste aussi **NO-GO** tant que les sorties d'observabilité et de
protection distribuée restantes ne sont pas prouvées. Le contrat UTC naïf du
catalogue et la concordance d'URL canonique Assistant/catalogue restent des
limites à suivre sans invalider le contrat fail-closed acquis.
