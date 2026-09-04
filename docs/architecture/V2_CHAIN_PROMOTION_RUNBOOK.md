# FILON — Runbook de promotion atomique de la chaîne V2

## Statut de ce document

Ce runbook décrit la promotion conjointe des shadows P0 et des Phases 1 à 10.
Il ne constitue pas une activation de production. La version courante du code
autorise les cinq modes, mais `CANARY` et `PUBLIC` exigent à la fois les
flags cohérents, le digest exact d'un reçu append-only et sa revalidation en
base avant toute lecture. Sans cette double preuve, le runtime échoue fermé.

La règle d'architecture est simple : une réponse publique ne doit jamais
mélanger un maillon V2 avec des dépendances V1 ou V2 non qualifiées. La chaîne
est promue ou retirée comme un seul produit.

## Chaîne atomique

Ordre exécuté sur une fenêtre commune :

1. Product Identity ;
2. Entity Resolution ;
3. Offer Graph ;
4. Merchant Intelligence ;
5. Evidence Engine ;
6. Offer Truth ;
7. Product Ontology ;
8. Hybrid Retrieval ;
9. Constraint Engine ;
10. Product Ranking ;
11. Offer Optimization ;
12. Confidence ;
13. BUY/WAIT V2.

Observation shadow reste une dépendance obligatoire des writers qui consomment
les raws et leur provenance. Le mode `SHADOW` active atomiquement les quatorze
flags nécessaires, sans raccorder de lecteur public.

## États autorisés

| Mode | Writers V2 | Lecteur canary | Lecteur public | Comportement actuel |
|---|---:|---:|---:|---|
| `off` | OFF par défaut | OFF | OFF | autorisé ; Core v1 seul |
| `shadow` | tous ON | OFF | OFF | autorisé ; chaîne journalisée et bornée |
| `dark` | tous ON | OFF | OFF | V1 servi ; V2 calculé sur trafic réel et seulement observé |
| `canary` | tous ON | cohorte fermée | OFF | autorisable uniquement par reçu `CANARY_AUTHORIZED` exact |
| `public` | tous ON | OFF | ON | autorisable uniquement par reçu `PUBLIC_AUTHORIZED` exact et filiation canary |

Un flag writer explicitement `false` sous tout mode actif invalide la
configuration. Un lecteur activé sous `off` ou `shadow` invalide également la
configuration. Le mode `dark` garde les lecteurs promus OFF et autorise
uniquement l'observation dual-read non influente. Le mode `canary` exige une
cohorte fermée de digests et interdit
le lecteur public ; le mode `public` interdit toute cohorte canary résiduelle.

La variable `V2_PROMOTION_RECEIPT_EVALUATION_ID` désigne l'identité externe du
reçu, jamais seulement son gate interne. Le garde `promotion_guard` relit cette
ligne exacte et vérifie : état autorisé, ensemble complet de gates, références
de preuves SHA-256, partition exhaustive des types de réponse et absence de
payload brut. En `public`, il exige aussi le reçu SHADOW → CANARY source et
interdit d'autoriser un type absent de cette filiation.

## Lease, journal et reprise

La table additive `v2_chain_executions` conserve uniquement :

- mode, état et fenêtre bornée ;
- instant d'évaluation et verticale ;
- checkpoints numériques ;
- liste des étapes terminées ;
- heartbeat, curseur et état terminal ;
- identifiant du rapport et motif d'échec neutralisé au type d'exception.

Elle ne conserve aucun payload brut, contexte utilisateur ou valeur secrète.
Un index partiel unique interdit deux lignes `running`. Chaque étape terminée
rafraîchit le heartbeat. Une interruption stale peut être terminalisée
`interrupted` sans démarrer automatiquement un successeur.

Le curseur automatique lit uniquement le dernier `apply` terminalement
`succeeded`. Un run `failed` ou `interrupted` ne fait donc jamais avancer la
fenêtre. Le successeur rejoue la même plage et s'appuie sur les contraintes
d'idempotence de chaque writer.

## Gates héritées par phase

Les gates historiques restent des planchers : une qualification de chaîne ne
peut pas les affaiblir.

