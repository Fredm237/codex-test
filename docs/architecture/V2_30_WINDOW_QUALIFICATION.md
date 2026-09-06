# FILON — Qualification des 30 fenêtres V2

- Verdict : **30/30 VALIDES**
- Campagne : `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d`
- Exécutions de progression : `4`, puis `6` à `34`
- Replay hors volume : `5`, source `4`

## Contrôles persistés

| Contrôle | Résultat |
|---|---|
| fenêtres distinctes | 30 |
| statuts terminaux `succeeded` | 30 |
| actives / failed / interrupted | 0 / 0 / 0 |
| première plage | 0 → 100, exécution `4` |
| dernière plage | 128 → 129, exécution `34` |
| curseur monotone / contigu / non chevauchant | oui / oui / oui |
| RAW réellement scannés | 129 |
| p95 des progressions | 28 282 ms |
| plafond ratifié | 30 000 ms |
| erreurs métier persistées | 0 |

La première fenêtre a commencé le `2026-09-04T21:02:30Z` et s'est terminée le
`2026-09-04T21:12:18Z`. La trentième s'est exécutée de
`2026-09-04T21:33:24Z` à `2026-09-04T21:33:46Z`.

## Résultat de couverture

Les 129 raws ont donné **81 `IDENTIFIED`**, **81 `RESOLVED`**, **48
`unresolved`/quarantaines**, puis zéro record à partir de `VERIFIED OFFER`.
Les 81 sorties acceptées sont restées `ABSTAIN`. Ce résultat est une preuve
positive du fail-closed et une preuve négative de couverture actionnable : il
ne peut qualifier ni `BUY_NOW` ni `WAIT`.

Les valeurs proviennent des 30 objets `v2-window-metrics/v1` persistés dans
`v2_chain_executions`, relus sans mutation le `2026-09-05T22:15:46Z`.
