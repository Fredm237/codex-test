# ADR-004 — Merchant Intelligence measurement shadow

- Statut : **proposed / implémenté en shadow local**
- Date : 31 août 2026
- Révision expand : `d7b2e5f9a4c1`
- Policy : `merchant-measurement-shadow-v1`

## Contexte

Le mandat exige une couche marchand couvrant relation commerciale, fraîcheur,
couverture, fiabilité de livraison, retours, garantie, support, paiement,
exactitude prix et seller type. Les raws Awin et les deux Graphs ne prouvent
qu'une partie de ces dimensions. Une note globale calculée sur cette preuve
partielle serait trompeuse.

## Décision

1. `merchant_quality_snapshots` stocke des fenêtres append-only de compteurs
   bruts, sans `score`, `confidence`, bonus ni malus.
2. Les dénominateurs sont conservés avec les numérateurs : raws, observations
   offre, GTIN connu, prix connu/frais, stock connu, lien connu/invalide,
   identité résolue et offre éligible.
3. `joined=true` signifie seulement `AFFILIATED`. `DIRECT_PARTNER` et
   `MARKETPLACE` exigent une preuve distincte et ne sont jamais déduits.
4. La région Awin peut rendre `merchant_country` observé, mais ne prouve pas
   `ships_to_country`.
5. Livraison, retours, garantie, support, sécurité paiement, seller type,
   exactitude prix après clic, stabilité, mismatch stock et shipping restent
   `not_measurable` ou `unknown` tant que leurs observations n'existent pas.
6. Le taux de lien invalide est seulement syntaxique. Aucun test HTTP live ni
   taux de lien cassé réel n'est revendiqué.
7. Le temps d'évaluation est explicite, avec offset UTC obligatoire. Un raw
   futur produit `invalid_future`, jamais une fraîcheur positive.
8. Le backfill est dry-run par défaut, borné à 10 000 raws, cursorisé et
   idempotent. Son apply exige les quatre flags shadow.

## Conséquences

- Les rapports peuvent montrer couverture et lacunes sans fabriquer une
  fiabilité marchande.
- Ces mesures n'influencent ni Offer Quality, ni ranking, ni clients avant un
  protocole indépendant et une décision GO.
- La feedback loop réelle exigera des retours après clic/achat, incidents,
  shipping et politiques marchands sourcées.

## Rollback

Couper `MERCHANT_INTELLIGENCE_SHADOW_ENABLED`. Conserver la table et les
snapshots ; aucun lecteur v1 ne les consulte. Le downgrade structurel est
réservé aux bases éphémères ou à une restauration sauvegardée.
