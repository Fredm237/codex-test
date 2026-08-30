# FILON — export de traces OTLP/HTTP fail-closed

- Date : **30 août 2026**
- Lot : **P0.6 / traces distribuées**
- Statut : **exporteur qualifié localement ; collecteur non déployé**
- Production : **`TRACE_EXPORT_BACKEND=disabled` ; aucun envoi**
- Décision : **GO technique du chemin d'export ; GO production interdit sans collecteur, rétention et reçu**

## Objet

FILON produisait déjà des identifiants W3C et des journaux bornés pour les
étapes pipeline et les dépendances. Ce lot ajoute un export standard
OTLP/HTTP avec les composants officiels OpenTelemetry Python :

- `TracerProvider` privé, sans auto-instrumentation ;
- `OTLPSpanExporter` HTTP/protobuf ;
- `BatchSpanProcessor` borné à 512 spans, lots de 128 ;
- arrêt et vidage explicites dans le lifespan FastAPI.

Références officielles :
[exporteurs Python](https://opentelemetry.io/docs/languages/python/exporters/),
[configuration du Collector](https://opentelemetry.io/docs/collector/configuration/)
et [SDK de trace](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/trace/sdk.md).

## Configuration fermée

L'état par défaut est `disabled`. Une activation exige simultanément :

```text
TRACE_EXPORT_BACKEND=otlp_http
OTLP_TRACES_ENDPOINT=https://<collecteur>/v1/traces
OTLP_TRACE_EXPORT_TOKEN=<secret dédié de 32 à 512 caractères ASCII>
TRACE_EXPORT_SAMPLE_RATIO=<valeur strictement positive, au plus 1>
TRACE_EXPORT_TIMEOUT_SECONDS=<0.1 à 5>
```

En production, l'endpoint doit être HTTPS, sans identifiants, query string ni
fragment, et son chemin doit finir par `/v1/traces`. HTTP n'est accepté que
pour `localhost` hors production. Un endpoint ou jeton présent alors que le
backend reste désactivé rend aussi la configuration invalide : aucun secret
orphelin ne donne l'illusion d'une collecte active.

## Confidentialité et cardinalité

L'export n'utilise pas l'auto-instrumentation. Il accepte seulement :

- les noms fermés `filon.pipeline.<stage>` et
  `filon.dependency.<dependency>.<operation>` ;
- `filon.span.kind` ;
- `filon.stage`, `filon.dependency`, `filon.operation` ;
- `filon.outcome` dans l'ensemble fermé existant.

Les ressources sont limitées à `service.name`, `service.version` et
`deployment.environment.name`. Aucun argument, retour, titre, produit, offre,
marchand, URL, message d'exception, traceback, attribut de processus ou
identifiant de machine n'est collecté. Les erreurs marquent seulement le statut
OTLP `ERROR` et un outcome borné.

Le trace-id FILON reste le trace-id OTLP. Le span-id W3C sortant est celui du
span de dépendance exporté. Une trace non échantillonnée conserve sa
corrélation et propage le drapeau W3C `00` ; elle ne produit aucun span dans
l'exporteur.

## Preuves locales

- configuration, cycle de vie, observabilité et export : **88/88** ;
- backend complet : **2 131 réussis, 2 ignorés** en 99,96 s ;
- `pip check` : aucune dépendance cassée ;
- compilation Python et `git diff --check` : verts.

Les tests utilisent l'exporteur mémoire officiel. Ils prouvent la concordance
trace/span avec `traceparent`, l'échantillonnage, l'absence d'exception et de
payload, le refus d'une double configuration et la fermeture à l'arrêt.

## Activation et preuve encore requises

Avant tout changement de variable Railway :

1. approuver le fournisseur/collecteur, son coût, sa région et sa politique de
   rétention/suppression ;
2. créer un endpoint OTLP HTTPS protégé par un secret dédié ;
3. activer d'abord un canary avec un ratio borné ;
4. prouver la réception d'un pipeline et d'une dépendance corrélés, sans
   attribut interdit ;
5. tester panne, timeout, vidage à l'arrêt, accès, rétention et suppression ;
6. archiver un reçu expurgé puis seulement étendre l'échantillonnage.

## Rollback

Remettre `TRACE_EXPORT_BACKEND=disabled` et supprimer simultanément endpoint
et jeton. Le rollback ne demande ni migration, ni changement de schéma, ni
modification des journaux structurés existants.

## Limites

Ce lot ne prouve aucune réception externe, rétention, recherche de traces,
alerte ou disponibilité du collecteur. Il ne crée aucune ressource Railway et
ne lève ni le NO-GO P0.6, ni le gate Quality humain.
