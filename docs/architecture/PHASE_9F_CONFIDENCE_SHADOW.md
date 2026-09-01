# FILON — Phase 9F Confidence shadow

- Date : **2 septembre 2026**
- Migration : `e2b0d4f6a8c1`
- Parent : `d1a9c3e5f7b0`
- Flag : `CONFIDENCE_SHADOW_ENABLED=false`
- Lecteur public : **AUCUN**
- Statut : **QUALIFIÉ LOCAL — PRODUCTION À QUALIFIER**

## Expansion additive

La migration ajoute `confidence_calibration_runs` et
`confidence_dimension_records`. Chaque run référence un reçu Offer
Optimization, conserve uniquement des digests et agrégats, impose cinq
dimensions et interdit tout contexte brut. Chaque dimension est unique par run
et une probabilité non nulle exige l'état `CALIBRATED`, un profil et un support
strictement positif.

Le writer est append-only et idempotent par `run_key`. Une divergence de replay
est une erreur. Le dry-run n'écrit rien ; l'apply exige le flag uniquement dans
le processus de maintenance et dépend explicitement d'Offer Optimization.

## Replay borné

Le replay lit au plus 100 runs Offer Optimization, avec une borne
`after_offer_optimization_run_id` et un instant UTC fixe. En l'absence de
profils empiriques de production, il persiste une abstention explicite : cinq
dimensions inconnues et aucune probabilité.

## Rollback

Le rollback opérationnel laisse le flag à `false`. Les lecteurs existants
ignorent les deux tables. Aucun downgrade de production n'est requis ; la
migration reste réversible en environnement jetable.

## Reçu local

- 80 tests ciblés verts ;
- upgrade, head, drift, sauvegarde/restauration et downgrade SQLite verts ;
- dry-run sans écriture, apply unique et replay identique verts ;
- cinq records `UNKNOWN`, zéro probabilité et zéro contexte brut sur la fenêtre
  sans profil empirique ;
- 2 543 tests backend qualifiés au total ;
- trois tests PostgreSQL explicitement réservés à la CI.
