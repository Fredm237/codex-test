# FILON — bascule publique V2 uniquement

- Date : **10 septembre 2026**
- Cible : **V2 seule sur les routes d'achat publiques**
- Frontend : **expérience Phase 19**
- Fallback automatique Core V1 : **interdit lorsque le switch est ON**

## Contrat public

`V2_ONLY_PUBLIC_ENABLED=true` exige `V2_CHAIN_MODE=public`. Dans cet état :

- `/api/advise` et `/api/advise/stream` ne calculent pas Core V1 ;
- la recherche exécute P5 Retrieval, P6 Constraints, P7 Ranking v2, P8 Offer
  Optimization, P9 Confidence et P10 BUY/WAIT ;
- seules les options portant prix, devise, stock, marché et fraîcheur prouvés
  traversent la frontière publique ;
- si la preuve manque, V2 retourne une abstention explicite ;
- aucune étape d'analyse simulée ni aucune offre de démonstration n'est émise ;
- `BUY_NOW` et `WAIT` restent absents tant que l'optimisation et la confiance
  ne disposent pas des preuves nécessaires.

La verticale `general` couvre les recherches sans marqueur catégoriel explicite
sans les forcer artificiellement dans smartphones, audio, mode ou pneus.

## Retour d'urgence

Core V1 reste présent dans le binaire uniquement comme retour opérateur. Remettre
`V2_ONLY_PUBLIC_ENABLED=false` rétablit l'ancien routeur sans migration destructive
ni perte de données. Il ne s'agit pas d'un fallback automatique servi aux
utilisateurs lorsque V2 seule est active.

## Preuves exigées après déploiement

1. sondes application, PostgreSQL et Redis vertes ;
2. en-tête `X-Filon-Engine: v2-only` sur le flux public ;
3. une recherche couverte rend uniquement des offres courantes ;
4. une recherche sans preuve rend `real=false` et zéro carte ;
5. aucune trace d'exécution Core V1 sur ces deux requêtes ;
6. frontend public chargé et proxy SSE fonctionnel ;
7. audit de dépendances frontend sans vulnérabilité connue.
