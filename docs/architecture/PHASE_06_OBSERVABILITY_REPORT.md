# FILON — Rapport P0.6 Observabilité

Date : 29 août 2026

## Décision

**GO production pour le backend Core, les probes fail-closed et l'export
OpenMetrics authentifié. NO-GO pour considérer P0.6 entièrement terminé tant
que l'agrégation, les traces, le pager et la protection distribuée ne sont pas
prouvés.**

Le backend propage désormais un identifiant de requête opaque jusque dans les
sous-étapes décisionnelles et les dépendances, mesure les latences HTTP agrégées
et refuse la readiness quand la base ou la révision Alembic n'est pas prête. Un
moteur local provisoire évalue cinq violations manifestes. L'export
OpenMetrics standard, fermé sans secret, est désormais vérifié sur le backend
Railway de production. Sa configuration Prometheus, ses rollups multi-réplica
et un dashboard Grafana descriptif sont versionnés et validés localement, mais
aucun agrégateur, backend de traces, dashboard, sink/pager ou trafic
représentatif n'est encore qualifié.

Le 29 août 2026, le backend Core a été déployé sur Railway après sauvegarde et
restore drill. `/health/live` et `/health/ready` répondent HTTP 200, la base est
`ok`, la révision active est `f4c81a9d2e70`, le runtime journalise
`env=production` et un seul réplica est `RUNNING`. La preuve détaillée et les
limites de cette qualification sont dans le
[reçu Railway](PHASE_0_RAILWAY_DEPLOYMENT_RECEIPT.md).

## Périmètre livré

### Corrélation

- l'éventuel `X-Request-ID` externe est ignoré ; un identifiant opaque est
  toujours généré côté serveur pour empêcher injection et collision ;
- identifiant renvoyé dans `X-Request-Id` et disponible dans un `ContextVar` ;
- durée ajoutée dans `X-Response-Time` ;
- les réponses 429 et les erreurs 500 non gérées reçoivent les mêmes
  en-têtes ; une 500 reste générique et ne remonte pas son traceback au serveur ;
- logs de requête corrélés sans payload, IP, terme de recherche ni identifiant
  produit.

### Front door et confiance proxy

- le middleware ne lit jamais directement `X-Forwarded-For` ; seul Uvicorn
  peut réécrire le pair après validation d'une allowlist IP/CIDR explicite ;
- wildcard, `/0`, unions universelles et CIDR non canoniques font échouer le
  démarrage ; Uvicorn `>=0.49.0` garantit CIDR, doublons et ports de chaîne ;
- l'adresse validée devient un HMAC éphémère et n'est jamais persistée ;
- une fenêtre glissante exacte de 60 secondes, atomique, suit au plus 10 000
  couples pseudonyme/classe et rejette toute nouvelle clé à saturation ;
- toutes les lectures catalogue sont limitées ; Assistant, Outfit, agrégats
  lourds, admin/debug/sync et probes de dépendances ont le quota strict ;
- seul `GET`/`HEAD /health/live` est exempt, et Railway utilise cette sonde ;
- les 429 sont agrégés par bucket fermé et journalisés au plus une fois par
  minute et par bucket, sans perdre leurs compteurs métriques.

### Métriques bornées

`GET /health/metrics` expose uniquement des agrégats en mémoire :

- requêtes et groupes de statuts `2xx` à `5xx` ;
- moyenne, maximum, P50, P95 et P99 ;
- routes FastAPI templatisées ou buckets 429 fermés, jamais le chemin dynamique
  reçu ;
- rétention maximale de 5 000 échantillons globaux et 512 par route ;
- cardinalité maximale de 100 séries, avec un seau `OTHER` réservé.

Seul l'exact `GET`/`HEAD /health/live` est exclu des statistiques. Les probes de
dépendances et leurs erreurs restent mesurées.

### Export standard authentifié

`GET /health/metrics/openmetrics` traduit les mêmes registres en OpenMetrics
1.0. Sans `METRICS_EXPORT_TOKEN`, il répond 503 ; avec un secret explicite, il
exige un Bearer comparé en temps constant. Le token n'apparaît ni dans le
corps, ni dans les labels, ni dans les logs. Le cache est interdit.

Le rendu est déterministe, borne ses labels aux dimensions du contrat et
échoue sans détail sur un nombre non fini, une valeur négative, une structure
invalide ou une version inconnue. Les latences sont exportées en secondes sous
forme de gauges statistiques : elles ne sont pas présentées comme un
histogramme multi-replica.

