# FILON — Phase 7D Product Ranking déterministe

- Date : **1er septembre 2026**
- Mode : **shadow-only**
- Version : `product-ranking-policy/v1`
- Lecteurs publics : **inchangés**

## Moteur

Le moteur reçoit des identités produit déjà évaluées par le Constraint Engine.
Il classe uniquement les candidats `ELIGIBLE` dont les quatre dimensions sont
connues, comprises entre 0 et 1 et reliées à au moins une référence de preuve.

Les poids sont figés par verticale pour smartphones, laptops, audio, fashion,
électroménager/HVAC et pneus. La somme vaut toujours 1. Les égalités sont
résolues de manière stable par l'identité produit ; un digest canonique permet
de détecter toute divergence.

## Fail-closed

- `EXCLUDED` ou `UNKNOWN` en entrée devient `INELIGIBLE`, sans réintroduction ;
- une dimension absente, inconnue, invalide, conflictuelle ou non sourcée
  devient `UNRANKABLE` ;
- sans candidat classable, le résultat est `ABSTAINED` ou
  `NO_ELIGIBLE_PRODUCT` ;
- aucune valeur de repli et aucun score neutre fictif ne sont utilisés.

## Séparation produit / offre

Le contrat ne contient ni offre gagnante, ni marchand, ni commission, ni taux
d'affiliation. Le prix peut contribuer à une future preuve de `value`, mais une
offre commerciale ne peut jamais modifier le rang produit. Le choix de la
meilleure offre appartient à la Phase 8.

## Limite de qualification

Les tests et le benchmark prouvent les invariants d'ingénierie. Ils ne prouvent
pas que les poids reproduisent les préférences humaines réelles. Cette limite
reste `NOT_INDEPENDENTLY_VALIDATED`, mais elle est non bloquante conformément à
la décision fondateur : aucune annotation humaine externe ne sera attendue.
