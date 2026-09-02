# Phase 18 — Personal Commerce Model

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-18-personal-commerce`

## Objectif

Choisir une solution personnelle cross-domain sans maximiser les achats. La
politique réemploie les solutions complètes de Phase 17, exige le consentement,
n'utilise que les préférences explicitement déclarées et conserve exactement
les décisions BUY/WAIT qualifiées en amont.

## Tranches

| Tranche | Preuve requise | État local |
|---|---|---|
| P18A — contrat | consentement, préférences, actions et inconnues versionnés | **GO** |
| P18B — sélection | politique déterministe sans score ni priorité commerciale | **GO** |
| P18C — owned-first | `USE_WHAT_YOU_OWN` avant toute solution achetée | **GO** |
| P18D — BUY/WAIT | action amont et preuve obligatoires, budget/devise respectés | **GO** |
| P18E — Quality Lab | ≥ 10 cas, zéro bypass consentement ou fausse action | **GO** |
| P18F — shadow réel | journal append-only, effacement et replay borné | **NO-GO — non exécuté** |
| P18G — canary/public | cohorte cross-domain et chaîne V2 atomique qualifiées | **NO-GO — non exécuté** |

## Ordre lexicographique public

La politique n'additionne aucun poids arbitraire. Parmi les solutions complètes
et éligibles, elle minimise d'abord le nombre d'achats, maximise ensuite le
nombre d'éléments possédés, respecte les préférences positives explicites, puis
minimise le coût comparable. L'identifiant stable tranche uniquement une
égalité totale. Une préférence négative explicite exclut la solution.

Commission, rémunération d'affiliation et relation marchande ne sont pas des
entrées du moteur.

## Conditions SHADOW → CANARY

- 0 décision personnelle sans consentement actif ;
- 0 préférence implicite ou contradictoire utilisée ;
- 0 solution Phase 17 incomplète ou contrainte inconnue sélectionnée ;
- 0 altération d'une preuve BUY/WAIT ;
- 0 dépassement de budget ou mélange de devise ;
- 0 priorité fondée sur l'affiliation ;
- 100 % des résultats sans score non calibré ;
- replay réel borné, idempotent, effaçable et sans contexte brut conservé.

## Conditions CANARY → PUBLIC

- activation atomique et réversible de la chaîne V2 nécessaire ;
- cohorte consentante, export et effacement de ses données vérifiés ;
- seuils ratifiés d'abstention, erreur, latence, correction et action marchande ;
- explications accessibles indiquant pourquoi, ce qui est inconnu et ce qui est
  possédé ;
- test de neutralité affiliée et rollback terminal ;
- aucune promotion d'un writer ou lecteur shadow isolé.
