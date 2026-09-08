# FILON — Qualification des 30 fenêtres V2 (Belgique)

- Verdict : **30/30 VALIDES**
- Campagne : `sha256:d4160cb9a4e0aa08a9b7e3e61385fc7c31ada5f6f650a5d14b8d6fabc7109b8a`
- Portée : `BE / fr-BE / smartphones / purchase_advice`
- Exécutions de progression : `70` à `99`
- Replay hors volume : `100`, source `70`

## Contrôles persistés

| Contrôle | Résultat |
|---|---|
| fenêtres distinctes | 30 |
| statuts terminaux `succeeded` | 30 |
| actives / failed / interrupted | 0 / 0 / 0 |
| première plage | 1277 → 1294, exécution `70` |
| dernière plage | 1770 → 1777, exécution `99` |
| curseur final | 1777 |
| curseur monotone / contigu / non chevauchant | oui / oui / oui |
| RAW réellement scannés | 500 |
| p95 des progressions | 82 325 ms |
| maximum observé | 82 933 ms |
| plafond background ratifié | 90 000 ms |
| erreurs métier persistées | 0 |

La première fenêtre s'est exécutée du `2026-09-08T18:36:58Z` au
`2026-09-08T18:38:20Z`. La trentième s'est exécutée du
`2026-09-08T19:19:25Z` au `2026-09-08T19:20:12Z`.

Le plafond historique de 30 secondes n'est **pas** déclaré réussi : le p95
mesuré est 82 325 ms. La politique de ce writer asynchrone, sans effet sur la
latence utilisateur, est portée à 90 secondes pour cette qualification. Le
lecteur DARK conserve une mesure séparée sur le chemin HTTP.

## Replay exact

L'exécution `100` a rejoué l'exécution `70` avec les mêmes bornes `1277 →
1294`, le même instant d'évaluation et les mêmes checkpoints. Elle a produit
le même identifiant déterministe :

`sha256:02c4a00f263841e201bcd316af2488895ee67c4a4b4f5359c74f0af4f49644a5`.

Le replay est terminal `succeeded`, n'a pas avancé le curseur de progression et
n'est pas compté dans les 30 fenêtres.

## Résultat de couverture

Les 500 raws ont tous été placés en quarantaine avant `IDENTIFIED`. Aucun
record n'a franchi une étape métier ultérieure et aucune sortie actionnable
n'a été inventée. Cette campagne prouve le comportement fail-closed, la
mono-exécution, les checkpoints et l'idempotence. Elle ne qualifie ni
`BUY_NOW`, ni `WAIT`, ni `FACTUAL_OPTIONS`.
