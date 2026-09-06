# FILON — Reçu Continuous Shadow V2

- Statut terminal : **SHADOW QUALIFIED**
- Campagne : `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d`
- Révision : `3fb33d5a776511ca8da3c16876715aa5fa3cc79c`
- Schéma : `f9c7d1e3a5b8`
- Qualification : `2026-09-04T21:54:42Z`

## Preuve d'exécution continue

Les writers atomiques P0/P1–P10 étaient ON et les lecteurs canary/public OFF.
La campagne a persisté 30 fenêtres `progression` distinctes, toutes
`succeeded`, sur le curseur `smartphones` 0 → 129. Il n'existait aucun lease
actif à la clôture, aucun échec, aucune interruption, aucun trou et aucun
chevauchement.

Le p95 des fenêtres réelles était de **28 282 ms**, sous le plafond ratifié de
**30 000 ms**. Les sondes `live`, `ready` et `health` répondaient HTTP 200 ;
PostgreSQL et Redis étaient `ok`.

## Idempotence et sécurité

L'apply `4` et son replay exact `5` partagent l'identité
`sha256:7d701379fec01f8eb218b95f1f728ef6d15ae13c85987986fdbc9f0e65c5a07b`.
Le replay n'a ni créé de volume supplémentaire ni avancé le curseur. Les
129 raws ont produit 81 résolutions, 48 quarantaines, zéro erreur et aucune
sortie actionnable inventée.

Le journal ne retient ni payload brut, ni requête, ni contexte utilisateur, ni
secret. Core V1 est resté le seul résultat servi.

## Frontière

Ce reçu qualifie le writer SHADOW continu et son orchestration. Il n'autorise
pas à lui seul CANARY ou PUBLIC. Le détail exhaustif du funnel se trouve dans
`V2_COVERAGE_FUNNEL.md`; les preuves canary restent limitées à `ABSTAIN`.
