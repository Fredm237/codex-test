# FILON — Reçu de rollback V2 vers Core V1

- Verdict : **DARK → SHADOW/V1 PROUVÉ, RESTAURATION DARK PROUVÉE**
- Campagne : `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d`
- Qualification : `2026-09-04T21:54:42Z`

## Exercice réel

1. Le déploiement Railway `c0ad9f93-2645-44b6-a04b-4022f299a653` a ramené le
   mode de `dark` à `shadow`.
2. Une requête de production a obtenu **HTTP 200** via Core V1.
3. Le compteur DARK est resté exactement à **30 avant et 30 après** la sonde,
   prouvant que le lecteur DARK ne s'exécutait plus.
4. Le déploiement `4c4fed4d-f355-4b5a-8211-e86c4258e555` a restauré le mode
   `dark`, avec readers canary/public OFF et Core V1 toujours servi.

Les tables shadow, checkpoints et journaux ont été conservés. Aucune migration
destructive, aucune perte de preuve et aucune réécriture d'historique n'ont eu
lieu.

## Portée exacte

Ce reçu prouve le retour **DARK → SHADOW/Core V1**. Il ne prétend pas prouver
un rollback depuis un canary ou un public réellement activé. Ces exercices
restent associés à leurs futurs reçus et ne doivent pas être déclarés à partir
de cette preuve.
