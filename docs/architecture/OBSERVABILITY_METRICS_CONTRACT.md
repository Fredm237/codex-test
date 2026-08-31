# FILON — contrat des métriques d'observabilité locales

Version : 2
Date : 29 août 2026
Endpoints : `GET /health/metrics` et `GET /health/metrics/openmetrics`

## Statut

Ce contrat décrit des compteurs **locaux à un processus**. Il rend mesurables
les requêtes HTTP et certaines sorties Product Intelligence sans stocker la
requête, le produit, l'offre, le pays, l'utilisateur ou l'adresse IP.

Le snapshot JSON historique reste disponible. Un second endpoint traduit les
mêmes registres en OpenMetrics 1.0 pour une collecte standard authentifiée.
Il ne constitue toujours ni un dashboard distribué, ni un SLO, ni une mesure
de trafic représentatif. Les compteurs repartent de zéro au redémarrage.

## Export OpenMetrics authentifié

`GET /health/metrics/openmetrics` est désactivé par défaut. Sans
`METRICS_EXPORT_TOKEN`, il répond `503 metrics_export_disabled`. Une fois un
secret explicite de 32 à 256 caractères ASCII non blancs configuré, l'appel exige :

```
Authorization: Bearer <METRICS_EXPORT_TOKEN>
```

Une absence ou une différence répond `401` avec un challenge Bearer générique.
Le token n'est jamais renvoyé, ajouté aux labels ou journalisé. L'endpoint
répond avec `Cache-Control: no-store` et le type
`application/openmetrics-text; version=1.0.0; charset=utf-8`.

Le rendu est déterministe, termine par `# EOF` et refuse nombres non finis,
compteurs négatifs, structures invalides et versions de schéma inconnues. Dans
ce cas il répond `503 metrics_export_invalid` sans exposer le détail interne.

Les familles exportées couvrent :

- uptime, requêtes, familles de statut et latences HTTP globales ;
- requêtes, statuts et latences par méthode/template de route borné ;
- décisions, scopes, fraîcheur, inconnues, preuves et exclusions ;
- réponses documentées/abstentions, provenance de livraison et cartes `buy` ;
- exécutions, sorties et latences des cinq étapes pipeline.

Les percentiles locaux sont des gauges portant le label fermé `statistic`. Ils
ne sont pas présentés comme des histogrammes distribués. Le collecteur doit
sommer les compteurs par replica et traiter les resets de processus comme tels.

Le pack versionné
[`filon-backend/observability`](../../filon-backend/observability/README.md)
prépare ce raccordement : cibles vides par défaut, secret lu depuis un fichier,
labels conservés par allowlist, rollups de taux multi-réplica et dashboard sans
seuil de santé. Il ne constitue pas une preuve de collecte distante.

## Compatibilité de l'endpoint

Les champs HTTP existants restent à la racine :

- `uptime_seconds` ;
- `retention` ;
- `overall` ;
- `routes`.

Le nouveau champ additif `product_intelligence` porte un `schema_version: 1`.
Un consommateur du contrat HTTP précédent n'a donc pas besoin de changer.

## Métriques HTTP

Les routes sont les templates FastAPI (`/products/{product_id}`), jamais le
chemin dynamique reçu. Le registre conserve au plus :

- 5 000 latences globales ;
- 512 latences par route ;
- 100 séries de route, avec un seau `OTHER`.

Il expose le nombre de requêtes, les groupes de statut, la moyenne, le maximum,
P50, P95, P99 et la taille de l'échantillon retenu.

## Métriques Product Intelligence

### `decision_evaluations`

Une évaluation correspond à un appel au moteur `compute_decision`. Ce n'est
pas un utilisateur unique ni une requête HTTP : une page catalogue peut évaluer
plusieurs offres.

