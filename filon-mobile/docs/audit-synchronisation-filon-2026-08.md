# Audit de synchronisation FILON — Web, backend et application mobile

**Date d’audit :** 16 août 2026  
**Périmètre :** dépôt `Fredm237/codex-test` à `eb9990a`, application mobile FILON à `768848e5` avant les prochaines intégrations.

> Cet audit ne présente pas une promesse de couverture. Il distingue ce que l’application consomme déjà du backend, ce qu’elle ignore encore et ce qui doit être intégré avant de revendiquer une parité avec le site.

## 1. Évolutions vérifiées dans la source FILON

Les commits récents concentrent les changements sur la qualité de classification, la visibilité des offres et l’expérience Catalogue : disponibilité explicite (`153e1a4`), refonte catalogue (`9f0758c`), reclassement ciblé d’offres (`7408c38`), corrections de rayons Mode et beauté (`5e3a4bd`, `e601bab`) et enrichissement de règles 2dehands/2deKansje (`984a30e`, `5f61c45`, `1d053fe`, `b270b66`).

| Domaine | Capacité vérifiée | Source de vérité | Effet mobile actuel |
|---|---|---|---|
| Taxonomie | Départements → rayons → sous-rayons, avec volumes et slugs stables | `filon-backend/app/api/routes/catalog.py`, `app/services/taxonomy.py` | **Consommée** : le mobile ingère les branches `departments`, `roots`, `children`, `categories` et `subcategories`. |
| Classification | Corrections de catégories et reclassements appliqués au niveau des offres | `app/services/taxonomy.py`, endpoint catalogue | **Héritée automatiquement** pour toute offre lue depuis l’API ; aucune duplication de règles n’est nécessaire côté mobile. |
| Catalogue | Recherche, filtre département/rayon/sous-rayon, marque, marchand, fourchette de prix, tri, pagination et déduplication | `GET /api/catalog/offers` | **Partielle** : recherche, taxonomie, prix maximum et pagination sont utilisés ; tri, marque, marchand, prix minimum et disponibilité ne le sont pas encore entièrement. |
| Disponibilité | `in_stock` explicite, y compris une valeur inconnue | `GET /api/catalog/offers`, `ProductCard.tsx` web | **Écart critique** : le mobile convertit actuellement `null` en disponibilité positive. |
| Fraîcheur | Dernier relevé, relevés 24 h et baisses 24 h réelles | `GET /api/catalog/pulse` | **Non consommée** par l’application. |
| Découverte | Rangées secondaires basées sur `/api/catalog/highlights`, chargées sans bloquer la grille web | `filon-web/lib/catalogue.ts` | **Non consommée** ; à intégrer comme contenu éditorial différé, jamais comme blocant du premier parcours. |
| Produits | Regroupement EAN et fiches multi-marchands | `app/services/catalog_grouping.py`, `/api/catalog/product/{ean}` | **Partiellement consommé** : les fiches EAN existent ; les indicateurs de couverture et de comparabilité doivent être alignés. |
| Assistant | Flux SSE catalogue-only et cartes d’offres réelles | `app/api/routes/stream.py`, `app/services/recommend.py` | **Consommée** : le mobile conserve désormais offre, EAN, image et lien sûr, puis expose comparaison et suivi. |

## 2. Comparaison de contrat : priorités de mise à niveau mobile

| Priorité | Écart constaté | Risque utilisateur | Mise à jour mobile proposée | Critère de validation |
|---|---|---|---|---|
| P0 | `in_stock: null` devient `true` dans `normalizeOffer` | Une offre d’état inconnu peut être présentée comme disponible | Conserver `true`, `false` ou `null` dans le type mobile ; afficher « disponibilité non confirmée » pour `null` | Trois réponses API distinctes donnent trois états visuels distincts. |
| P0 | Filtres `brand`, `merchant`, `price_min` et `sort` disponibles mais absents du contrat mobile | Le mobile donne une exploration moins précise que le site | Étendre `FilonOfferSearch`, sérialiser les paramètres et les exposer dans une feuille de filtres native | Les mêmes filtres produisent les mêmes paramètres API que le site. |
| P1 | Le pulse catalogue n’est pas visible | L’utilisateur ne sait pas si les données sont fraîches | Ajouter un indicateur compact « dernier relevé » dans Catalogue, masqué si `live=false` | Aucun nombre n’est affiché quand le backend ne confirme pas la fraîcheur. |
| P1 | Les highlights ne sont pas consommés | L’application ne profite pas de la découverte éditoriale du site | Ajouter une rangée différée après la navigation, avec état vide silencieux | L’accueil Catalogue reste rapide si `/highlights` échoue. |
| P1 | Les champs `offer_kind`, `source_category`, `subcategory` des offres ne sont pas préservés par le normaliseur mobile | Les vues mobiles ne peuvent pas distinguer l’objet comparable de ses métadonnées source | Préserver ces métadonnées pour diagnostic et cartes explicables, sans les utiliser comme taxonomie de navigation | Une offre API garde ses champs publics sans changer la hiérarchie FILON. |
| P2 | Statistiques de regroupement EAN et couverture marchands non exposées à l’utilisateur mobile | Il est difficile d’interpréter l’étendue réelle d’une comparaison | Consommer les indicateurs de couverture uniquement dans les fiches EAN, avec libellés factuels | Une fiche dit « X offres observées » et jamais « tout le marché ». |
| P2 | Connexion de compte native incomplète faute de configuration OAuth embarquée | Les synchronisations multi-appareils ne peuvent pas être garanties | Injecter les paramètres OAuth/API publics dans la build native, puis tester callback + session | Connexion, retour profond, session et déconnexion vérifiés sur appareil. |

## 3. Décisions d’architecture

Le backend est l’autorité unique pour **taxonomie, disponibilité, classification, comparaison et recommandations**. L’application ne doit conserver localement que l’état d’interface, les préférences, les favoris privés et les files de reprise. Elle ne doit jamais recréer des règles de reclassement à partir du nom d’un produit.

La navigation mobile doit rester une interprétation native de la même taxonomie, et non un miroir de la mise en page web. Les ajouts issus du site — pulse, highlights et filtres avancés — doivent être introduits de façon progressive : feuille de filtre, rangée différée, signal de fraîcheur compact.

## 4. Ordre d’intégration recommandé

1. **Corriger immédiatement la sémantique de disponibilité** et étendre le contrat de recherche mobile aux filtres/tri disponibles.
2. **Ajouter pulse et highlights** comme enrichissements non bloquants du Catalogue, avec absence silencieuse en cas de service indisponible.
3. **Enrichir les fiches EAN** avec les métadonnées de regroupement et les preuves observées, sans promesse de couverture exhaustive.
4. **Réparer OAuth natif** après injection de la configuration publique appropriée, car il conditionne les alertes synchronisées et les collections multi-appareils.

## 5. Références internes

| Référence | Source |
|---|---|
| [1] | `filon-audit/filon-backend/app/api/routes/catalog.py` |
| [2] | `filon-audit/filon-backend/app/services/taxonomy.py` |
| [3] | `filon-audit/filon-backend/app/services/catalog_grouping.py` |
| [4] | `filon-audit/filon-web/lib/catalogue.ts` |
| [5] | `filon-audit/filon-web/components/filon/ProductCard.tsx` |
| [6] | `filon-mobile/lib/filon-api.ts` |