Le contrôle production du 29 août 2026 confirme HTTP 401 sans Bearer, avec un
Bearer incorrect et avec le secret en query string, puis HTTP 200 uniquement
avec le Bearer correct. Le corps OpenMetrics réel respecte le content type 1.0,
`Cache-Control: no-store`, le suffixe `# EOF`, les familles `filon_` et les
labels fermés ; le secret est absent de toutes les réponses. Le
[reçu production expurgé](PHASE_06_PRODUCTION_OBSERVABILITY_RECEIPT.md) borne
précisément cette preuve.

### Pack agrégateur et dashboard

`filon-backend/observability` fournit une configuration Prometheus 3.13.2 LTS
qui ne scrape rien sans inventaire explicite. Elle lit le Bearer depuis un
fichier secret, refuse les cibles sans `environment`, `cluster` et `replica`,
borne cibles, séries, labels et taille de réponse, puis conserve uniquement la
liste fermée des labels FILON.

Onze règles calculent sur cinq minutes des taux et ratios multi-réplica pour
HTTP, Assistant, Decision et pipeline. Les percentiles ne sont jamais agrégés :
le dashboard les affiche par `instance`. Le dashboard ne contient ni seuil,
ni alerte, ni datasource secret, et décrit explicitement qu'une abstention peut
être correcte et qu'un scrape réussi n'est pas une preuve de santé. Le fichier
de cibles livré est `[]` ; aucune cible ou identité de production n'est simulée.

L’activation dispose maintenant de deux outils fail-closed. Le compilateur
d’inventaire exige le compte de réplicas observé sur la plateforme, une cible
DNS par réplica et les trois labels fermés ; il rejette URL, IP, secret, doublon
ou inventaire partiel avant un remplacement atomique. Le vérificateur HTTPS
interroge ensuite l’API Prometheus : version 3.13.2 exacte, roster et santé des
11 règles, compte exact des cibles, scrapes récents et une série présente par
rollup. Son reçu versionné ne contient ni hôte, ni instance, ni URL, ni token.
Aucun reçu d'agrégation réel n’est encore produit faute d'un Prometheus déployé
et d'un inventaire externe ; cela n'annule pas la qualification directe de
l'endpoint Railway.

### Sorties Product Intelligence

Le même endpoint expose un bloc additif versionné qui agrège :

- périmètres de décision, niveaux documentaires et natures d'offre ;
- états et tranches d'âge de fraîcheur ;
- dimensions inconnues et états des preuves ;
- exclusions bornées (`missing_price`, `out_of_stock`, `policy`) ;
- réponses documentées ou abstentions, origine cache/génération/timeout et
  nombre de cartes.

Les listes de valeurs sont fermées et toute nouveauté devient `OTHER`. Aucun
terme de recherche, nom, pays, identifiant produit/offre ou utilisateur n'est
conservé. Le contrat et ses limites sont documentés dans
`OBSERVABILITY_METRICS_CONTRACT.md`.

### Corrélation du pipeline

Les étapes `catalogue`, `retrieval`, `decision`, `ingestion` et `observation`
réutilisent le contexte de requête ou créent un identifiant opaque pour un job
hors HTTP. Elles exposent exécutions, sorties et latences bornées, avec un état
`degraded` pour l'ingestion partielle. Les événements du décorateur ne reçoivent
aucun argument, retour ni message d'exception. Un contrôle AST ciblé et des
contrôles runtime couvrent les références directes, les champs de log, le
middleware, le contexte non fiable et la corrélation HTTP → pipeline.
Une fermeture SSE annule et attend la tâche catalogue ; une erreur déjà
terminée est consommée sans laisser asyncio republier son message.

Le parcours de décision émet aussi un roster fermé de huit jalons : `intent`,
`retrieval`, `candidate_count`, `filtering`, `product_ranking`,
`offer_selection`, `evidence` et `decision`. Les seuls détails admis sont des
comptes entiers bornés, trois booléens opérationnels et des codes de sortie ou
d'abstention fermés. Requête, produit, offre, marchand, URL, clé de cache,
payload, retour et message d'exception sont exclus ; une valeur hors contrat
devient `OTHER` ou est ignorée.

