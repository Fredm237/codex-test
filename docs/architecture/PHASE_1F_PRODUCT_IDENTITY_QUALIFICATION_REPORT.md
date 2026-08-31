# FILON — Phase 1F Product Identity Qualification Report

- Date : **31 août 2026**
- Verdict : **PASS — GATES PRODUCT IDENTITY SATISFAITES**
- Benchmark : `sha256:f71c3f3e8024cca02f037722d28b8612421fba529eca3e3a6694ce2754101560`
- Corpus réel : **1 000 offres Awin shadow**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Résumé

Le resolver exact-GTIN satisfait à la fois son benchmark autonome adversarial
et les invariants vérifiables sur le premier lot réel de production. Le lot
réel ne révèle ni faux merge structurel, ni faux split GTIN, ni rattachement
résolu incomplet. Les 670 offres sans GTIN restent en quarantaine et ne sont
jamais transformées en correspondance favorable.

Cette qualification autorise la sortie de Product Identity shadow. Elle
n'autorise pas un matching probabiliste, une déduction Family/Model depuis le
titre, ni la promotion des lecteurs publics v1.

## Gates ratifiées

| Gate | Résultat | Preuve |
|---|---|---|
| Exact-product | **PASS** | benchmark : 960/960 correspondances exactes |
| Variant resolution | **PASS** | benchmark : 3 840/3 840 ; production : 330 liens exact-GTIN |
| Offer attachment | **PASS** | benchmark : 2 880/2 880 ; production : 0 lien Offer manquant |
| Faux merge | **PASS** | benchmark : 0/2 880 ; production : 0 variante avec GTIN contradictoires |
| Faux split | **PASS borné** | production : 0 GTIN réparti entre plusieurs variantes |
| Abstention | **PASS** | 670/1 000 offres sans GTIN en `quarantine / missing_gtin` |
| Provenance | **PASS** | 330 preuves d'identifiant, 2 330 assertions sourcées |
| Idempotence | **PASS** | replay : 0 assertion, 0 lien et 0 variante créés |
| Unknown | **PASS** | aucune Family, Model ou MPN inventée depuis le titre |
| Compatibilité v1 | **PASS** | lecteurs publics et contrats Core v1 inchangés |
| Réversibilité | **PASS** | expansion Alembic isolée, flags processus, aucun writer public promu |

## Invariants relus en production

La lecture SQL après le replay établit :

- `gtins_split_across_variants=0` ;
- `variants_with_conflicting_gtins=0` ;
- `orphan_variants=0` ;
- `resolved_links_without_variant=0` ;
- `resolved_links=330` ;
- 7 identifiants possèdent plusieurs preuves, avec un maximum de 3 preuves
  par identifiant.

Ces sept identifiants multi-preuves représentent plusieurs offres convergeant
sur la même identité globale. Ils ne créent ni variantes concurrentes ni GTIN
contradictoires.

## Benchmark et CI

Le benchmark Product Identity autonome conserve ses résultats ratifiés :

- 10 565 / 10 565 checks ;
- 960 / 960 cas exact-product ;
- 3 840 / 3 840 résolutions Variant ;
- 2 880 / 2 880 rattachements Offer ;
- 0 faux merge sur 2 880 hard negatives, borne Wilson 95 % à 0,1332 % ;
- cinq verticales couvertes avec résultat identique et reproductible.

Le run GitHub Actions `33425556598` est terminal `success`. Ses quatre jobs
Web, Backend/contrats/Quality Lab, Extension et Mobile sont verts. Dans le job
Backend `99598128288`, migrations PostgreSQL, suite complète, Quality Lab
fail-closed et étape « Exécuter le benchmark Product Identity exact-product »
sont tous `success`.

## Interprétation des mesures réelles

La couverture exacte du lot est **33 %** (330/1 000) et l'abstention **67 %**
(670/1 000). Ces taux décrivent la présence de GTIN dans ce feed, pas la
qualité globale du catalogue. La décision correcte pour les 670 inconnus est
l'abstention : améliorer la couverture est une mission d'Entity Resolution,
pas une raison de relâcher le gate exact-product.

Les 330 offres exactes produisent 321 variantes et 321 identifiants. Les neuf
preuves supplémentaires au-delà d'une preuve par variante sont cohérentes
avec les identifiants multi-offres observés et ne créent aucune duplication.

## Limites non bloquantes

- corpus réel limité à un feed et 1 000 offres ;
- une seule source Awin qualifiée dans cette preuve ;
- Family, Model, MPN et attributs complexes restent inconnus sans source
  structurée ;
- aucun jugement humain indépendant n'est revendiqué ;
- performance du backfill ligne par ligne à optimiser avant extension au
  catalogue complet ;
- aucun lecteur public Product Graph activé à ce stade.

Ces limites sont transmises à Phase 2. Elles ne contredisent aucun gate de
sortie de Phase 1, dont la promesse est une identité exacte, sourcée,
abstentionniste et rejouable.
