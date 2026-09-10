# FILON — Product Ranking v2 evidence-scoped

- Date : **10 septembre 2026**
- Statut : **QUALIFIÉ LOCALEMENT / REPLAY PRODUCTION REQUIS**
- Contrat : `contracts/product-ranking/v2`
- Politique : `product-ranking-policy/v2`
- Lecteur public : **inchangé**
- Verdict BUY/WAIT : **inchangé et bloqué**

## Problème mesuré

L'audit agrégé de production a trouvé 560 candidats déclarés
`ELIGIBLE_CANDIDATES` par le Constraint Engine mais 0 produit classé. Les 560
candidats étaient `ABSTAINED` par Product Ranking v1 parce que le replay
persistant déclarait les quatre dimensions inconnues.

Le catalogue possède cependant déjà deux preuves factuelles utilisables sans
inventer de préférence : le rang de récupération Hybrid Retrieval et les
références de sources persistées pour chaque candidat. Le lot v2 transforme
exclusivement ces preuves en `need_fit` et `evidence`.

## Politique v2

- `need_fit` et `evidence` sont obligatoires, bornés et sourcés ;
- `product_quality` et `value` restent `UNKNOWN` tant qu'aucune preuve dédiée
  n'existe ;
- une dimension inconnue ne reçoit jamais une moyenne ou un score neutre ;
- les poids sont renormalisés uniquement sur les dimensions connues ;
- tout fait invalide, conflictuel ou déclaré connu sans source bloque le
  candidat ;
- le résultat partiel nomme les dimensions inconnues avec
  `evidence_scoped_partial_ranking` ;
- commission, marchand, offre gagnante, profil utilisateur et contexte brut
  restent hors contrat.

Ce classement ordonne des candidats factuels. Il ne prétend pas mesurer la
qualité intrinsèque du produit, choisir une offre ni produire `BUY_NOW` ou
`WAIT`.

## Quality Lab autonome

Le holdout v2 couvre 6 048 cas déterministes répartis entre sept verticales et
trois locales : preuve complète, dimensions optionnelles inconnues, preuve
requise inconnue, fait requis non sourcé, fait optionnel invalide, candidat
inéligible, mutation commerciale et égalité stable.

Les gates exigent notamment :

- exactitude top-1 de 100 % contre l'oracle de politique indépendant ;
- borne basse Wilson 95 % d'exactitude d'ordre au moins égale à 0,995 ;
- zéro candidat classé si une preuve requise manque ;
- zéro candidat classé si un fait est invalide ou non sourcé ;
- divulgation complète des dimensions inconnues sur 100 % des classements
  partiels ;
- provenance complète, déterminisme et invariance à la commission à 100 %.

La limite `NO_EXTERNAL_HUMAN_GROUND_TRUTH` reste explicite et non bloquante :
le Quality Lab prouve les règles factuelles, pas une préférence humaine
subjective.

## Gate production restant

La production ne peut être déclarée qualifiée par cette preuve locale. Le lot
doit être déployé avec la portée publique actuelle inchangée, puis exécuté en
shadow par `dry-run → apply unique → replay identique` sur une fenêtre bornée.
Le reçu attendu doit prouver : au moins un produit classé à partir de preuves
persistées, zéro réintroduction d'un candidat exclu, zéro score pour une
dimension inconnue, identités de résultat stables et aucune modification du
lecteur public.
