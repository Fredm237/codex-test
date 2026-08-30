# ADR-005 — Evidence Engine et Claim Eligibility shadow

- Statut : **proposed / implémenté en shadow local**
- Date : 31 août 2026
- Révision expand : `e8c3f6a0b5d2`
- Policy : `claim-eligibility-shadow-v1`

## Contexte

Le mandat interdit qu'une valeur absente, périmée ou non calibrée devienne un
fait favorable, une confiance ou une recommandation. Les shadows Product,
Offer et Merchant fournissent la provenance technique, mais aucun registre ne
matérialisait encore, claim par claim, ce qui est vérifié, inconnu ou interdit.

## Décision

1. `evidence_claim_records` conserve chaque évaluation append-only avec sujet,
   valeur, statut `VERIFIED`/`INFERRED`/`UNKNOWN`, source, observation, fenêtre
   de validité, éligibilité, raison et version de policy.
2. Une valeur n'est présente que si le claim est `VERIFIED` et `eligible`.
   Aucune confiance n'est fabriquée : `confidence` reste `NULL` sans calibration.
3. Quatre faits atomiques peuvent devenir éligibles : prix observé, disponibilité
   observée, lien marchand observé et identité variante exacte.
4. Les claims forts `LOWEST_OBSERVED_PRICE`, `BEST_VERIFIED_OFFER`, `BUY_NOW`,
   `WAIT`, `HIGH_CONFIDENCE`, `CERTIFIED_REFURB` et `MAX_CASHBACK` restent
   explicitement inéligibles en v1 faute de couverture, shipping/pays,
   calibration, certification ou couverture cashback.
5. `decision_eligibility_records` conserve le plus haut niveau autorisé :
   `DISCOVERABLE`, `COMPARABLE`, `RANKABLE` ou `DECISION_ELIGIBLE`.
6. La v1 ne produit jamais `DECISION_ELIGIBLE` : pays et shipping ne sont pas
   observés. Une offre hors stock peut être comparable mais jamais classable.
7. Les faits d'offre expirent provisoirement après 72 heures. Une observation
   future est invalide. L'identité exacte ne reçoit pas de TTL arbitraire.
8. Le backfill est dry-run par défaut, borné à 10 000 raws, cursorisé et
   idempotent. Son apply exige les cinq flags shadow.

## Conséquences

- Les absences de preuve et prérequis deviennent interrogeables sans influencer
  les endpoints v1.
- Un claim fort ne peut pas être déduit de la simple présence d'un prix ou d'un
  marchand affilié.
- Le passage à une lecture v2 exige encore le holdout humain, la calibration,
  la couverture pays/shipping et une policy ratifiée.

## Rollback

Couper `EVIDENCE_ENGINE_SHADOW_ENABLED`. Conserver les deux tables et leurs
preuves ; aucun lecteur public ne les consulte. Un downgrade structurel est
réservé aux bases éphémères ou à une restauration sauvegardée.
