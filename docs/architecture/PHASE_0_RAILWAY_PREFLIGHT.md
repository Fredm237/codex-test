# FILON — préflight Railway de production

- Date de coupure : **29 août 2026, 13:37 CEST**
- Environnement : `production`
- Projet Railway : `feisty-rejoicing`
- Décision initiale : **accès confirmé ; déploiement NO-GO avant backup et restore drill**
- Décision après exécution : **backup, restore drill, adoption Alembic et backend Core qualifiés**

Le reçu d'exécution canonique est
[PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md).

Ce rapport ne contient ni jeton, ni valeur de variable, ni chaîne de connexion.
L'identifiant transmis par le propriétaire a été validé comme jeton de projet
Railway limité à un environnement. Toutes les opérations réalisées pendant ce
préflight ont été des lectures de métadonnées ; aucune variable protégée n'a été
récupérée et aucune ressource n'a été créée, modifiée ou redéployée.

## Topologie observée

L'API Railway authentifiée expose deux services dans `production` :

- `Postgres` ;
- `web`, relié au dépôt public `Fredm237/codex-test`, avec
  `filon-backend` comme répertoire racine et le domaine actif
  `web-production-c6842.up.railway.app`.

Le dernier déploiement réussi du service web date du 20 août 2026 à
12:36:21 UTC. Il provient de `main`, commit
`af08f9089e9cc20acfd2cdf692714ec2847634cf`, et déclare explicitement le fichier
de configuration `/filon-backend/railway.json`. Cette métadonnée lève
l'ambiguïté du runbook : le chemin legacy « Config as Code 1A » est bien celui
qui pilote déjà le service.

## Écart entre le runtime actif et la cible

Le déploiement actif a encore la configuration historique :

- builder `RAILPACK` ;
- démarrage direct par `uvicorn api.main:app --host 0.0.0.0 --port $PORT` ;
- aucune commande de pré-déploiement ;
- aucune healthcheck Railway déclarée.

La branche candidate contient au contraire la configuration cible dans
`filon-backend/railway.json` : Dockerfile, `alembic upgrade head` avant
démarrage, `python -m app`, readiness `/health/ready`, délai 120 secondes et
redémarrage borné. Un déploiement de cette branche changerait donc à la fois le
code et le chemin opérationnel de migration. Il ne doit pas être déclenché sans
preuve de restauration.

## Outil qualifié

La CLI officielle Railway v5.30.1 pour macOS arm64 a d'abord été téléchargée
dans un répertoire temporaire, sans installation globale. L'archive vérifiée
porte le SHA-256 :

`305dbcacfe3c1241b1375e40aaa06bceeefce6fdbcd827c04b06219bf7d703e5`.

Pour corriger le comportement de scale et poursuivre avec la version courante,
la copie temporaire a été remplacée par la v5.45.7 officielle. Son archive
macOS arm64 a été vérifiée contre le digest GitHub publié :

`b8f0692f585875b1d1767ad65e62b93488cf38b4b6af2665bcf530c8a58d9dbe`.

Références opératoires : [API Railway](https://docs.railway.com/integrations/api),
[CLI Railway](https://docs.railway.com/cli),
[déploiement CLI](https://docs.railway.com/cli/deploying) et
[backups/restores PostgreSQL](https://docs.railway.com/guides/postgres-backups-restores).

## Gate avant toute mutation

L'ordre obligatoire est désormais :

1. autoriser explicitement le chargement temporaire, sans affichage ni écriture,
   des variables protégées PostgreSQL dans un processus local ;
2. produire un `pg_dump` logique en format custom et son empreinte ;
3. restaurer ce dump dans une base jetable distincte, puis vérifier révision
   Alembic, tables, comptes et sentinelle sans toucher à la base source ;
4. déployer la branche candidate avec le fichier Config as Code déjà rattaché ;
5. vérifier pré-déploiement Alembic, `/health/live`, `/health/ready`, logs et
   rollback ;
6. seulement ensuite qualifier ordonnanceur, scrapes multi-réplica, rétention,
   dashboard, traces, WAF/CIDR et pager.

Les étapes 1 à 5 sont désormais prouvées dans le reçu d'exécution. Cette
qualification couvre le backend Core, sa migration et ses probes ; elle ne
vaut ni preuve Quality humaine, ni qualification de l'agrégateur, des traces,
du WAF, du pager ou d'un SLO sur trafic représentatif.
