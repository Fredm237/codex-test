# FILON Contracts v1

Statut : `frozen` depuis le 28 août 2026.

| Contrat | Producteur | Consommateurs | Unknown |
|---|---|---|---|
| `catalog-offer` | FastAPI `/api/catalog/*` | web, mobile | `in_stock: null`, marque/catégorie/image nullable |
| `advise-offer` | Pipeline `/api/advise` | clients historiques | devise et observation additives ; livraison, garantie et stock nullable |
| `extension-search-context` | extension MV3 | `filon.be/recherche` | requête facultative ; aucune donnée commerciale déduite |

Les fichiers `examples/*.unknown.json` sont les cas sentinelles : chaque client doit démontrer qu'il conserve l'inconnu jusqu'au rendu.
