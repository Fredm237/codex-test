# FILON — Politique de sécurité de la front door

Date : 29 août 2026
Statut : **GO pour le socle et le mode Redis opt-in ; NO-GO distribué tant que
Redis et le proxy réels ne sont pas qualifiés en production**

## Décision

La front door du backend applique une défense locale, déterministe et
fail-closed contre les abus ordinaires. Le middleware ne lit jamais directement
`X-Forwarded-For` : Uvicorn ne peut l'utiliser qu'après validation du pair TCP
par une allowlist explicite. La front door borne strictement sa mémoire et évite
de journaliser les termes de recherche encore transportés dans les query
strings.

Le compteur Redis atomique est désormais disponible en opt-in pour coordonner
les réplicas. Ce socle ne remplace ni un WAF, ni une politique réseau de
production. Son rôle est de fermer les failles applicatives immédiates sans
modifier les schémas de réponse ou les données métier. Il modifie
volontairement le comportement opérationnel : toute route protégée peut
répondre `429` lorsque son quota est épuisé et, si Redis a été explicitement
activé mais ne peut plus rendre une décision fiable, `503` sans fallback local.

## Menaces couvertes

- rotation d'un faux `X-Forwarded-For` pour contourner un quota ;
- croissance mémoire sans borne par multiplication d'adresses ;
- rafale à la frontière de deux fenêtres fixes ;
- contournement d'une exemption par préfixe ressemblant à une route publique ;
- exemption involontaire des routes catalogue admin, debug ou sync ;
- fuite du besoin libre de l'Assistant via le log d'accès Uvicorn ;
- course concurrente permettant de dépasser le quota.

## Frontière de confiance proxy

Le middleware lit exclusivement `request.client.host`, déjà présent dans le
scope ASGI. Il ne lit jamais un en-tête `Forwarded` ou `X-Forwarded-For`.

