# Personal Stylist v1

Le moteur Phase 16 compose au plus trois propositions à partir d'un contexte
explicitement déclaré et de preuves courantes. Il privilégie les pièces du
dressing avant toute offre marchande.

## Invariants

- occasion, instant, lieu, style et météo applicables sont nécessaires ;
- une météo absente, périmée ou visant un autre lieu provoque l'abstention ;
- aucune aptitude d'un vêtement à la pluie, au froid ou à la chaleur n'est
  inventée ;
- une pièce possédée a un coût marginal nul et exclut l'achat du même rôle ;
- tout ajout marchand exige identité de rôle, taille, stock, prix, devise,
  horodatage et URL sûrs ;
- aucun mélange de devise ni conversion implicite ;
- aucun score de compatibilité n'est publié sans calibration indépendante ;
- aucun contenu de dressing n'est transmis ou persisté par ce moteur pur.

Ce contrat est local et shadow-only. Il ne crée ni table, writer, lecteur public
ou Cron.
