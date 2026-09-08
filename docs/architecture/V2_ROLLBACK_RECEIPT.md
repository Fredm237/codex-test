# FILON — Reçu de rollback V2 vers Core V1

- Verdict : **DARK → SHADOW/V1 PROUVÉ, RESTAURATION DARK PROUVÉE**
- Campagne : `sha256:d4160cb9a4e0aa08a9b7e3e61385fc7c31ada5f6f650a5d14b8d6fabc7109b8a`
- Qualification : `2026-09-08T19:54:54Z`

## Exercice réel

1. Le déploiement Railway `ca451c85-3a5a-4140-a320-ca2ee233eaf8` a ramené le
   mode de `dark` à `shadow`.
2. Une requête réelle de qualification a obtenu **HTTP 200** via Core V1.
3. Le compteur DARK est resté exactement à **30 avant et 30 après** la sonde :
   aucun calcul DARK n'a été écrit quand le mode était `shadow`.
4. Le déploiement `87b90c68-7179-4429-a629-e9db03e4537f` a restauré `dark`,
   avec readers canary/public OFF et Core V1 toujours servi.
5. Après restauration, `/health/live`, `/health/ready` et `/health` sont HTTP
   200 ; PostgreSQL et Redis sont `ok`, schéma `2d0f4a6c8e1b`.

Les tables shadow, checkpoints et journaux ont été conservés. Aucune migration
destructive, aucune perte de preuve et aucune réécriture d'historique n'ont eu
lieu.

## Portée exacte

Ce reçu prouve le retour **DARK → SHADOW/Core V1** pour la campagne et la
portée belges exactes. Il ne prétend pas prouver un retrait depuis CANARY ou
PUBLIC ; ces exercices doivent être liés à leurs futurs reçus.
