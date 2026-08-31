# FILON — activation Redis privé et Cron Railway

- Date : **31 août 2026**
- Environnement : **Railway `production`**
- Décision : **GO Redis distribué ; GO Cron ; premier cycle réel en cours**
- Verdict global : **Phase 1 et Immersive restent NO-GO**

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

## Limites restantes

Cette activation ferme les manques Redis et Cron de P0.6. Elle ne qualifie pas
le collecteur OTLP externe, l'agrégateur Prometheus, la rétention, le dashboard
hébergé, le pager, le trafic représentatif ni les sept datasets humains. Le
NO-GO métier et le NO-GO Immersive restent donc inchangés.
