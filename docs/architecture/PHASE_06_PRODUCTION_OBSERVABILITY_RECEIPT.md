# FILON — reçu production OpenMetrics et résilience Railway

- Date : **29 août 2026**
- Fenêtre de contrôle : **16:10–16:29 CEST**
- Environnement : `production`
- Service applicatif : `web`
- Déploiement contrôlé : `c832d1c8-e50f-4fac-94b3-8b59bb6cfff1`
- Décision : **GO pour l'export OpenMetrics direct ; résilience stockage encore
  EN COURS**

Ce reçu est volontairement expurgé. Il ne contient ni jeton, ni chaîne de
connexion, ni valeur de variable protégée, ni corps métrique complet.

## Export OpenMetrics direct

Le contrat réel de `GET /health/metrics/openmetrics` a été vérifié contre le
déploiement production, en récupérant le secret uniquement dans le contexte
d'exécution Railway et sans l'afficher.

| Requête | Résultat |
|---|---:|
| sans `Authorization` | HTTP 401 |
| Bearer incorrect | HTTP 401 |
| secret placé en query string | HTTP 401 |
| Bearer correct | HTTP 200 |

La réponse autorisée déclare
`application/openmetrics-text; version=1.0.0`, interdit le cache avec
`Cache-Control: no-store`, se termine par `# EOF` et ne contient pas le secret.
Le payload contrôlé compte **15 260 octets**, **199 lignes**, **24 familles de
métriques** et **15 noms de labels**, tous dans les listes fermées attendues.
Aucune famille hors préfixe `filon_` n'a été observée. La readiness vérifiée
après le contrôle est restée `true`.

Cette preuve qualifie l'endpoint direct et son authentification. Elle ne prouve
pas encore un scrape Prometheus, une rétention, une agrégation multi-réplica,
un reset observé, un dashboard importé ou un pager.

## Sauvegardes du volume PostgreSQL

Après autorisation explicite du coût incrémental, les trois cadences ont été
activées atomiquement le 29 août 2026 à 14:28:16 UTC, puis relues via l'API :

| Cadence | Cron Railway UTC | Rétention API |
|---|---|---:|
| `DAILY` | `54 13 * * *` | 518 400 s — 6 jours |
| `WEEKLY` | `33 19 * * 6` | 2 332 800 s — 27 jours |
| `MONTHLY` | `21 7 1 * *` | 7 689 600 s — 89 jours |

Les horaires ont été générés par Railway. Les deux sauvegardes manuelles sans
expiration restent présentes :

| Sauvegarde | Date UTC | Planning | Données propres rapportées |
|---|---|---|---:|
| `Online resize to 20000MB` | 12 août 2026 | aucun | 3 734 Mio |
| `FILON pre-core-deploy 2026-08-29` | 29 août 2026 | aucun | 310 Mio |

Railway décrit les snapshots comme incrémentaux et Copy-on-Write. Sa
documentation résume les rétentions comme 6 jours, 1 mois et 3 mois ; l'API
fournit ci-dessus les durées exactes effectivement appliquées. Leur stockage
incrémental est facturé au tarif du stockage de volume. Références officielles :
[sauvegardes](https://docs.railway.com/volumes/backups) et
[tarification](https://docs.railway.com/pricing).

La mutation a seulement géré les plannings de l'instance de volume PostgreSQL.
Elle n'a déclenché ni déploiement, ni restauration, ni écriture applicative.
Juste après activation, `GET /health/live` et `GET /health/ready` sont restés
verts ; la base est `ok` et la révision demeure `f4c81a9d2e70`.

## Capacité et alerte plateforme

Le volume est `READY` à **7 855,56 Mio sur 20 000 Mio**, soit **39,28 %** et
environ **12 144,44 Mio libres**. Aucun dashboard Railway Observability et donc
aucun moniteur de seuil associé n'est configuré dans l'environnement
production.

La marge instantanée est correcte, mais le risque n'est pas fermé : les logs du
28 août 2026 ont déjà montré `No space left on device` pendant la création de
fichiers temporaires PostgreSQL. Une alerte de capacité indépendante et un
test périodique de restauration restent obligatoires avant de déclarer la
résilience stockage terminée.

## Verdict borné

- endpoint OpenMetrics production : **QUALIFIÉ** ;
- authentification et non-fuite du secret : **QUALIFIÉES** ;
- sauvegarde manuelle et restore drill : **QUALIFIÉS** ;
- sauvegardes planifiées `DAILY + WEEKLY + MONTHLY` : **QUALIFIÉES** ;
- alerte de capacité Railway : **ABSENTE** ;
- agrégateur, rétention, dashboard, pager et trafic représentatif : **NON
  PROUVÉS**.

P0.6 reste donc `en_cours`. Ce reçu ne lève pas le NO-GO Phase 1, également
maintenu par l'absence de datasets humains Quality Lab.
