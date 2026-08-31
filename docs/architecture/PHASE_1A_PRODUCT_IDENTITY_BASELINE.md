# FILON — Phase 1A Product Identity Baseline

- Date de capture : **31 août 2026**
- Statut : **BASELINE ÉTABLIE — aucun lecteur public v2 activé**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Source : API catalogue de production en lecture seule et code shadow qualifié

## Verdict

FILON dispose déjà d'un socle exact-GTIN sûr pour identifier une variante,
mais pas encore d'une identité complète Brand → Family → Model → Variant.
Le catalogue Core groupe largement par EAN et Awin fournit souvent une marque,
mais les familles, codes modèles et attributs de variante structurés ne sont
pas suffisamment prouvés pour être promus automatiquement.

La recherche par mots-clés ne constitue pas un roster de verticale fiable :
les requêtes smartphones et laptops ramènent beaucoup de coques, housses et
accessoires ; `casque` ramène aussi des casques de vélo. Phase 1 utilisera donc
des sous-catégories FILON explicites et un rôle produit admissible, jamais une
simple présence lexicale.

## État de production observé

| Signal | Valeur |
|---|---:|
| Marchands | 251 |
| Offres | 2 025 776 |
| Snapshots prix | 20 610 944 |
| Produits Core groupés | 597 846 |
| Produits multi-marchands | 104 183 |
| Offres liées à un produit Core | 1 086 764 |

Ces volumes décrivent le Core v1 ; ils ne prouvent pas que chaque groupe est
un ProductModel ou une Variant correctement décomposée.

## Méthode d'échantillonnage

Un échantillon stratifié de **3 200 produits** a été lu sur 16 positions
réparties dans les 597 846 produits publics, par lots de 200. Cette méthode
borne le coût de lecture et réduit le biais du premier lot, mais ne remplace
pas une agrégation PostgreSQL exhaustive ni une vérité humaine.

| Mesure | Résultat |
|---|---:|
| Marque présente et non sentinelle | 3 192 / 3 200 (**99,75 %**) |
| Catégorie présente | 2 955 / 3 200 (**92,34 %**) |
| Catégorie absente | 245 / 3 200 (**7,66 %**) |
| EAN de longueur/checksum admissible | 3 200 / 3 200 |
| Produits multi-marchands | 600 / 3 200 (**18,75 %**) |
| Produits avec prix actuellement comparable | 292 / 3 200 (**9,13 %**) |
| EAN dupliqué dans cet échantillon | 0 |

Le taux EAN de cet endpoint est structurellement élevé : le Core ne publie
comme `catalog_products` que ses groupes EAN admissibles. Il ne mesure donc pas
la couverture GTIN de toutes les offres brutes. La couverture réelle du writer
Graph doit être mesurée sur `RawSourceRecord`, pas extrapolée depuis ce taux.

## Collisions et incohérences observables

Des libellés distincts produisent la même forme normalisée sans pour autant
constituer une preuve suffisante de fusion canonique :

| Libellé A | Libellé B | Risque |
|---|---|---|
| `Esituro` | `eSituro` | casse |
| `Rc Design` | `Rc-design` | ponctuation |
| `Koeka` | `koeka` | casse |
| `Main Sauvage` | `Main sauvage` | casse interne |

Conséquence : une marque observée est d'abord une assertion sourcée. La
normalisation seule peut proposer un candidat, mais ne doit pas créer une
fusion globale silencieuse.

Les catégories source sont également hétérogènes : codes numériques comme
`460` ou `443`, libellés marchands multilingues et valeurs absentes coexistent.
La taxonomie FILON est donc une projection versionnée, pas une identité source.

## Verticales prioritaires

### Volumes taxonomiques observés

| Sous-catégorie FILON | Offres |
|---|---:|
| Smartphones | 16 475 |
| Ordinateurs portables | 4 677 |
| Téléviseurs | 1 551 |
| Casques audio | 715 |
| Écouteurs | 1 079 |
| Enceintes | 1 249 |
| Barres de son | 73 |
| Platines & Hi-Fi | 348 |
| Gros électroménager | 2 911 |
| Petit électroménager | 1 211 |
| Aspirateurs | 1 309 |
| Climatisation | 1 647 |
| Pneus, verticale de contrôle structurée | 165 986 |

### Décision de séquencement

1. **Pneus comme verticale de contrôle**, car le volume, le GTIN et la
   comparaison multi-marchands offrent une surface structurée ; cette
   verticale ne remplace pas les verticales produit mandatées.
2. **Smartphones et ordinateurs portables** comme premier lot fonctionnel,
   après filtrage taxonomique et exclusion des accessoires.
3. **TV et audio** comme second lot ; les mots ambigus et les écrans proches
   exigent des hard negatives explicites.
4. **Électroménager** comme troisième lot ; les attributs et la comparabilité
   sont plus clairsemés dans l'échantillon public.
5. Fashion reste hors promesse de production pendant cette phase.

Un produit appartient au roster initial seulement si la sous-catégorie FILON
est explicitement admise et si le rôle est `primary_product`. Une requête
lexicale, une marque ou un titre ne suffisent jamais.

## Capacités et lacunes du Graph actuel

| Capacité | État | Limite |
|---|---|---|
| Variant par GTIN exact | Disponible en shadow | ne prouve pas Model/Family |
| Identifiant + evidence raw | Disponible, append-only | namespace v1 limité à GTIN |
| Offer → Variant | Disponible, versionné | absence/invalide en quarantaine |
| Brand | Table présente | aucun writer canonique sûr |
| Brand alias | Table présente | exige déjà une Brand canonique |
| ProductFamily | Table présente | aucune preuve Awin exploitée |
| ProductModel | Table présente | code modèle non projeté |
| Attributs de Variant | Contrat présent | projection Awin actuelle vide |
| MPN / merchant SKU | Non supportés par l'identifiant v1 | scopes à définir avant écriture |

## Risques Phase 1 à traiter

- faux merge marque par normalisation agressive ;
- confusion produit/accessoire dans la constitution des verticales ;
- assimilation d'un GTIN à un modèle alors qu'il identifie une variante ;
- perte de la provenance lors de la promotion d'une assertion ;
- SKU marchand pris à tort pour un identifiant global ;
- attribut inconnu converti en valeur favorable ;
- score de benchmark artificiellement élevé par des cas triviaux ou vus
  par le moteur.

## Décision de sortie P1A

La baseline est suffisante pour figer le contrat d'identité. Elle ne valide
aucun cutover et ne revendique aucune exactitude humaine. La prochaine étape
est un contrat fail-closed qui sépare explicitement :

- assertion source ;
- candidat canonique ;
- identité canonique promue ;
- inconnue/quarantaine ;
- preuve et version du resolver.
