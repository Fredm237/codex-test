# Confidence v1

Ce contrat sépare cinq probabilités calibrables de la couverture des preuves :

- `RETRIEVAL_CONFIDENCE`
- `ENTITY_MATCH_CONFIDENCE`
- `ATTRIBUTE_CONFIDENCE`
- `OFFER_CONFIDENCE`
- `DECISION_CONFIDENCE`
- `evidence_coverage`, ratio de complétude non probabiliste

Une dimension `CALIBRATED` exige un profil empirique, un bucket soutenu et une
provenance. Une dimension sans profil reste `UNKNOWN`; aucune valeur `0.5` ou
agrégation additive ne la remplace. `DECISION_CONFIDENCE` exige son propre
profil et ne peut pas être dérivée des quatre autres dimensions.

Les exemples sont entièrement synthétiques. Le contrat ne conserve ni contexte
brut, ni payload d'offre, ni donnée utilisateur.