Les lectures PostgreSQL, écritures Awin en lot, opérations Redis, appels Awin
Publisher, listing/téléchargement de feeds, SerpAPI et LLM ont un span
applicatif opaque qui partage le même trace-id et journalise uniquement la
dépendance, l'opération fermée, la durée, la sortie et le type d'erreur. Les
appels HTTP sortants portent un `traceparent` W3C et un `X-Request-Id` générés
par FILON ; aucun identifiant client entrant n'est réutilisé. PostgreSQL et
Redis sont corrélés par span applicatif sans modifier le texte SQL ni les clés.

### Évaluation locale d'alertes

`evaluate_local_alerts()` conserve une instance canonique par processus et lit
des fenêtres FIFO fermées de 512 événements sans passer par
`/health/metrics`. Cinq règles provisoires couvrent le ratio HTTP 5xx, les
erreurs catalogue/retrieval, les timeouts Assistant et le P95 retrieval.

Le moteur impose minima, hystérésis, génération de reset, rejet des replays,
conflit fail-closed, couverture conservatrice des annulations et silences
bornés. Il ne retourne jamais `healthy` ou `ok`; hors violation, l'état global
reste `insufficient_data`. La politique, le runbook et la preuve isolée sont
respectivement consignés dans `LOCAL_ALERT_POLICY.md`,
`OBSERVABILITY_INCIDENT_RUNBOOK.md` et `LOCAL_ALERT_EVALUATION_REPORT.md`.

### Santé et readiness

- la sonde base est bornée à deux secondes et ne divulgue plus les exceptions
  brutes de la base ou de Redis ;
- `GET /health/ready` retourne `503` pour une base lente/en erreur ou une
  révision Alembic invalide ;
- une base désactivée n'est tolérée que dans les environnements locaux et de
  test, jamais en production ;
- `GET /health/live` reste une preuve de vie du processus, distincte de la
  capacité à servir le catalogue.

## Vérification

- lot OpenMetrics du 29 août 2026 : **182 tests ciblés réussis** ; suite
  backend complète **1 934 réussis + 1 ignoré**, avec 4 avertissements
  historiques `datetime.utcnow()` ; token faible/ambigu refusé, query string
  non authentifiante, endpoint absent de l'OpenAPI, format déterministe et
  snapshot invalide rendu 503 sans fuite ;
- pack agrégateur : **5/5 tests de contrat** ; Prometheus/promtool **3.13.2
  LTS** accepte la configuration, lint les **11 règles** et réussit le scénario
  officiel à deux réplicas couvrant chaque rollup ; dashboard JSON valide, sans
  chevauchement, secret, alerte, seuil ou métrique hors contrat ;
- activation : contrats JSON Draft 2020-12, compilation atomique et preuve
  distante expurgée couvertes avec le pack par **49/49 tests** ; état vide
  explicitement compilé en `sha256:37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` ;
- production Railway : matrice d'authentification **401/401/401/200**, content
  type OpenMetrics 1.0, `no-store`, `# EOF`, **24 familles**, **15 labels
  fermés**, aucun préfixe hors `filon_` et aucune fuite du secret ;
- corrélation décisionnelle et dépendances : **8/8 tests ciblés** ; même
  trace-id sur les jalons et spans imbriqués, isolation concurrente,
  `traceparent` LLM et sur les trois chemins Awin, restauration de contexte,
  listes fermées et absence de requête/produit/marchand/URL/token/message
  d'exception vérifiées ;
- ingestion Awin bornée : **11 nouveaux cas ciblés** couvrent valeurs de
  configuration, gzip découpé, CSV brut, plafond dur de lignes, corps reçu trop
  grand et bombe de décompression ; le flux quitte la mémoire après 8 MiB et
  les erreurs restent corrélées sans URL ni clé ;
- suite observabilité ciblée du lot précédent : **227 réussis** ; suite backend
  complète courante sous Python 3.12.14 : **2 012 réussis, 1 ignoré**, 4
  warnings historiques, en 102,54 s ; l’archive autonome publiée par Astral
  `cpython-3.12.14+20260825-aarch64-apple-darwin-install_only.tar.gz` correspond
  au SHA-256 publié `62eef3fcf48fa4f792d0d6d267c140b81aaea0edca4ae0641d8021854314f966` ;
- commit `8b6be85d1f45f228ef8ff87603873a73f54a1042` vérifié dans un
  worktree détaché propre sous Python 3.12.13 ;
