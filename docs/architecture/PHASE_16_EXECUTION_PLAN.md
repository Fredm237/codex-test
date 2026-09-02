# Phase 16 — Personal Stylist

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-16-personal-stylist`

## Objectif

Composer jusqu'à trois propositions mesurables à partir d'une occasion, d'un
instant, d'un lieu, d'une météo applicable, d'un style déclaré, du dressing et
du budget. Le moteur doit proposer d'abord ce que la personne possède et
s'abstenir plutôt que d'inventer une compatibilité.

## Tranches

| Tranche | Preuve requise | État local |
|---|---|---|
| P16A — contrat | entrées, sorties, inconnues et abstentions versionnées | **GO** |
| P16B — contexte | occasion/style explicites et météo fraîche visant lieu/instant | **GO** |
| P16C — owned-first | aucun achat d'un rôle déjà couvert, coût dressing égal à zéro | **GO** |
| P16D — commerce | rôle, taille, offre, stock, devise et URL prouvés | **GO** |
| P16E — Quality Lab | corpus adversarial, zéro fausse solution, aucun score fabriqué | **GO** |
| P16F — shadow réel | replay borné sur contexte consentant et métriques agrégées | **NO-GO — non exécuté** |
| P16G — canary/public | cohorte, UX, appareil, rollback et garde-fous qualifiés | **NO-GO — non exécuté** |

## Politique fail-closed

Le moteur s'abstient si l'occasion ou le style manque, si la météo est absente,
périmée ou vise un autre lieu/instant, ou si ses propriétés exigeraient une
capacité vêtement non modélisée. Tout achat requis impose un budget positif et
une taille explicitement vérifiée sur la variante marchande. Les offres doivent
être actuelles, en stock, mono-devise EUR et dotées d'un lien sûr.

La compatibilité de style et d'occasion reste `not_calibrated` et son score reste
`null`. Une proposition n'est donc pas une vérité esthétique.

## Conditions SHADOW → CANARY

- 100 % des abstentions attendues restent fermées ;
- 0 offre périmée, hors stock, dangereuse, hors taille ou hors budget retenue ;
- 0 achat ajouté lorsqu'une pièce possédée couvre le même rôle ;
- 100 % des coûts dressing égaux à zéro ;
- 100 % des sorties sans score non calibré ;
- replay consentant, borné et sans contenu personnel brut dans les journaux ;
- effacement du contexte et rollback vérifiés.

## Conditions CANARY → PUBLIC

- activation réversible pour une cohorte explicite ;
- mesure ratifiée des abstentions, erreurs, latence et actions marchandes ;
- confirmation humaine avant toute navigation marchande ;
- accessibilité et textes d'incertitude qualifiés sur iOS/Android ;
- audit confidentialité des lieux, occasions, tailles et contenus de dressing ;
- activation coordonnée avec les lecteurs V2, Fashion et Wardrobe nécessaires.