| Périmètre | Gate mesurable conservée pour la promotion |
|---|---|
| P0 shadows | 100 % des raws sélectionnés ont une provenance et un checksum ; aucune perte silencieuse ; aucune double exécution |
| P1 Product Identity | exact-product 960/960 ; variant 3 840/3 840 ; offer attachment 2 880/2 880 ; faux merge 0/2 880 ; unknown sans fallback |
| P2 Entity Resolution | faux merge 0/3 844 avec borne Wilson haute ≤ 0,5 % ; conflits 2 884/2 884 en abstention ; signaux faibles 961/961 en abstention |
| P3 Offer Truth | support ≥ 10 000 cas ; bornes Wilson basses exactitude/claims/abstention/provenance ≥ 0,995 ; fallback dangereux ≤ 0,5 % ; prix/devise atomiques |
| P4 Product Ontology | support ≥ 3 000 par strate ; bornes Wilson basses rôles ≥ 0,995 et abstention ≥ 0,99 ; faux `PRIMARY_PRODUCT` et fausse relation ≤ 0,5 % |
| P5 Hybrid Retrieval | support ≥ 4 000 positifs et strates du manifest ; recall@50 ≥ 0,95 ; NDCG@10 ≥ 0,85 ; top-3 Wilson bas ≥ 0,90 ; zéro violation/grouping/semantic-only |
| P6 Constraint Engine | support ≥ 4 500 ; exactitude Wilson basse ≥ 0,995 ; zéro faux éligible, unknown satisfait ou candidat réintroduit ; provenance 100 % |
| P7 Product Ranking | support ≥ 4 500 ; ordre Wilson bas ≥ 0,995 ; top-1 = 1,0 ; zéro inéligible/unknown classé ou échec d'invariance à l'affiliation |
| P8 Offer Optimization | support ≥ 5 700 ; sélection Wilson basse ≥ 0,995 ; zéro offre inéligible/unknown sélectionnée ou mutation par commission ; provenance 100 % |
| P9 Confidence | 18 000 prédictions et support par bucket ≥ 3 500 ; ECE ≤ 0,001 ; Brier ≤ 0,171 ; zéro inconnue promue ; provenance 100 % |
| P10 BUY/WAIT | support actionnable ≥ 3 600 ; exactitude = 1,0 et Wilson basse ≥ 0,995 ; zéro action dans le mauvais sens, non supportée ou avec fuite future |

`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` reste une limitation déclarée,
pas une autorisation pour inventer une preuve. Les invariants autonomes,
temporels et contradictoires restent bloquants.

## Gate SHADOW → CANARY

Toutes les conditions suivantes sont obligatoires :

1. une seule tête Alembic, migration PostgreSQL verte et rollback expand-only
   documenté ;
2. dry-run, apply unique puis replay strictement identique sur une même fenêtre :
   même `evaluation_id`, zéro création au replay et treize étapes terminales ;
3. curseur monotone sur les fenêtres réussies, aucun saut après échec et aucune
   exécution concurrente ;
4. toutes les gates héritées du tableau précédent restent vertes avec les
   versions réellement déployées ;
5. les sorties `unknown`, `conflict`, `excluded`, `unrankable` et `abstain` ne
   sont jamais transformées en résultat favorable ;
6. chaque sortie que le lecteur canary pourra afficher a été observée au moins
   une fois sur une chaîne réelle entièrement prouvée ; les sorties non
   observées restent désactivées ;
7. au moins 30 fenêtres réelles terminales fournissent une distribution de
   performance comparable aux baselines P5/P6 déjà ratifiées ;
8. un exercice de collision, un exercice d'interruption stale et un replay de
   reprise sont verts ;
9. le lecteur sombre calcule V2 sans modifier la réponse Core v1 et produit un
   diff agrégé sans payload brut ;
10. le rollback du lecteur sombre vers Core v1 est testé sans migration
    destructive et sans perte des tables shadow.

Tant qu'une de ces conditions manque, aucun reçu `CANARY_AUTHORIZED` ne peut
être produit ; le garde runtime refuse alors le lecteur même si un déploiement
tente de positionner le mode.

### Garde et routage canary préparés

Le module `quality_lab.v2_canary` traduit les dix conditions ci-dessus en un
reçu déterministe `CANARY_HOLD` ou `CANARY_AUTHORIZED`. Il n'accepte pas un
simple booléen manuel : migration, replay, curseur, benchmarks, invariants,
30 fenêtres terminales, distribution de performance, exercices de reprise,
lecteur sombre et rollback doivent chacun fournir leur preuve.

Le module privé `app.v2_chain.canary` prépare le routage réversible :

