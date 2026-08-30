# FILON — export de traces OTLP/HTTP fail-closed

- Date : **30 août 2026**
- Lot : **P0.6 / traces distribuées**
- Statut : **exporteur qualifié localement, en CI et dans l'image de production ; collecteur non déployé**
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

- configuration, cycle de vie, observabilité et export : **89/89** ;
- backend complet : **2 132 réussis, 2 ignorés** en 65,89 s ;
- `pip check` : aucune dépendance cassée ;
- compilation Python et `git diff --check` : verts.

Les tests utilisent l'exporteur mémoire officiel et un récepteur OTLP/HTTP
loopback réel. Ils prouvent la concordance trace/span avec `traceparent`,
l'échantillonnage, le Bearer dédié, le chemin et le type protobuf, le décodage
des ressources/spans, l'absence du payload, de la classe d'exception et du
jeton dans le corps, le refus d'une double configuration et la fermeture à
l'arrêt.

## Preuves distantes et production désactivée

Le commit local `0bd6bad860031cbc87a99d1afaa8db817966c8c3` et le commit
distant `216f38be5c5c6f8e5cd0ce6ec0425a86bfc9df0c` portent exactement
l'arbre `11e0956e1caa96c8df3300c5705ba03aee3c83e6`. La comparaison GitHub
confirme un seul commit en avance, sans divergence et avec les seize fichiers
attendus seulement.

GitHub Actions **#364** (`33336304758`) a terminé avec :

- Web, Mobile et Extension : **succès** ;
- baseline, stamp, drift et restauration Alembic : **succès** ;
- **2 131** régressions backend : **succès** ;
- readiness Quality normale : **succès** ;
- gate humain strict : **échec attendu**, les sept datasets restant à zéro.

L'artefact `9739162091`, nommé
`quality-readiness-7e282136a33ab27f2f9941e4136b63882b0d269c`, fait
1 785 octets, porte le digest
`sha256:6b7c1ec0fb0db1b2cc81c7789e1686695381743f9c3e361448c17482b58a0efb`
et expire le 13 septembre 2026.

Railway a déployé l'image sous l'identifiant
`b591c7cd-bc8b-43e6-a7a7-efe8de8f6b5a` avec le statut
`Deployment successful`, en EU West et avec un réplica. Les sondes publiques
ont retourné `alive=true`, `ready=true`, PostgreSQL `ok` et la révision
`e8c3f6a0b5d2`. La variable reste `TRACE_EXPORT_BACKEND=disabled` : ce reçu
prouve la compatibilité de l'image, pas un envoi OTLP.

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
