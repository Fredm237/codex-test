# Constraint Engine v1

Ce contrat décrit le filtre déterministe placé entre Hybrid Retrieval et le
futur ranker. Il ne choisit pas le « meilleur » produit et ne produit aucun
score.

Règles fermées :

- une contrainte dure `UNSATISFIED` exclut le candidat ;
- une contrainte dure requise `UNKNOWN` rend le candidat `UNKNOWN`, donc non
  éligible au ranking ;
- toutes les contraintes dures doivent être `SATISFIED` ou `NOT_APPLICABLE`
  pour obtenir `ELIGIBLE` ;
- les préférences restent des observations séparées et ne peuvent jamais
  réintroduire un candidat `EXCLUDED` ou `UNKNOWN` ;
- aucun contexte brut ni profil utilisateur n'est persisté ; seul un digest
  stable et les résultats sourcés peuvent être écrits en shadow.

Les exemples sont entièrement synthétiques. Le contrat ne modifie aucun
lecteur public.
