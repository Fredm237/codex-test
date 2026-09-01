# FILON — Phase 5B Hybrid Retrieval Baseline

- Date de lecture : **1er septembre 2026**
- Statut : **TERMINÉE — BASELINE RÉELLE AGRÉGÉE**
- Portée : code legacy, schéma PostgreSQL et agrégats de production
- Données brutes de production : **NON LUES / NON PUBLIÉES**
- Lecteur public : **INCHANGÉ**
- Writer Hybrid Retrieval : **ABSENT / NON ACTIVÉ**

## Conclusion

FILON dispose déjà d'une base exploitable pour un retrieval hybride : catalogue
structuré, regroupements produit, extension `pg_trgm` et index GIN sur le nom et
la marque. Le chemin lexical historique n'utilise toutefois pas l'index dans sa
forme actuelle, car il recherche `lower(name)` alors que l'index porte sur
`name`. Un non-match doit donc parcourir le catalogue complet.

Le second écart majeur est conceptuel : le lecteur Assistant mélange encore
résolution d'intention, récupération exhaustive, filtres métier, sélection
d'offres, regroupement, décision et présentation. Phase 5 doit isoler un
générateur de candidats product-first, sourcé et borné avant toute promotion.

## Corpus réel agrégé

Les compteurs suivants proviennent d'une requête d'agrégation en lecture seule
sur PostgreSQL de production. Aucun titre, requête utilisateur, payload marchand
ou identifiant d'offre n'a été lu ou affiché.

| Mesure | Compteur | Couverture |
|---|---:|---:|
| Offres | 2 025 852 | 100,0000 % |
| Offres canoniques legacy | 1 568 368 | 77,4177 % |
| Offres reliées à un produit | 1 086 764 | 53,6448 % |
| Catégorie FILON connue | 1 905 019 | 94,0354 % |
| Sous-catégorie FILON connue | 1 289 025 | 63,6288 % |
| Type d'offre non nul | 2 025 849 | 99,9999 % |
| Marque non vide | 1 829 141 | 90,2900 % |
| EAN non vide | 1 146 090 | 56,5732 % |
| Prix et devise non nuls | 2 025 852 | 100,0000 % |
| État de stock non nul | 2 025 852 | 100,0000 % |
| Image non vide | 1 962 091 | 96,8526 % |
| Clé de déduplication non vide | 2 025 847 | 99,9998 % |
| Groupes de déduplication | 1 087 572 | — |
| Produits | 597 846 | 100,0000 % |
| Produits reliés à au moins une offre | 595 399 | 99,5907 % |
| Produits multi-marchands | 104 183 | 17,4264 % |

Le champ de stock non nul est une propriété du schéma legacy et de sa
normalisation ; il ne prouve pas que le marchand a observé ou confirmé le stock.
De même, `is_canonical` et `dedup_key` sont des signaux historiques, pas une
identité canonique Phase 1/2. Ces compteurs mesurent la disponibilité des champs,
pas leur vérité sémantique.

## Baseline PostgreSQL

L'extension `pg_trgm` est active en production. Les index suivants sont présents
sur `offers` :

- `ix_offers_name_trgm`, GIN `name gin_trgm_ops` ;
- `ix_offers_brand_trgm`, GIN `brand gin_trgm_ops` ;
- index B-tree sur catégorie, sous-catégorie, type, produit, marchand, canonical,
  adulte, déduplication, EAN et marque ;
- unicité `(merchant_id, awin_product_id)`.

La migration Alembic de baseline crée explicitement l'extension et les deux
index trigrammes. La production est donc conforme au schéma déclaré.

## Mesure du chemin lexical

Deux `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)` ont été exécutés avec des termes
entièrement synthétiques. Aucun résultat ni contenu d'offre n'a été retourné.
Les latences sont des observations ponctuelles de baseline, pas des SLO.

| Scénario | Plan observé | Exécution | Blocs lus |
|---|---|---:|---:|
| Terme fréquent, chemin actuel `lower(name) LIKE` | scan séquentiel parallèle borné à 100 | 8,587 ms | 944 |
| Terme fréquent, `name ILIKE` | scan séquentiel choisi par le planner, borné à 100 | 1,434 ms | 111 |
| Non-match, chemin actuel `lower(name) LIKE` | scan séquentiel parallèle complet | 572,366 ms | 145 448 |
| Non-match, `name ILIKE` | bitmap scan sur `ix_offers_name_trgm` | 9,137 ms | 622 |

