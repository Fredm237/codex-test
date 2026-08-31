# ADR-007 — Contrat de décision Entity Resolution v1

- Statut : **accepté pour implémentation shadow**
- Date : 1er septembre 2026
- Portée : Phase 2 Entity Resolution
- Compatibilité : lecteurs Core v1 inchangés

## Contexte

Phase 1 prouve 330 offres par GTIN exact dans un lot réel de 1 000 offres et
laisse 670 offres sans GTIN en quarantaine. Entity Resolution doit augmenter
la couverture par MPN, modèle et attributs structurés sans transformer la
similarité lexicale en identité et sans dégrader le resolver exact-GTIN.

Une confiance numérique seule n'exprime ni la nature de la preuve, ni son
scope, ni les conflits. Elle ne peut donc pas gouverner une fusion.

## Décision

### 1. États de décision

| État | Minimum | Canonical ID | Effet Phase 2 |
|---|---|---:|---|
| `EXACT_VERIFIED` | GTIN global exact, valide, sourcé, sans conflit | requis | shadow |
| `HIGH_CONFIDENCE` | au moins deux preuves structurées fortes, sans preuve exacte ni conflit | requis | shadow |
| `PROBABLE` | candidat utile mais preuve insuffisante | interdit | candidat seulement |
| `AMBIGUOUS` | plusieurs candidats et conflit explicite | interdit | abstention |
| `UNRESOLVED` | aucun candidat suffisamment prouvé | interdit | abstention |

Un `canonical_id` doit appartenir à la liste bornée `candidate_ids`. Cette
contrainte relationnelle est vérifiée par l'implémentation ; le JSON Schema
impose déjà la présence ou l'absence du canonical ID selon l'état.

### 2. Hiérarchie des preuves

- `exact` : GTIN global seulement dans v1 ;
- `strong` : MPN dans une Brand prouvée, modèle structuré ou attribut de
  variante structuré ;
- `weak` : titre, image, similarité sémantique et libellé non corroboré.

Titre, image et similarité ne peuvent être que `candidate_only` ou
`corroborating`. Ils ne peuvent jamais être une preuve exacte ni lever un
conflit d'identifiant ou d'attribut.

Merchant SKU et source product ID restent scopés. Leur égalité entre scopes
distincts n'est jamais une preuve globale.

### 3. Vetos

Une fusion favorable est interdite si l'un de ces conflits subsiste :

- GTIN valides différents ;
- MPN identique sans même Brand prouvée ou MPN différents dans le même scope ;
- modèle structuré contradictoire ;
- stockage, mémoire, taille, capacité, couleur, génération, condition,
  édition ou quantité de pack contradictoire ;
- produit principal contre accessoire, consommable, bundle ou pièce ;
- scope d'identifiant incompatible ;
- plusieurs candidats non départageables.

Un score élevé ne contourne jamais un veto. La sortie devient `AMBIGUOUS` ou
`UNRESOLVED` et reste sans identité canonique.

### 4. Score et politique

`confidence_score` est une mesure secondaire et versionnée. Le contrat exige
`resolver_version` et `policy_version` afin qu'une décision soit rejouable.
Les seuils HIGH/PROBABLE ne sont pas figés dans le contrat : P2C doit les
ratifier sur le benchmark et les distributions réelles.

Le target initial de sécurité est la borne supérieure Wilson 95 % du faux
merge **≤ 0,5 %**, avec zéro conflit connu promu favorablement. Ce target est
un bootstrap explicite issu du gate Phase 1 ; P2C peut le rendre plus strict,
jamais plus permissif sans ADR et preuve nouvelles.

### 5. Provenance

Chaque élément de preuve porte raw, source, horodatage, signal, champ, valeur
normalisée, force, rôle, transformation et version. Une décision sans preuve
est invalide. Un conflit cite ses raws concernés et n'écrase aucune valeur.

### 6. Compatibilité et rollback

Le contrat est additif dans `contracts/entity-resolution/v1`. Il ne modifie ni
les contrats Product Identity v1 figés, ni les tables, ni les lecteurs Core.
P2A ne déploie aucun writer. Le rollback consiste à ne pas consommer ce
contrat ; aucune donnée ou migration n'est à retirer.

## Conséquences

- le resolver exact-GTIN Phase 1 reste autoritatif pour `EXACT_VERIFIED` ;
- le futur resolver multi-signal doit produire preuves et conflits, pas un
  score opaque ;
- HIGH/PROBABLE restent shadow jusqu'au gate P2G ;
- augmenter l'abstention est acceptable si cela évite un faux merge ;
- les lecteurs publics ne changent pas pendant Phase 2.

## Rejeté

- seuil unique sur similarité de titre ;
- fusion titre + marque sans MPN/modèle structuré ;
- image ou embedding comme preuve primaire ;
- MPN global sans scope Brand ;
- Merchant SKU global ;
- canonical ID pour `PROBABLE`, `AMBIGUOUS` ou `UNRESOLVED` ;
- score capable de contourner un conflit.
