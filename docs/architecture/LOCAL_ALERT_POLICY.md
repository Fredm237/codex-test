# FILON — politique locale provisoire d'alertes

Version : `local-alert-policy-v1`
Date : 29 août 2026
Statut : **évaluation locale uniquement — ni SLO, ni pager, ni preuve de santé**

## Décision

FILON peut désormais détecter localement quelques violations manifestes dans
des fenêtres bornées d'événements. En l'absence de violation, la politique ne
retourne jamais `healthy` ou `ok` : son état global demeure
`insufficient_data`, car aucun trafic représentatif, agrégat multi-réplica ou
seuil ratifié n'existe encore.

L'évaluateur n'est relié à aucun endpoint, exporteur, dashboard ou service de
notification. Il lit directement les registres du processus. Cette frontière
évite d'élargir l'endpoint public `/health/metrics`, déjà distinct de tout
contrat d'alerte opérationnel.

## Flux local

```text
événement HTTP / recommandation / étape pipeline
                 │
                 ▼
fenêtre FIFO bornée aux 512 derniers événements
                 │
                 ▼
collect_local_alert_inputs() — agrégats fermés, aucun payload
                 │
                 ▼
evaluate_local_alerts() — instance canonique + seuils + hystérésis
```

`evaluate_local_alerts()` conserve une instance canonique pendant toute la vie
du processus. Cette continuité est requise pour l'hystérésis, la déduplication,
le rejet des replays et le suivi des signaux silencés. Construire un
`LocalAlertEvaluator` à chaque lecture réinitialiserait volontairement cet état ;
la classe reste exportée pour les tests et les isolations explicites seulement.
Le lot ne programme toutefois aucun appel périodique et ne livre aucun signal à
un canal externe.

La fenêtre est définie en **nombre d'événements**, jamais en minutes. Elle ne
permet donc aucune affirmation telle que « taux d'erreur sur dix minutes ».
Un redémarrage ou un reset vide la fenêtre et rend la règle
`insufficient_data` ; il ne constitue pas une résolution.

Chaque registre associe au compteur `events_seen` une `generation` strictement
croissante lors d'un reset. L'évaluateur compare la position
`(generation, events_seen)` : une position plus ancienne est rejetée avec
`stale_snapshot`, et une position identique ne peut produire une nouvelle
transition. Une nouvelle génération distingue donc une fenêtre neuve même si son
compteur atteint exactement la même valeur que la précédente.

Une position récente dont l'agrégat est invalide avance quand même le watermark,
afin qu'un snapshot valide plus ancien ne puisse résoudre ou redéclencher le
signal. Une correction structurellement valide est admise une seule fois à cette
même position. Après acceptation, un contenu différent sous la même position
devient `conflicting_snapshot` et reste fail-closed, sans mutation du latch.

## Règles v1

Tous les identifiants et seuils sont fermés. Les seuils sont des garde-fous
proposés pour validation locale, pas des objectifs de service ratifiés.

| Règle | Source, fenêtre max. 512 | Minimum | Déclenchement inclusif | Résolution inclusive |
|---|---|---:|---:|---:|
| `http_5xx_ratio` | groupes de statut HTTP hors `/health` | 100 | ≥ 5 % | ≤ 2 % |
| `catalogue_error_ratio` | sorties `error` de l'étape catalogue | 50 | ≥ 10 % | ≤ 2 % |
| `retrieval_error_ratio` | sorties `error` de retrieval | 50 | ≥ 10 % | ≤ 2 % |
| `assistant_timeout_ratio` | livraisons Assistant `timeout` | 100 | ≥ 5 % | ≤ 1 % |
| `retrieval_p95_ms` | latences P95 de retrieval | 200 | ≥ 750 ms | ≤ 600 ms |

Les sorties `cancelled` sont comptées séparément puis exclues du dénominateur et
des latences d'alerte : une déconnexion SSE n'est pas une panne retrieval. Les
sorties `degraded` restent observables mais ne sont pas transformées en `error`.
Si moins de la moitié de la fenêtre reste observable après exclusion, une valeur
sous le seuil de déclenchement devient `insufficient_data` : les annulations ne
peuvent ni créer un faux non-déclenchement, ni résoudre un signal. Une violation
manifeste au seuil ou au-dessus reste toutefois `firing`, même dans une fenêtre
dominée par les annulations.

## États et transitions

Une règle porte exactement l'un des états suivants :

