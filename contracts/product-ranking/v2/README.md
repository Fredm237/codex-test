# Product Ranking v2

Ce contrat permet un classement factuel lorsque les seules dimensions
objectivement prouvées sont l'adéquation à la requête (`need_fit`) et la
couverture de preuve (`evidence`).

Règles fermées :

- seuls les candidats `ELIGIBLE` du Constraint Engine sont classés ;
- `need_fit` et `evidence` doivent être connus, bornés et sourcés ;
- `product_quality` et `value` peuvent rester `UNKNOWN` et ne reçoivent alors
  aucun score ;
- les poids connus sont renormalisés, sans valeur neutre ou moyenne inventée ;
- une valeur déclarée connue mais invalide ou non sourcée ferme le classement ;
- chaque classement partiel porte `evidence_scoped_partial_ranking` et nomme
  explicitement ses dimensions inconnues ;
- ce résultat ne constitue ni une note de qualité produit, ni une sélection
  d'offre, ni un verdict BUY/WAIT ;
- commission, affiliation, contexte brut et profil utilisateur restent hors
  contrat.

L'exemple est synthétique. L'activation publique reste gouvernée par les reçus
de promotion V2.
