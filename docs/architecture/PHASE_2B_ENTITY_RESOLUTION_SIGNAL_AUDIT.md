# FILON — Phase 2B Entity Resolution Signal Audit

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — AUDIT PRODUCTION EN LECTURE SEULE**
- Révision Alembic observée : `b3e1a7c4d9f2`
- Corpus raw : **1 000 offres, un feed Awin, un marchand**
- Corpus Core : **échantillons déterministes bornés, maximum 500 offres par verticale**
- Lecteurs publics et writers : **inchangés**

## Verdict

Le corpus raw réellement rejouable ne contient pas encore les signaux
structurés nécessaires à une décision `HIGH_CONFIDENCE` au-delà du GTIN. Il
fournit Brand, GTIN lorsqu'il existe, identifiant produit marchand, titre,
image et taxonomie marchande, mais aucun MPN, modèle structuré ni attribut de
variante structuré.

Les titres contiennent des fragments lexicaux utiles pour générer des
candidats. Ils ne constituent ni une ground truth, ni une preuve forte et ne
peuvent pas être promus par simple expression régulière. Le contrat
[ADR-007](ADR-007-ENTITY-RESOLUTION-DECISION-CONTRACT.md) reste donc
fail-closed : les 670 raws sans GTIN demeurent `UNRESOLVED` tant qu'une source
structurée supplémentaire n'est pas disponible.

P2B qualifie la disponibilité des données, pas la qualité d'un resolver. Aucun
merge, writer, variable Railway ou lecteur public n'a été modifié pendant
l'audit.

## Méthode

Deux populations ont été relues directement dans PostgreSQL :

1. les 1 000 `RawSourceRecord` capturés et observés pendant P1E, seuls raws
   actuels disposant d'une provenance rejouable de bout en bout ;
2. les `Offer` Core historiques, échantillonnés par ordre d'identifiant avec
   une limite de 500 lignes par sous-catégorie, afin de mesurer la présence
   indicative des signaux selon les verticales.

Cet échantillonnage Core n'est ni aléatoire, ni une ground truth. Il mesure la
présence de champs et de motifs, pas leur exactitude. Les offres Core
historiques ne peuvent pas être injectées artificiellement dans le pipeline
shadow : elles ne portent pas toutes la chaîne raw/observation requise par le
contrat de provenance.

Pour le tableau Core :

- `GTIN plausible` signifie uniquement 8, 12, 13 ou 14 chiffres ; le checksum
  n'est pas validé dans cette mesure de présence ;
- `lien produit` signifie que l'offre porte un `product_id` Core existant ;
- `catégorie` mesure le libellé marchand non vide ;
- `capacité`, `dimension`, `code modèle` et `couleur` sont des détections
  lexicales candidates dans le titre ;
- un motif lexical peut être faux, ambigu ou décrire un accessoire. Il n'est
  jamais compté comme fait structuré ni preuve de fusion.

## Corpus raw réel et rejouable

### Portée

| Mesure | Résultat |
|---|---:|
| Raws | 1 000 |
| Marchands distincts | 1 |
| Feeds | 1 |
| Catégorie marchande | `Bijoux & Montres` |
| Raws avec EAN | 330 |
| Raws sans EAN | 670 |
| Sous-catégorie FILON `Bagues` | 1 |
| Sous-catégorie FILON `Montres` | 76 |
| Sous-catégorie inconnue | 923 |

### Schéma source observé

Les payloads portent exactement les clés suivantes :

`aw_deep_link`, `aw_product_id`, `brand_name`, `currency`, `ean`,
`in_stock`, `merchant_category`, `merchant_image_url`, `product_name` et
`search_price`.

Tous ces champs sont présents sur le lot ; 330 valeurs EAN sont renseignées.
Aucun champ structuré MPN, référence fabricant, modèle, capacité, stockage,
mémoire, taille, couleur, génération, édition, condition ou quantité de pack
n'est exposé par ce feed.

### Indices lexicaux dans les titres raw

| Motif candidat | Raws détectés | Interprétation autorisée |
|---|---:|---|
| Capacité ou stockage | 11 | génération de candidats seulement |
| Taille ou dimension | 191 | génération de candidats seulement |
| Forme ressemblant à un code modèle | 903 | **très bruité**, non fiable comme extraction |
| Couleur lexicale | 52 | corroboration candidate seulement |

La détection de 903 formes « code modèle » sur 1 000 titres de bijoux illustre
précisément le risque : une regex générale confond références, dimensions,
codes marchands et tokens de titre. Ce chiffre ne mesure pas 903 modèles
réels.

## Audit Core borné par verticale

