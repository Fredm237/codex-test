# FILON — Audit des 15 commits de promotion V2

Date de l'audit : **2026-09-04**

## Verdict

**V2 NOT READY**

Le lot constitue une base solide et largement testée, mais il ne respecte pas
encore le mandat Phase 19.5 sur quatre points structurants : le mode atomique
`dark` est absent, le lecteur sombre ne traite pas le trafic réel, les fenêtres
ne portent pas encore le funnel de couverture demandé, et le calcul du gate
peut agréger des exécutions historiques qui ne font pas partie de la campagne
continue à qualifier.

Les classifications ci-dessous portent sur l'intention et le contenu de chaque
commit. `FIX` signifie que le commit est conservé après correction ; `REWRITE`
signifie que son contrat principal doit être remplacé ; `DROP` signifie qu'il
n'apporte aucun changement produit vérifiable.

## Registre

| Commit | Classification | Décision et preuve |
|---|---|---|
| `1ca0a47` | **FIX** | Conserver le scheduler, le lease unique et l'abstention pendant le catalogue. Corriger la provenance de campagne, le curseur continu et la persistance des compteurs de fenêtre. |
| `ca68143` | **REWRITE** | La table privée et les invariants de non-rétention sont réutilisables, mais le lecteur reconstruit uniquement des requêtes synthétiques de replay et n'est raccordé à aucune requête utilisateur. Le mandat exige un dual-read réel où V1 reste servi. |
| `9f4c90d` | **FIX** | Le routage atomique et le fallback Core sont utiles. Ajouter l'éligibilité fonctionnelle explicite : verticale, locale, type de décision, fraîcheur, dépendances et UNKNOWN critique. |
| `ceaa13b` | **KEEP** | Le lecteur en mémoire est volontairement borné à `ABSTAIN`, sans invention de ranking ou de confidence. Cette limite doit rester visible et les types `BUY_NOW`/`WAIT` rester OFF tant qu'ils ne sont pas qualifiés. |
| `9e70861` | **FIX** | La télémétrie canary est privée, agrégée et idempotente. Elle doit être raccordée au chemin public gouverné et enrichie avec l'éligibilité/fallback sans conserver la requête. |
| `e17f08b` | **FIX** | Le gate est déterministe, mais il compte toutes les exécutions `apply` historiques. Il doit qualifier une campagne/époque précise, 30 fenêtres distinctes, terminales, complètes et contiguës, et des dark reads réels. |
| `fe3990b` | **FIX** | Le gate public et les mesures appariées sont une bonne base. Les SLO doivent être proposés à partir des distributions réelles puis ratifiés ; des digests fournis seuls ne doivent pas transformer une preuve absente en booléen vert. |
| `8994e07` | **FIX** | Les reçus append-only et leur filiation sont à conserver. Les références externes doivent pointer vers des artefacts persistés et vérifiables, pas seulement respecter la syntaxe SHA-256. |
| `cac4c83` | **FIX** | Le garde runtime fail-closed est correct pour `canary`/`public`. Ajouter `dark` aux invariants atomiques sans lui donner d'autorisation de réponse publique. |
| `d73d352` | **FIX** | La commande privée est bornée et ne modifie pas directement les flags. Ajouter la transition gouvernée `shadow → dark → canary` et refuser tout saut de mode. |
| `e943d9d` | **KEEP** | La récupération stale est explicite, bornée et séparée du Cron normal ; un heartbeat frais n'est jamais interrompu automatiquement. |
| `9d6e44a` | **KEEP** | Le reçu de lease expose l'état utile sans payload brut et laisse l'opérateur décider d'une récupération. |
| `f04c2d8` | **DROP** | Le message annonce un test, mais le commit ne modifie que le journal de mission. Il n'apporte aucune preuve exécutable et doit être absorbé ou retiré lors du rebase. |
| `2fbeeb9` | **FIX** | La reprise réutilise timestamp, limite et checkpoints de l'exécution interrompue. Ajouter une filiation persistée et empêcher qu'un replay historique puisse faire régresser le curseur continu. |
| `9e8aaac` | **KEEP** | Constat documentaire fidèle du run catalogue 25 ; aucune mutation opérationnelle. À conserver comme historique, puis actualiser uniquement avec un état terminal prouvé. |