Uvicorn peut réécrire cette adresse seulement si le pair TCP direct appartient
à `FORWARDED_ALLOW_IPS`. Cette variable accepte une liste explicite d'adresses
IP ou de CIDR. Une valeur `*`, un réseau IPv4 ou IPv6 `/0`, ou une valeur
invalide fait échouer le démarrage. Les unions de CIDR couvrant tout un espace
IPv4 ou IPv6 et les réseaux non canoniques avec bits hôte sont également
refusés. La valeur locale par défaut est `127.0.0.1`. Le minimum Uvicorn est
fixé à `0.49.0` : cette borne inclut le support CIDR et garantit aussi la
consommation des en-têtes de forwarding dupliqués dans une chaîne proxy. Cette
garantie correspond aux
[notes de version Uvicorn](https://www.uvicorn.org/release-notes/#0490-june-3-2026).

Le propriétaire du déploiement doit vérifier puis configurer les adresses ou
CIDR réels du proxy Railway. Une allowlist trop étroite agrège plusieurs
visiteurs sous l'adresse du proxy ; une allowlist trop large rendrait l'identité
réseau falsifiable. Aucun CIDR de production n'est inventé dans le dépôt.

## Politiques de quota

| Classe | Routes | Quota local par pseudonyme |
|---|---|---:|
| `expensive` | Assistant, Outfit, agrégats catalogue lourds et opérations catalogue | 30/minute |
| `general` | toute autre route non exemptée | 240/minute |

Les budgets `expensive` et `general` sont séparés. Une route est reconnue par
frontière exacte : le chemin est égal au préfixe ou commence par `préfixe/`.

Seuls `GET` et `HEAD` sur l'exact `/health/live` sont exemptés. `/health`,
`/health/ready` et `/health/metrics` sont limités avec le budget strict, car les
deux premiers interrogent des dépendances. Toutes les lectures catalogue sont
limitées. Les agrégats `categories`, `facets`,
`highlights`, `pulse`, `relief`, `sitemap/products` et `stats`, ainsi que les
sous-arbres `admin`, `debug` et `sync`, utilisent le quota strict. Les chemins
ressemblants comme `/healthcheck` et `/api/catalogue` restent limités et
observés. L'analyse et le feedback Outfit partagent également le budget strict.

## Comptage et mémoire

- l'adresse est transformée par HMAC-SHA-256 avec un secret aléatoire propre au
  processus ; l'adresse brute n'est ni conservée ni journalisée ;
- la clé de suivi combine ce pseudonyme et la classe de politique ;
- chaque clé possède une fenêtre glissante exacte de 60 secondes, stockée dans
  un tableau circulaire compact ;
- un verrou protège atomiquement purge, lecture, consommation et insertion ;
- au plus 10 000 couples pseudonyme/classe sont suivis ;
- une clé inactive depuis 60 secondes est retirée dès la prochaine décision ;
- quand le plafond est plein, toute nouvelle clé est rejetée sans allocation.

Le mode `redis` conserve les mêmes classes et quotas mais remplace l'horloge et
les fenêtres locales par un script Lua atomique :

- `TIME` fournit une horloge commune aux réplicas ;
- un `ZSET` par couple pseudonyme/classe contient au plus le quota de la minute ;
- un registre partagé expire les identités inactives et borne globalement à
  10 000 le nombre de couples actifs ;
- les clés et membres ne contiennent qu'un HMAC-SHA-256 issu d'un secret partagé
  distinct ; l'adresse brute n'est jamais envoyée à Redis ;
- une URL Redis, un schéma `redis`/`rediss`, un secret de 32 à 256 caractères et
  un timeout entre 50 ms et 2 s sont obligatoires pour activer ce mode ;
- erreur réseau, timeout, réponse invalide ou plafond global donnent une
  décision fermée ; le plafond répond `429`, l'indisponibilité Redis `503`.

Le mode historique `local` reste la valeur par défaut. Il n'existe aucun
fallback automatique de `redis` vers `local`, car chaque réplica retrouverait
alors un budget neuf et la barrière annoncée deviendrait fausse.

Le dépassement retourne `429`, `Retry-After: 60` et la limite de la classe.
Le middleware de corrélation, placé à l'extérieur, ajoute aussi les en-têtes de
requête. Les refus sont comptés dans les métriques, mais les logs 429 sont
échantillonnés à un événement par minute et par bucket canonique fermé. Quand
le routeur n'a pas encore exécuté la requête bloquée, le limiteur inscrit ce
bucket dans le scope ASGI afin d'éviter de fusionner tous les refus sous
`<unmatched>`. Le prochain événement indique combien ont été supprimés depuis
le précédent.

## Confidentialité des journaux

Le journal applicatif conserve seulement l'identifiant opaque généré par FILON,
la méthode, la route FastAPI templatisée, le statut et la durée. Il ne conserve
ni query string, ni adresse IP, ni payload, ni nom de produit, ni identifiant
externe de requête.

Le canal `uvicorn.access` est désactivé dans la configuration des logs et
`uvicorn.run(..., access_log=False)`, car son format inclut la query string.
Seul l'exact `GET`/`HEAD /health/live` est exclu du bruit ; les probes de
dépendances, leurs erreurs et un lookalike comme `/healthcheck` restent
observés. Railway utilise cette liveness bon marché plutôt que `/health`.

## Limites et travaux restants

1. La production reste configurée en mode local tant qu'un Redis privé n'a pas
   été créé, relié et testé ; le quota actif repart donc encore à zéro au
   redémarrage et ne se coordonne pas entre réplicas.
2. Il ne protège pas à lui seul la bande passante, les sockets, la sonde de
   liveness exemptée ou l'infrastructure en amont du processus.
3. Les utilisateurs partageant une même adresse validée partagent un quota.
4. Le proxy, le navigateur ou une plateforme en amont peuvent encore observer
   le paramètre `q=` avant FILON. Une future migration vers un corps `POST` ou
   un identifiant SSE opaque devra être coordonnée avec les propriétaires des
   clients et du composant `SearchAssistant` protégé.
5. Les diagnostics du grand module catalogue protégé ne font pas partie de ce
   lot et restent consignés comme dette de confidentialité P2.
6. Aucune adresse proxy Railway, règle WAF, activation Redis production ou
   mesure de trafic représentatif n'est validée par cette preuve locale.

## Vérification et rollback

Les tests couvrent la falsification d'en-têtes, les frontières exactes, la
fenêtre glissante, le plafond et sa libération, la concurrence, la séparation
des classes, la configuration proxy et l'absence de query/IP dans les logs.

Le commit `7cbb81d06d84525cdf5d7063e430d4bb19ceb2a8` a été vérifié dans un
worktree détaché propre sous Python 3.12.13 : **104 tests ciblés** et **1 370
tests backend** réussis, avec 7 avertissements historiques
`datetime.utcnow()`. Deux relectures indépendantes, complétées par fuzzing de la
fenêtre glissante et concurrence multithread, ne trouvent plus aucun P0, P1 ou
P2 dans ce périmètre.

Le changement ne crée ni migration, ni endpoint, ni schéma de payload, ni donnée
persistée. Il ajoute toutefois la réponse opérationnelle `429` aux lectures
catalogue auparavant exemptées. Le rollback consiste à rétablir les composants
de front door, la sonde Railway et la borne de dépendance Uvicorn ; aucune
restauration de base n'est requise.
