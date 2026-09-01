# FILON — Phase 3B Offer Truth Production Baseline

- Date : **1er septembre 2026**
- Statut : **TERMINÉ — AUDIT PRODUCTION EN LECTURE SEULE**
- Déploiement observé : `d76ce26f-c2b6-4cbf-ac94-8b645612b60d`
- Révision Alembic : `c4f2b8d5e0a3`
- Corpus : **1 000 raws Awin, un feed, un marchand**
- Writers et lecteurs publics : **inchangés**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Verdict

Le corpus rejouable fournit une excellente couverture syntaxique pour le prix,
la devise, le stock et le lien marchand : 1 000/1 000 valeurs sont reconnues
par les normaliseurs actuels. Il ne fournit aucun champ exploitable pour la
livraison, les retours, la garantie, le vendeur marketplace, la condition, le
cashback, les coupons ou les promotions.

L'identité reste la première frontière d'éligibilité : 330 raws possèdent une
Variant résolue et deviennent `eligible` dans le dry-run Offer Graph ; 670
restent `quarantine / identity_unresolved`. Aucun lien d'offre Core ne manque.

Cette baseline mesure la présence et la validité déterministe des données. Elle
ne prouve pas que le prix marchand affiché est exact, que le stock correspond à
la réalité ou que le lien aboutit encore au bon produit. P3C doit construire la
gate d'exactitude sans fabriquer une ground truth externe.

## Méthode

Deux lectures bornées ont été exécutées dans le conteneur web Railway, sans
flag et sans écriture :

1. `app.offer_graph.backfill --after-raw-id 0 --limit 1000` en mode dry-run ;
2. une agrégation des mêmes payloads par les normaliseurs versionnés, qui ne
   conserve ni ne publie aucune valeur source.

Les raws sont ordonnés par clé primaire. Cette fenêtre correspond au corpus
P1/P2 déjà qualifié et ne constitue pas un échantillon aléatoire du catalogue.

## Résultat Offer Graph

| Mesure | Résultat |
|---|---:|
| raws scannés | 1 000 |
| offres `eligible` | 330 |
| offres `quarantine` | 670 |
| offres `unknown` | 0 |
| offres `ineligible` | 0 |
| liens Core manquants | 0 |
| observations écrites | 0 |
| dernier raw | 1 000 |

Les 670 quarantaines sont dues à l'identité Variant non résolue. Le second
audit sépare donc volontairement les claims d'offre de cette décision
d'identité.

## Couverture des claims

| Claim | Connu | Inconnu / absent | Lecture autorisée |
|---|---:|---:|---|
| prix | 1 000 | 0 | syntaxiquement valide et strictement positif |
| devise | 1 000 EUR | 0 | aucune devise de fallback observée |
| stock | 1 000 `in_stock` | 0 | valeur source normalisée, pas une validation externe |
| lien marchand | 1 000 | 0 | HTTPS public et syntaxiquement sûr |
| marchand | 1 distinct | 0 | identité Registry présente |
| shipping / livraison | 0 | 1 000 | `unknown`, jamais gratuit |
| retours | 0 | 1 000 | `unknown` |
| garantie | 0 | 1 000 | `unknown` |
| vendeur marketplace | 0 | 1 000 | `unknown` |
| condition | 0 | 1 000 | `unknown` |
| cashback | 0 | 1 000 | `unknown` |
| coupon | 0 | 1 000 | `unknown` |
| promotion | 0 | 1 000 | `unknown` |

Les alias de livraison contrôlés étaient `shipping_cost`, `delivery_cost`,
`postage`, `shipping`, `delivery_price`, `delivery_country`, `delivery_time`
et `estimated_delivery`. Les alias retours/garantie contrôlés couvrent les
formes actuellement prévues par le mandat ; aucune valeur non vide n'existe
sur la fenêtre.

## Fraîcheur observée

Les 1 000 raws portent le même horodatage d'observation :
`2026-08-31T21:40:12.454546Z`. Au snapshot d'audit
`2026-09-01T07:38:54Z`, leur âge est d'environ 35 922 secondes, sous la
frontière provisoire de 259 200 secondes (72 h).

Cette mesure ne ratifie pas un TTL commun prix/stock. P3C doit conserver le
seuil provisoire comme règle fail-closed, puis exiger une policy versionnée par
type de claim avant toute promotion publique.

## Décision P3B

P3B est fermé avec les décisions suivantes :

- prix/devise, stock, marchand et lien peuvent être extraits en shadow avec
  provenance complète ;
- shipping, retours et garantie doivent produire `unknown` sur ce feed ;
- aucune inférence depuis le titre ou un LLM n'est autorisée pour ces claims ;
- la quarantaine d'identité reste indépendante de la vérité des autres champs ;
- P3C doit ratifier séparément exactitude, abstention et fraîcheur avant tout
  writer Phase 3 ou lecteur public.