- une identité pseudonymisée n'entre dans la cohorte que si son digest figure
  exactement dans une allowlist fermée ;
- Core v1 est toujours calculé avant V2 et reste la réponse de repli ;
- V2 ne remplace Core que comme un objet entier, jamais champ par champ ;
- chaîne incomplète, provenance incomplète, état invalide, exception ou type
  de réponse non observé rendent immédiatement la réponse Core entière ;
- le reçu ne conserve ni sujet, ni requête, ni payload, ni texte d'exception.

Cette primitive n'est pas encore reliée à une route servante. La configuration
accepte `V2_CHAIN_MODE=canary` uniquement avec tous les writers ON, le lecteur
canary seul ON, une cohorte explicite, un périmètre d'éligibilité complet et le
digest exact d'un reçu autorisé. Elle qualifie le comportement atomique et le
rollback logiciel ; elle ne constitue pas un canary actif tant que ces preuves
et le déploiement correspondant n'existent pas.

### Lecteur en ligne borné à l'abstention

`app.v2_chain.online_reader` exécute la chaîne réelle P5 → P10 en mémoire à
partir des snapshots Product Ontology et des offres canoniques. Il ne persiste
rien et n'est importé par aucune route publique. La première version est
volontairement bornée au seul type de réponse qui ne peut provoquer une action
commerciale : `ABSTAIN`.

Le contrat `contracts/v2-chain/v1/online-response.schema.json` exige :

- un digest de requête sans texte brut ;
- exactement les six provenances Retrieval, Constraints, Ranking,
  Optimization, Confidence et BUY/WAIT ;
- une liste `items` vide ;
- `raw_query_retained=false` ;
- aucune autre sortie que `ABSTAIN`.

Un index vide, un candidat non éligible, une dimension de ranking inconnue,
l'absence de calibration et l'absence de profil historique aboutissent à cette
abstention honnête. Toute sortie interne différente du chemin qualifié fait
échouer le lecteur. Le routeur canary peut donc, après satisfaction de toutes
les gates de production, ouvrir `ABSTAIN` sans ouvrir implicitement BUY_NOW ou
WAIT. Ces deux types restent individuellement bloqués.

### Journal de qualification canary

La migration additive `d7a5b9c1e3f6` ajoute
`v2_canary_read_observations`. Le journal ne contient jamais la requête, un
digest de sujet, les candidats ou la réponse. Il conserve seulement :

- l'identifiant du gate, la cohorte et la raison d'assignation ;
- la source effectivement servie et le type de réponse ;
- le motif neutre d'un fallback Core ;
- les latences Core, V2 et totale en microsecondes ;
- la complétude de chaîne, l'état de sécurité et la provenance ;
- l'instant d'évaluation et une clé opérationnelle aléatoire.

Une observation V2 exige atomiquement une cohorte canary, un type non-Core,
zéro fallback, une chaîne et une provenance complètes, ainsi qu'un état
`SAFE` ou `ABSTAIN`. Toute autre combinaison est refusée par le service et par
les contraintes SQL. L'apply/replay est idempotent ; une même clé portant des
mesures différentes est une erreur, jamais un écrasement.

Le schéma de reçu `v2-canary-read-receipt/v1` est testé avec le code. Cette
télémétrie rend les gates CANARY → PUBLIC calculables sans collecter de
contexte utilisateur. Elle ne raccorde toujours aucune route et n'active aucun
mode.

### Reçu autoritaire SHADOW → CANARY

`app.v2_chain.qualification` remplace la compilation manuelle du gate par un
calcul borné sur les journaux persistés. Il lit au maximum 10 000 exécutions et
10 000 observations puis produit le contrat
`v2-shadow-qualification/v1` :

- seules les exécutions `apply` réussies avec les treize étapes, un rapport
  digesté et un curseur avancé comptent comme fenêtres réelles ;
- un replay strictement identique est reconnu mais ne gonfle jamais le nombre
  de fenêtres ; une même plage avec un rapport différent invalide le curseur ;
- chaque verticale doit reprendre exactement au dernier curseur réussi : un
  recul comme un trou ferme le gate ;
- toute exécution encore active, intervalle temporel incohérent ou
  chevauchement ferme la preuve mono-exécution ;
- le p95 est calculé uniquement sur les fenêtres de progression distinctes et
  comparé au plafond ratifié dans la politique de performance ;
