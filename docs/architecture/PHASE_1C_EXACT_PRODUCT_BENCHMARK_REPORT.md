# FILON — Phase 1C Exact-Product Benchmark Report

- Date : **31 août 2026**
- Verdict : **PASS déterministe pour le resolver exact-GTIN shadow**
- Evaluation : `sha256:f71c3f3e8024cca02f037722d28b8612421fba529eca3e3a6694ce2754101560`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Qualité : `DETERMINISTICALLY_VERIFIED`

## Portée

Le benchmark qualifie les invariants de Product Identity qui possèdent un
oracle calculable. Il ne revendique ni une compréhension humaine des titres,
ni une extraction Model/Family déjà opérationnelle, ni la qualité du catalogue
complet.

Il exécute cinq verticales, trois seeds et 64 échantillons par
verticale/seed. Les cas générés ne sont pas utilisés comme entrées du moteur de
développement. Cinq régressions statiques couvrent aussi chaque verticale.

## Résultat

| Mesure | Cas | Résultat | IC 95 % | Gate |
|---|---:|---:|---:|---:|
| Exact-product, même GTIN | 960 | 100 % | borne basse 99,601 % | ≥ 98 % |
| Variant resolution | 3 840 | 100 % | borne basse 99,900 % | ≥ 97 % |
| Offer attachment | 2 880 | 100 % | borne basse 99,867 % | ≥ 97 % |
| False merge sur hard negatives | 2 880 | 0 / 2 880 | borne haute 0,133 % | ≤ 0,5 % |
| Tous checks | 10 565 | 10 565 / 10 565 | — | 0 échec |

Chaque verticale porte 2 113 checks et termine sans échec : smartphones,
laptops, TV, headphones/audio et appliances.

## Hard negatives

Le corpus ne se limite pas au cas positif. Il contient notamment :

- titres identiques avec GTIN différents ;
- produit principal contre accessoire ou pièce de remplacement ;
- stockage, mémoire, taille, couleur ou capacité différents ;
- casques audio contre casques de vélo ;
- TV OLED contre moniteur OLED ;
- aspirateur contre filtre de remplacement ;
- identifiants manquants, invalides ou contradictoires ;
- offre exacte, mismatch candidat et offre sans identifiant.

Le resolver n'utilise ni titre, ni marque, ni rôle produit comme fallback. Il
prouve une même Variant avec un GTIN exact, sinon il s'abstient, met en
quarantaine ou rejette selon le contrat.

## Reproductibilité et fail-closed

- manifest versionné : `quality/product-identity-manifest.json` ;
- régressions : `quality/product-identity-regressions.json` ;
- moteur : `quality_lab.product_identity` ;
- le même manifest produit le même `evaluation_id` ;
- limitation, roster, seed policy, budget d'échec et seuils invalides sont
  refusés ;
- supprimer une verticale des régressions invalide le run ;
- la scorecard utilise les intervalles de Wilson, pas seulement les taux
  ponctuels.

## Interprétation

Ce PASS lève le gate P1C pour l'identité exacte GTIN et la protection contre
les faux merges déterministes. Il ne clôt pas Phase 1 : le schéma d'assertions
Brand/Family/Model, les writers, le backfill réel borné et la provenance
persistée restent à qualifier.
