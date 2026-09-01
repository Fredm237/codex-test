# FILON — Phase 6F Constraint Engine shadow

- Date : **1er septembre 2026**
- Migration : `a8d6f0b2c4e7`
- Parent : `f7c5e9a1b3d6`
- Flag : `CONSTRAINT_ENGINE_SHADOW_ENABLED=false`
- Lecteurs publics : **inchangés**

## Expansion

La migration ajoute :

- `constraint_evaluation_runs`, identité de run, digest du contexte, résultat,
  compteurs et instant d'évaluation ;
- `constraint_candidate_evaluations`, statut candidat, résultats durs,
  préférences et motifs.

Le schéma interdit la conservation du contexte brut et ne possède aucune
colonne de score. Les lignes pointent vers les runs et candidats Hybrid
Retrieval existants ; le composant ne peut donc pas inventer un candidat.

## Writer et replay

Le writer est sec par défaut, append-only et idempotent. Un apply exige le flag
process-local, un instant UTC fixe, une fenêtre bornée et un mapping complet
des candidats. Un replay identique réutilise la ligne existante ; une
divergence de digest ou de cardinalité échoue fermée.

Le replay production projettera uniquement les faits prouvables des offres
attachées : prix atomique, disponibilité et safety. Une absence d'offre ou de
stock reste `UNKNOWN`. Aucun contexte personnel, pays, budget ou préférence
n'est inventé pour la qualification.

## Rollback

Le rollback opérationnel consiste à maintenir le flag à `false`. L'ancien
lecteur ignore les nouvelles tables. Aucun downgrade n'est nécessaire ; la
migration technique reste réversible en environnement jetable.
