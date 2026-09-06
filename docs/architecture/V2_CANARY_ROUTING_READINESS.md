# FILON — V2 Canary Routing Readiness

- Date : **5 septembre 2026**
- Branche locale : **`codex/filon-v2-dark-qualification`**
- Portée : **raccordement CANARY/PUBLIC fail-closed, sans activation**
- Type de réponse qualifié : **`ABSTAIN` uniquement**
- Verdict code : **READY LOCAL**
- Verdict production : **HOLD — ingestion catalogue 26 active**

## Frontière livrée

Les routes `/api/advise` et `/api/advise/stream` calculent toujours Core V1
avant toute tentative V2. Les modes `off`, `shadow` et `dark` rendent le bloc
Core exact. Les modes `canary` et `public` ne peuvent appeler le lecteur V2
qu'après validation du reçu append-only désigné, de ses preuves enregistrées,
du périmètre fonctionnel et de la fraîcheur.

La seule adaptation publique disponible est une abstention complète : aucune
offre, carte, recommandation ou alternative. `BUY_NOW` et `WAIT` demeurent
fermés. Une sortie actionnable interne provoque le repli du bloc entier vers
Core V1.

## Corrections de sûreté

1. La fraîcheur est mesurée sur les snapshots qui ont effectivement produit
   les candidats. Un snapshot récent sans rapport avec la requête ne peut plus
   autoriser une preuve candidate plus ancienne.
2. Une preuve future, absente ou trop ancienne rend la requête inéligible.
3. L'inspection en mémoire est liée au digest de requête, à la verticale, à
   la locale, au pays, au budget et à l'instant exact. Elle ne peut pas être
   réutilisée pour une autre demande.
4. Une abstention V2 ne peut jamais effacer un résultat Core réel. Elle ne
   remplace Core que lorsque Core n'a lui-même aucun résultat.
5. Les fallbacks d'une requête inéligible restent journalisés mais ne sont pas
   comptés comme panne V2. Tout fallback après éligibilité demeure bloquant
   pour PUBLIC.
6. Le journal ne conserve ni texte de requête, ni sujet, ni candidat, ni
   payload marchand ou réponse.

## Qualification locale

| Contrôle | Résultat |
|---|---:|
| lecteur/routage/garde/observation ciblés | **51 passed** |
| qualification publique/routage/garde ciblés | **47 passed** |
| preuve manifestée et reproductible | **17 passed** |
| suite backend complète, environnement conforme | **2 796 passed, 3 skipped** |
| suite web + TypeScript | **PASS** |
| build Next.js de production | **PASS, 43 routes générées** |
| diff et compilation | **PASS** |

La suite a été relancée avec `uvicorn>=0.49`, conformément à
`requirements.txt`, et avec l'ouverture loopback requise par le test du
transport OTLP. Les deux échecs auparavant causés par l'environnement local ne
se reproduisent pas dans cette configuration.

## Production lue sans modification

Lecture du **5 septembre 2026 vers 21:38 UTC** :

| Signal | État |
|---|---|
| `/health/live` | HTTP 200, vivant |
| `/health/ready` | HTTP 200, PostgreSQL `ok` |
| `/health` | application, PostgreSQL et Redis `ok` |
| schéma | `f9c7d1e3a5b8` |
| catalogue | run `26` unique, `running` |
| heartbeat catalogue | frais, environ 7 secondes |
| modification production par ce lot | **aucune** |

Le run 26 n'est ni interrompu ni concurrencé. Aucun writer, lecteur, flag,
Cron, déploiement ou reçu de promotion n'a été modifié.

Une lecture privée complémentaire du `2026-09-05T22:43:56Z` confirme que ce
run est productif : **44 checkpoints de feed terminés**, **413 761 lignes
validées**, puis un seul feed `87833` encore `running` avec **16 200 lignes** au
dernier heartbeat observé. Les compteurs du run public restent volontairement
à zéro jusqu'à son état terminal ; ils ne doivent pas être interprétés comme
une absence de progression.

## Gates encore requis

Ce reçu qualifie le code de raccordement ; il ne remplace aucun gate de
production. Les 30 fenêtres, le funnel contigu, le replay, la distribution de
performance, les exercices de collision/récupération, le DARK réel et le
rollback vers Core V1 sont maintenant prouvés. Les onze preuves exactes sont
préparées dans `V2_SHADOW_PROMOTION_PROOF_MANIFEST.json`, mais les tables
`v2_promotion_proofs` et `v2_promotion_receipts` sont encore vides.

Restent nécessaires : état terminal du run catalogue 26, absence d'une autre
ingestion, enregistrement idempotent des onze preuves, calcul/persistance du
reçu `CANARY_AUTHORIZED`, activation de la cohorte fermée `ABSTAIN`,
observations canary réelles puis reçu public.

Après un reçu `PUBLIC_AUTHORIZED`, le même journal privé continue à enregistrer
chaque tentative promue avec le gate public exact. Il ne conserve ni requête ni
identité ; une panne de cette preuve fait revenir la requête entière sur Core
V1. La vue de contrôle sépare les volumes et fallbacks PUBLIC des observations
ayant servi à qualifier le canary.

## Verdict

**ROUTING READY LOCAL / PRODUCTION HOLD.**

Ce lot ne doit pas être publié, fusionné ou déployé pendant l'ingestion
catalogue active. Il n'autorise pas `BUY_NOW`, `WAIT` ou une surface P14–P19.
