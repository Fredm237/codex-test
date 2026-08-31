# ADR-006 — Frontières Product Identity v1

- Statut : **accepté pour implémentation shadow**
- Date : 31 août 2026
- Portée : Phase 1 Product Identity
- Compatibilité : lecteurs Core v1 inchangés

## Contexte

Le Graph Phase 0 prouve une variante uniquement par GTIN exact. Il contient
déjà des tables Brand, Family, Model et Variant, mais Awin ne fournit pas
toujours une famille, un code modèle ou des attributs structurés. Promouvoir
le titre ou la marque normalisée en identité canonique créerait des faux
merges, particulièrement entre produit principal, accessoire, bundle et pièce
de remplacement.

La [baseline réelle](PHASE_1A_PRODUCT_IDENTITY_BASELINE.md) montre aussi que
la recherche lexicale n'est pas un roster de verticale fiable et que des
variantes orthographiques de marque entrent en collision après normalisation.

## Décision

### 1. Hiérarchie et signification

| Entité | Signification | Minimum de promotion v1 |
|---|---|---|
| Brand | organisation qui porte une marque | identifiant externe fiable ou assertion structurée corroborée ; jamais le titre seul |
| ProductFamily | gamme commerciale d'une Brand | relation explicite sourcée ; peut rester absente |
| ProductModel | modèle commercial stable | Brand prouvée + code modèle structuré/scopé ou relation externe exacte |
| Variant | configuration vendable précise | GTIN global exact v1 ; attributs inconnus restent absents |

Une Variant peut exister avec `model_id = null`. Un ProductModel peut exister
avec `family_id = null`. Ces absences sont des états valides, pas des erreurs à
combler par similarité.

### 2. Cycle de vérité

```text
RawSourceRecord
  → assertion sourcée
  → validation déterministe
  → candidat canonique ou quarantaine
  → promotion shadow versionnée
  → benchmark
  → lecteur futur, seulement après GO explicite
```

Une assertion n'est jamais une identité canonique par le simple fait d'avoir
été observée. Toute promotion conserve l'identifiant du raw, la source,
l'horodatage, la transformation et la version du resolver.

### 3. Scopes des identifiants

| Namespace | Scope | Règle |
|---|---|---|
| `gtin` | `global` | checksum et longueur valides ; une valeur, une Variant |
| `mpn` | `brand:<brand_id>` | jamais global sans Brand prouvée |
| `merchant_sku` | `merchant:<merchant_id>` | identité source seulement ; aucune fusion inter-marchands |
| `source_product_id` | `source:<source_type>:<source_ref>` | replay et provenance, pas preuve globale |

La première écriture de production reste GTIN-only. Les autres namespaces
sont contractuels mais restent sans writer tant que leur migration, leurs
collisions et leur benchmark ne sont pas qualifiés.

### 4. Merge et abstention

Un merge favorable exige une preuve positive compatible. Une valeur absente,
un titre similaire, une même catégorie ou une marque normalisée ne sont pas
des preuves suffisantes.

- même GTIN valide : même Variant ;
- GTIN différents : relation Model et Product `ambiguous` en v1 ;
- GTIN absent/invalide : `quarantine` ;
- identifiants contradictoires : `quarantine` ;
- MPN sans Brand prouvée : `quarantine` ;
- SKU identique chez deux marchands : aucune relation globale ;
- attributs différents sans identifiant global : aucune fusion ;
- unknown : reste unknown.

Les faux merges sont plus graves que les faux splits. Le système doit donc
préférer une abstention mesurable à une couverture inventée.

### 5. Attributs de variante

Les dimensions initiales admises sont : `color`, `storage`, `memory`, `size`,
`capacity`, `configuration`, `region`, `pack_quantity`, `condition` et
`edition`. Elles ne peuvent être persistées que comme assertions scalaires
sourcées. Une valeur contradictoire n'est pas écrasée ; elle crée un conflit
explicite ou reste hors de la projection canonique.

### 6. Roster de verticale

Le roster Phase 1 est déterminé par taxonomie FILON versionnée et rôle
`primary_product`. Les requêtes lexicales servent à produire des hard
negatives, pas à déclarer l'appartenance d'un produit à une verticale.

Ordre : pneus comme contrôle, smartphones et laptops, puis TV/audio, puis
électroménager. Fashion reste hors production.

### 7. Benchmark exact-product

Le gate Phase 1 doit inclure des cas multi-seed et des hard negatives :

- même GTIN sous titres/marques différents ;
- GTIN distincts avec titre identique ;
- stockage, couleur, taille et pack différents ;
- produit contre accessoire, bundle et pièce ;
- GTIN invalide, manquant ou contradictoire ;
- MPN identique sous Brand différente ;
- SKU identique sous marchands différents ;
- replay idempotent et provenance append-only.

Les oracles déterministes portent le statut
`DETERMINISTICALLY_VERIFIED`. Les dimensions non déterministes restent
`PROVISIONAL` ou `UNRESOLVED`. Aucune ligne n'est marquée human-validated.

Seuils initiaux :

| Gate | Seuil |
|---|---:|
| Exact Variant avec preuve globale | 100 % des cas déterministes |
| Faux merge sur hard negatives | 0 |
| Conflit promu favorablement | 0 |
| Provenance manquante après écriture | 0 |
| Replay non idempotent | 0 |
| Lecteur public v1 modifié | 0 |

Le seuil mandaté `EXACT PRODUCT MATCH ≥ 98 %` sera publié dans la
scorecard, mais un petit corpus synthétique ne doit pas masquer son intervalle
d'incertitude. Le gate fail-closed utilise les comptes et intervalles de
confiance appropriés, pas seulement une moyenne.

## Conséquences

- le writer exact-GTIN Phase 0 peut rester la première projection Variant ;
- Brand/Family/Model requièrent une couche d'assertions avant promotion ;
- l'élargissement MPN/SKU sera expand-only et opt-in ;
- une couverture initiale faible est acceptable et visible ;
- aucun endpoint public, ranking ou carte ne lit ce Graph avant la revue de
  sortie Phase 1 ;
- le rollback ordinaire coupe les writers et conserve les preuves pour audit.

## Rejeté

- fusionner sur titre + marque ;
- créer une Brand globale sur un simple libellé normalisé ;
- considérer deux GTIN différents comme deux ProductModels différents ;
- traiter MPN ou SKU comme global sans scope ;
- utiliser le volume Core v1 comme mesure de couverture Graph ;
- activer un dual-read avant benchmark et décision GO.
