# Personal Commerce Model v1

La Phase 18 choisit une solution complète pour un objectif personnel à partir
des sorties déjà qualifiées de la chaîne V2 et du Solution Composer.

## Invariants

- consentement `personal_commerce` obligatoire ;
- seules des préférences explicites, traçables et non contradictoires sont lues ;
- aucune préférence n'est déduite d'un clic, d'une absence ou d'un attribut
  sensible ;
- les solutions possédées sans achat sont prioritaires ;
- les solutions incomplètes, contraintes inconnues, hors budget ou hors devise
  sont rejetées ;
- une action marchande conserve exactement la preuve BUY/WAIT amont ;
- commission et affiliation ne participent jamais au choix ;
- la politique est lexicographique et ne publie aucun score d'utilité ;
- la sortie ne retient ni objectif brut ni valeur de préférence brute.

Actions possibles : `USE_WHAT_YOU_OWN`, `BUY`, `WAIT`, `ABSTAIN`.