Le non-match synthétique a retiré 675 284 lignes par worker sur trois boucles,
soit la totalité des 2 025 852 offres. Le digest du terme, publié sans le terme,
est `sha256:af6e1044b1ca645f688c2bcd135fa04b4e282ce31be1083460e0f4a01254714c`.

La conclusion n'est pas que `ILIKE` doit être promu sans benchmark. Elle établit
que l'index actuel est opérationnel et que la forme SQL historique le neutralise
pour les recherches négatives. P5D devra comparer une forme compatible GIN,
PostgreSQL FTS et leur combinaison sur le même holdout P5C.

## Chemins applicatifs actuels

### Recherche catalogue legacy

`app/services/search.py` :

- normalise accents et casse en Python ;
- conserve au plus six termes ;
- applique un stemming d'accords très borné ;
- exige chaque terme dans `lower(name)` ou `lower(brand)` ;
- expose un classement heuristique en six paliers, séparé de la sélection SQL.

La requête est prudente sur les accords, mais elle n'est ni product-first ni
reproductible comme un `RetrievalRun` versionné. Elle n'expose pas la provenance
par source et n'a pas de fenêtre candidate commune à plusieurs adaptateurs.

### Assistant historique

`app/services/catalog_search.py` :

- résout d'abord une intention taxonomique déterministe ;
- peut demander un enrichissement sémantique strictement contraint aux scopes
  FILON, avec fallback fail-closed vers l'intention déterministe ;
- récupère toutes les offres admissibles d'un scope reconnu avant classement ;
- applique fraîcheur, devise, budget, stock, rôle, accessoires et preuves ;
- regroupe certaines offres par `product_id` pour comparer prix et marchands ;
- construit ensuite les objets de présentation et les décisions.

Ce chemin contient des garde-fous utiles, mais son retrieval reste couplé aux
contraintes et à la décision. La suppression locale de `limit` sur le chemin de
repli rend en outre la taille de fenêtre dépendante du scope réel plutôt que
d'un contrat de candidats borné.

### Pertinence et intention

`app/services/relevance.py` protège des régressions observées : accessoires,
produits satellites, cartes cadeaux, termes de budget et équivalences FR/NL/EN.
Il reste un ranking heuristique d'offres et ne doit pas devenir l'identité ni le
retrieval canonique.

`app/intelligence/intent_resolution.py` est fail-closed : le composant
sémantique choisit uniquement parmi les catégories et sous-catégories autorisées,
et une sortie invalide ou indisponible conserve le résultat déterministe. Cette
frontière est compatible avec P5A, à condition que le semantic retrieval ne
puisse qu'étendre la liste sourcée et jamais résoudre une identité à lui seul.

## Écarts à fermer

1. rendre la requête lexicale compatible avec un index mesuré, sans régression
   sur les accents, langues ou termes courts ;
2. produire des candidats produit, pas une liste d'offres dupliquées ;
3. borner chaque adaptateur et la fenêtre fusionnée avant hydratation ;
4. séparer retrieval, contraintes, ranking, décision et présentation ;
5. publier la provenance, le rang source, la version et les abstentions ;
6. ne jamais promouvoir un candidat uniquement sémantique en entité résolue ;
7. mesurer rappel, NDCG, no-match, ambiguïtés, violations et faux groupements
   sur le même corpus P5C ;
8. conserver le lecteur public inchangé jusqu'au gate P5J.

## Limites

- aucun log de requête utilisateur n'a été lu ; la baseline ne mesure donc pas
  la distribution réelle des formulations ;
- aucun jugement humain externe ne qualifie encore les préférences de rang ;
- les mesures de latence sont ponctuelles et ne remplacent pas P50/P95/P99 ;
- la couverture élevée des colonnes legacy ne prouve pas leur exactitude ;
- les 46,3552 % d'offres sans `product_id` imposent une abstention ou une
  quarantaine product-first, jamais un regroupement inventé.

## Décision P5B

P5B est terminale. La production démontre une base PostgreSQL exploitable et un
défaut lexical reproductible sans exposition de données. P5C peut maintenant
figer un holdout adversarial ; P5D comparera les adaptateurs sur ce corpus avant
toute migration, activation shadow ou modification d'un lecteur public.