- les observations sombres doivent toutes être complètes, sans état `INVALID`
  et sans requête brute ;
- migration, rollback, replay, benchmarks, invariants et exercices de reprise
  sont fournis comme références SHA-256 obligatoires, jamais comme simples
  libellés `green` ;
- seul un type de réponse effectivement observé peut être ouvert. Les autres
  apparaissent dans `blocked_response_types` et restent OFF.

Le reçu et sa propre identité sont déterministes. Il n'est importé par aucune
route et ne modifie ni configuration ni trafic.

## Gate CANARY → PUBLIC

Le canary doit router une cohorte fermée vers la chaîne entière, jamais vers un
maillon isolé. La promotion publique exige simultanément :

1. zéro 5xx attribuable à V2 et zéro échec de readiness sur les observations
   canary ;
2. zéro violation des invariants de sécurité du tableau des phases ;
3. pour la latence et le taux d'erreur, la borne supérieure à 95 % de la
   différence `V2 - Core v1`, mesurée sur les mêmes requêtes, est ≤ 0 ;
4. 100 % des réponses V2 comportent la provenance exigée par leur contrat ;
5. chaque type de réponse publiquement activable a traversé le canary ; un type
   non couvert reste OFF même si les autres sont promus ;
6. une coupure volontaire du writer ou d'une dépendance produit une abstention
   ou un retour atomique vers Core v1, jamais une carte partiellement prouvée ;
7. le basculement `canary → shadow` est exécuté et prouve la disparition du
   trafic V2 sans perte du journal ;
8. sauvegarde, restauration, observabilité, alertes et capacité ont un reçu
   terminal sur la révision candidate ;
9. aucune régression des benchmarks et tests des Phases 0 à 10 ;
10. aucun blocker ouvert d'intégrité, de récupérabilité ou de sécurité.

Les conditions statistiques sont évaluées sur des observations, pas sur un
nombre de jours. Le canary continue tant que les bornes ne sont pas conclues.

### Reçu autoritaire CANARY → PUBLIC

`quality_lab.v2_public` et
`app.v2_chain.qualification.evaluate_persisted_canary_to_public` rendent cette
seconde décision calculable sans ouvrir de route :

- le reçu SHADOW → CANARY candidat doit être `CANARY_AUTHORIZED` et son
  `evaluation_id` doit correspondre à la preuve fournie ;
- seules les observations de la cohorte canary portant exactement ce gate sont
  auditées, dans une fenêtre bornée à 10 000 lignes ;
- le nombre minimal d'observations appariées et le support minimal par type de
  réponse sont explicitement ratifiés dans la politique ;
- tout fallback Core dans cette cohorte, toute erreur du lecteur V2, chaîne ou
  provenance incomplète, état invalide ou rétention brute ferme le gate ;
- le p95 empirique apparié de `latence V2 - latence Core` doit être inférieur
  ou égal à zéro ;
- les types servis doivent être exactement les types demandés, et chacun doit
  atteindre son support minimal ;
- santé/readiness, injection d'échec, retour à shadow, backup/restore,
  capacité/alertes, non-régression et audit des blockers exigent chacun une
  référence SHA-256 ;
- un reçu `PUBLIC_AUTHORIZED` n'autorise que les types listés. Les autres
  restent dans `blocked_response_types`.

Le cas contractuel initial autorise seulement `ABSTAIN`. Il ne raccorde pas le
lecteur, n'active aucun flag et ne vaut pas preuve de production : les mesures
réelles et les reçus externes restent obligatoires.

### Journal append-only des promotions

La migration additive `e8b6c0d2f4a7` ajoute `v2_promotion_receipts`. Le service
privé `app.v2_chain.promotion_receipt` y conserve les deux reçus avec :

- identité du rapport, identité du gate et gate source pour la promotion
  publique ;
- étape, état, types autorisés et types maintenus OFF ;
- gates, métriques agrégées, références de preuves et politique appliquée ;
- date d'évaluation et marqueur obligatoire `raw_payload_retained=false`.

Le service recalcule l'identité du rapport avant toute écriture, exige
exactement les preuves attendues, refuse une dérive au replay et ne réécrit
jamais un reçu existant. Un `HOLD` shadow marque tous les types OFF. La table ne
contient ni requête, ni identité, ni candidat, ni payload marchand. Elle n'est
reliée à aucune route.

