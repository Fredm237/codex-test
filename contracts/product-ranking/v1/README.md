# Product Ranking v1

Ce contrat classe uniquement des identités produit déjà déclarées `ELIGIBLE`
par le Constraint Engine. Il ne choisit aucune offre et ne reçoit aucun signal
de commission.

Règles fermées :

- `EXCLUDED` et `UNKNOWN` ne sont jamais classés ;
- Need Fit, Product Quality, Value et Evidence doivent être connus et sourcés ;
- une dimension absente, invalide ou conflictuelle produit `UNRANKABLE` ;
- les poids sont propres à la verticale ;
- les égalités sont départagées de façon déterministe par l'identité ;
- aucun contexte brut, profil personnel ou signal commercial n'est persisté ;
- l'absence de labels humains externes reste une limitation explicite et non
  bloquante ; elle n'est jamais présentée comme une validation humaine.

Les exemples sont synthétiques. Aucun lecteur public n'est modifié.
