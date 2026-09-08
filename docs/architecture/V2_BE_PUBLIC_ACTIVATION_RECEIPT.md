# FILON — Reçu d’activation publique V2 Belgique

- Date : **9 septembre 2026**
- Verdict : **PUBLIC BELGIQUE ACTIVÉ ET PROUVÉ**
- Portée : **smartphones / Belgique / `fr-BE` / `purchase_advice`**
- Type de réponse autorisé : **`ABSTAIN` uniquement**
- Lecteur public V2 : **ON**
- Lecteur canary : **OFF**
- Core V1 : **calculé en premier, fallback et kill switch conservés**
- `BUY_NOW`, `FACTUAL_OPTIONS` et `WAIT` : **BLOQUÉS**

## Autorisation append-only

La promotion repose sur la filiation exacte de la campagne belge :

- campagne :
  `sha256:d4160cb9a4e0aa08a9b7e3e61385fc7c31ada5f6f650a5d14b8d6fabc7109b8a` ;
- reçu canary source :
  `sha256:c979b6353767d64d4e63a8775afebf835d56e3326ae437afdb2a34b515c5576d` ;
- gate canary source :
  `sha256:a9c35db4450c7b0c4ef1f184264bf84e7227d53dabd7b9323b5a18c5b94707f6` ;
- reçu public :
  `sha256:1d6270ec321564ad73fd988e734161584c7fb388f1f98179be065e3885a264ff` ;
- gate public :
  `sha256:27da309ad4964c5871c85f2766353d604e8c34622935e01d256c5c3b84636c9f`.

La commande `dry-run → apply unique → replay identique` a produit
`PUBLIC_AUTHORIZED`. L’apply a créé le reçu `7` ; le replay a retrouvé le même
reçu sans duplication. Les huit preuves publiques reproductibles ont été
enregistrées sous les lignes `51` à `58` de leur registre append-only.

## Qualification canary belge

Le gate a utilisé exclusivement les 30 observations belges `113` à `142` :

- 30 observations réelles appariées Core V1 / V2 ;
- 30 réponses V2 `ABSTAIN` ;
- 0 fallback dans le cohort éligible ;
- 0 erreur lecteur ou violation de sûreté ;
- chaîne et provenance complètes : **30/30** ;
- 0 requête brute conservée ;
- p95 `latence V2 - latence Core V1` : **-2 766 304 µs**.

Le rollback canary vers shadow a été exercé sur le déploiement
`bf1de86c-d4e7-4af5-9986-d01f6a4dc149` : Core V1 a continué à répondre,
le journal est resté intact et le compteur canary est resté à 30. Le canary a
ensuite été restauré par `1808f2aa-faf4-4a61-9225-2671421b4a16`.

## Déploiement public

Le commit `30ca0009679c04b1742135811f9578b9da241232` et la CI GitHub Actions
`34281348334` sont verts. Le service Railway `web` sert le déploiement
`0a620a3c-b005-44fa-8ee4-c0e27059df50`, instance
`d354adff-0e88-445f-b58c-26c59f370f23`, avec :

- `V2_CHAIN_MODE=public` ;
- lecteur public V2 activé ;
- lecteur canary désactivé ;
- cohorte canary résiduelle vide ;
- reçu public exact désigné ;
- Core V1 et son kill switch conservés.

Un premier déploiement, `abcd25a2-f231-410d-a9cd-673060a9077b`, a refusé de
démarrer car une ancienne cohorte canary était encore présente. Le garde-fou
fail-closed a maintenu l’ancien service actif. Après fermeture explicite de
cette cohorte, le déploiement public ci-dessus est devenu `Active`.

## Preuve de service public

Une requête synthétique impossible, envoyée sans en-tête canary à la vraie
route `/api/advise`, a retourné HTTP 200 sans recommandation ni alternative.
L’observation append-only `143` prouve :

| Champ | Valeur |
|---|---|
| assignment | `public_authorized` |
| source | `v2` |
| response type | `ABSTAIN` |
| scope | `smartphones / fr-BE / purchase_advice` |
| chain complete | `true` |
| safety state | `ABSTAIN` |
| fallback | aucun |
| raw query retained | `false` |
| receipt | reçu public exact ci-dessus |

Le contrôle opératoire post-requête rapporte `mode=public`, une observation
publique, zéro fallback public et zéro violation de sûreté.

## Santé finale

Après activation :

- `/health/live` : HTTP 200 ;
- `/health/ready` : HTTP 200, PostgreSQL prêt ;
- `/health` : HTTP 200, PostgreSQL et Redis `ok` ;
- schéma Alembic : `2d0f4a6c8e1b` ;
- ingestion catalogue active : **0** ;
- exécution V2 active : **0** ;
- dernier catalogue : run `29`, terminal `succeeded`, 1 feed et 500 offres ;
- sauvegardes PostgreSQL quotidiennes, hebdomadaires et mensuelles présentes ;
- restauration disponible ; PITR non activé, limitation connue et non
  bloquante avec les sauvegardes et l’exercice de restauration déjà prouvé.

## Limites fail-closed

Cette activation ne permet pas à V2 d’inventer un produit ni un verdict. Le
seul résultat belge que V2 peut actuellement servir est une abstention sûre.
Toute portée non autorisée, donnée trop ancienne, provenance incomplète,
erreur lecteur ou réponse autre que `ABSTAIN` conserve le bloc Core V1 entier.

**V2 PUBLIC / ABSTAIN BELGIQUE / CORE V1 FALLBACK CONSERVÉ.**

Ce reçu n’autorise aucune extension implicite de pays, verticale ou type de
réponse.
