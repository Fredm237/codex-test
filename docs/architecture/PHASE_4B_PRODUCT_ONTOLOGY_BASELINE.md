# FILON — Phase 4B Product Ontology Baseline

- Date de lecture : **1er septembre 2026**
- Statut : **BASELINE AGRÉGÉE PRÉPARÉE — ÉCRITURES INTERDITES AVANT P3H**
- Portée : code legacy, corpus de régression local et agrégats publics
- Données brutes de production : **NON LUES**
- Writer Product Ontology : **ABSENT / NON ACTIVÉ**

## Conclusion

La taxonomie existante est une base de compatibilité solide, mais elle n'est
pas une ontologie produit. Elle sait ranger de nombreux libellés dans des
rayons ; elle ne démontre pas encore de façon uniforme le type de produit, son
rôle, ses attributs, ses relations ou ses facettes. La Phase 4 doit donc
conserver ces règles comme signaux et régressions, sans les promouvoir comme
vérité centrale.

## Baseline locale

| Surface | Constat |
|---|---:|
| Départements legacy | 7 |
| Catégories legacy | 27 |
| Sous-catégories déclarées | 136 |
| Catégories sans sous-catégorie déclarée | 3 |
| Régressions taxonomie/rôle/golden exécutées | 808 vertes |
| Contrats Phases 1 à 4 exécutés | 92 verts |
| Cas du golden sémantique | 14 |

Le golden sémantique couvre actuellement quatre `main_product`, deux
`replacement_part`, deux `consumable`, puis un cas pour chacun de `service`,
`screen_protector`, `protective_case`, `bundle`, `bag` et `accessory`. Ce petit
corpus protège des comportements historiques utiles, mais il ne peut pas
qualifier à lui seul le roster fermé Product Role v1.

## Baseline publique de production

Les endpoints publics observés indiquaient :

- 2 025 852 offres et 597 846 produits ;
- 1 841 120 offres visibles, avec image et marchand autorisé, réparties dans
  les 27 catégories publiées ; ce total n'est **pas** un taux de couverture du
  catalogue complet, car le périmètre du dénominateur diffère ;
- 136 sous-catégories publiées ;
- 46,20 % des offres visibles concentrées dans les cinq premières catégories ;
- 169 546 offres visibles en Téléphonie, dont 126 501 dans « Coques &
  Protections » et 16 475 dans « Smartphones » ;
- 65 039 offres dans la catégorie générique « Mode ».

Ces agrégats ne contiennent aucun payload marchand ni donnée utilisateur. Ils
montrent toutefois qu'une catégorie seule ne distingue pas sûrement le produit
principal de l'accessoire : dans le rayon Téléphonie visible, les coques et
protections représentent environ 74,6 % du volume.

## Écarts structurels

### Rôle produit

Le moteur legacy expose dix-neuf libellés détaillés. Plusieurs sont des
sous-types utiles (`protective_case`, `screen_protector`, `charger`, `cable`,
`battery`, `adapter`, `stand`, `mount`, `holder`, `bag`) mais ne correspondent
pas directement au roster fermé Phase 4.

Deux comportements doivent disparaître du futur writer ontologique :

1. un bien physique sans signal contraire devient aujourd'hui
   `main_product` avec une confiance moyenne ; l'ontologie devra s'abstenir en
   `UNKNOWN` sans preuve positive du rôle principal ;
2. `accommodation` devient `service` et `digital_content` devient `software`,
   alors que le contrat Phase 4 conserve `ACCOMMODATION` et
   `DIGITAL_CONTENT` comme rôles distincts.

### Relations

Le moteur legacy ne produit que `compatible_with`, `replacement_for` et
`included_in`, avec une cible textuelle observée. Cette prudence est correcte
et doit être conservée. Le contrat Phase 4 ajoute des types explicites, mais
aucune cible ne pourra devenir canonique sans résolution d'entité positive.

### Attributs et facettes

Le pilote actuel extrait seulement le stockage, l'état reconditionné/occasion
et la personnalisation par gravure. Il ne fournit pas encore de représentation
générale typée des unités, ni les huit familles de facettes du mandat : cas
d'usage, audience, compatibilité, style, matière, saison, occasion et fonction.

### Taxonomie

Les 808 régressions vertes prouvent la stabilité du système existant, pas son
exactitude ontologique globale. Le fichier de taxonomie contient de nombreuses
règles ordonnées, multilingues et parfois bornées à un marchand. Ces règles
restent des signaux auditables de fallback ; une correspondance regex ou une
catégorie marchande ne doit pas devenir automatiquement un concept connu.

## Corpus requis pour P4C

Le benchmark taxonomy/role devra au minimum stratifier :

- produit principal contre accessoire dans une même catégorie ;
- pièce de remplacement, consommable, bundle, service, contenu numérique et
  hébergement ;
- compatibilité textuelle sans cible canonique ;
- libellés ambigus, négations, bundles incomplets et catégories marchandes
  contradictoires ;
- valeurs absentes, unités invalides, attributs conflictuels et textes
  multilingues ;
- cas historiques merchant-specific et familles à fort volume ;
- abstentions attendues, en particulier faux `PRIMARY_PRODUCT` et fausse
  compatibilité.

Le score devra publier séparément exactitude, couverture, abstention, faux
`PRIMARY_PRODUCT`, fausses relations canoniques et intervalles d'incertitude.

## Limites et gate

Les agrégats publics ne donnent ni la distribution réelle des rôles, ni la
couverture des attributs, ni le volume non classé sur un périmètre strictement
comparable. Ces mesures nécessiteront un audit borné après P3H, puis un replay
shadow P4F. Elles ne peuvent pas être inventées à partir des endpoints publics.

P4B est donc suffisamment préparée pour définir P4C, mais reste **non terminale
pour la production** tant que Phase 3 n'a pas atteint son état GO.
