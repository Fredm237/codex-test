# FILON — politique provisoire de fraîcheur des offres

Date : 29 août 2026
Référence : `f5ae21b`

## Décision

Une offre ne peut participer à une recommandation `/advise` ou au moteur de
décision générale que si l'observation prix/stock :

- porte un horodatage lisible ;
- n'est pas datée dans le futur ;
- a au plus **72 heures**.

Une date absente, invalide, future ou expirée rend l'offre inéligible. Elle ne
devient ni un stock disponible, ni un prix actuel, ni une valeur zéro. La
devise et `observed_at` sont conservés dans le contrat additif `advise-offer`
afin que le montant rendu reste auditable.

## Périmètre exact

Le seuil de 72 heures reprend la frontière déjà utilisée par le Decision
Service pour qu'un prix récent renforce une décision. Il est désormais partagé
par le comparateur historique et le planificateur général. Pour les
consommateurs Core déjà durcis, `offers.updated_at` n’est plus une preuve : le
prix, la devise et le stock doivent correspondre à un `PriceSnapshot`
append-only. Ce contrat est maintenant appliqué aux endpoints publics du
catalogue par le commit `4a95a42` ; l'intégration et ses preuves sont consignées
dans la [prévalidation devenue post-validation](PROTECTED_TRUTH_INTEGRATION_PREFLIGHT.md).

Cette règle ne prétend pas que prix et stock ont naturellement le même TTL. Le
mandat cible des durées distinctes — stock très court, prix court, identité et
attributs plus longs — mais leur ratification exige une cadence d'ingestion
réelle, des timestamps de source et une mesure de dérive. Jusqu'à cette preuve,
72 heures est une frontière provisoire fail-closed, pas un SLO de production.

## Invariants associés

- livraison absente reste `unknown`, jamais gratuite ;
- un montant sans devise EUR n'entre pas dans `/advise` ;
- deux devises ne sont jamais comparées sans moteur FX ;
- un total non fini, une remise impossible ou un montant déjà hors budget est
  exclu avant classement ;
- une recommandation non calibrée du parcours général reste `null` /
  `not_calibrated` et « non mesuré » dans le client web ; son abstention
  historique `0`/`low` reste à normaliser et ne doit pas être interprétée comme
  une calibration. Le score heuristique distinct de Fashion n'est pas couvert
  par cette preuve et reste également à supprimer ou calibrer.

## Preuve et prochaine gate

Les tests ciblés couvrent dates absentes, invalides, futures, à la frontière et
expirées, ainsi que les deux moteurs consommateurs. L'état cumulé
`f5ae21b` + `45e7768` passe **1 659/1 659 tests backend** le 29 août 2026.

La gate de production reste ouverte : introduire des timestamps de source,
ratifier un TTL par type de claim et verticale à partir de la cadence réelle,
mesurer la couverture/fraîcheur, puis versionner la politique et son rollback.