- `insufficient_data` : source absente, agrégat invalide ou minimum non atteint ;
- `not_firing_provisional` : seuil non franchi, sans conclure que le service est
  sain ;
- `firing` : violation du seuil ou maintien dans la bande d'hystérésis.

`triggered` et `resolved` sont des transitions, pas des états durables. Une
seconde lecture du même snapshot ne redéclenche rien. Un replay plus ancien est
`insufficient_data` avec `stale_snapshot` et ne mute aucun latch. Une règle déjà
`firing` reste active dans la bande entre seuil de résolution et seuil de
déclenchement. Une baisse au seuil de résolution produit `resolved` seulement
sur une nouvelle observation ; un manque soudain de données produit
`insufficient_data`, jamais une fausse résolution.

L'état global vaut `firing` dès qu'une règle tire. Sinon il reste
`insufficient_data`, y compris quand toutes les règles suffisamment alimentées
sont `not_firing_provisional`.

## Silence

Un silence agit uniquement sur le candidat de notification. L'état sous-jacent,
la valeur, l'échantillon et la transition restent visibles.

- durée strictement positive et maximale : une heure ;
- règle fixe obligatoire ; aucun silence global ;
- raison fermée : `maintenance`, `controlled_test` ou `dependency_incident` ;
- horodatages avec un décalage UTC réel obligatoire (`tzinfo` seul ne suffit
  pas si `utcoffset()` est absent) ;
- doublon actif interdit ;
- expiration automatique ; si une **nouvelle observation** confirme ensuite que
  le signal tire encore, un nouveau candidat de notification est produit ; la
  relecture du snapshot resté inchangé ne renotifie pas ;
- temps d'évaluation monotone dans l'instance canonique : une évaluation
  retardée horodatée avant une expiration déjà observée ne peut pas réarmer le
  silence ni créer une seconde notification ;
- readiness base/schéma n'appartient pas à cette politique et ne peut donc pas
  être silencée par elle.

Le code ne persiste pas les silences et ne fournit aucun endpoint de mutation.
Un futur stockage devra ajouter owner, authentification, audit et expiration
sans accepter de raison libre.

## Confidentialité et cardinalité

Les entrées locales contiennent seulement les métadonnées de fenêtre fermées
(`window_kind`, capacité, troncature, génération, compteurs d'événements), les
groupes de statuts/livraisons/sorties autorisés et le P95 agrégé. La sortie
évaluée contient seulement : code de règle, version de politique, état,
transition, position `(generation, events_seen)`, taille d'échantillon, ratio ou
P95 agrégé, seuil, état de notification et code de raison fermé. La position
retournée est celle qui a effectivement servi à l'évaluation ; aucune seconde
collecte non atomique n'est nécessaire au triage.

Elles excluent requête, payload, route, chemin dynamique, IP, header, cookie,
identifiant de requête, utilisateur, produit, offre, marchand, feed, exception,
traceback, URL et secret. Les champs inconnus d'un snapshot ne sont jamais
recopiés. Une entrée mal formée devient `insufficient_data` avec un code fermé.

Les verbes HTTP sont désormais bornés à sept méthodes standard ; toute autre
valeur devient `OTHER_METHOD`. Un client ne peut plus remplir les 99 séries de
route avec des verbes fabriqués.

## Limites connues

1. Les 512 événements sont locaux à un processus, non horodatés et perdus au
   redémarrage. La génération distingue les resets mais ne transforme pas ce
   stockage en fenêtre temporelle.
2. Aucun P99 n'est alerté : 512 points ne fournissent pas assez d'observations de
   queue pour une décision stable.
3. La latence catalogue mélange cache et génération ; aucun seuil catalogue
   P95 n'est défini avant séparation de ces chemins.
4. Aucun seuil ne porte sur abstention, unknown, confiance ou fraîcheur avant une
   baseline représentative segmentée.
5. Les statuts 4xx agrégés ne distinguent pas 429 et 404 ; aucune alerte d'abus
   n'est revendiquée.
6. Le probe Redis actuel peut retomber sur le cache local ; aucune règle Redis
   n'est autorisée avant un probe strict sans fallback.
7. Les règles ne voient pas la couverture des marchands, les dépendances
   distribuées ni le coût complet d'un flux SSE.

Le passage production exige des événements horodatés, un export authentifié,
une agrégation multi-réplica, un trafic représentatif, des seuils ratifiés, un
canal de notification testé et une revue de sécurité de l'accès aux métriques.
