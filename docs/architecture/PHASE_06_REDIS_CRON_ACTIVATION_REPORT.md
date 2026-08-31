# FILON — activation Redis privé et Cron Railway

- Date : **31 août 2026**
- Environnement : **Railway `production`**
- Décision : **GO Redis distribué ; GO Cron ; reprise bornée qualifiée**
- Verdict global : **Phase 0 = GO ; Phase 1 ouverte ; Immersive reste NO-GO**

## Topologie activée

Le projet Railway `feisty-rejoicing`
(`d5f2a738-67b2-4634-ae5f-efb9f540c283`) contient désormais quatre
services de production :

| Rôle | Service Railway | Exposition |
|---|---|---|
| API Core | `web` — `db05c3f5-e8d3-4034-ba9e-a96c3eb6b391` | domaine public existant |
| Base durable | `Postgres` — `d68db2c1-3ff8-45ca-a329-c89b4e81fab9` | réseau privé |
| Quota/cache | `Redis` — `11201b89-a758-4969-9068-955855af5cda` | réseau privé uniquement |
| Synchronisation catalogue | `filon-catalog-cron` — `b45d89cd-7be9-4e0e-b40e-0983fdf32c0e` | aucun domaine public |

Redis utilise le volume `97caf82b-2557-40b3-aa09-b52c0b6d624c`. Aucun
proxy TCP public n'a été créé. Le service web référence la variable privée
`Redis.REDIS_URL`; aucune URL, aucun mot de passe et aucun secret ne sont
recopiés dans ce rapport.

## Activation Redis fail-closed

Le service web possède maintenant les trois éléments atomiques du contrat :

- `RATE_LIMIT_BACKEND=redis` ;
- `REDIS_URL` comme référence Railway privée ;
- un `RATE_LIMIT_IDENTITY_SECRET` aléatoire dédié, stocké uniquement dans les
  variables Railway.

Railway a construit le déploiement web
`f8fdf3d6-8a77-4101-818a-7603c624d00d` et l'a activé sans interrompre
l'ancienne version. Après bascule :

- `/health/live` : `alive=true` ;
- `/health/ready` : `ready=true`, PostgreSQL `ok`, révision
  `e8c3f6a0b5d2` ;
- `/health` : Redis `status=ok`, une lecture réussie, aucune erreur et statut
  global `ok` ;
- aucune dégradation locale n'est autorisée si Redis devient indisponible : le
  middleware répond alors `503 rate_limit_unavailable`.

## Préflight Cron réel

Le Cron utilise la branche `codex/filon-phase-0-core`, la racine
`/filon-backend`, la région EU West et aucun domaine public. Ses variables
sensibles sont des références Railway vers `web` ou `Postgres`, jamais des
copies publiées.

Le premier déploiement `712c31cf-dff3-4f08-8fc4-d4956611c93c` a exécuté
uniquement :

```text
python -m app.ingest.scheduler --check
```

Il s'est terminé avec succès et a rendu le reçu expurgé suivant :

```json
{"catalog_state":"interrupted","due":true,"interval_hours":6,"schema_revision":"e8c3f6a0b5d2","status":"ready"}
```

Ce préflight n'a lancé aucune ingestion. Il a confirmé la configuration Awin,
les plafonds de volume, PostgreSQL, Alembic et l'absence de conflit actif.

## Cadence et premier cycle

La commande active est `python -m app.ingest.scheduler`. La cadence Railway
est `0 */6 * * *`, en UTC. Railway saute automatiquement une occurrence si le
cycle précédent est encore actif ; le job applicatif conserve en plus son
journal PostgreSQL mono-exécution.

L'image active est le déploiement
`88cd96b7-6311-441b-8192-ae58e846c60d`. Un premier cycle réel a été lancé
manuellement après le préflight :

- journal persistant : run `16`, trigger `scheduler`, état `running` ;
- 243 marchands Awin synchronisés au démarrage ;
- 830 feeds listés, 190 retenus par les régions FILON ;
- premières lectures Awin, écritures PostgreSQL et commits périodiques `ok` ;
- `5 600` relevés sur 24 h au dernier contrôle, contre `3 600` six minutes
  auparavant ;
- site public resté `ready`, PostgreSQL `ok`, révision Alembic inchangée.

Le cycle est volontairement long : le dernier cycle comparable enregistré,
run `14`, avait terminé 176 feeds et 1 287 889 offres en environ 3 h 39. Le
présent reçu ne transforme donc pas un cycle encore actif en succès final. Une
mise à jour devra consigner son état terminal, ses compteurs et sa durée.

## Qualification locale

