# FILON — Phase 8 Offer Optimization Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **TERMINÉE — PHASE 8 = GO**
- Gate d'entrée : Phase 7 Product Ranking shadow terminale avec verdict GO
- Lecteurs publics : **INCHANGÉS**
- Activation persistante : **OFF**

## Lots

| Lot | État | Preuve attendue |
|---|---|---|
| P8A — contrat | **TERMINÉ V2** | ADR-014, schéma v2, manifest et exemples synthétiques |
| P8B — baseline | **TERMINÉ** | séparation produit/offre et preuves disponibles explicites |
| P8C — benchmark | **PASS LOCAL** | 5 760 cas, contrôle sûr PASS, legacy commercial UNSAFE |
| P8D — moteur | **TERMINÉ V2** | coût livré, cashback, retours, fiabilité, fraîcheur |
| P8E — neutralité | **TERMINÉ** | commission, affiliation et revenu absents des entrées |
| P8F — shadow | **PASS LOCAL V2** | migration `d1a9c3e5f7b0`, writer OFF, idempotence |
| P8G — replay borné | **PASS PRODUCTION** | dry/apply/replay sans fallback |
| P8H — revue de sortie | **GO** | CI, migration, santé et reçu terminal |

## Invariants

1. Une offre ne peut être optimisée que pour le produit classé numéro un.
2. `BEST PRODUCT` reste distinct de `BEST OFFER`.
3. Une offre doit être `VERIFIED`, disponible et reliée au produit exact.
4. Le coût livré vaut prix + livraison - cashback dans une devise explicite.
5. Cashback, retours, fiabilité marchand et fraîcheur doivent être connus et sourcés.
6. Commission, affiliation et revenu FILON ne sont jamais des entrées.
7. Une inconnue provoque `UNOPTIMIZABLE` ou une abstention, jamais un fallback.
8. Aucun contexte brut ni profil utilisateur n'est persisté.
9. Le writer reste OFF et aucun lecteur public ne change avant la revue finale.
10. `NO_EXTERNAL_HUMAN_GROUND_TRUTH` demeure non bloquant sans être transformé
    en validation humaine.

## Reçu local

- tests ciblés Phase 8, contrats, configuration et migration : PASS ;
- benchmark autonome v2 : PASS sur 5 760 cas ;
- suite backend : 2 528 tests PASS, 3 intégrations PostgreSQL réservées à la CI ;
- l'unique contrôle utilisant un récepteur OTLP loopback passe hors restriction
  de port du bac à sable ;
- aucun lecteur public, flag persistant ou état de production n'a été modifié.
