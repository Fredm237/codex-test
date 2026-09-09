# FILON — Qualification V2 factuelle avant canary

## Verdict

La campagne `sha256:f74167696ec2db95509be9fa1a5f8187a51c2bad95981e001d228fd2c91aa9f9`
possède désormais une preuve réelle de `FACTUAL_OPTIONS` en Belgique, en plus
de l'abstention fail-closed. Elle est **candidate au canary fermé** pour les
verticales `audio` et `smartphones`, les locales `fr` et `fr-BE`, le pays `BE`
et la décision `purchase_advice`.

Ce verdict n'active aucun lecteur. Core V1 reste servi tant qu'un reçu
`CANARY_AUTHORIZED` exact n'est pas persisté et désigné par la configuration.
`BUY_NOW` et `WAIT` restent interdits.

## Preuves persistées observées

- 41 fenêtres `progression` terminales et réussies : 30 smartphones, 11 audio ;
- 687 lignes réelles auditées, sans sélection favorable ;
- 654 lignes identifiées, résolues et vérifiées ;
- 604 ontologies vérifiées et 519 lignes admissibles ;
- zéro fenêtre active, échouée ou interrompue ;
- curseurs contigus par verticale et exécutions non concurrentes ;
- replay `136` de l'exécution `135` : mêmes bornes et même identité ;
- 38 observations DARK françaises et belges complètes ;
- 37 `ABSTAIN` et une `FACTUAL_OPTIONS` réelle ;
- observation factuelle `134` : un candidat, chaîne et provenance complètes,
  état `SAFE`, classification `BOTH_VALID` ;
- aucune requête brute conservée et aucune influence sur la réponse Core V1.

## Politique de performance

Le writer est un traitement de fond, jamais le chemin de réponse utilisateur.
Sur les 41 fenêtres réelles, son p95 est de **149 780 ms** et son maximum de
**155 739 ms**. La borne de qualification est fixée mécaniquement à **160 000
ms**, soit le maximum observé arrondi au prochain multiple de dix secondes :

`ceil(155739 / 10000) * 10000 = 160000`.

Cette borne ne remplace pas le SLO du lecteur en ligne. Le canary mesure
séparément la latence appariée Core V1/V2 et reste fail-closed si le lecteur
V2 régresse, échoue ou perd sa provenance.

## Portée autorisable

Le prochain reçu SHADOW → CANARY peut autoriser uniquement les types observés
`ABSTAIN` et `FACTUAL_OPTIONS`. Le passage PUBLIC demandera une qualification
canary appariée dédiée ; il pourra être restreint à `FACTUAL_OPTIONS` si c'est
le seul type à publier. Aucun résultat non observé n'est promu implicitement.

La preuve machine complète est conservée dans
`docs/architecture/V2_FACTUAL_CANARY_QUALIFICATION_EVIDENCE.json`.
