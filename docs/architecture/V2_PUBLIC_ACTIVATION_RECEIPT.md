# FILON — Reçu d’activation publique V2

- Date : **8 septembre 2026**
- Verdict : **PUBLIC FACTUEL ACTIVÉ ET PROUVÉ**
- Portée prouvée : **smartphones / France / `fr` / `purchase_advice`**
- Type de réponse autorisé : **`FACTUAL_OPTIONS` uniquement**
- Lecteur public V2 : **ON**
- Lecteur canary : **OFF**
- Fallback Core V1 : **ON et exercé**
- `ABSTAIN`, `BUY_NOW` et `WAIT` : **NON AUTORISÉS**

## Autorisation persistée

La promotion repose sur des lignes append-only et sur la filiation exacte de
la campagne canary :

- reçu public :
  `sha256:6360c99b1597885e2fc1f799d18e6e5bb282040b87140eb6b69c506d4bff8acc` ;
- gate public :
  `sha256:04dc0b082c169f4771e3feaf574daa6502d7aab7a387863c62be558c0fbffea9` ;
- reçu canary source :
  `sha256:65fac702d451e5ec31c1976dc84552cb5e47d3f66f8467a731116e9c0515f428` ;
- gate canary source :
  `sha256:5f8eb7638b1d54958c4d783fff305286dda2ead085cdd1a69e6cbd9193e8efe4` ;
- campagne :
  `sha256:c16fe38cd6787f362a1270ba6d22b02c6e36fea44017fdd1f2abb9b8251722fb`.

Le calcul `dry-run → apply unique → replay identique` a convergé vers le même
reçu `PUBLIC_AUTHORIZED`. Les huit preuves exigées ont été enregistrées puis
rejouées sans duplication : readiness/5xx, injection d’échec, rollback vers
shadow, backup/restore, capacité/alerting, régressions héritées, audit des
blockers et politique publique.

## Qualification canary réelle

Le gate public a utilisé uniquement les observations portant simultanément le
reçu canary et le gate canary exacts. L’ancienne télémétrie d’autres campagnes
n’a pas été mélangée :

- 30 requêtes réelles appariées Core V1 / V2 ;
- 30 réponses servies par V2 ;
- 30 réponses `FACTUAL_OPTIONS` ;
- 0 fallback éligible ;
- 0 erreur lecteur ;
- 0 requête brute conservée ;
- p95 apparié `latence V2 - latence Core V1` : **-275 337 µs** ;
- provenance, chaîne et état de sûreté complets : **30/30**.

Une injection d’échec a servi le bloc Core V1 entier avec le motif neutre
`v2_reader_error`. Un processus isolé configuré en `shadow` a prouvé le kill
switch : source `core_v1`, raison `reader_off`, réponse Core inchangée.

## Déploiement

Le service Railway `web` sert le déploiement
`1cfe9474-a2ba-42b1-9c3d-6442f561ab3e`, instance
`e1b13be2-3f0e-40f2-a8db-f61e434fadea`, avec :

- `V2_CHAIN_MODE=public` ;
- `V2_PUBLIC_READER_ENABLED=true` ;
- `V2_CANARY_READER_ENABLED=false` ;
- aucune cohorte canary résiduelle ;
- le reçu public exact désigné ;
- les writers atomiques maintenus ON ;
- le schéma Alembic `1c9e3b5d7f0a`.

Le routeur calcule toujours Core V1 en premier. V2 ne remplace Core que comme
un bloc entier lorsque périmètre, fraîcheur, provenance, complétude et sûreté
sont tous admissibles.

## Preuve de service public

Une requête non personnelle `iPhone 15`, exécutée par la vraie route
`/api/advise/stream` avec `country=fr` et `locale=fr`, a retourné HTTP 200 et
un produit réel vérifié. L’observation append-only `109` prouve :

| Champ | Valeur |
|---|---|
| assignment | `public_authorized` |
| source | `v2` |
| response type | `FACTUAL_OPTIONS` |
| chain complete | `true` |
| safety state | `SAFE` |
| provenance complete | `true` |
| fallback | aucun |
| raw query retained | `false` |

Le gate et le reçu portés par cette observation sont exactement les identités
publiques ci-dessus.

## Santé finale observée

Après activation :

- `/health/live` : HTTP 200, vivant ;
- `/health/ready` : HTTP 200, prêt ;
- `/health` : HTTP 200, PostgreSQL et Redis `ok` ;
- ingestion catalogue active : **0** ;
- exécution V2 active : **0** ;
- sauvegardes volume PostgreSQL : actives, restauration disponible ;
- schéma : `1c9e3b5d7f0a` ;
- CI GitHub Actions `34213980406` : **4/4 jobs verts**, y compris le contrôle
  Alembic baseline/stamp/drift/restauration.

## Limites explicites et fail-closed

Cette promotion n’autorise ni verdict d’achat ni recommandation temporelle.
`BUY_NOW`, `WAIT` et `ABSTAIN` restent bloqués. Les autres verticales restent
sur Core V1.

La Belgique n’a actuellement aucun snapshot Product Ontology régional qualifié
malgré la présence d’offres. Une requête `country=be`, `locale=fr-BE` a donc
servi Core V1 intégralement (observation `110`, HTTP 200, aucune requête brute
conservée). Cette limite est sûre mais signifie que le trafic belge n’utilise
pas encore `FACTUAL_OPTIONS` V2. Son ouverture exigera une campagne BE bornée,
des observations canary liées à un nouveau reçu, puis une nouvelle promotion ;
elle ne peut pas être déduite de la preuve France.

## Verdict

**V2 PUBLIC / FACTUAL_OPTIONS FRANCE / CORE V1 FALLBACK PROUVÉ.**

Ce reçu n’autorise aucune extension implicite de pays, verticale ou type de
réponse.
