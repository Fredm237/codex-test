# FILON — décision fondatrice de timebox et sortie de Phase 0

- Date : **31 août 2026**
- Statut : **DÉCISION ACTIVE**
- Principe : **SUFFICIENTLY SAFE TO PROCEED ≠ PERFECT**
- Immersive : **NO-GO inchangé**

## Décision

Phase 0 ne construit pas une infrastructure SRE parfaite. Elle se termine dès
que Product Identity peut commencer sans risque réel de corruption, de perte,
de migration irrécupérable, de concurrence d'ingestion ou d'absence de
rollback. Aucune limitation utile mais non dangereuse ne devient un nouveau
gate infini.

## Blockers de Phase 1

Un élément reste bloquant uniquement s'il protège directement l'intégrité ou
la récupérabilité nécessaires à Product Identity :

- production, PostgreSQL ou Redis réellement instables ;
- migration ou rollback non qualifiés ;
- sauvegarde/restauration non qualifiée ;
- journal catalogue non fiable ou ingestions concurrentes ;
- cycle réel sans état terminal prouvé ;
- heartbeat et récupération fail-closed non déployés ;
- CI requise rouge ;
- absence d'alerte sur API, PostgreSQL, Redis, catalogue stale, taux d'erreur
  critique ou capacité critique.

## Non-blockers déplacés après Phase 0

Prometheus/Grafana avancés, backend OTLP, rétention longue, dashboards
supplémentaires, pager secondaire, trafic représentatif additionnel, SLO
ratifiés, optimisation de coût et infrastructure hyperscale figurent désormais
dans le [backlog de durcissement post-Phase 0](POST_PHASE_0_HARDENING.md). Ils
peuvent progresser parallèlement, sans retarder Product Identity.

## Minimum viable observability

Le minimum bloquant combine :

1. les sondes Railway `/health/live`, `/health/ready` et `/health` ;
2. `/api/catalog/pulse` pour distinguer `fresh`/`syncing` d'un cycle réellement
   stale ou interrompu ;
3. `/health/metrics` pour un ratio 5xx critique à partir de 100 requêtes ;
4. les moniteurs Railway PostgreSQL existants à 70 % et 85 % du volume ;
5. le workflow externe `Production — critical monitor`, toutes les quinze
   minutes, qui échoue fermé avec un code neutre et déclenche la notification
   GitHub du compte.

Le workflow est activé sur `main` après le déploiement du heartbeat. Une
exécution manuelle verte prouve le job de bout en bout. La première occurrence
planifiée réelle reste surveillée ; si GitHub ne crée aucune occurrence malgré
un workflow présent, valide et actif, cette attente fournisseur est
`EXTERNAL_PROVIDER_PENDING / NON_BLOCKING` et ne devient pas un gate infini.

## Exit criteria Phase 0

Phase 0 devient `GO` lorsque toutes les conditions suivantes sont prouvées :

- production, PostgreSQL et Redis sains ;
- migrations, rollback, backup et restore qualifiés ;
- CI verte et branche principale protégée ;
- Quality Lab autonome vert, sans prétention de validation humaine ;
- architectures Observation/Product/Offer shadow sûres ;
- cycle catalogue 17 dans un état terminal prouvé ;
- heartbeat, reprise fail-closed et checkpoints par feed déployés et qualifiés ;
- alerting critique minimum opérationnel ;
- aucun blocker d'intégrité ou de récupérabilité encore ouvert.

Une observabilité parfaite, une infrastructure hyperscale et une validation
humaine ne sont pas des exit criteria.

## Sortie obligatoire

À la satisfaction des critères, produire sans délai :

- `PHASE_0_FINAL_RECEIPT` ;
- state snapshot ;
- backup status ;
- Git/CI status ;
- known limitations ;
- backlog `POST_PHASE_0_HARDENING`.

Puis ouvrir Phase 1 — Product Identity. Aucun travail immersif n'est autorisé
par cette décision.

## Amendement fournisseur externe — 31 août 2026

Le workflow GitHub `346700815` est présent sur la branche par défaut, actif,
accepté avec le calendrier `*/15 * * * *`, doté de la permission minimale
requise, et son exécution manuelle `33404840701` est terminale `success`.
GitHub n'avait créé aucune occurrence `schedule` au snapshot final. Cette
absence exclusivement externe est donc une limitation non bloquante. Le
[reçu final](PHASE_0_FINAL_RECEIPT.md) ferme Phase 0 et ouvre Phase 1 tout en
conservant la surveillance du premier événement réel.
