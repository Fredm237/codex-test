# FILON — runbook local d'incident observabilité

Date : 29 août 2026
Périmètre : politique `local-alert-policy-v1`

## Statut opérationnel

Ce runbook traite uniquement des évaluations locales du processus. Il ne décrit
ni pager de production, ni SLO, ni agrégation distante. Une sortie `firing` est
un signal à examiner ; une sortie `insufficient_data` ou
`not_firing_provisional` n'est jamais une preuve de bonne santé.

La readiness reste séparée : `/health/ready` décide si la base et la révision de
schéma permettent de recevoir du trafic. Une règle statistique ne doit ni
redémarrer le service ni masquer une readiness rouge.

## Triage

1. Relever le commit, `policy_version`, `scope`, état de règle, transition,
   taille d'échantillon, valeur agrégée et seuil.
2. Vérifier `representative_traffic=false` et le type de fenêtre
   `last_events`. Ne jamais convertir ces données en durée.
3. Lire la readiness base/schéma séparément. Une 503 readiness prime sur
   l'interprétation des règles locales.
4. Vérifier si la fenêtre est tronquée. Une troncature signifie que seuls les
   512 derniers événements participent au signal.
5. Vérifier la position `(generation, events_seen)`. `stale_snapshot` indique
   un replay ancien : ne pas l'utiliser pour déclencher ou résoudre.
6. Corréler localement avec le changement récent et les types d'erreur déjà
   nettoyés, sans copier de ligne brute dans l'incident.
7. Identifier si le signal concerne le chemin HTTP, catalogue, retrieval,
   timeout Assistant ou latence retrieval. Ne pas extrapoler à un autre chemin.
8. Consigner l'action, le rollback éventuel et un nouvel agrégat borné. La
   résolution doit provenir de nouvelles observations sous le seuil.

## `insufficient_data`

- ne pas abaisser le minimum pour obtenir artificiellement un état favorable ;
- ne pas remplacer une source absente par zéro ;
- ne pas annoncer « aucune erreur » ;
- après redémarrage, attendre de nouveaux événements : l'ancien incident n'est
  ni résolu ni confirmé par une fenêtre vide ;
- si les annulations laissent moins de la moitié des événements observables, ne
  pas utiliser une valeur sous le seuil pour conclure ou résoudre ; une violation
  manifeste reste néanmoins exploitable ;
- sur `stale_snapshot`, collecter une position plus récente au lieu de rejouer
  l'agrégat ;
- sur `conflicting_snapshot`, ne choisir aucune des deux valeurs : conserver le
  latch, corriger la collecte et attendre une position plus récente ;
- un `invalid_aggregate` récent bloque les positions antérieures ; une correction
  structurellement valide peut être relue une fois à la même position ;
- si l'agrégat est invalide, corriger d'abord l'instrumentation et conserver le
  signal fail-closed.

## `firing`

- `http_5xx_ratio` : examiner seulement groupes de statut et types d'erreur
  nettoyés ; vérifier séparément readiness et dépendances ;
- `catalogue_error_ratio` : distinguer erreur du cycle catalogue et abstention
  documentée, qui reste un succès ;
- `retrieval_error_ratio` : vérifier la dépendance catalogue/DB et le type
  d'exception, jamais son message ;
- `assistant_timeout_ratio` : distinguer timeout explicite, cache et génération ;
- `retrieval_p95_ms` : confirmer que le minimum de 200 latences est atteint et
  ne pas interpréter le seuil comme un SLO ratifié.

Une seule lecture déclenchée suffit à signaler la violation provisoire. Les
lectures locales répétées du même snapshot ne doivent pas multiplier les
notifications. Elles doivent passer par l'instance canonique conservée par
`evaluate_local_alerts()` ; recréer l'évaluateur perdrait cet état.

## Silence contrôlé

Un silence n'est acceptable que pendant une maintenance, un test contrôlé ou un
incident de dépendance déjà identifié.

- choisir une règle précise ;
- utiliser uniquement le code de raison fermé ;
- fixer une expiration au plus à une heure ;
- fournir des horodatages avec un décalage UTC défini, pas seulement un objet
  `tzinfo` nominal ;
- vérifier que la règle reste `firing` sous silence ;
- ne jamais silencier readiness ou invalidité de schéma ;
- après expiration, attendre une nouvelle observation ; traiter le candidat si
  elle confirme que la règle tire encore, sans renotifier sur un snapshot figé ;
- ne pas faire reculer l'horloge d'évaluation : l'instance canonique conserve le
  dernier instant UTC et neutralise un appel retardé antérieur ;
- si le signal se résout pendant le silence, consigner la transition sans
  notification de panne.

Il n'existe ni endpoint de silence ni persistance dans ce lot. Toute future
commande doit être authentifiée, auditée et testée avant usage distant.

## Preuves autorisées

Une note d'incident peut contenir uniquement :

- code d'alerte et version de politique ;
- commit et fenêtre UTC de l'analyse humaine ;
- scope `single_process_last_512_events` ;
- génération, compteur d'événements, taille d'échantillon et indicateur de
  troncature ;
- ratio agrégé avec la précision émise ou P95 agrégé ;
- états bornés de readiness base/schéma ;
- action et résultat de rollback sans secret.

## Contenu interdit

Ne jamais joindre ou copier :

- dump complet de `/health` ou `/health/metrics` ;
- sortie réseau verbeuse ou trace HTTP ;
- requête, payload, chemin dynamique, IP, header, cookie ou identifiant de
  requête, même opaque ;
- environnement, token, mot de passe, URL ou clé Redis ;
- message d'exception, traceback ou `repr(snapshot)` ;
- ligne DB, payload Awin, feed, marchand, produit ou offre ;
- URL signée ou réponse brute d'un fournisseur.

Les diagnostics ingestion doivent rester limités aux codes fermés et compteurs.

## Résolution et rollback

Une règle `firing` se résout seulement quand de nouvelles observations placent
sa valeur au seuil de résolution ou en dessous. Une bande d'hystérésis évite les
oscillations. Un reset, un redémarrage, une fenêtre vide ou un silence ne vaut
pas résolution.

Le lot ne comporte ni migration ni stockage. Si l'instrumentation elle-même
aggrave le service, revenir au commit parent retire les fenêtres et l'évaluateur.
Conserver la readiness existante ; ne jamais la désactiver pour faire disparaître
un signal.

## Passage à une alerte de production

Avant toute notification distante :

1. protéger l'accès aux métriques et limiter son coût ;
2. introduire des événements horodatés et des fenêtres temporelles explicites ;
3. agréger les réplicas avec une rétention approuvée ;
4. mesurer un trafic représentatif et ratifier les seuils ;
5. tester déclenchement, déduplication, silence, expiration et résolution sur un
   environnement non productif ;
6. désigner owner, canal, escalade et rollback ;
7. réaliser une revue confidentialité/sécurité des pièces d'incident.