- alertes + observabilité + middleware : **78 réussis, 0 échec** ;
- suite backend complète isolée : **1 294 réussis, 0 échec**, avec 7
  avertissements historiques `datetime.utcnow()` ;
- trois relectures indépendantes : aucun bloquant sécurité, concurrence,
  confidentialité ou contrat restant ;
- commit `7cbb81d06d84525cdf5d7063e430d4bb19ceb2a8` vérifié dans un
  second worktree détaché propre sous Python 3.12.13 : **104 tests front
  door/observabilité/lifespan** et **1 370 tests backend** réussis, avec 7
  avertissements historiques `datetime.utcnow()` ;
- deux relectures indépendantes supplémentaires et un fuzz de fenêtre
  glissante/concurrence : aucun P0, P1 ou P2 restant dans la front door ;
- la preuve détaillée se trouve dans `LOCAL_ALERT_EVALUATION_REPORT.md` ;
- build web isolé du parent `922766e`, inchangé par ce commit backend/docs :
  compilation, types et 42 routes verts ; contrats v1 et claims verts ;
- contrat et syntaxe de l'extension isolés verts ;
- l'intégration autorisée de MegaMenu et de sa suite porte ensuite le web à
  **17/17**, avec typecheck et build de production verts localement et dans la
  qualification distante.

## Limites connues

1. Les métriques sont locales à un processus et repartent de zéro au
   redémarrage ; elles ne permettent pas un SLO multi-réplica.
2. L'export OpenMetrics qualifié reste un scrape de compteurs locaux ; le pack
   de collecte est prêt, mais aucun collecteur, rétention ou agrégation
   multi-replica n'est encore prouvé en environnement réel. Le compilateur et
   le vérificateur empêchent une preuve partielle, mais ne créent pas les
   réplicas ni l’accès manquants.
3. La mesure middleware couvre l'obtention de la réponse, pas la consommation
   intégrale du corps d'un flux SSE.
4. Le trace-id est propagé aux appels HTTP Awin, SerpAPI et LLM et corrèle les
   spans applicatifs PostgreSQL/Redis, mais aucun backend OTLP ni agent de
   collecte de traces n'est déployé ; l'acceptation ou la conservation du
   `traceparent` par les services tiers n'est donc pas prouvée à distance.
5. Aucun seuil P95/P99 n'est validé sur trafic représentatif. Les valeurs du
   plan restent des cibles proposées, pas des performances mesurées.
6. Le moteur d'alerte et le runbook sont locaux seulement : le dashboard est
   versionné mais non importé, et aucun sink ou pager ne le relie encore à
   l'export standard dans un environnement distant.
7. Les compteurs de décision portent sur des évaluations d'offre, pas sur des
   utilisateurs uniques ; une page peut en produire plusieurs.
8. Le contrôle direct valide un instant du contrat, pas la conservation à
   travers les redémarrages, les resets sous charge ou une période de trafic
   représentatif.
9. `FORWARDED_ALLOW_IPS` est fermé à `127.0.0.1` en production, sans wildcard.
   La chaîne de pairs réellement présentée par le proxy Railway doit encore
   être vérifiée avant de déclarer la front door entièrement qualifiée.
10. Le besoin Assistant reste transporté dans `q=` par le flux SSE actuel ; les
    logs applicatifs sont propres, mais un proxy ou une plateforme amont peut
    encore observer l'URL avant FILON.

## Sortie de P0.6 encore requise

- déployer le pack OpenMetrics sur une plateforme d'agrégation approuvée,
  compiler atomiquement l'inventaire avec le compte de plateforme, vérifier
  chaque replica puis conserver le reçu expurgé ;
- déployer un backend de traces approuvé, vérifier la réception des
  `traceparent` et relier sa rétention aux règles de confidentialité ;
- vérifier via l'agrégateur le contrat versionné unknown, fraîcheur, exclusions
  et abstentions sur une période représentative ;
- importer le dashboard, vérifier les rollups et percentiles locaux, puis
  conserver une preuve datée des scrapes et resets ;
- brancher l'instance canonique à un ordonnanceur contrôlé, puis tester son
  export, son canal, ses silences et son rollback hors production ;
- mesurer sur trafic représentatif avant de ratifier un SLO ;
- vérifier/configurer les pairs proxy Railway, puis ajouter une protection WAF
  ou une limite distribuée avant de revendiquer une barrière DDoS.
