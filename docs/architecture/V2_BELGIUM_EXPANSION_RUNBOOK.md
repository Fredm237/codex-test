# FILON — Extension factuelle V2 Belgique

## État

- Date de préparation : **8 septembre 2026**
- Date de fermeture : **9 septembre 2026**
- Production actuelle : **V2 `FACTUAL_OPTIONS` France** et **V2 `ABSTAIN`
  Belgique**, avec Core V1 calculé en premier et conservé comme fallback
- Lot présent : amorçage régional explicite, borné et journalisé
- Activation Belgique : **EFFECTUÉE ET PROUVÉE**, voir
  `V2_BE_PUBLIC_ACTIVATION_RECEIPT.md`

Ce runbook ne transforme pas la preuve France en preuve Belgique. La Belgique
doit accumuler ses propres données de provenance, exécutions V2, observations
dark/canary et reçus de promotion.

## Constat de production

L'audit en lecture seule a mesuré :

- **385 039** offres Core rattachées à des marchands belges ;
- **41** feeds Awin belges disponibles chez des marchands inscrits ;
- **507 153** produits déclarés par ces feeds ;
- aucun snapshot Offer Truth ou Product Ontology belge au moment de l'audit ;
- le feed belge `111943` déclare **2 324** produits ;
- sur une lecture de préqualification limitée aux 500 premières lignes, **6**
  produits ont été classés dans le sous-rayon `Smartphones` ;
- l'audit V2 ultérieur a prouvé que ces **500 lignes ne contiennent aucun EAN
  dans la colonne historique demandée** : ces lignes stockées ne pouvaient donc
  produire que `ABSTAIN` avec le resolver exact actuel ;
- le **9 septembre 2026**, une nouvelle lecture Awin strictement agrégée et sans
  écriture, incluant la colonne mappée `product_GTIN`, a mesuré sur les 500
  premières lignes du même feed : **490 identifiants renseignés**, **481 GTIN
  valides**, **8 smartphones**, et **8 smartphones avec GTIN valide** ; aucun
  catalogue ou writer V2 n'était actif pendant cette lecture.

Aucun nom, prix, URL ou payload produit issu de cette lecture n'est conservé
dans ce document.

## Préqualification factuelle du prochain feed

La liste Awin indique les colonnes réellement mappées par feed. FILON sait
désormais lire les identifiants globaux publiés sous `ean`, `product_GTIN` ou
`upc`, puis les valide avec le même checksum GS1. Une valeur invalide ne peut
jamais masquer une autre valeur valide et aucun SKU marchand n'est promu en
identifiant global.

Le diagnostic du feed `111943` prouve que le corpus belge nécessaire existe
déjà chez le fournisseur. La correction porte sur la projection des colonnes,
pas sur un assouplissement du resolver ni sur une donnée inventée.

Inventaire métadonnées, sans téléchargement de produit ni écriture :

```bash
python -m app.ingest.regional_feed_audit --region BE
```

Audit d'un petit groupe explicite, borné à 500 lignes par feed :

```bash
python -m app.ingest.regional_feed_audit \
  --region BE \
  --feed-id <feed-id> \
  --sample-rows 500
```

Le reçu ne conserve que les identifiants de feeds et cinq compteurs : lignes
échantillonnées, présence d'un identifiant, GTIN valides, smartphones et
intersection smartphone/GTIN valide. Les noms, prix, URLs et payloads restent
absents. Seul un feed dont `smartphone_valid_gtin_rows > 0` peut être proposé à
`regional_seed`; `no_qualified_feed`, `partial` et `scope_unavailable` ferment
le chemin sans writer.

## Pourquoi une commande dédiée

Le cycle catalogue normal parcourt les feeds éligibles dans l'ordre du
fournisseur. Une simple limite à un feed peut donc sélectionner une verticale
sans rapport avec le scope public V2. La commande régionale impose au contraire
trois bornes simultanées :

1. région ISO exacte ;
2. identifiant de feed explicite et rattaché à un marchand inscrit ;
3. plafond de lignes inférieur ou égal au plafond de production.

Elle réutilise ensuite le writer catalogue existant : upserts V1, RawSource,
observations, Product Graph, Offer Graph, checkpoints, heartbeat et journal
terminal restent identiques au chemin normal.

## Concurrence

Le démarrage d'un cycle catalogue et celui d'une chaîne V2 passent désormais
par un même verrou transactionnel PostgreSQL avant de consulter leurs leases
persistants. Ainsi :

- une chaîne V2 `running` interdit le démarrage catalogue ;
- un catalogue `running` interdit le démarrage V2 ;
- deux demandes simultanées ne peuvent plus franchir chacune leur contrôle
  avant que l'autre ait écrit son lease.

Les index partiels uniques propres à chaque journal restent la seconde ligne de
défense.

## Préflight sans écriture

À exécuter uniquement quand les sondes sont vertes :

```bash
python -m app.ingest.regional_seed \
  --region BE \
  --feed-id 111943 \
  --max-rows 500 \
  --check
```

Le seul état autorisant l'étape suivante est `ready`. `catalog_syncing`,
`v2_running` ou `feed_scope_unavailable` arrêtent l'opération sans writer.

## Amorçage borné

Après un préflight `ready`, la même commande sans `--check` lance exactement
un cycle :

```bash
python -m app.ingest.regional_seed \
  --region BE \
  --feed-id 111943 \
  --max-rows 500
```

Le reçu ne contient que région, identifiants de feeds, bornes, compteurs et
identifiant du run catalogue. Aucun payload brut n'y est retenu.

## Gates après amorçage

L'extension Belgique devait rester fermée tant que ces preuves n'étaient pas
toutes obtenues. Elles sont désormais fermées dans
`V2_BE_PUBLIC_ACTIVATION_RECEIPT.md` :

1. run catalogue terminal `succeeded`, un seul feed, au plus 500 lignes ;
2. absence de writer catalogue ou V2 concurrent ;
3. RawSource et provenance régionale réels, sans échec shadow ;
4. fenêtres V2 séquentielles et bornées jusqu'au dernier RawSource créé ;
5. replay exact idempotent de la dernière fenêtre ;
6. réponses belges uniquement lorsque pays, devise, fraîcheur, stock,
   provenance et chaîne sont admissibles ;
7. dark reads belges non influents et sans requête brute conservée ;
8. canary fermé Belgique avec fallback Core V1 et injection d'échec verte ;
9. nouveau reçu public autorisant explicitement le scope Belgique ;
10. vérification publique réelle suivie d'un test du kill switch.

Le routeur promu exige en plus `V2_SUPPORTED_COUNTRIES`. Une requête sans pays
ISO explicite, ou dont le pays ne figure pas dans cette liste fermée, retourne
Core V1 avant tout accès au lecteur V2. Pour la portée historique France, la
valeur doit rester `FR` ; `BE` ne peut être ajouté qu'après le nouveau reçu
Belgique.

Une absence de produit admissible reste une abstention ou un fallback Core V1.
`BUY_NOW`, `FACTUAL_OPTIONS` et `WAIT` ne sont pas ouverts par ce lot. La
promotion belge est strictement limitée à `ABSTAIN`.
