# FILON — qualification distante de la Phase 0

- Date de coupure initiale : **29 août 2026, 13:15 CEST**
- Préflight Railway authentifié : **29 août 2026, 13:37 CEST**
- Requalification du lot inventaire : **29 août 2026, 14:00 CEST**
- Requalification du workflow de curation : **30 août 2026, 21:27 CEST**
- Requalification du Catalog Quality Funnel : **30 août 2026, 22:00 CEST**
- Correction des douze étapes et requalification de production : **30 août 2026**
- Branche : `codex/filon-phase-0-core`
- Dépôt public : `Fredm237/codex-test`
- Décision : **code techniquement qualifié ; lancement et Phase 1 NO-GO**

## 1. Identité du contenu publié

Le push Git local n'était pas authentifié sur l'hôte. La publication a donc
utilisé l'API Git Data GitHub authentifiée, sans inclure le worktree non
commité. L'historique distant est consolidé, mais l'identité du contenu est
prouvée par l'arbre Git :

| Autorité | Commit | Arbre |
|---|---|---|
| Référence applicative locale courante | `594f51fc91651eb6e067dc9497b0b4337d0e57bc` | `9534214815bc6af2630bbf523fffb5c76f64980c` |
| Référence applicative distante courante | `9d8ade3ad671afe98f28be9c6f1fd5bf69fae414` | `9534214815bc6af2630bbf523fffb5c76f64980c` |

Le commit distant `e04dfc2c18ef58177d4182acbb67c966058ff9c0`
porte l'arbre applicatif validé
`77ca57dbd92a028dc693de66b5f3e00d381f1115`. Le commit suivant ne modifie que
le registre de mission ; il amène l'arbre distant au même SHA que le HEAD
local au moment de la qualification applicative. Les commits documentaires
ultérieurs s'appuient sur cet arbre sans changer le runtime qualifié. Les
modifications utilisateur conservées dans `filon-backend/README.md`,
`.python-version` et `pyproject.toml` ne font partie d'aucun de ces arbres.

## 2. GitHub Actions réel

Le workflow **Phase 0 — quality gates** a été déclenché manuellement sur
`e04dfc2` :

- run : `33249081566`, affiché comme **Qualité catalogue backend #343** ;
- migrations Alembic : **12/12** ;
- backend complet : **2 021/2 021** ;
- web : contrats/composants puis build Next.js réussis ;
- mobile : types, lint et tests hermétiques réussis ;
- extension : contrat v1, scripts Manifest V3 et manifeste réussis.

Le job backend a une conclusion rouge uniquement parce que l'étape stricte
`Bloquer un changement moteur sans benchmark humain prêt` sort avec le code 1.
Ce résultat est attendu et ne doit pas être relancé ou contourné : le rapport
est intègre, les **27 gates techniques** passent, mais `ready=false` et
`status=not_ready` car les sept datasets humains sont vides.

Le rapport a été publié malgré ce NO-GO :

| Artefact | Valeur |
|---|---|
| ID | `9713798390` |
| Nom | `quality-readiness-e04dfc2c18ef58177d4182acbb67c966058ff9c0` |
| Taille | 1 785 octets |
| Digest | `sha256:4806919878e3baccb939aba8db1c6b39e5ea078a4eb45e943c63db69bf5675dd` |
| Expiration | 12 septembre 2026 |

Le lot suivant a été republié sous le commit distant
`7f914b2bbfd28396a70319892477c3789f75b4c7`. Son arbre
`822edf543e8ba43943372cdbeff09357bc3e82fa` est exactement celui du commit local
`2cf314c9a5f53c956fc26377eefc03c464a21919` : l'inventaire réel, son collecteur
et le préflight Railway sont donc byte-identiques.

Le workflow manuel **#344** (`33251328350`) a requalifié cet arbre : migrations
**12/12**, backend **2 036/2 036**, web, mobile et extension verts. Le backend
est rouge uniquement sur le gate strict `not_ready` attendu ; les 27 gates
techniques passent et les sept datasets humains restent à zéro. L'artefact
`quality-readiness-7f914b2bbfd28396a70319892477c3789f75b4c7`, ID `9714475518`,
fait 1 785 octets, expire le 12 septembre 2026 et porte le digest
`sha256:3d0f2b97f003d2edd3a27e0489ac1d8268da348f6a0d68171413db9357d42250`.

Une qualification intermédiaire est le run **#352** (`33325481242`) sur le commit
distant `2725a464e046c3790ed20eb0533068760922a524`. Son arbre
`de9cc8944e82f42ae28361f43f5fa49791d6b1e1` est byte-identique au commit local
`04fe05bc7cc841e54b23341ef5208d4f0f61518e`. Web, Mobile, Extension, Alembic
et les régressions backend sont verts. Le seul échec reste le gate humain
strict attendu ; l'artefact Quality `9736128514` a été publié.

Le workflow de curation humaine a ensuite été publié au commit distant
`6a793ac5ac92951ff39f8a032ebc4af0cd747bdd`. Son arbre
`2a377adf6808bd5e7eafb6756d8949c2ce0b1e30` est exactement celui du commit
local `b1a18f2455bbb806cdf90b9a3135405bdde17131`. Le run **#354**
(`33330784097`) confirme : Web, Mobile, Extension, Alembic, régressions backend
et production de la readiness sont verts. Seul le gate strict
`Bloquer un changement moteur sans benchmark humain prêt` échoue comme prévu
avec zéro cas humain. L'artefact `9737603091`, conservé jusqu'au 13 septembre
2026, porte le digest
`sha256:30c3453c9c88bee3cf160c771cdb16a139b77624c4515fdee28d352fe7a334b0`.