| Dimension | Sens |
|---|---|
| `scopes` | périmètre de conclusion : prix observé, offre documentée, à vérifier, non recommandée ou tarif contextuel |
| `confidence` | niveau documentaire calculé, jamais probabilité de satisfaction |
| `offer_kinds` | nature bornée de l'offre |
| `freshness_status` | `positive`, `warning` ou `unknown` |
| `freshness_age_buckets` | `0_72h`, `73_168h`, `8_30d`, `over_30d` ou `unknown` |
| `missing_dimensions` | occurrences des dimensions explicitement inconnues |
| `evidence_states` | preuves `observed`, `missing` ou `not_applicable` |
| `exclusions` | motifs bornés d'une décision `non_recommandee` : prix absent, rupture ou politique |

Ces compteurs mesurent des occurrences. Par exemple, trois dimensions absentes
dans une même décision ajoutent trois occurrences à `missing_dimensions`.

### `recommendation_responses`

Une réponse correspond à un résultat remis par l'assistant, y compris depuis
le cache ou après un timeout :

- `documented` : au moins une carte issue du catalogue indexé ;
- `abstained` : aucune carte documentée ;
- `delivery` : `generated`, `cache` ou `timeout` ;
- `card_count_buckets` : nombre de cartes, borné à `0`…`5` ou `6_plus` ;
- `buy_cards` : cartes dont le moteur déterministe autorise explicitement
  `buy=true`.

Le nombre d'offres récupérées et les termes de recherche ne sont jamais
conservés dans ce registre.

### `pipeline_stages`

Cinq étapes portent une corrélation et des latences P50/P95/P99 locales :

- `catalogue` : cycle de réponse de l'assistant, cache inclus ;
- `retrieval` : récupération des offres internes ;
- `decision` : évaluation par lots des offres récupérées ;
- `ingestion` : cycle Awin ;
- `observation` : replay borné d'une source shadow ; la capture de masse reste
  agrégée dans `ingestion` pour ne pas produire deux logs par ligne.

Chaque série conserve au plus 512 latences et compte les sorties `ok`,
`degraded`, `error` ou `cancelled`. `degraded` est émis par l'ingestion quand
un feed est ignoré, qu'une projection shadow échoue ou qu'aucun feed n'est
traitable. Une valeur d'étape ou de sortie non prévue rejoint `OTHER`.

Sous HTTP, le middleware ignore l'éventuel `X-Request-Id` entrant et génère
un identifiant opaque renvoyé dans la réponse. Les étapes réutilisent cet
identifiant au moyen d'un jeton de contexte interne ; une chaîne préchargée
par un appelant n'est jamais considérée comme fiable. Un job hors HTTP reçoit
un autre identifiant, éphémère, que ses sous-étapes réutilisent. Les événements
de début/fin émis par le décorateur ne portent que cet identifiant, le nom
d'étape, la sortie, la durée et, en erreur, le type d'exception. Ils excluent
arguments, retours et messages d'exception.

### Trace décisionnelle et dépendances

La corrélation applicative complète les métriques sans ajouter de dimension à
OpenMetrics. Le roster de décision est fermé à :

1. `intent` ;
2. `retrieval` ;
3. `candidate_count` ;
4. `filtering` ;
5. `product_ranking` ;
6. `offer_selection` ;
7. `evidence` ;
8. `decision`.

Un événement accepte seulement les comptes `scopes_count`, `input_count`,
`candidate_count`, `eligible_count`, `rejected_count`, `ranked_count`,
`selected_count`, `evidenced_count` et `unknown_count`, plafonnés à
2 147 483 647. Les booléens sont limités à `semantic_used`, `model_used` et
`cache_used`. Les sorties et motifs sont des codes fermés ; une valeur future
rejoint `OTHER`. Aucun titre, identifiant produit/offre/marchand, terme,
montant, devise, pays, URL ou texte de justification n'est admissible.

Les dépendances sont fermées à `postgres`, `redis`, `awin`, `llm` et `serpapi` ;
leurs opérations sont également bornées. Chaque span émet seulement le
trace-id, un span-id opaque, la dépendance, l'opération, la sortie, la durée et,
en erreur, le nom de classe de l'exception dans le seul journal local. Les
appels HTTP sortants reçoivent
`traceparent: 00-<trace-id>-<span-id>-<flags>` et `X-Request-Id`, avec `flags`
égal à `01` si la trace est échantillonnée et `00` sinon. Les valeurs sont
créées par FILON ; l'en-tête client entrant reste ignoré. PostgreSQL et Redis
ne reçoivent ni commentaire SQL par requête ni clé enrichie : leur corrélation
reste applicative afin de préserver les requêtes préparées et les clés cache.

