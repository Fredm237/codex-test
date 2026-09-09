# FILON — Qualification publique V2 factuelle

## Verdict final

La campagne `sha256:f74167696ec2db95509be9fa1a5f8187a51c2bad95981e001d228fd2c91aa9f9`
a franchi le canary fermé pour `FACTUAL_OPTIONS` sur les verticales `audio` et
`smartphones`, les locales `fr` et `fr-BE`, le pays `BE` et la décision
`purchase_advice`.

Le lot contient **30 observations canary appariées** : 30 réponses V2
`FACTUAL_OPTIONS`, aucune réponse partielle, aucun fallback après éligibilité,
aucune erreur lecteur, 30 provenances complètes et aucune requête brute
persistée. Le p95 `latence V2 - latence Core V1` est de **-3 966 291 µs**.

La promotion publique bornée est désormais **active et prouvée**. Elle repose
sur le reçu append-only `PUBLIC_AUTHORIZED`
`sha256:b280e4f43efc9c92eb9967b6a947728add5b0ca5073958f7dd25e5aa048fac13`,
créé une seule fois puis retrouvé à l'identique au replay. Son gate est
`sha256:2a07332e34fd46396c0680d15b336e7da973c22ed7403151025d3a9fdc2791e5`.

## Repli exercé en production

Le canary a été basculé vers `dark` avec les deux lecteurs promus désactivés.
Le déploiement `da51ae4e-0f71-4e95-9265-39e736ce1826` a continué à servir Core
V1 en HTTP 200, sans trace ni alternative V2. Le journal canary est resté
intact. Le mode canary qualifié a ensuite été restauré par le déploiement
`e7ef37df-7896-4fe5-ab9b-4b7ce87dc640` avec lecteur public OFF.

## Portée publique active

La promotion est atomiquement limitée à `FACTUAL_OPTIONS`. Ces
options exposent des offres réelles avec preuve fraîche et provenance complète,
mais ne constituent jamais implicitement une recommandation ni un verdict
d'achat.

`BUY_NOW` et `WAIT` restent bloqués : le funnel persistant ne contient encore
aucune ligne rankable, optimizable, calibrated ou actionable. Tout périmètre
non autorisé et toute erreur conservent la réponse Core V1 entière.

La preuve machine est conservée dans
`docs/architecture/V2_FACTUAL_PUBLIC_QUALIFICATION_EVIDENCE.json`.

## Preuve de service public

Le commit de correction `f5f30d99961617d1ca36d213de12c5ca9fe900af` a passé
les quatre jobs du run GitHub Actions `34402385399`. Railway sert le
déploiement `c371a3be-981b-424b-a2b8-a11dbaf3618a`, instance
`7869b81d-f832-4a9e-b25f-15354d61bdf6`, avec le mode `public`, le lecteur
public ON, le lecteur canary OFF et le reçu exact ci-dessus.

Deux requêtes non personnelles ont ensuite exercé les deux chemins attendus :

- l'observation `182` a conservé Core V1 lorsque V2 a produit un type non
  autorisé, avec le motif neutre `response_type_not_qualified` et l'état sûr
  `ABSTAIN` ;
- l'observation `183` a servi une vraie option audio V2 `FACTUAL_OPTIONS`,
  avec provenance complète, état `SAFE` et aucun verdict d'achat implicite.

Le contrôle terminal
`sha256:b71c275640a6366c777da4304614c115753d26556964dc0134fe72ce5079cd06`
rapporte 2 observations publiques, 1 fallback public et **0 violation de
sûreté**. Les quatre sondes publiques répondent HTTP 200, PostgreSQL et Redis
sont `ok`, aucune fenêtre V2 n'est active et le schéma Alembic est
`2d0f4a6c8e1b`.

## Limite honnête

La V2 ne remplit pas encore toute la promesse FILON. Elle sert aujourd'hui des
options factuelles qualifiées en Belgique pour `audio` et `smartphones`. Les
verdicts `BUY_NOW` et `WAIT`, ainsi que les étapes ranking, optimisation et
calibration qui n'ont pas encore de corpus production admissible, restent
fermés. Dans tous ces cas, Core V1 demeure la réponse publique complète.
