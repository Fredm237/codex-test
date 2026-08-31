# ADR-002 — Identité Product/Variant Graph shadow exact-GTIN

- Statut : **proposé, implémenté uniquement en shadow**
- Date : 30 août 2026
- Décisionnaires : architecture FILON
- Resolver : `exact-gtin-shadow-v1`
- Révision expand : `8b2f4c7d9a10`

## Contexte

`catalog_products` regroupe historiquement les offres par EAN, sans séparer
Brand, ProductFamily, ProductModel et Variant. Ce regroupement est utile au
Core v1 mais ne prouve ni qu'un titre ressemblant décrit le même produit, ni
que deux GTIN différents décrivent deux modèles différents. Les faux merges
contamineraient prix, stock et recommandations ; les faux splits masqueraient
les variantes réellement comparables.

Les datasets humains restent vides. Le mandat spécial autorise l'avancement
technique, pas la fabrication d'un score. Le Graph doit donc pouvoir être
écrit, rejoué et mesuré tout en restant absent des lectures publiques.

## Décision

1. Huit tables `graph_*` sont ajoutées sans modifier les tables Core v1 :
   Brand, alias sourcé, Family, Model, Variant, identifiant, preuve
   d'identifiant et résolution Offer→Variant.
2. La v1 ne résout une variante qu'avec exactement un GTIN/EAN valide et non
   contradictoire. La clé stable est `gtin:<valeur normalisée>`.
3. Titre, marque, catégorie et similarité textuelle ne constituent jamais une
   preuve de fusion. Deux GTIN différents restent `ambiguous` au niveau produit,
   car ils peuvent être deux variantes d'un même modèle.
4. Une offre sans GTIN, avec GTIN invalide ou contradictoire produit un lien
   versionné `quarantine` sans `variant_id`. Elle ne reçoit aucun fallback.
5. Une preuve d'identifiant est append-only et reliée au `RawSourceRecord` qui
   la justifie. Un replay du même raw et de la même version est idempotent.
6. `PRODUCT_GRAPH_SHADOW_ENABLED=true` exige
   `OBSERVATION_SHADOW_ENABLED=true`. Les deux flags sont faux par défaut.
7. Le backfill est borné à 10 000 raws par lot, ordonné par identifiant et en
   lecture seule sans `--apply`. Aucun backfill ne s'exécute dans la migration.
8. Les adaptateurs Quality `entity_resolution`, `variant_resolution` et
   `offer_attachment` appellent le resolver réel. Leur confiance reste `0.0`
   et la readiness reste `not_ready` tant que les golds humains manquent.

## Conséquences

- Le lot peut mesurer l'abstention technique et préparer le holdout sans
  modifier une réponse catalogue, un classement ou une carte.
- Brand, Family et Model existent comme schéma mais ne sont pas auto-remplis
  par le texte Awin. Leur résolution attend une preuve et un benchmark dédiés.
- La politique minimise les faux merges mais aura une couverture faible. Ce
  compromis ne peut être changé qu'après mesure indépendante.
- Le rollback normal coupe le writer et conserve les tables pour audit. Le
  downgrade destructif vers `f4c81a9d2e70` est réservé à une base éphémère
  ou à une restauration explicitement préparée.

## Preuves attendues avant acceptation

- migration upgrade/check/downgrade/upgrade sans perte Core ;
- idempotence, provenance et quarantaine sur SQLite et PostgreSQL CI ;
- runner Quality sur les sept adaptateurs sans accès aux golds ;
- faux merges, faux splits, exactitude variante et attachement mesurés sur le
  holdout humain conforme ;
- backfill borné sur un lot réel, rapport de drift, revue de quarantaine et
  rollback du writer ;
- aucune lecture publique v2 avant une décision GO explicite.