Un exporteur OTLP/HTTP officiel est disponible derrière un opt-in complet. Il
n'exporte que les noms, dimensions et outcomes fermés ci-dessus, sans message
d'exception ni ressource de processus. Sa présence ne constitue pas un backend
de traces, un SLO ou une preuve de conservation par un fournisseur externe.
Collecteur, rétention, accès et suppression doivent être approuvés avant
activation.

`ok` signifie que la fonction instrumentée a rendu normalement, pas qu'une
offre a nécessairement été trouvée. Une absence documentée reste donc un
succès catalogue et apparaît séparément comme `abstained`. Une erreur de
récupération remonte jusqu'au décorateur `retrieval`, puis le catalogue peut
encore la convertir en abstention honnête.

## Cardinalité et confidentialité

Toutes les dimensions acceptent une liste fermée. Une valeur libre ou future
devient `OTHER` au lieu de créer une série. Les tests injectent volontairement
des identifiants et libellés secrets, puis vérifient leur absence du snapshot.
Un contrôle AST ciblé parcourt les modules du lot, refuse les tracebacks,
messages d'exception et certaines références directes aux entrées utilisateur.
Des tests runtime injectent aussi identifiant externe, contexte non fiable,
argument, retour, chemin dynamique et message d'exception secrets, puis
vérifient leur absence de tous les champs des événements FILON capturés.

Aucun endpoint de reset n'est exposé. La remise à zéro existe uniquement pour
les tests locaux.

## Évaluation locale d'alertes hors endpoint

Les registres conservent aussi des fenêtres FIFO internes limitées aux 512
derniers événements HTTP, recommandations et étapes pipeline. Ces fenêtres ne
sont ajoutées ni à `GET /health/metrics`, ni à un nouvel endpoint public. Elles
alimentent uniquement l'évaluateur local versionné
`local-alert-policy-v1` par appel direct en mémoire. L'entrée canonique
`evaluate_local_alerts()` conserve la même instance pendant la vie du processus,
condition nécessaire à l'hystérésis et à la déduplication. Aucun ordonnanceur ne
l'appelle encore dans ce lot.

Cette politique distingue `insufficient_data`, `not_firing_provisional` et
`firing`. Elle ne produit jamais `healthy` ou `ok`, n'envoie aucune notification
réseau et calcule seulement des candidats locaux. Elle ne modifie pas
`product_intelligence.schema_version: 1`. Ses seuils, l'hystérésis, le silence
borné et ses limites sont décrits dans
`LOCAL_ALERT_POLICY.md`; la procédure de triage et de confidentialité se trouve
dans `OBSERVABILITY_INCIDENT_RUNBOOK.md`.

La fenêtre est définie en événements, pas en temps. Aucun taux « sur N minutes »
ne peut en être déduit. Un reset ou redémarrage la rend insuffisante et ne prouve
pas la résolution d'un incident. Un couple fermé
`(generation, events_seen)` distingue les resets et rejette les snapshots
rejoués plus anciens sans transition d'état.

## Conditions avant exploitation production

1. approuver l'agrégateur et sa politique de rétention ;
2. configurer le secret depuis un coffre et tester chaque replica sans query string ;
3. compiler l’inventaire avec le compte de réplicas fourni par la plateforme ;
4. produire le reçu v1 du vérificateur HTTPS et rapprocher ses comptes ;
5. conserver les mêmes listes fermées et l'absence de payload ;
6. distinguer les évaluations d'offre des requêtes et utilisateurs ;
7. importer puis valider le dashboard versionné sur trafic représentatif ;
8. ratifier les seuils provisoires, puis tester notifications, silence et rollback ;
9. ne ratifier un SLO qu'après ces mesures.