La migration additive suivante `f9c7d1e3a5b8` ajoute aussi
`v2_promotion_proofs`. Une référence fournie à un gate ne devient vraie que si
elle résout une ligne append-only `VERIFIED` du type attendu et de la portée
exacte : campagne V2 pour SHADOW → CANARY, gate canary pour CANARY → PUBLIC.
La ligne lie un localisateur opérationnel autorisé, le digest de l'artefact, la
version du vérificateur et l'instant. Un hash seulement bien formé, absent,
rejeté, d'un autre type ou d'une autre portée garde le gate fermé. Aucun contenu
de preuve ni payload brut n'est stocké.

### Commande privée de décision

`app.v2_chain.promote` est le seul point d'entrée prévu pour calculer et
persister les reçus à partir des journaux. Il exige une date d'évaluation
explicite et identique entre dry-run, apply et replay ; il n'offre donc aucun
mode implicite « maintenant » susceptible de changer l'identité du reçu.

La commande `proof` enregistre d'abord chaque artefact vérifié par
`dry-run → apply → replay`. La commande `canary` n'est admise qu'en mode `dark`,
lecteurs promus OFF. Elle exige
exactement les onze références SHA-256 de `SHADOW_PROOF_KEYS`, calcule le gate
sur les journaux persistés et reste en dry-run sans `--apply`. L'apply crée une
ligne append-only ; le replay strictement identique retourne `existing`.

La commande `public` n'est admise qu'en mode `canary`, lecteur canary seul ON.
Elle doit nommer le reçu canary actif exact, le relit en base, reconstruit son
gate autorisé et refuse tout élargissement de type. Elle exige exactement les
huit nouvelles références SHA-256 de `PUBLIC_PROOF_KEYS` ;
`shadow_gate_ref` est dérivé du reçu relu et ne peut pas être fourni par
l'opérateur.

Dans les deux cas, la sortie suit
`contracts/v2-chain/v1/promotion-command-receipt.schema.json` et ne contient
que les identités de reçu/gate, les types autorisés ou bloqués et l'état de
persistance. Aucun contexte, sujet, candidat, preuve brute ou secret n'est
imprimé. Une erreur produit seulement son type et un état `refused`.

## Commandes de qualification

Dry-run borné et immuable :

```text
python -m app.v2_chain.orchestrator \
  --evaluated-at 2026-09-02T16:00:00Z \
  --vertical smartphones \
  --after-raw-id 0 \
  --limit 10
```

L'apply exige `V2_CHAIN_MODE=shadow` et reprend les mêmes paramètres avec
`--apply`. Le replay identique réutilise en plus les six checkpoints imprimés
par le premier rapport.

Après qualification de ce triplet, un service Cron privé peut avancer par
fenêtres bornées :

```text
python -m app.v2_chain.orchestrator \
  --evaluated-at-now \
  --vertical smartphones \
  --continue-after-last-success \
  --campaign-id sha256:<campaign> \
  --execution-kind progression \
  --limit 100 \
  --apply
```

Le schedule doit être désactivé avant toute opération de récupération. Une
exécution fraîche n'est jamais interrompue pour en lancer une autre.

Chaque artefact externe est enregistré avant d'être référencé par une
décision. Exemple sans écriture, puis même appel avec `--apply` et replay :

```text
python -m app.v2_chain.promote proof \
  --scope-ref sha256:<campaign> \
  --proof-kind single_alembic_head_ref \
  --artifact-ref test:alembic/single-head \
  --artifact-digest sha256:<artifact> \
  --verifier-version phase19.5-v1 \
  --verification-status VERIFIED \
  --verified-at 2026-09-04T01:00:00Z
```

Après accumulation et enregistrement de toutes les preuves SHADOW → CANARY,
la décision se calcule d'abord sans écriture :

```text
python -m app.v2_chain.promote canary \
  --evaluated-at 2026-09-04T01:00:00Z \
  --maximum-p95-window-ms 500 \
  --proof single_alembic_head_ref=sha256:<digest> \
  --proof postgresql_migration_ref=sha256:<digest> \
  --proof expand_only_rollback_ref=sha256:<digest> \
  --proof replay_idempotence_ref=sha256:<digest> \
  --proof inherited_benchmarks_ref=sha256:<digest> \
  --proof safety_invariants_ref=sha256:<digest> \
  --proof collision_exercise_ref=sha256:<digest> \
  --proof stale_interruption_ref=sha256:<digest> \
  --proof recovery_replay_ref=sha256:<digest> \
  --proof dark_reader_rollback_ref=sha256:<digest> \
  --proof performance_policy_ref=sha256:<digest>
```