- configuration, santé, middleware Redis et scheduler : **161 réussis** ;
- suite backend : **2 131 réussis, 2 ignorés**, avec un seul refus du bac à
  sable sur l'ouverture du récepteur OTLP loopback ;
- test OTLP concerné réexécuté avec loopback autorisé : **1 réussi** ;
- total logique qualifié : **2 132 réussis, 2 ignorés**.

## Rollback

- Redis : remettre `RATE_LIMIT_BACKEND=local` seulement dans une fenêtre de
  rollback explicitement acceptée, redéployer, puis retirer la référence ; ne
  jamais supprimer Redis avant la bascule web.
- Cron : retirer la cadence pour empêcher toute nouvelle exécution, attendre
  l'état terminal du cycle courant, puis supprimer le seul service Cron si un
  rollback est décidé.
- PostgreSQL : aucune migration ni modification de schéma n'a été nécessaire.

## Fermeture timeboxée du cycle long

Le cycle historique `18`, repris depuis `17`, a fourni deux checkpoints de
feeds terminés avec `20 000` offres chacun. Il a ensuite été interrompu de
manière contrôlée par retrait de son déploiement Railway. Son historique, ses
données déjà commitées et ses checkpoints ont été conservés ; l'API Pulse l'a
classé `interrupted` sans réécriture favorable.

La capacité permanente `--stop-after-current-feed` a été publiée au commit
`437dae27725c55eb5dd0543b55274e795df2ef83`. Elle vérifie la demande d'arrêt
après le commit du checkpoint et clôt le run en `interrupted` avec le motif
neutre `stop_after_current_feed`. La suite ciblée publique a passé **42 tests**
et la suite backend locale a qualifié **2 166 réussis, 3 ignorés** en comptant
le test OTLP loopback rejoué dans l'environnement autorisé.

Une seule reprise bornée a ensuite été exécutée :

- exécution Railway : `5fa66804-f096-4522-9aad-91afdcb2ab75` ;
- journal PostgreSQL : run `19`, `resumed_from_run_id=18` ;
- checkpoints repris : `3` ;
- feed sélectionné : `1 / 834` ;
- feed déjà terminé reconnu puis sauté : `20 000` offres ;
- téléchargement ou réingestion inutile : **aucun** ;
- état terminal : `succeeded` à `2026-08-31T14:39:40.931716Z` ;
- compteurs terminaux : `243` marchands, `1` feed, `20 000` offres,
  `0` ignoré.

Le déploiement de restauration
`7d707084-7d3f-4ae1-a1b5-1799ab59ca47` a remis
`AWIN_FEED_LIMIT=0` et la cadence `0 */6 * * *`. Il est devenu `Active` sans
créer de nouvelle exécution. La liste Railway conserve le run borné terminé en
`42m 6s` et annonce la prochaine occurrence normale.

## Intégration et moniteur critique

La PR GitHub `#385` a été fusionnée dans `main` au commit
`50a04b85944e6a5363092692572859fbeb00c5a0`. Le run CI `33404710182` a terminé
ses quatre jobs avec succès. Le workflow `Production — critical monitor` est
désormais actif sur la branche par défaut :

- exécution manuelle `33404840701` : `success` ;
- exécution planifiée : **`EXTERNAL_PROVIDER_PENDING / NON_BLOCKING`** ;
  GitHub n'avait créé aucun événement `schedule` au snapshot final.

Le workflow `346700815` est présent sur la branche par défaut `main`, accepté
par GitHub, actif, déclaré à `*/15 * * * *` et limité à la permission
`contents: read`. Le même job a réussi manuellement de bout en bout. Aucune
erreur de syntaxe, permission ou configuration n'est observable. L'attente
relève donc de l'ordonnanceur externe GitHub et ne bloque plus Phase 1. Un
second lancement manuel ne doit jamais être présenté comme une preuve
planifiée ; la première occurrence réelle reste surveillée.

## Limites restantes

Cette activation ferme les manques Redis, Cron, heartbeat, reprise et
checkpoints de P0.6. Le collecteur OTLP externe, l'agrégateur Prometheus, la
rétention, le dashboard hébergé, le pager secondaire et le trafic
représentatif restent dans le backlog post-Phase 0. Les sept datasets humains
restent à zéro sous la limitation explicite `NO_EXTERNAL_HUMAN_GROUND_TRUTH` ;
ils ne sont plus une gate Phase 0. Aucun blocker d'intégrité, de récupération
ou de sécurité nécessaire à Product Identity ne reste ouvert. L'occurrence
GitHub planifiée est une limitation fournisseur non bloquante consignée dans
[`PHASE_0_FINAL_RECEIPT`](PHASE_0_FINAL_RECEIPT.md).
