# Audit — Contrôles Catalogue FILON

**Date :** 16 août 2026

Le contrat public de production expose `merchant`, `brand`, `price_min`, `price_max` et `sort` sur `GET /api/catalog/offers`. Les valeurs de tri annoncées sont `relevance`, `price_asc`, `price_desc` et `name`. L’API fournit également les marques fréquentes via `GET /api/catalog/facets` et les marchands avec nom, slug, région et secteur via `GET /api/catalog/merchants`.

L’application mobile ne doit pas coder une liste de marchands ou de marques dans le bundle : elle doit conserver les valeurs sélectionnées sous forme de critères textuels et alimenter les suggestions depuis ces endpoints. Les contrôles doivent rester secondaires dans une feuille native ; la recherche, les rayons et les sous-catégories restent les entrées principales.

Le comportement de disponibilité reste indépendant de cette extension : l’API peut fournir `in_stock: null`, qui doit rester affiché comme « À confirmer » plutôt que comme une disponibilité positive.
