# Fashion Expert v1

Fashion v1 compose uniquement à partir d'offres Core courantes et de contraintes
explicitement déclarées. Il peut recommander une composition minimale ou
s'abstenir. Il ne certifie ni style, ni coupe, ni taille, ni matière, ni adéquation
à une occasion.

## Invariants

- prix positif, devise reconnue, stock explicite et observation ≤ 72 h ;
- budget en EUR : aucune offre d'une autre devise n'est utilisée ;
- aucun assemblage entre devises ;
- identité, prix, stock et lien proviennent du Core ;
- occasion, couleur et style sont enregistrés comme intentions, pas comme faits ;
- `style_score`, `confidence_score` et tout score de relation restent `null` sans
  vérité terrain humaine indépendante ;
- une absence de pièce principale démontrable produit une abstention ;
- les trois flags Intelligence/Fashion/Outfit restent OFF par défaut.

L'absence de vérité terrain humaine externe est une limitation explicite et
non un prétexte pour fabriquer une probabilité :
`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING`.
