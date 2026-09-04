# FILON — V2 Continuous Shadow Readiness

- Date de qualification locale : **4 septembre 2026**
- Branche : **`codex/filon-v2-continuous-shadow`**
- Base locale avant correctifs : **`9e8aaacbe1397e30ce7e5316f35bd25d011b9995`**
- Verdict logiciel : **READY LOCAL**
- Verdict activation : **NO-GO tant que le run catalogue 25 est actif**
- Publication : **non autorisée pour ce lot**
- Production : **inchangée, Core V1 seul**

## Résultat

Le lot Phase 19.5 ferme localement les vides qui empêchaient une promotion
mesurable de la chaîne P0/P1–P10 : cinq modes atomiques, campagne continue,
curseur monotone, replay/reprise séparés, funnel de couverture, dual-read réel,
éligibilité canary, preuves externes persistées, reçus append-only, garde
runtime et vue de contrôle privée.

Ce résultat ne constitue ni un déploiement, ni une activation. Les writers,
lecteurs et Crons V2 de production restent OFF.

## Frontières atomiques

| Mode | Writers P0/P1–P10 | Dark read | Canary | Public |
|---|---:|---:|---:|---:|
| `off` | OFF | OFF | OFF | OFF |
| `shadow` | ON | OFF | OFF | OFF |
| `dark` | ON | ON, non influent | OFF | OFF |
| `canary` | ON | OFF | cohorte fermée | OFF |
| `public` | ON | OFF | OFF | types autorisés seulement |

Une combinaison partielle est invalide. CANARY et PUBLIC exigent le reçu
append-only exact, tous ses gates vrais, les preuves enregistrées, une portée
fonctionnelle explicite et une fraîcheur bornée. La configuration seule ne
peut ouvrir aucun lecteur.

## Exécution continue et récupération

Le scheduler privé :

- limite chaque fenêtre à 100 raws ;
- s'abstient devant un run catalogue ou V2 actif ;
- utilise un lease global unique avec heartbeat ;
- isole les curseurs par verticale et campagne ;
- compte seulement `progression` et `recovery` dans les 30 fenêtres réelles ;
- n'utilise jamais un `replay` pour gonfler le volume ou faire avancer le
  curseur ;
- ne terminalise un lease stale que par commande explicite, schedule coupé ;
- reprend exactement la fenêtre, l'instant et les checkpoints du run
  interrompu ;
- ne conserve ni payload, ni contexte, ni secret dans son journal.

Chaque fenêtre persiste son identité et les compteurs :

`RAW → IDENTIFIED → RESOLVED → VERIFIED OFFER → ONTOLOGY VERIFIED → RETRIEVED → ELIGIBLE → RANKABLE → OPTIMIZABLE → CALIBRATED → ACTIONABLE`.

Le funnel devient `READY` seulement avec au moins 30 fenêtres distinctes,
terminales, complètes et contiguës, zéro lease actif, un volume RAW positif et
des comptages monotones.

## Dark reader réel

En mode `dark`, `/advise` et `/advise/stream` servent d'abord Core V1 puis
programment V2 en arrière-plan. La sortie V2 ne modifie jamais la réponse
utilisateur. Hors mode `dark`, le chemin sort avant toute session DB.

Le texte de requête existe uniquement en mémoire pendant le calcul. Le journal
`v2_live_dark_read_observations` contient seulement : campagne, surface,
verticale/locale, résultats agrégés, compteurs, latences, complétude,
provenance, sécurité et classification. Il ne possède aucune colonne pour la
requête, le sujet, les candidats ou un payload marchand.

Sans vérité humaine externe, une divergence n'est jamais baptisée
artificiellement amélioration. Les classifications automatiques sont
`BOTH_VALID`, `V2_ABSTAINS_CORRECTLY`, `V2_UNSUPPORTED`, `ENGINE_PROBLEM` et
`AMBIGUOUS`. `NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` reste explicite.

## Éligibilité CANARY

Avant tout appel V2, une décision digestée exige simultanément :

- verticale, locale et type de décision dans le périmètre autorisé ;
- dépendances disponibles ;
- données sous la borne de fraîcheur ;
- aucune inconnue critique ;
- aucune violation de contrainte ;
- confiance suffisante lorsque requise ;
- rollback disponible.

