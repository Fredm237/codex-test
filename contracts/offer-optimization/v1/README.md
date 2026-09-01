# Offer Optimization v1

Ce contrat sélectionne une offre uniquement pour le produit classé numéro un
par Product Ranking. L'objectif est lexicographique et auditable : coût total
minimal, puis fiabilité marchand, fraîcheur et identifiant stable.

Une offre n'est optimisable que si son snapshot Offer Truth est `VERIFIED`, son
stock est explicitement disponible et le prix, la livraison, la fraîcheur et la
fiabilité sont connus, sourcés et cohérents dans la même devise.

Commission, taux d'affiliation, statut affilié, enchère publicitaire et revenu
FILON sont absents du contrat. Une donnée inconnue produit une abstention ; elle
n'est jamais remplacée par zéro, une moyenne ou un score neutre.