| Sous-catégorie | N | Brand | GTIN plausible | GTIN distincts | Lien produit | Image | Catégorie | Physique | Marchands | Capacité | Dimension | Code modèle | Couleur |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Smartphones | 500 | 499 | 89 | 78 | 89 | 472 | 305 | 371 | 13 | 0 | 11 | 224 | 37 |
| Ordinateurs portables | 500 | 382 | 274 | 105 | 274 | 480 | 498 | 492 | 10 | 220 | 58 | 279 | 33 |
| Téléviseurs | 500 | 477 | 101 | 67 | 101 | 462 | 378 | 492 | 20 | 2 | 70 | 89 | 33 |
| Casques audio | 500 | 500 | 110 | 109 | 110 | 500 | 498 | 490 | 8 | 10 | 1 | 131 | 93 |
| Écouteurs | 500 | 483 | 25 | 17 | 25 | 450 | 451 | 493 | 8 | 18 | 6 | 135 | 35 |
| Enceintes | 500 | 479 | 96 | 85 | 96 | 464 | 298 | 500 | 16 | 15 | 46 | 227 | 72 |
| Barres de son | 73 | 51 | 44 | 31 | 44 | 73 | 72 | 73 | 8 | 0 | 2 | 44 | 5 |
| Platines & Hi-Fi | 348 | 339 | 91 | 73 | 91 | 348 | 252 | 346 | 16 | 7 | 65 | 166 | 69 |
| Gros électroménager | 500 | 493 | 153 | 125 | 153 | 496 | 500 | 500 | 10 | 11 | 34 | 26 | 111 |
| Petit électroménager | 500 | 490 | 247 | 237 | 247 | 494 | 393 | 500 | 13 | 153 | 39 | 193 | 57 |
| Aspirateurs | 500 | 434 | 257 | 212 | 257 | 496 | 426 | 500 | 16 | 72 | 31 | 219 | 48 |
| Climatisation & Chauffage | 500 | 492 | 357 | 296 | 357 | 499 | 418 | 500 | 13 | 75 | 183 | 174 | 140 |
| Pneus | 500 | 500 | 499 | 499 | 499 | 500 | 500 | 500 | 1 | 0 | 0 | 169 | 9 |

`Barres de son` et `Platines & Hi-Fi` comptaient respectivement 73 et 348
lignes dans la population disponible ; toutes ont été relues. La population
`Climatisation & Chauffage` compte 1 648 lignes, dont les 500 premières ont
été mesurées comme pour les autres grandes verticales.

## Lecture par signal

### Signaux exploitables immédiatement

- GTIN plausible, à revalider avec le contrat exact Phase 1 ;
- Brand lorsqu'elle est normalisée et sourcée ;
- Merchant ID + Awin product ID comme identifiant strictement scopé ;
- rôle produit, taxonomie et contexte marchand pour filtrer ou former des
  hard negatives ;
- titre et image pour générer une liste bornée de candidats.

### Signaux absents du raw contract actuel

- MPN ou référence fabricant structurée ;
- modèle fabricant structuré ;
- attributs de variante structurés : stockage, mémoire, capacité, taille,
  couleur, génération, édition et pack ;
- relation explicite produit principal/accessoire ;
- ground truth indépendante confirmant les regroupements non-GTIN.

### Conséquence

Avec le seul feed raw actuel, P2D peut construire des extracteurs shadow qui
produisent des **candidats**, des `unknown` et de la provenance. Il ne peut pas
fabriquer les deux preuves structurées fortes requises pour
`HIGH_CONFIDENCE`. Avant tout resolver favorable non-GTIN, il faut soit :

1. étendre les colonnes demandées aux feeds Awin lorsqu'elles existent ;
2. ajouter une source structurée indépendante portant MPN/modèle/attributs ;
3. conserver l'abstention lorsque ces données n'existent pas.

## Verticales de travail recommandées

L'ordre d'apprentissage proposé pour P2C/P2D est :

1. **Smartphones et ordinateurs portables** pour les hard negatives de
   capacité, stockage, génération et variante ;
2. **Pneus** comme contrôle à GTIN presque complet et forte répétition de
   motifs dimensionnels susceptibles d'être confondus avec des modèles ;
3. **Climatisation & Chauffage** et électroménager pour éprouver dimensions,
   capacité, rôle produit et taxonomie ;
4. audio pour les modèles, couleurs et accessoires ambigus.

Ce choix décrit la densité apparente de signaux dans un échantillon borné. Il
ne ratifie aucun taux de qualité et ne privilégie pas la couverture au
détriment du faux merge.

## Décision P2B

P2B est fermé avec les décisions suivantes :

- l'absence de signal structuré reste `unknown`, jamais favorable ;
- le titre, l'image et la similarité servent uniquement à la génération de
  candidats ou à une corroboration non décisive ;
- P2C doit construire un benchmark de hard negatives et ratifier les seuils
  avant tout score favorable ;
- P2D doit commencer par un inventaire/versionnage des extracteurs et par
  l'extension contrôlée du feed contract, sans writer canonique ;
- les 670 raws Phase 1 sans GTIN restent non résolus dans l'état actuel des
  preuves.

La prochaine gate est P2C : benchmark étendu, false merge Wilson 95 % sous le
target bootstrap de 0,5 %, zéro conflit connu promu et budget d'abstention
explicite.
