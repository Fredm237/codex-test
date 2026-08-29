# FILON — qualification distante de la Phase 0

- Date de coupure : **29 août 2026, 13:15 CEST**
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
| Référence applicative locale avant ce rapport | `7026f4a9864720c201119e264dc9283c8b831e74` | `fcac4bb28bd2c26835afbc74949eaa37a96b8ab6` |
| Référence applicative distante avant ce rapport | `9beeda8c6f694d8a797cdc580e8d048752bb8e42` | `fcac4bb28bd2c26835afbc74949eaa37a96b8ab6` |

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

## 3. Vercel

L'intégration GitHub Vercel a construit avec succès les commits `e04dfc2` et
`9beeda8`. La preview de branche est protégée par l'authentification Vercel ;
son succès est attesté par le statut de déploiement GitHub et non par un test
public anonyme. Aucun jeton copié dans la conversation n'a été utilisé.

La production `https://www.filon.be` répond encore depuis la branche de
production historique : serveur Vercel, HTTPS avec HSTS et cache Vercel. Elle
n'est pas utilisée comme preuve de cette branche et n'a pas été redéployée.

## 4. Railway et production backend

Le `GET /health` public de
`https://web-production-c6842.up.railway.app` répond, mais décrit encore un
processus antérieur :

- `status=ok`, version `0.1.0` ;
- `env=dev` ;
- uptime observé : `772307` secondes ;
- PostgreSQL `ok`, Redis `local_only` ;
- Qdrant `disabled` ;
- edge Railway à Bruxelles.

Cette réponse prouve la joignabilité, pas le déploiement du nouveau core. Elle
confirme au contraire l'absence de preuve production pour le scheduler, la
collecte OpenMetrics multi-réplica, le backend de traces, le WAF, le CIDR proxy,
le pager et le trafic représentatif.

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
quatre surfaces. La CI prouve aussi que son gate métier ferme correctement la
promotion. Les conditions suivantes restent bloquantes : datasets humains
indépendants, Product/Variant Graph mesuré, qualification production et
protection `main` effectivement enregistrée. Le lot CI/gouvernance est acquis ;
les trois premiers blocages restent ouverts. Le verdict reste **NO-GO Phase 1,
NO-GO production, NO-GO immersive**.