Le Catalog Quality Funnel fail-closed a ensuite été publié au commit distant
`7a39348804e4a9106bbd0d31317c756d56dc623b`. Son arbre
`1706a0be2418173a6fb68782c01ae38b2e1f12d2` est exactement celui du commit
local `34a4f856c47b73220950134271a3e904b29a67f8`. Le run **#356**
(`33332272585`) confirme : Web, Mobile, Extension, Alembic, les **2 118**
régressions backend et la production de readiness sont verts. Seul le gate
strict humain échoue avec les sept datasets toujours vides. L'artefact
`9738018876`, nommé
`quality-readiness-50a4796db383af540b7d156e6c701031191e299e`, fait 1 785 octets,
expire le 13 septembre 2026 et porte le digest
`sha256:a1f5349879a8db7b7b05339c354317240b54eb3f220c1df29aa10faf79d1e10e`.

La correction finale qui restitue explicitement la douzième étape
`HIGH_CONFIDENCE_DECISION` a été publiée au commit distant
`9d8ade3ad671afe98f28be9c6f1fd5bf69fae414`, byte-identique au commit local
`594f51fc91651eb6e067dc9497b0b4337d0e57bc` par leur arbre commun
`9534214815bc6af2630bbf523fffb5c76f64980c`. Le run **#358**
(`33332958611`) valide Web, Mobile, Extension, Alembic, les **2 118**
régressions backend et la readiness normale. Le gate humain strict reste le
seul échec attendu. L'artefact `9738202431` porte le digest
`sha256:b2bdbd23cd83f6c7372e81987af4af3619f2aeae56215b8b79eefe73b951b50a`.

## 3. Vercel

L'intégration GitHub Vercel a construit avec succès les commits `e04dfc2`,
`9beeda8` et `7f914b2`. La preview de branche est protégée par l'authentification Vercel ;
son succès est attesté par le statut de déploiement GitHub et non par un test
public anonyme. Aucun jeton copié dans la conversation n'a été utilisé.

La production `https://www.filon.be` répond encore depuis la branche de
production historique : serveur Vercel, HTTPS avec HSTS et cache Vercel. Elle
n'est pas utilisée comme preuve de cette branche et n'a pas été redéployée.

## 4. Railway et production backend

Le backend Core est désormais réellement déployé en `production`, région
`EU West (Amsterdam, Netherlands)`, depuis la branche
`codex/filon-phase-0-core`. Le déploiement actif
`cd88cf30-354d-4be0-8206-493a829432f9` est `SUCCESS` avec un réplica. Il utilise
le Dockerfile, `alembic upgrade head`, `python -m app` et le healthcheck
`/health/ready`.

Repères d'exploitation publics autorisés :

| Ressource | Identifiant |
|---|---|
| Projet `feisty-rejoicing` | `d5f2a738-67b2-4634-ae5f-efb9f540c283` |
| Environnement `production` | `b843980b-13e3-414b-8568-890a953310ed` |
| Service `web` | `db05c3f5-e8d3-4034-ba9e-a96c3eb6b391` |
| Service `Postgres` | `d68db2c1-3ff8-45ca-a329-c89b4e81fab9` |
| Volume PostgreSQL | `e4ebe095-06e2-492a-99b5-06ddf79d5065` |

Ces UUID ne sont pas des secrets. Aucun jeton, mot de passe, URL privée ou
valeur de variable n'est publié.

Les contrôles publics postérieurs au déploiement actif prouvent :

- `/health/ready` HTTP 200, `ready=true`, PostgreSQL `ok`, révision
  `e8c3f6a0b5d2` ;
- `/health/live` HTTP 200, `alive=true` ;
- `/health` HTTP 200 avec `env=production` et Python 3.12.14 ;
- `/health`, qui n'est pas exemptée du quota, reste HTTP 200 après injection
  cliente d'un `X-Real-IP` invalide puis de deux valeurs dupliquées. FILON
  aurait répondu 503 si l'application avait reçu ces valeurs : l'edge fournit
  donc exactement une identité canonique.

Les seuls services présents dans l'environnement sont `web` et `Postgres` ;
aucun Redis n'est actuellement créé. Le quota actif reste `local_only`. Cette
preuve ne qualifie donc ni Redis
multi-réplica, ni WAF, ni agrégateur OpenMetrics, ni backend de traces, pager ou
trafic représentatif. Le reçu complet, y compris sauvegarde, restore drill,
migration et rollback, est dans
[PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md).

## 5. Protection de `main`

La ruleset GitHub `21798272`, **Phase 0 — protect main**, est active et limitée
à `~DEFAULT_BRANCH`, actuellement `main`. L'API GitHub confirme :

- suppression et force-push interdits ;
- pull request obligatoire ;
- conversations résolues ;
- branche à jour avant fusion ;
- les quatre jobs Phase 0 requis, sourcés depuis GitHub Actions ;
- politique stricte : la branche doit être à jour avant fusion ;
- `bypass_actors=[]` et `current_user_can_bypass=never`.

Les contexts requis sont exactement : backend/contrats/Quality Lab, web,
mobile et extension. L'interface a confirmé « Ruleset created » et l'API
publique a ensuite relu l'objet complet ; cette protection est donc prouvée,
pas seulement configurée dans un formulaire.

## 6. Verdict

Le code de Phase 0 est publié, byte-identique et techniquement qualifié sur les
quatre surfaces. Le backend Core, sa migration et son identité Railway sont
qualifiés en production. La CI prouve aussi que son gate métier ferme
correctement la promotion. Les conditions suivantes restent bloquantes pour la
Phase 1 : datasets humains indépendants, Product/Variant Graph mesuré et sorties
d'observabilité distribuée restantes. Le verdict est **GO backend Core ; NO-GO
Phase 1 et NO-GO immersive**.
