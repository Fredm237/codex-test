# FILON — Phase 12 Extension Execution Plan

- Ouverture : **2 septembre 2026**
- Gate d'entrée : **Phase 11F qualifiée localement**
- Statut : **P12A/P12B QUALIFIÉS LOCALEMENT ; P12C NON RACCORDÉ**
- Manifest : **V3 conservé**
- Transmission automatique : **OFF**
- Lecteurs V2 publics : **OFF**

## Objective

Transformer l'extension en surface d'observation exacte sans y créer un second
cerveau. Elle extrait les preuves de la page ; le Core demeure seul
propriétaire de l'Entity Resolution, de la vérité d'offre et de la décision.

## Architecture

```text
page marchande
  → extracteur local borné
  → action explicite utilisateur
  → GTIN exact : fiche /produits/{gtin}
  → sinon : recherche par titre borné

transport futur, après autorisation dédiée :
  → Page Product Observation v1
  → Core Observation Store append-only
  → Entity Resolution Core
  → comparaison courante fail-closed
```

## Lots and gates

| Lot | Livrable | Gate |
|---|---|---|
| P12A | baseline, dépendances et frontière de responsabilité | aucun moteur de décision dans l'extension |
| P12B | contrat, extracteur local et navigation exacte | GTIN/prix/devise/URL adversariaux à 100 % |
| P12C | transport explicite vers le Core | consentement, destination, rate limit et writer OFF par défaut |
| P12D | capture Observation + Entity Resolution | append-only, idempotence, faux merge nul |
| P12E | comparaison instantanée | même variante, devise unique, preuves courantes |
| P12F | Quality Lab et package store | benchmark vert, permissions minimales, zip reproductible |
| P12G | production canary | CI, déploiement, sondes, métriques et reçu terminal |

## Data contract

Le contrat `extension-observation/v1` autorise uniquement URL canonique,
marchand, titre, marque, SKU, MPN, GTIN, prix avec devise, disponibilité,
variante, présence/noms de champs JSON-LD et horodatage. HTML, cookies,
référent, formulaires, identifiants de personne, requête et fragment sont
interdits.

## Migration plan

P12A/P12B ne modifient aucune table. Le prototype de projection P12D réutilise
les tables append-only `raw_source_records` et `observations`, déjà migrées et
réversibles par arrêt du writer. Si le transport public exige plus tard un
journal de consentement ou une rétention dédiée, une migration additive
séparée devra précéder son activation ; aucune DDL implicite n'est admise.

## Tests and benchmark

- schémas Draft 2020-12 et exemples synthétiques ;
- extraction JSON-LD simple, `@graph`, multi-produits et AggregateOffer ;
- checksum GTIN, prix/devise, disponibilité tri-state et URL sûre ;
- projection Core déterministe et persistance idempotente ;
- benchmark adversarial de 12 cas ;
- test statique interdisant tout `fetch` dans l'extension tant que P12C n'est
  pas autorisé.

Résultats actuels : benchmark **12/12**, projection Core **12/12**, régression
backend **2 599 réussis + 1 test loopback réussi isolément**, **3 ignorés** et
aucun échec applicatif.

## Promotion conditions

1. **SHADOW** : transport explicitement autorisé, writer isolé OFF par défaut,
   100 % des payloads conformes, replays identiques sans doublon.
2. **CANARY** : échantillon opt-in, aucune collecte en arrière-plan, zéro URL
   avec query/fragment, faux merge nul, exact GTIN et comparaison courante
   prouvés en production.
3. **PUBLIC** : taux de résolution et d'abstention documentés sur trafic réel,
   rétention/effacement audités, permissions store revues et rollback testé.

La progression P12C est volontairement arrêtée au gate d'autorisation du
payload réseau. Cela ne bloque ni les tests locaux, ni la construction des
composants Core sans transport.