## Contrôles transverses

| Domaine | État | Motif |
|---|---|---|
| contrats | **FIX** | Les contrats canary/public existent ; il manque le contrat DARK réel et le funnel par fenêtre. |
| migrations | **FIX** | Les trois migrations sont additives et ont une tête unique locale. Une migration additive supplémentaire est requise pour les campagnes, compteurs de fenêtre et dark reads réels. |
| curseurs | **FIX** | Le scheduler prend le dernier run réussi par identifiant. Un replay ancien exécuté plus tard peut donc faire régresser la tête de progression. |
| locking | **KEEP** | Index unique partiel sur l'unique statut `running`, complété par une gestion explicite de collision. |
| idempotence | **FIX** | L'identité de replay est vérifiée, mais le curseur et la campagne continue doivent distinguer replay de progression. |
| scheduling | **FIX** | Le Cron est privé, borné et s'abstient pendant le catalogue ; il manque le mode `dark` et une campagne continue identifiable. |
| fail-closed | **FIX** | `off`, `shadow`, `canary`, `public` sont gouvernés ; `dark` manque. |
| secrets/privacy | **KEEP** | Aucun secret ni payload brut n'est ajouté. Les requêtes sont représentées par digest et les observations déclarent explicitement `raw_query_retained=false`. |
| observabilité | **FIX** | Heartbeat, statut et curseur existent ; les compteurs exigés par fenêtre et la classification des divergences réelles manquent. |
| rollback | **FIX** | Les switches existent, mais l'exercice réel `DARK → OFF → V1 ONLY` et son reçu ne sont pas encore produits. |
| concurrence | **KEEP** | Le scheduler refuse un catalogue actif et un lease V2 actif ; la contrainte DB empêche deux writers V2 simultanés. |

## Corrections obligatoires avant publication

1. ajouter `V2_CHAIN_MODE=dark` et ses invariants fail-closed ;
2. distinguer campagne continue, fenêtre de progression et replay ;
3. garantir un curseur monotone sans masquer les trous ;
4. persister les compteurs de funnel demandés pour chaque fenêtre ;
5. remplacer le dark reader synthétique par un dual-read réel, non influent et
   respectueux de la vie privée ;
6. classifier les divergences sans inventer de vérité externe ;
7. lier les gates à une campagne et à des preuves persistées vérifiables ;
8. tester la migration PostgreSQL, les collisions, l'interruption/reprise, le
   replay, le rollback de mode et les chemins de fallback.

## Ce qui n'est pas rouvert

Cet audit ne rouvre aucune Phase 1–18. Les corrections portent exclusivement
sur l'orchestration, l'observation et la promotion du système déjà construit.
Le lecteur limité à `ABSTAIN` reste honnête : il réduit la couverture autorisée,
mais ne constitue pas une permission d'inventer `BUY_NOW` ou `WAIT`.

## Résolution locale post-audit

Les huit corrections obligatoires ont été intégrées dans l'écart local Phase
19.5 : mode `dark`, campagne et filiation des fenêtres, curseur monotone,
funnel persisté, dual-read réel non influent, classification prudente,
registre de preuves persistées, éligibilité canary et tests de rollback/
fallback. La migration additive `f9c7d1e3a5b8` porte les nouvelles colonnes et
tables sans réécrire l'historique.

La qualification terminale locale compte **2 770 tests backend verts, 3
ignorés**, plus **3 tests PostgreSQL 16 verts** couvrant upgrade, drift,
verrouillage et restauration. Ce résultat ferme les `FIX/REWRITE` au niveau
logiciel ; il ne remplace pas les fenêtres, dark reads, canary ou reçus réels
encore à produire en production.
