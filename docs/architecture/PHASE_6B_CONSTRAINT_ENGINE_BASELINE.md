# FILON — Phase 6B Constraint Engine Baseline

- Observation : **1er septembre 2026**
- Mode : **lecture seule, agrégats uniquement**
- Déploiement web observé : `41be846b-7e70-4a1c-8c25-06c262856f11`
- Schéma : `f7c5e9a1b3d6`
- Payload brut publié : **aucun**

## Surface Hybrid Retrieval disponible

| Mesure | Valeur |
|---|---:|
| runs Hybrid Retrieval | 1 |
| runs `CANDIDATES` | 1 |
| candidats persistés | 1 |
| offres distinctes attachées | 1 |
| prix connus | 1 / 1 |
| devises connues | 1 / 1 |
| stocks connus | 1 / 1 |
| offres en stock | 1 / 1 |
| offres marquées adultes | 0 / 1 |

Ce corpus est suffisant pour qualifier le chemin technique borné de Phase 6,
mais pas pour prétendre mesurer la couverture métier générale. La limitation
`SINGLE_HYBRID_CANDIDATE_SHADOW_SAMPLE` reste explicite.

## Santé observée

- web Railway : Online ;
- `/health/live` : 200 ;
- `/health/ready` : 200, PostgreSQL ok, schéma `f7c5e9a1b3d6` ;
- `/health` avec l'identité edge Railway attendue : 200, PostgreSQL et Redis
  `ok` ;
- Redis Railway : Online ; PostgreSQL Railway : Online.

Un appel interne à `/health` sans `X-Real-IP` reçoit volontairement
`rate_limit_unavailable`; ce résultat prouve le fail-closed de l'identité edge
et ne constitue pas une panne Redis.

## Écart opérationnel détecté

Le service Cron est encore attaché à un déploiement Phase 4
`89bdef84-2e3c-47bb-9c05-e2b6e39bcd3a`. Son occurrence du 1er septembre à
12:00 UTC a terminé `Crashed` après 6 secondes avec un motif public neutre
`RuntimeError`. Le web est déjà sur `main` Phase 5. Aucun changement n'a été
effectué pendant cette baseline.

Cet écart doit être corrigé et une occurrence bornée doit réussir avant toute
activation production du Constraint Engine. Il n'invalide ni les agrégats de
la base ni la qualification locale du moteur.
