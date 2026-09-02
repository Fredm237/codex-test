# Phase 14 — Fashion Expert V1

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-14-fashion-v1`

## Objectif

Qualifier un premier expert Fashion déterministe, explicable et fail-closed,
sans transformer une préférence, une occasion ou une relation stylistique en
fait catalogue. Product Core conserve l'identité, les offres, les prix, stocks,
devises et horodatages.

## Tranches

| Tranche | Preuve requise | État local |
|---|---|---|
| P14A — contrat | Schéma v1, états recommend/abstain, scores non calibrés à `null` | **GO** |
| P14B — filtrage | prix, devise, stock, fraîcheur et pièce principale prouvés | **GO** |
| P14C — composition | mono-devise, budget explicite, identité Core préservée | **GO** |
| P14D — critique | lacunes listées sans pénalité ou probabilité arbitraire | **GO** |
| P14E — Quality Lab | corpus indépendant ≥ 10 cas, zéro faux recommend, identité exacte | **GO** |
| P14F — canary | writers/lecteurs publics OFF ; replay shadow borné et métriques réelles | **NO-GO — non exécuté** |
| P14G — public | corpus réel, stabilité, sécurité, accessibilité et rollback qualifiés | **NO-GO — non exécuté** |

## Gouvernance humaine

`NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` autorise la progression des
gates techniques. Il interdit en revanche d'afficher un Style Score, un score de
relation ou une probabilité de confiance comme s'ils étaient calibrés. Les
feedbacks explicites peuvent être collectés avec consentement, mais ne deviennent
pas automatiquement une vérité universelle.

## Conditions SHADOW → CANARY

1. 100 % des cas d'abstention ingénierie attendus restent des abstentions ;
2. 0 offre sans preuve courante ou hors stock retenue ;
3. 0 composition multidevise ;
4. 100 % des identités sélectionnées correspondent aux identités Core ;
5. 100 % des sorties gardent les scores subjectifs à `null` ;
6. replay réel borné et idempotent, avec résultats agrégés sans payload brut ;
7. aucun lecteur public actif avant revue du canary.

## Conditions CANARY → PUBLIC

- cohorte explicite et réversible ;
- taux d'erreur, abstention, latence et actions invalides sous les seuils ratifiés
  avant activation ;
- confirmation que les utilisateurs voient les limites et peuvent corriger ou
  refuser une recommandation ;
- audit de confidentialité des intentions et feedbacks ;
- rollback testé ;
- activation coordonnée avec les lecteurs Product Core nécessaires, jamais avec
  les tables shadow directement.
