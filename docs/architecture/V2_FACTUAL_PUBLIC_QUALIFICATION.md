# FILON — Qualification publique V2 factuelle

## Verdict avant promotion

La campagne `sha256:f74167696ec2db95509be9fa1a5f8187a51c2bad95981e001d228fd2c91aa9f9`
a franchi le canary fermé pour `FACTUAL_OPTIONS` sur les verticales `audio` et
`smartphones`, les locales `fr` et `fr-BE`, le pays `BE` et la décision
`purchase_advice`.

Le lot contient **30 observations canary appariées** : 30 réponses V2
`FACTUAL_OPTIONS`, aucune réponse partielle, aucun fallback après éligibilité,
aucune erreur lecteur, 30 provenances complètes et aucune requête brute
persistée. Le p95 `latence V2 - latence Core V1` est de **-3 966 291 µs**.

Ce document ne vaut pas activation. La publication exige encore un reçu
append-only `PUBLIC_AUTHORIZED` calculé depuis cette filiation exacte.

## Repli exercé en production

Le canary a été basculé vers `dark` avec les deux lecteurs promus désactivés.
Le déploiement `da51ae4e-0f71-4e95-9265-39e736ce1826` a continué à servir Core
V1 en HTTP 200, sans trace ni alternative V2. Le journal canary est resté
intact. Le mode canary qualifié a ensuite été restauré par le déploiement
`e7ef37df-7896-4fe5-ab9b-4b7ce87dc640` avec lecteur public OFF.

## Portée publique candidate

La promotion demandée est atomiquement limitée à `FACTUAL_OPTIONS`. Ces
options exposent des offres réelles avec preuve fraîche et provenance complète,
mais ne constituent jamais implicitement une recommandation ni un verdict
d'achat.

`BUY_NOW` et `WAIT` restent bloqués : le funnel persistant ne contient encore
aucune ligne rankable, optimizable, calibrated ou actionable. Tout périmètre
non autorisé et toute erreur conservent la réponse Core V1 entière.

La preuve machine est conservée dans
`docs/architecture/V2_FACTUAL_PUBLIC_QUALIFICATION_EVIDENCE.json`.
