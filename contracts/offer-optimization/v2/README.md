# Offer Optimization v2

Ce contrat sélectionne une offre uniquement pour le produit classé numéro un
par Product Ranking. L'objectif auditable est : coût livré minimal (`prix +
livraison - cashback`), puis fiabilité marchand, fenêtre de retour, fraîcheur
et identifiant stable.

Prix, livraison, cashback, retours, disponibilité, fiabilité et fraîcheur
doivent tous être connus et sourcés. Un cashback absent n'est jamais remplacé
par zéro. Une politique de retour refusée rend l'offre inéligible ; une période
de retour inconnue la rend inoptimisable.

Commission, taux d'affiliation, statut affilié, enchère publicitaire et revenu
FILON restent absents du contrat. La version v1 demeure un artefact historique
et n'est plus la politique active.
