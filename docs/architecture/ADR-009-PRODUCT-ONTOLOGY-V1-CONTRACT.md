# ADR-009 — Product Ontology v1, rôles et relations sourcés

- Statut : **accepté pour shadow**
- Date : **1er septembre 2026**
- Portée : Phase 4 Product Ontology
- Contrat : `contracts/product-ontology/v1`
- Lecteurs publics : **inchangés**

## Contexte

La taxonomie legacy contient des règles utiles et de nombreux correctifs
merchant-specific, mais une catégorie plate ne peut représenter ni la nature de
l'objet vendu, ni sa compatibilité, ni ses attributs ou relations. Transformer
encore plus de mots-clés en architecture centrale augmenterait les faux
positifs et rendrait les décisions impossibles à expliquer.

## Décision

1. La Product Ontology porte catégorie, sous-catégorie, type produit, rôle,
   attributs, relations et huit familles de facettes.
2. Le roster Product Role est fermé et reprend les neuf états du mandat.
3. Une relation observée dans un titre reste textuelle tant qu'Entity
   Resolution n'a pas prouvé sa cible.
4. Une relation canonique porte exclusivement une `target_variant_id`.
5. Les attributs sont typés ; les décimaux restent des chaînes exactes.
6. Chaque concept, attribut ou relation connue possède une provenance ; les
   concepts utilisent une clé stable sous un contrat versionné.
7. La taxonomie legacy reste disponible comme `legacy_fallback`, avec un état
   de migration explicite.
8. Les règles merchant-specific restent des signaux de nettoyage et des
   régressions, jamais des concepts centraux implicites.
9. `VERIFIED` exige identité Variant, catégorie, type produit et rôle connus.
10. Le contrat reste shadow-only jusqu'aux benchmarks taxonomy/role et au
    replay production Phase 4.

## Invariants

- texte de compatibilité ≠ identité canonique ;
- mot accessoire ≠ relation démontrée ;
- catégorie legacy ≠ vérité ontologique automatique ;
- absence de facette ≠ facette favorable ;
- aucun attribut connu sans type et provenance ;
- aucune promotion publique avant la gate taxonomy/role.

## Rollback

P4A n'active ni writer ni lecteur. Les futurs writers seront append-only et
désactivés par défaut ; leur rollback opérationnel conservera les assertions
et coupera uniquement le flag Product Ontology.
