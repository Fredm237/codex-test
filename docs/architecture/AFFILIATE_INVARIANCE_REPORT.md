# FILON — rapport d'invariance du classement affilié

Date : 29 août 2026
Commit vérifié : `987d4b1`

## Décision

**GO local borné pour la séparation testée entre classement et projection
affiliée. NO-GO pour une affirmation de neutralité commerciale absolue ou
d'absence d'effet sur le prix final.**

Le contrat `CoreOfferSnapshot` ne porte aucun taux commercial et sa clé de rang
reste identique lorsque seuls les liens projetés changent. Au niveau du reranker
Assistant, deux barèmes synthétiques inversés conservent exactement le même
contexte, le même gagnant et le même ordre d'offres. La projection affiliée
simulée modifie ensuite les liens, et seulement les liens.

## Scénario contrôlé

Le test `AFFILIATE_INVARIANCE_TEST` exécute deux passages séquentiels avec les
mêmes identifiants, noms, prix, devises, marchands, liens source, besoin, budget
et locale :

| Offre | Premier barème synthétique | Barème inversé |
|---|---:|---:|
| `101` / Alpha | 900 points de base | 0 |
| `202` / Beta | 0 | 1 200 points de base |

Le fournisseur de classement est déterministe et place volontairement l'offre
`202` avant l'offre `101`. Cela démontre qu'une offre non rémunérée peut rester
première alors qu'une offre moins bien classée est rémunérée. Après inversion,
l'ordre reste `202`, `101`.

Les assertions vérifient simultanément que :

- les taux injectés sont bien `900/0`, puis `0/1200` ;
- les messages complets et le payload du reranker sont identiques ;
- aucun champ `commission`, `affiliate`, `payout` ou `revenue` n'atteint ce
  contexte ;
- la construction des liens intervient après la complétion du reranking ;
- les liens changent exactement par `offer_id` ;
- l'intégralité du résultat hors champ `link` reste identique ;
- la clé de rang Core reste identique malgré deux variantes de lien commercial.

## Vérification indépendante

- worktree détaché frais sur `987d4b1` ;
- Python 3.12.13 ;
- tests dédiés : **2 réussis, 0 échec** ;
- suite backend complète : **1 241 réussis, 0 échec**, avec 7 avertissements
  historiques `datetime.utcnow()` ;
- aucun réseau, taux Awin réel, cache distant ou état global Awin utilisé ;
- aucun fichier local protégé inclus dans le commit.

## Limites obligatoires

1. Les taux sont synthétiques. FILON n'ingère actuellement aucun barème éditeur
   réel dans ce parcours.
2. La preuve couvre la clé de rang Core actuelle et
   `_rank_real_products`/construction des cartes Assistant, pas tous les moteurs,
   clients ou parcours historiques.
3. Elle ne mesure pas la couverture des marchands, leur inclusion en amont, un
   placement sponsorisé, un EPC, un payout ou une priorité commerciale manuelle.
4. Le fournisseur déterministe garantit un gate de CI reproductible ; il ne
   mesure pas la stabilité statistique d'un LLM réel.
5. Le panier marchand, les frais, l'éligibilité et le prix final ne sont ni lus
   ni comparés. Le claim « le prix n'augmente jamais » reste interdit.
6. Le cashback ou une promotion client est distinct d'une commission éditeur et
   peut légitimement modifier le coût effectif dans un autre parcours.

La seule conclusion défendable est donc : **dans la clé Core et le reranker
Assistant testés, des taux synthétiques ne modifient pas le classement à offres
fixes.**

## Rollback

Le lot ajoute uniquement des tests et de la documentation. Il ne modifie ni le
runtime, ni les contrats publics v1, ni la base. Son rollback consiste à revenir
sur `987d4b1` ; aucune migration ni restauration de données n'est nécessaire.