Le même appel avec `--apply`, puis exactement le même appel une seconde fois,
doit retourner successivement `created` puis `existing` avec le même
`evaluation_id`. Un résultat `CANARY_HOLD` peut être persisté pour audit mais
n'autorise aucun lecteur. La promotion publique utilise le sous-ordre
`public`, le reçu canary actif exact, les huit preuves publiques, les seuils
d'observations et la liste explicite des types demandés ; `--help` expose ces
paramètres sans valeur opérationnelle.

### Scheduler continu fail-closed

Le point d'entrée d'exploitation est distinct du replay manuel :

```text
python -m app.v2_chain.scheduler \
  --vertical smartphones \
  --limit 100 \
  --check
```

`--check` n'exécute aucun writer. Lorsqu'un lease V2 existe, son reçu expose
uniquement l'identifiant d'exécution, l'instant et l'âge du heartbeat ainsi que
`stale_recovery_eligible`; aucun payload n'est relu ni imprimé. Sans ce flag, le
scheduler lance au plus une fenêtre `apply` et retourne un reçu JSON neutre. Il
s'abstient avec un code de sortie normal lorsque :

- la synchronisation catalogue possède un run `running` ;
- une autre chaîne V2 possède le lease unique ;
- aucun nouveau `RawSourceRecord` Awin n'existe après le dernier curseur réussi
  de la verticale.

Le curseur est isolé par verticale. Le lease reste global afin que deux
verticales ne puissent jamais écrire la chaîne simultanément. Le scheduler ne
termine jamais automatiquement un lease stale : la récupération reste une
opération explicite après inspection du heartbeat et désactivation du schedule.
Une fois ces deux conditions vérifiées, l'opérateur peut exécuter :

```text
python -m app.v2_chain.scheduler \
  --vertical smartphones \
  --limit 100 \
  --interrupt-stale
```

La commande utilise la borne `V2_CHAIN_STALE_AFTER_SECONDS` (quatre heures par
défaut). Un heartbeat plus frais est conservé. Un heartbeat plus ancien rend
le lease terminal `interrupted`, puis la commande s'arrête sans lancer de
successeur. La reprise ne peut donc avoir lieu qu'à l'occurrence suivante.
Cette occurrence reprend obligatoirement l'instant d'évaluation, la borne et
les six checkpoints du run interrompu. Elle rejoue la chaîne entière de façon
idempotente : les étapes déjà committées sont retrouvées et leurs sorties ne
peuvent pas être dépassées par une nouvelle capture de checkpoints. Un run
`failed` n'est jamais repris automatiquement et retourne `status=v2_failed`
jusqu'à une décision d'exploitation.

L'apply refuse de démarrer si `V2_CHAIN_MODE` n'est pas actif, si le schéma
n'est pas piloté par Alembic, si la base est absente ou si la fenêtre dépasse
100 raws. Les invariants de configuration garantissent séparément que seuls
les lecteurs correspondant à l'état atomique peuvent être actifs. Ce point
d'entrée n'est importé par aucune route publique.

L'ordre d'activation d'une verticale est donc :

1. `--check` terminal avec `status=due` ou `status=fresh` ;
2. un lancement manuel borné et un reçu terminal `succeeded` ;
3. replay manuel identique avec les checkpoints du journal ;
4. activation d'un seul schedule privé ;
5. ajout d'une nouvelle verticale seulement après preuve que le curseur de la
   précédente progresse sans contention.

Le 3 septembre 2026, l'audit en lecture seule de production montrait un run
catalogue actif avec heartbeat frais et plusieurs feeds effectivement commit.
Un scheduler V2 conforme se serait donc abstenu avec
`status=catalog_syncing`. Cette observation qualifie la garde, pas encore le
déploiement du nouveau point d'entrée.

### Lecteurs sombres V2/Core v1

Le point d'entrée `app.v2_chain.dark_reader` n'est relié à aucune route. Il
lit une fenêtre de runs Hybrid Retrieval terminés, reconstruit en mémoire leur
requête synthétique depuis Product Ontology, vérifie le digest, applique les
garde-fous de prix, devise, stock et fraîcheur du Core puis suit les clés
étrangères V2 jusqu'à BUY/WAIT.

