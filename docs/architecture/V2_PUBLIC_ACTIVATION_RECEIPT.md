# FILON — Reçu d’activation publique V2

- Date : **7 septembre 2026**
- Verdict : **PUBLIC ACTIVÉ ET PROUVÉ**
- Portée : **smartphones / `fr` / `fr-BE` / `purchase_advice`**
- Type de réponse autorisé : **`ABSTAIN` uniquement**
- Lecteur public V2 : **ON**
- Lecteur canary : **OFF**
- Fallback Core V1 : **ON et exercé**
- `BUY_NOW` / `WAIT` : **NON AUTORISÉS**

## Autorisation persistée

La promotion repose sur le reçu append-only :

- reçu public :
  `sha256:aec9c600d9cda149ab792323688f4ea96827400e7408a86b38c3ac4dc9a18b6d` ;
- gate public :
  `sha256:fed54c4ed2d4aebea44d4080171ada0ee2dd03d017f0898b529d18c9a5f98dad` ;
- campagne :
  `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d` ;
- reçu de base SHADOW :
  `sha256:871ce08cdf0afd1faa1694241042f88acc2a6d4b7d49dcefebd31c537a8a9449`.

Le dry-run, l’apply unique et le replay exact ont convergé vers la même
identité. Les huit preuves PUBLIC ont été enregistrées dans
`v2_promotion_proofs` puis relues par leur digest exact : readiness/5xx,
failure injection, rollback, backup/restore, capacité/alerting, régressions,
audit des blockers et politique publique.

## Déploiement

Le service Railway `web` sert le déploiement
`0ad257bc-c778-4e0e-9504-ac48f6c42bed` avec :

- `V2_CHAIN_MODE=public` ;
- `V2_PUBLIC_READER_ENABLED=true` ;
- `V2_CANARY_READER_ENABLED=false` ;
- le reçu public exact désigné ;
- les writers atomiques maintenus ON ;
- le schéma Alembic `f9c7d1e3a5b8`.

Le routeur calcule toujours Core V1 en premier. Il ne remplace Core que si le
périmètre, la fraîcheur, la provenance, la complétude et la sûreté V2 sont
admissibles. Toute autre situation conserve le bloc Core V1 complet.

## Données réelles et exécutions

Le corpus initial ne contenait aucune preuve smartphone dans les 1 000 raws.
Un flux Awin E.Leclerc FR strictement borné a donc été inspecté puis arrêté
après la première fenêtre commitée :

- 200 raws persistés ;
- 43 lignes correspondant à des smartphones identifiables ;
- run catalogue `28` terminal `interrupted`, raison neutre
  `v2_seed_window_complete` ;
- aucune ingestion catalogue ou chaîne V2 concurrente.

La chaîne a ensuite traité la fenêtre réelle `1001–1100` :

- exécution initiale `38` : **succeeded**, 13/13 étapes ;
- rafraîchissement `39` : **succeeded**, 13/13 étapes ;
- evaluation `39` :
  `sha256:1832e2a7a5d92beb73ff1b6847aed565812a881fdac39d6c8d8d05367e6882dd` ;
- 100 snapshots Product Ontology : 17 `VERIFIED`, 83 `PARTIAL`.

## Preuve de service public

Une requête synthétique non personnelle sur `iPhone 15`, avec un budget
incompatible, a produit une abstention V2 réelle. Le journal agrégé et sans
requête brute a persisté l’observation `69` :

| Champ | Valeur |
|---|---|
| assignment | `public_authorized` |
| eligibility | `eligible` |
| vertical | `smartphones` |
| source | `v2` |
| response type | `ABSTAIN` |
| chain complete | `true` |
| safety state | `ABSTAIN` |
| provenance complete | `true` |
| fallback | aucun |

Une requête pour laquelle Core disposait d’un résultat réel est restée sur
Core V1 avec la raison `critical_unknown`. Une requête sans dépendances V2
admissibles est également revenue entièrement à Core V1. Ces deux cas
prouvent que l’activation publique n’efface pas une réponse existante et
n’invente aucune donnée.

## Santé finale observée

Après activation et preuve de routage :

- `/health/live` : HTTP 200 ;
- `/health/ready` : HTTP 200 ;
- `/health` : HTTP 200, statut `ok` ;
- `/api/catalog/pulse` : HTTP 200 ;
- PostgreSQL et Redis : disponibles ;
- ingestion catalogue active : **0** ;
- exécution V2 active : **0** ;
- violations de sûreté observées : **0**.

La CI GitHub Actions `34048734311`, utilisée pour le code déployé, est
terminale et verte sur ses quatre jobs : backend/Quality Lab, web, mobile et
extension.

## Limite explicite

`PUBLIC` ne signifie pas que V2 rend déjà des recommandations actionnables.
La seule sortie promue est l’abstention prouvée. `BUY_NOW`, `WAIT`, les autres
verticales et tout élargissement de locale restent fermés jusqu’à leurs
propres preuves objectives et reçus append-only. Core V1 reste le fallback et
le kill switch opérationnel.

## Verdict

**V2 PUBLIC / ABSTAIN-ONLY / CORE V1 FALLBACK PROUVÉ.**

Ce reçu n’autorise aucune extension implicite du périmètre public.
