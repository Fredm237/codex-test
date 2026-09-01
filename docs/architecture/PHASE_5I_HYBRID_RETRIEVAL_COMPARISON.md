# FILON — Phase 5I Hybrid Retrieval Comparison

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — QUALIFIED SHADOW**
- Lecteur public : **INCHANGÉ**
- Backend vectoriel réel : **ABSENT**
- Limitation principale : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Comparaison sur le holdout immuable

Le même corpus synthétique et adversarial de 9 224 cas a été utilisé pour
chaque étape. Aucun résultat d'oracle n'est présenté comme une préférence
humaine ou une mesure de trafic production.

| Adaptateur | Statut | Mismatches | Failures bloquantes | Décision |
|---|---:|---:|---:|---|
| oracle de contrat | `QUALIFIED / non promouvable` | 0 | 0 | contrôle du benchmark uniquement |
| legacy offer-first | `UNSAFE` | 5 765 | 4 612 | rejeté |
| lexical | `SAFE_INCOMPLETE` | 1 153 | 0 | abstention semantic-only conservée |
| structured + semantic expand-only | `QUALIFIED` | 0 | 0 | admissible en shadow |
| fusion RRF product-first | `QUALIFIED` | 0 | 0 | admissible en shadow |

La fusion finale conserve Recall@50 et NDCG@10 à 1,0 sur 4 612 positifs,
zéro violation de contrainte, zéro faux regroupement, une provenance complète
et zéro fausse résolution semantic-only. Son évaluation est
`sha256:412ef7ca58cdf7a4acf672ec470be7a3c9c631e9090ecccebb765f234bf9617e`.

## Comparaison production bornée

Le corpus Product Ontology shadow contenait 330 snapshots avec Variant résolue :

| Rôle observé | Snapshots |
|---|---:|
| `UNKNOWN` | 328 |
| `BUNDLE` | 1 |
| `PRIMARY_PRODUCT` | 1 |

Une première fenêtre de 100 lignes a correctement échoué fermée : 100
`NO_MATCH`, aucun candidat et aucune écriture. Cette observation ne constitue
pas un échec du retrieval : les 100 rôles étaient `UNKNOWN` et ne pouvaient pas
être promus comme produits principaux.

La fenêtre qualifiable a donc été réduite au seul snapshot
`PRIMARY_PRODUCT`, avec `after_snapshot_id=183`, `limit=1` et
`evaluated_at=2026-09-01T18:00:00Z`. Le dry-run a produit un candidat, un top-1
égal à la Variant cible et l'identité stable
`sha256:6b7526f54012e7288ee1037c7969e472fe48e760197cc968972091e5ff3beb10`.

## Latence production

Trente dry-runs identiques ont été exécutés sur cette fenêtre de taille 1 :

| Mesure | Résultat |
|---|---:|
| P50 | 434,591 ms |
| P95 | 519,885 ms |
| P99 | 1 715,433 ms |
| maximum | 1 715,433 ms |
| identités d'évaluation distinctes | 1 |

Le P95 respecte la gate Phase 5 de 750 ms. Le P99 reflète un unique outlier sur
30 échantillons ; ces chiffres qualifient la mécanique shadow sur un snapshot,
pas un SLO de trafic public ni une grande fenêtre.

## Coût et complexité

- aucun service, index ou stockage vectoriel supplémentaire ;
- PostgreSQL existant uniquement, avec deux tables append-only ;
- proxy sémantique déterministe sans appel externe ;
- une migration réversible, un writer OFF par défaut et un replay borné ;
- coût infrastructurel incrémental observé : **aucune ressource dédiée**.

Un vrai backend vectoriel devra battre cette baseline sur le même holdout et
sur un corpus production plus représentatif avant toute adoption.

## Gate

P5I est terminale dans le périmètre shadow. Les limitations
`SINGLE_PRIMARY_PRODUCT_SHADOW_SAMPLE`, `NO_REAL_VECTOR_BACKEND` et
`NO_PUBLIC_TRAFFIC_SLO` restent explicites et n'autorisent aucune promotion du
lecteur public.
