# Mobile Barcode Lookup v1

Ce contrat borne le parcours Phase 13 entre la caméra FILON et le catalogue
Core. Le scan est déclenché par une action utilisateur explicite. Le code brut
reste sur l'appareil ; seul le GTIN canonique validé peut entrer dans la route
publique de consultation existante.

## Invariants

- longueurs admises : GTIN-8, UPC-A, EAN-13 et GTIN-14 ;
- checksum GS1 obligatoire et codes de remplissage répétés interdits ;
- UPC-A et GTIN-14 préfixé par zéro convergent vers la clé EAN-13 Core ;
- une réponse portant une autre identité que la clé demandée est rejetée ;
- `404` signifie `not_found`, une panne réseau signifie `unavailable` ;
- aucun prix, stock, lien marchand ou disponibilité n'est inféré du scan ;
- seules les offres Core courantes, mono-devise et explicitement en stock sont
  rendues actionnables par les contrôles existants.

Le contrat ne crée aucun writer produit, aucun lecteur shadow et aucun Cron.
