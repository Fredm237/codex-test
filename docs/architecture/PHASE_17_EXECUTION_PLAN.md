# Phase 17 — Solution Composer

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-17-solution-composer`

## Objectif

Assembler des solutions complètes `outfit`, `setup`, `kit` ou `routine` en
réemployant d'abord les éléments possédés. Chaque rôle obligatoire doit être
couvert par une preuve et le moteur s'abstient sans renvoyer une solution
partielle lorsque l'intégrité n'est pas démontrable.

## Tranches

| Tranche | Preuve requise | État local |
|---|---|---|
| P17A — contrat | quatre domaines, slots, résultat et abstention versionnés | **GO** |
| P17B — contraintes | seuls les composants `ELIGIBLE` couvrent un rôle | **GO** |
| P17C — owned-first | élément possédé prioritaire et coût marginal nul | **GO** |
| P17D — Offer Truth | offre `VERIFIED`, non dupliquée, mono-devise et sous budget | **GO** |
| P17E — Quality Lab | ≥ 10 cas, zéro fausse composition ou score inventé | **GO** |
| P17F — shadow réel | journal append-only et replay borné sur corpus réel | **NO-GO — non exécuté** |
| P17G — canary/public | chaîne V2, personnalisation et rollback coordonnés | **NO-GO — non exécuté** |

## Conditions SHADOW → CANARY

- 100 % des rôles obligatoires couverts, sinon abstention atomique ;
- 0 composant `UNKNOWN`, `EXCLUDED`, partiel, périmé ou quarantiné sélectionné ;
- 0 achat lorsqu'un élément possédé éligible couvre le rôle ;
- 0 doublon connu avec les possessions ;
- 0 mélange ou conversion de devise ;
- 100 % des solutions sous budget explicite ;
- replay borné, idempotent et sans contexte personnel brut retenu ;
- cohérence vérifiée avec Constraint Engine, Offer Truth, Ranking et
  Offer Optimization.

## Conditions CANARY → PUBLIC

- cohorte explicite, réversible et consentante ;
- seuils de solution, abstention, erreur, latence et clics marchands ratifiés ;
- confirmation humaine avant action marchande ;
- explications par rôle et inconnues accessibles ;
- tests de suppression du contexte, rollback et non-régression multi-domaine ;
- promotion atomique avec les lecteurs V2 nécessaires, jamais directement sur
  une table shadow.
