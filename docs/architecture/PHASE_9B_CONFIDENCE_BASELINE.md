# FILON — Phase 9B Confidence Baseline

- Observation source : **2 septembre 2026**
- Schéma de production d'entrée : `d1a9c3e5f7b0`
- Source Phase 8 : **reçu Offer Optimization shadow qualifié**
- Payload brut publié : **aucun**

## Signaux réellement disponibles

Les phases précédentes conservent des états, motifs, preuves, décisions et
digests déterministes. Elles ne fournissent pas encore de corpus de résultats
binaires de production indépendant permettant d'estimer des fréquences de
succès. Aucun profil empirique de production n'est donc ratifié pour les cinq
dimensions Confidence.

La présence d'une décision, d'un rang ou d'un nombre de preuves ne devient pas
une probabilité. En particulier :

- le score lexical/sémantique ne vaut pas Retrieval Confidence ;
- une décision Entity Resolution ne vaut pas Entity Match Confidence ;
- un nombre d'attributs connus ne vaut pas Attribute Confidence ;
- le statut Offer Truth ne vaut pas Offer Confidence ;
- une sélection Offer Optimization ne vaut pas Decision Confidence ;
- Evidence Coverage reste une complétude non probabiliste.

## Conclusion de baseline

Le replay initial doit s'abstenir avec cinq dimensions `UNKNOWN` et une
couverture `UNKNOWN`. Cette abstention est la seule sortie honnête tant que des
profils empiriques de production, versionnés et suffisamment soutenus,
n'existent pas.

Limites : `NO_PRODUCTION_CALIBRATION_PROFILE`,
`NO_INDEPENDENT_PRODUCTION_OUTCOME_LABELS`,
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING`.