```text
python -m app.v2_chain.dark_reader \
  --evaluated-at 2026-09-03T20:30:00Z \
  --after-hybrid-run-id 0 \
  --limit 25
```

Le même appel avec `--apply` persiste uniquement dans
`v2_dark_read_observations` : digest de requête, compteurs, recouvrement en
parties par million, concordance top-1, complétude de la chaîne, verdict
terminal et état de sécurité. La requête, les candidats et les payloads ne
sont pas des colonnes du modèle. Un replay au même instant retrouve la ligne
existante ; une divergence est refusée.

Une mesure est refusée si le catalogue ou la chaîne V2 écrit. Un digest
incohérent devient `INVALID`, une chaîne incomplète reste `INCOMPLETE`, et une
sortie prudente reste `ABSTAIN`. Le Quality Lab qualifie la mécanique à partir
de 30 fenêtres réelles complètes, sans invalide ni requête brute. Il publie
l'accord avec Core comme observation seulement :
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` reste explicite.

Le chemin de qualification sur trafic réel est
`app.v2_chain.live_dark_reader`. En mode `dark`, les routes existantes
`/advise` et `/advise/stream` servent d'abord et intégralement Core V1, puis
programment une comparaison V2 en arrière-plan. Le texte de la requête reste
uniquement en mémoire pendant le calcul. La table additive
`v2_live_dark_read_observations` conserve une clé aléatoire, la campagne, la
surface, la verticale/locale, les résultats agrégés, latences, complétude,
provenance, état de sécurité et classification ; elle ne possède aucune
colonne de requête, candidat, sujet ou payload. Hors mode `dark`, la fonction
retourne `off` avant d'ouvrir une session de base.

Les divergences sont classées sans inventer de vérité humaine :
`BOTH_VALID`, `V2_ABSTAINS_CORRECTLY`, `V2_UNSUPPORTED`, `ENGINE_PROBLEM` ou
`AMBIGUOUS`. Les libellés directionnels `V1_IMPROVEMENT` et
`V2_IMPROVEMENT` restent réservés à une preuve externe future et ne sont pas
attribués automatiquement.

### Funnel et vue de contrôle

Chaque fenêtre terminale persiste `v2-window-metrics/v1` avec les compteurs
`RAW → IDENTIFIED → RESOLVED → VERIFIED OFFER → ONTOLOGY VERIFIED → RETRIEVED
→ ELIGIBLE → RANKABLE → OPTIMIZABLE → CALIBRATED → ACTIONABLE`. Le générateur
`app.v2_chain.coverage_funnel` agrège seulement les exécutions de progression
ou de reprise de la campagne exacte : un replay ne compte jamais comme une
fenêtre ou un volume supplémentaire. Il exige 30 fenêtres réussies, complètes,
contiguës, sans lease actif, avec des compteurs monotones.

`app.v2_chain.control.build_promotion_control` est la vue privée unique
de pilotage. Elle expose sans payload : MODE, fenêtre courante et précédente,
curseur, taux d'erreur, p95, statut du funnel, UNKNOWN, ABSTAIN, fallback,
violations de sécurité, divergences dark, état canary et preuve de rollback.
Elle borne chaque lecture à 10 000 lignes et filtre toutes les observations par
la campagne ou le gate actif ; elle ne mélange pas l'historique.

La vue effective du déploiement se lit sans mutation avec :

```text
python -m app.v2_chain.control --evaluated-at 2026-09-04T14:00:00Z
```

### Politique d'incident et retour arrière

- **SEV-1 — truth/safety** : prix, devise, stock, marchand ou décision inventé,
  mauvais produit fusionné, contrainte dure violée, fuite privée ou temporelle.
  Arrêt immédiat du canary/public et retour V1.
- **SEV-2 — disponibilité/latence** : erreurs ou saturation V2 sévères. Fallback
  V1 immédiat, réduction/arrêt de la cohorte et retour au mode précédent.
- **SEV-3 — couverture** : hausse d'UNKNOWN/ABSTAIN ou baisse du funnel sans
  violation de vérité. Investigation au mode courant, aucune sortie fabriquée.

| Signal | Action automatique ou opératoire obligatoire |
|---|---|
| deux writers ou collision de lease | le second échoue fermé ; conserver le propriétaire frais et diagnostiquer |
| fenêtre V2 échouée/interrompue | ne pas avancer le curseur ; suspendre le schedule avant toute récupération explicite |
| hausse des `UNKNOWN` ou `ABSTAIN` hors politique ratifiée | rester au mode courant, bloquer la promotion, auditer le funnel |
| erreur, chaîne/provenance incomplète ou invariant violé en dark | V1 reste servi ; marquer l'observation et bloquer CANARY |
| erreur/incomplétude/fraîcheur insuffisante en canary | servir le bloc V1 entier ; bloquer PUBLIC |
| 5xx, readiness, fallback ou violation de sécurité après promotion | `PUBLIC → CANARY` si cohorte sûre, sinon `PUBLIC/CANARY → DARK → OFF`; V1 reste le chemin de secours chaud |
| régression confirmée d'intégrité ou de récupérabilité | revenir à `off`, désactiver le Cron V2, préserver journaux/tables shadow, ouvrir un incident |

Le rollback est un changement de mode/lecteur et non une migration destructive.
Les journaux et tables shadow sont conservés pour l'analyse. Une reprise ne
peut être tentée qu'après un reçu terminal de l'incident et une nouvelle
qualification des gates affectées ; les phases produit déjà GO ne sont pas
rouvertes.

## Ce qui est testable immédiatement

| Contrôle | Maintenant | Preuve attendue |
|---|---:|---|
| expansion atomique des writers | oui | tests de configuration |
| refus des lecteurs et modes non qualifiés | oui | tests fail-closed |
| apply/replay end-to-end local | oui | même identité, zéro duplication |
| lease unique, heartbeat, état terminal | oui | tests du journal |
| migration SQLite et unicité de tête | oui | tests Alembic locaux |
| migration PostgreSQL | en CI ou environnement PostgreSQL | upgrade, drift, downgrade/restore |
| benchmarks autonomes P1–P10 | oui | seuils du tableau |
| volumes réels continus | après déploiement shadow | curseur et agrégats du journal |
| dark reader réel | implémenté et raccordé de façon non influente | V1 inchangé, mode OFF sans DB, confidentialité et diff agrégé testés ; observations réelles encore requises |
| garde canary | implémentée localement | dix gates objectives, allowlist fermée, fallback Core atomique ; aucun raccordement public |
| reçu SHADOW → CANARY | implémenté localement | dérivé des journaux ; replays dédupliqués, curseurs contigus, preuves externes persistées et vérifiées |
| reçu CANARY → PUBLIC | implémenté localement | cohorte/gate exacts, support par type, zéro fallback, provenance et p95 appariés |
| journal de promotion | implémenté localement | migrations `e8b6c0d2f4a7` et `f9c7d1e3a5b8`, preuves/références append-only |
| garde runtime des promotions | implémenté localement | reçu exact, gates et lignes de preuve revérifiés ; filiation et types bornés ; configuration seule insuffisante |
| canary | volontairement bloqué | 30 fenêtres réelles et toutes les gates SHADOW → CANARY ; seul ABSTAIN possède actuellement un lecteur contractuel |
| public | volontairement bloqué | toutes les gates CANARY → PUBLIC |

## Plan unique de promotion

1. intégrer le contrôle atomique, le journal et la migration avec lecteurs OFF ;
2. déployer la migration seule et vérifier santé, schéma et absence de run ;
3. exécuter un dry-run, un apply et son replay identique sur une fenêtre courte ;
4. activer un seul Cron privé shadow à curseur monotone ;
5. accumuler les fenêtres jusqu'à satisfaction mesurable des gates héritées et
   de performance ;
6. déployer le dark reader qualifié localement et accumuler 30 comparaisons
   réelles sans servir V2 ;
7. prouver reprise et rollback, persister le reçu `CANARY_AUTHORIZED`, puis
   configurer son `evaluation_id` exact et la cohorte fermée ;
8. lancer le canary atomique jusqu'à conclusion des bornes statistiques ;
9. persister et désigner le reçu `PUBLIC_AUTHORIZED` seulement après le canary
   terminal et la vérification de sa filiation ;
10. promouvoir la chaîne entière, conserver Core v1 comme rollback immédiat et
    surveiller en continu les mêmes invariants.

Ce plan évite deux échecs symétriques : laisser indéfiniment les Phases 1 à 10
en shadow, ou les exposer une par une dans un ordre incohérent.
