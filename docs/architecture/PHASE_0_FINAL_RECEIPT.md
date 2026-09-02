# FILON — PHASE_0_FINAL_RECEIPT

- Date de décision : **31 août 2026**
- Snapshot final : **2026-08-31T16:07:12Z**
- Preuve planifiée ajoutée : **2026-09-02**
- Verdict : **PHASE 0 = GO**
- Phase suivante : **PHASE 1 — PRODUCT IDENTITY OUVERTE**
- Immersive : **NO-GO inchangé**

## Décision exécutive

Phase 0 a rendu FILON suffisamment sûr, mesurable et récupérable pour commencer
Product Identity. Aucun risque ouvert de corruption, perte, migration
irrécupérable, rollback absent, concurrence d'ingestion ou instabilité de
production n'a été identifié lors de l'audit final.

La limitation fournisseur historique est désormais levée : GitHub a produit
deux exécutions réelles `schedule`, terminales et vertes, sur le commit courant
de `main` `e667f3e52d3b4adb476b1e4c889b5b221373369e`.

## Gates de sortie

| Gate | Verdict | Preuve autoritative |
|---|---|---|
| Production | **GO** | `/health/live` vivant ; `/health/ready` prêt ; `/health` global `ok` |
| PostgreSQL | **GO** | connexion `ok`, révision Alembic `a2d7e9f4c1b6` |
| Redis privé | **GO** | dépendance `ok`, lectures réussies, aucune erreur au snapshot |
| Backup / restore | **GO** | sauvegardes Railway DAILY/WEEKLY/MONTHLY ; dump logique restauré sous PostgreSQL 18 et contrôlé par `pg_amcheck` |
| Migration / rollback | **GO** | baseline, stamp, upgrade, drift, invariance métier et runbook de rollback qualifiés |
| Ingestion mono-exécution | **GO** | run 18 terminal `interrupted` ; aucune réécriture favorable de l'historique |
| Heartbeat / checkpoints / reprise | **GO** | run 19 `succeeded`, `resumed_from_run_id=18`, trois checkpoints repris, feed terminé sauté sans téléchargement ni réingestion |
| Quality Lab | **GO autonome** | 571/571 contrôles objectifs et 7/7 tests ; `NO_EXTERNAL_HUMAN_GROUND_TRUTH` conservé |
| Shadows Product/Offer/Evidence | **GO shadow** | migrations expand-only, flags off, exact-GTIN, replay et protections anti-faux-merge qualifiés |
| CI et protection | **GO** | PR #385 fusionnée ; ruleset `21798272` sans bypass ; run `33404710182` terminal `success` sur quatre jobs |
| Moniteur critique manuel | **GO** | run `33404840701`, événement `workflow_dispatch`, commit `50a04b85944e6a5363092692572859fbeb00c5a0`, terminal `success` |
| Moniteur critique planifié | **GO** | runs `33578462794` et `33596363980`, événement `schedule`, terminaux `success` sur `main` |

## Qualification GitHub du moniteur

La vérification finale établit :

- dépôt public `Fredm237/codex-test`, branche par défaut `main` ;
- workflow `.github/workflows/production-critical-monitor.yml` présent sur
  `main` ;
- workflow GitHub `346700815` en état `active` ;
- YAML accepté par GitHub, avec `schedule` déclaré à `*/15 * * * *` et
  `workflow_dispatch` disponible ;
- permissions minimales `contents: read`, suffisantes pour le checkout et
  l'exécution du moniteur HTTP ;
- job identique exécuté manuellement avec succès de bout en bout ;
- aucune erreur de syntaxe, permission ou configuration observable dans l'API
  GitHub ;
- au snapshot initial, zéro run `schedule` avait été créé malgré plusieurs
  créneaux éligibles ; le suivi a ensuite observé les runs `33578462794` à
  `2026-09-02T01:12:36Z` et `33596363980` à `2026-09-02T05:51:14Z`, tous deux
  terminaux `success` sur `e667f3e52d3b4adb476b1e4c889b5b221373369e`.

Le premier événement réel et sa répétition sont donc prouvés sans lancement
manuel de substitution. Un futur échec reste un incident d'exploitation et ne
réécrit pas rétroactivement ce reçu.

## Snapshot production final

À `2026-08-31T16:07:12Z` :

- API : `alive=true`, `ready=true`, statut global `ok` ;
- PostgreSQL : `status=ok` ;
- Redis : `status=ok`, `errors=0` ;
- schéma : `a2d7e9f4c1b6` ;
- catalogue : `fresh` ;
- dernier succès : run `19`, terminé à
  `2026-08-31T14:39:40.931716Z` ;
- compteurs run 19 : 243 marchands, 1 feed borné, 20 000 offres, 0 feed
  ignoré ;
- aucune ingestion concurrente exposée par le Pulse ;
- configuration normale restaurée : `AWIN_FEED_LIMIT=0`, cadence Railway
  `0 */6 * * *`.

## Git et déploiements

- PR : `#385` ;
- commit de fusion `main` :
  `50a04b85944e6a5363092692572859fbeb00c5a0` ;
- CI `main` : run `33404710182`, quatre jobs `success` ;
- statuts associés au commit : Vercel `success`, Railway `success` ;
- moniteur manuel : run `33404840701`, job `99529746613`, `success` ;
- déploiement de reprise bornée :
  `5fa66804-f096-4522-9aad-91afdcb2ab75` ;
- déploiement de restauration Cron :
  `7d707084-7d3f-4ae1-a1b5-1799ab59ca47`.

## Limites connues non bloquantes

- aucun `EXTERNAL_PROVIDER_PENDING` ne subsiste sur le moniteur planifié ;
- aucune validation humaine indépendante : limitation explicite
  `NO_EXTERNAL_HUMAN_GROUND_TRUTH` ;
- OTLP hébergé, Prometheus/Grafana multi-réplica, rétention avancée, pager
  secondaire, trafic représentatif et SLO ratifiés restent dans
  [POST_PHASE_0_HARDENING](POST_PHASE_0_HARDENING.md) ;
- coût rendu complet, confiance subjective, sources après clic/achat et claims
  correspondants restent non supportés ;
- l'Immersive Experience demeure interdite jusqu'à sa gate Core propre.

## Passage de phase

Les critères d'intégrité, récupérabilité et sécurité nécessaires à la suite
sont satisfaits. **Phase 0 est fermée avec le verdict GO. Phase 1 — Product
Identity est ouverte.** Son périmètre commence par Brand, ProductFamily,
ProductModel, Variant, identifiers et provenance, avec un benchmark exact
product comme gate de sortie.
