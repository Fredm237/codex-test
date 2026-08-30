# FILON — Rapport P0.5c Merchant Intelligence shadow

## Verdict

**Mesure technique locale livrée. Influence sur Offer Quality : NO-GO.**

La couche mesure ce que les sources actuelles prouvent et conserve le reste
comme non mesurable. Aucun statut commercial fort, score de fiabilité ou
confiance n'est inventé.

## Livré

- migration expand-only `d7b2e5f9a4c1` ;
- snapshots append-only par marchand et fenêtre raw ;
- statuts `INDEXED`, `AFFILIATED`, `DIRECT_PARTNER`, `MARKETPLACE`,
  `UNVERIFIED`, sans promotion implicite ;
- compteurs de couverture GTIN, prix, prix frais, stock, lien, identité et
  éligibilité ;
- âge du dernier feed avec rejet des timestamps futurs ;
- registre structuré des dimensions observées, inconnues ou non mesurables ;
- heure de mesure ISO-8601 avec offset obligatoire ;
- backfill dry-run/apply borné et idempotent ;
- flag off par défaut `MERCHANT_INTELLIGENCE_SHADOW_ENABLED`.

## Preuves locales

- **81/81** tests Product/Offer/Merchant, migration et configuration ciblés ;
- **377/377** tests Quality Lab inclus dans la suite complète ;
- **2 091 réussis + 2 ignorés** sur le backend complet ;
- une seule tête Alembic `d7b2e5f9a4c1`, sans drift de modèle.

## Commande

```bash
python -m app.merchant_intelligence.backfill \
  --evaluated-at 2026-08-31T00:00:00+02:00 \
  --after-raw-id 0 \
  --limit 1000
```

Sans `--apply`, aucune écriture n'a lieu. L'apply exige Observation,
Product/Variant Graph, Offer Graph et Merchant Intelligence activés ensemble.

## Limites honnêtes

- Aucun snapshot marchand n'est encore calculé en production.
- `AFFILIATED` ne signifie ni `DIRECT_PARTNER`, ni vendeur fiable.
- La validité syntaxique d'une URL ne prouve pas qu'elle répond.
- Livraison, retours, garantie, support, paiement, shipping, exactitude prix et
  mismatch stock ne sont pas mesurables avec les sources actuelles.
- Aucun score Merchant Quality ni effet de ranking n'existe.
- Les données humaines Quality restent à zéro ; aucune qualité marchande
  perçue ne peut être calibrée.
