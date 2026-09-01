# FILON — Runbook de promotion atomique de la chaîne V2

## Statut de ce document

Ce runbook décrit la promotion conjointe des shadows P0 et des Phases 1 à 10.
Il ne constitue pas une activation de production. La version courante du code
autorise `OFF` et `SHADOW` ; elle refuse encore `CANARY` et `PUBLIC`.

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
| `canary` | tous ON | cohorte fermée | OFF | refusé fail-closed jusqu'aux gates |
| `public` | tous ON | inclus | ON | refusé fail-closed jusqu'aux gates |

Un flag writer explicitement `false` sous `V2_CHAIN_MODE=shadow` invalide la
configuration. Un lecteur activé sous `off` ou `shadow` invalide également la
configuration.

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

Tant qu'une de ces conditions manque, `V2_CHAIN_MODE=canary` doit continuer à
être refusé par la configuration.

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
  --limit 100 \
  --apply
```

Le schedule doit être désactivé avant toute opération de récupération. Une
exécution fraîche n'est jamais interrompue pour en lancer une autre.

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
| dark reader | non implémenté | diff sans impact sur Core v1 |
| canary | volontairement bloqué | toutes les gates SHADOW → CANARY |
| public | volontairement bloqué | toutes les gates CANARY → PUBLIC |

## Plan unique de promotion

1. intégrer le contrôle atomique, le journal et la migration avec lecteurs OFF ;
2. déployer la migration seule et vérifier santé, schéma et absence de run ;
3. exécuter un dry-run, un apply et son replay identique sur une fenêtre courte ;
4. activer un seul Cron privé shadow à curseur monotone ;
5. accumuler les fenêtres jusqu'à satisfaction mesurable des gates héritées et
   de performance ;
6. construire le dark reader et comparer V2/Core v1 sans servir V2 ;
7. prouver reprise et rollback, puis seulement autoriser `canary` dans le code ;
8. lancer le canary atomique jusqu'à conclusion des bornes statistiques ;
9. autoriser `public` seulement après le reçu CANARY terminal ;
10. promouvoir la chaîne entière, conserver Core v1 comme rollback immédiat et
    surveiller en continu les mêmes invariants.

Ce plan évite deux échecs symétriques : laisser indéfiniment les Phases 1 à 10
en shadow, ou les exposer une par une dans un ordre incohérent.