Un échec sert le bloc Core V1 entier et n'appelle pas V2. Les observations
canary persistent la décision d'éligibilité et restent liées au gate exact.
Seul `ABSTAIN` dispose actuellement d'un contrat de lecture V2 qualifié ;
`BUY_NOW` et `WAIT` restent OFF jusqu'à leurs preuves propres.

## Preuves et reçus

La migration `f9c7d1e3a5b8` est additive et réversible. Elle ajoute :

- provenance de campagne, type d'exécution et métriques aux fenêtres ;
- éligibilité aux observations canary ;
- observations live dark sans payload ;
- registre `v2_promotion_proofs` sans contenu brut.

Une preuve externe ne vaut vrai que si son digest résout une ligne
`VERIFIED`, du type attendu et de la portée exacte. La ligne lie un localisateur
opérationnel sûr, le digest de l'artefact, la version du vérificateur et
l'instant. Un digest arbitraire, absent, rejeté ou d'une autre portée ferme le
gate.

Les reçus SHADOW → CANARY et CANARY → PUBLIC sont append-only, déterministes,
idempotents et reliés. Le garde runtime revérifie aussi le registre de preuves ;
une insertion manuelle d'un reçu contenant seulement des hashes bien formés ne
peut pas ouvrir un lecteur.

## Vue de contrôle

`app.v2_chain.control` fournit une vue privée bornée à 10 000 lignes :

- MODE ;
- fenêtre courante et dernière fenêtre ;
- curseur ;
- taux d'erreur et p95 ;
- funnel ;
- UNKNOWN, ABSTAIN et fallback ;
- violations de sécurité ;
- divergences dark ;
- état canary ;
- preuve de rollback.

Les mesures sont filtrées par campagne et gate actif. L'historique d'une autre
campagne ne peut pas autoriser la candidate.

## Qualification locale terminale

| Contrôle | Résultat |
|---|---|
| suite backend Python 3.12 | **2 770 passed, 3 skipped** |
| PostgreSQL 16 jetable | **3 passed** |
| migration | upgrade, drift, verrou, downgrade/restauration verts |
| contrats JSON | validés par la suite |
| funnel | progression/recovery seulement ; replay exclu |
| preuves | dry-run/apply/replay, scope/type/statut et non-rétention testés |
| garde runtime | refuse preuve absente/non vérifiée et filiation invalide |
| dark routing | V1 inchangé et absence d'effet hors mode dark testées |
| fichiers protégés | non modifiés |

Le PostgreSQL de test a été supprimé après la preuve.

## Production lue sans modification

Dernière revalidation publique : **2026-09-04T16:06Z**.

| Signal | État |
|---|---|
| `/health/live` | HTTP 200 |
| `/health/ready` | HTTP 200, PostgreSQL `ok` |
| `/health` | HTTP 200, PostgreSQL et Redis `ok` |
| schéma | `b5d3f7a9c1e4` |
| catalogue | run 25 unique, `running` |
| heartbeat run 25 | frais, environ 5 s |
| mode V2 production | `off` |
| lecteurs publics | Core V1 |

Le run 25 a commencé le `2026-09-02T18:03:39Z`. Son heartbeat frais prouve un
processus encore vivant. Conformément au mandat, aucun writer V2, flag, Cron,
déploiement ou migration de production n'a été lancé.

## Gates restant avant activation réelle

1. état terminal honnête du run catalogue 25 et absence d'autre ingestion ;
2. autorisation nominative de publication du lot Phase 19.5 ;
3. CI distante terminale verte ;
4. déploiement lecteurs OFF et migration additive `f9c7d1e3a5b8` ;
5. snapshot production puis fenêtre manuelle dry-run/apply/replay ;
6. un seul Cron shadow privé et 30 fenêtres réelles valides ;
7. funnel réel et preuves de collision/interruption/reprise/performance ;
8. passage en `dark`, trafic réel observé et rollback `DARK → OFF → V1` ;
9. enregistrement des preuves et reçu `CANARY_AUTHORIZED` ;
10. canary fonctionnel fermé, mesures appariées et rollback vers shadow ;
11. SLO proposés depuis les distributions réelles puis ratifiés ;
12. reçu `PUBLIC_AUTHORIZED`, activation atomique et observation post-bascule.

## Verdict

**READY LOCAL / NO-GO ACTIVATION.**

Le code peut être proposé à la publication et à la CI. La prochaine action de
production reste interdite tant que le run 25 est actif. Aucune phase produit
déjà GO n'est rouverte ; seuls les gates de promotion de la chaîne sont encore
à produire.
