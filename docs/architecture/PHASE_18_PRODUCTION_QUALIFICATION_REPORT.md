# FILON — Phase 18 Personal Commerce production qualification

- Date : **2 septembre 2026**
- Décision : **P18F = GO shadow production**
- Mode : **journal privé append-only, fail-closed**
- Writer persistant : **OFF**
- Lecteurs canary et public : **OFF**
- P18G canary/public : **NO-GO inchangé**

## Livraison

- pull request : GitHub `#413`, fusionnée ;
- commit de fusion : `e48529bfde73c958f15ae00e1eaff953d382fedc` ;
- CI terminale sur `main` : run `33656618219`, quatre jobs réussis ;
- déploiement de migration : `c60a2674-ff63-4832-ac68-1c9335a288c7` ;
- déploiement après configuration HMAC :
  `d444580f-6977-4610-83eb-4797b1ddd087` ;
- révision Alembic production : `b5d3f7a9c1e4`.

Les journaux Railway prouvent l'upgrade transactionnel
`a4e2c6f8b0d3 -> b5d3f7a9c1e4`, le redémarrage du serveur, la validation du
schéma et une sonde `/health/ready` à 200. L'ancien déploiement reste présent
dans l'historique Railway comme point de rollback.

## Secret et activation

`PERSONAL_COMMERCE_SUBJECT_SECRET` est configuré dans Railway avec une valeur
aléatoire de 64 caractères. Sa valeur n'est ni consignée, ni publiée, ni
rapatriée hors de Railway. La configuration persistante relue dans le
conteneur confirme :

- secret HMAC présent et longueur valide ;
- `PERSONAL_COMMERCE_SHADOW_ENABLED=false` ;
- `V2_CHAIN_MODE=off` ;
- lecteurs V2 canary et public `false`.

Les prérequis shadow ont été activés uniquement dans le processus de
maintenance qui exécutait le replay. Aucun autre moteur n'a été lancé et aucun
flag Railway persistant n'a été promu.

## Replay production borné

Fenêtre unique et identique pour les trois passages :

- `evaluated_at=2026-09-02T17:30:00Z` ;
- `after_buy_wait_run_id=0` ;
- `limit=1` ;
- source : `buy_wait_run_id=1`.

| Passage | Scannés | Sélectionnés | Abstentions | Créés | Existants |
|---|---:|---:|---:|---:|---:|
| dry-run | 1 | 0 | 1 | 0 | 0 |
| apply unique | 1 | 0 | 1 | 1 | 0 |
| replay identique | 1 | 0 | 1 | 0 | 1 |

Les trois passages partagent l'identité :
`sha256:188d0add8e3127cda74923c659c79775ccb8454acf0f0ecd9764efe2a9d77ae0`.

Deux tentatives d'apply ont auparavant été refusées avant toute écriture : la
première sans BUY/WAIT shadow, la seconde avec un mode chaîne incompatible
avec les flags persistants explicitement OFF. Elles démontrent le comportement
fail-closed ; un seul apply a réellement créé une ligne.

## Invariants de la ligne produite

La table `personal_commerce_decision_runs` contient une ligne et la table
`personal_commerce_erasure_receipts` aucune, ce qui est attendu sans cohorte
consentante. La ligne créée possède :

- `personalization_consent=false` ;
- aucun digest sujet et aucune échéance de rétention ;
- `raw_context_retained=false` ;
- résultat `ABSTAINED`, action `ABSTAIN` ;
- aucune solution sélectionnée ;
- `measurement_status=not_calibrated` ;
- raison `personalization_consent_missing`.

Aucune préférence, garde-robe, taille, budget, contexte personnel ou payload
marchand brut n'est conservé.

## Santé après qualification

- `/health/live` : HTTP 200, `alive=true` ;
- `/health/ready` : HTTP 200, PostgreSQL et schéma
  `b5d3f7a9c1e4` `ok` ;
- `/health` : HTTP 200, application, PostgreSQL et Redis `ok` ;
- statuts de déploiement GitHub : Railway web, Railway Cron et Vercel
  `success` ;
- CI `33656618219` : Backend, Web, Mobile et Extension `success`.

Le pulse catalogue reste à HTTP 200 mais expose le run historique `24` avec
heartbeat obsolète et `recovery_required=true`. Aucun second run catalogue n'a
été lancé pendant P18F. Cet état précède la qualification Personal Commerce et
doit être traité par le chantier d'exploitation catalogue, sans être masqué par
ce reçu.

## Hygiène d'accès

La qualification a utilisé une clé SSH dédiée et temporaire, limitée au projet
Railway FILON. La clé a été supprimée de Railway immédiatement après les
contrôles, son agent local arrêté et les fichiers de clé supprimés de `/tmp`.

## Décision

Migration additive, configuration HMAC, abstention sans consentement,
persistance append-only, absence de contexte brut et idempotence sont prouvées
sur PostgreSQL de production. Les lecteurs publics sont restés OFF.

**P18F = GO shadow production.**

P18G reste fermé jusqu'à une cohorte consentante autorisée permettant de
prouver export, effacement, rétention, neutralité, rollback et promotion
atomique de la chaîne nécessaire. Aucun résultat de P18F ne vaut autorisation
de canary ou de lecteur public.
