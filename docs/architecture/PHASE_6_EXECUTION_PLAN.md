# FILON — Phase 6 Constraint Engine Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **TERMINÉ — PHASE 6 SHADOW = GO**
- Gate d'entrée : Phase 5 Hybrid Retrieval terminale avec verdict GO
- Lecteurs publics : **INCHANGÉS**
- Ranking et personnalisation : **HORS PÉRIMÈTRE DE PROMOTION**

## Avancement

| Lot | État | Preuve attendue |
|---|---|---|
| P6A — contrat | **TERMINÉ** | ADR-011, schéma v1, manifest et trois exemples synthétiques |
| P6B — baseline réelle | **TERMINÉ** | 1 run/candidat/offre ; Cron réaligné sur `main`, déploiement réussi, prochain schedule à observer |
| P6C — benchmark | **TERMINÉ** | 4 608 cas, moteur sûr PASS, legacy UNSAFE |
| P6D — moteur dur | **TERMINÉ** | 0 faux éligible, 0 unknown favorable, provenance 100 % |
| P6E — préférences | **TERMINÉ** | tableau séparé, aucun score ni réintroduction |
| P6F — shadow | **TERMINÉ** | migration `a8d6f0b2c4e7`, writer OFF, idempotence PostgreSQL |
| P6G — replay réel | **TERMINÉ** | dry → create → existing sur une fenêtre de 1 run |
| P6H — comparaison | **TERMINÉ** | qualité, couverture, latence et limites publiées |
| P6I — revue de sortie | **TERMINÉ** | Phase 6 shadow GO ; ouverture Phase 7 Product Ranking |

## Invariants

1. `unknown` n'est jamais une contrainte satisfaite.
2. Une seule contrainte dure non satisfaite suffit à exclure.
3. Une préférence n'annule jamais une exclusion ou une abstention.
4. Le moteur ne produit aucun score, ordre, offre gagnante ou verdict Buy/Wait.
5. Chaque résultat possède un motif et, lorsqu'elle existe, une preuve.
6. Le contexte brut et le profil personnel ne sont jamais persistés.
7. Affiliation et commission ne participent à aucune évaluation.
8. Le writer reste OFF et aucun lecteur public ne change avant la revue finale.

## Séquence

1. Figer le contrat et les états fermés.
2. Mesurer la couverture réelle des faits utilisables sans publier de payload.
3. Construire un holdout synthétique, déterministe et adversarial.
4. Implémenter le moteur dur fail-closed.
5. Ajouter les observations de préférence sans scoring.
6. Ajouter la persistance append-only et la migration réversible.
7. Rejouer un lot production borné et prouver l'idempotence.
8. Publier la comparaison et décider GO/NO-GO vers Phase 7.
