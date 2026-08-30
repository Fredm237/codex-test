# FILON — Rapport P0.5b Offer Graph shadow

## Verdict

**Shadow technique local livré. Activation et lecture publique : NO-GO.**

Le lot rend l'Offer Graph observable et rejouable sans transformer l'absence de
données humaines en preuve métier. Il n'active aucun writer en production et ne
modifie aucun contrat client.

## Livré

- migration expand-only `c6a1d4e8f2b3` ;
- table append-only `graph_offer_observations` ;
- projection `awin-offer-graph-v1` ;
- argent décimal et devise atomiques ;
- stock tri-state et lien HTTPS public strict ;
- lien nullable vers la résolution Product/Variant Graph ;
- quatre états fermés : `eligible`, `ineligible`, `unknown`, `quarantine` ;
- raisons bornées, sans texte source libre dans les compteurs ;
- writer Awin isolé par savepoint ;
- backfill dry-run/apply borné, cursorisé et idempotent ;
- flag off par défaut `OFFER_GRAPH_SHADOW_ENABLED`.

## Invariants prouvés

1. Une offre sans identité variante résolue est quarantinée, même si ses
   autres champs paraissent complets.
2. Une identité résolue ne compense jamais un prix/devise absent ou invalide,
   un stock inconnu ou épuisé, ni un lien absent ou dangereux.
3. Aucun montant n'est conservé sans devise explicite valide.
4. Les littéraux IP, hôtes locaux/réservés, credentials et HTTP sont refusés.
5. Un replay ne duplique pas l'observation ; la migration ne backfille rien.
6. Les tables et lectures Core v1 restent inchangées.

## Preuves locales

- **76/76** tests Product/Offer Graph, migration et configuration ciblés ;
- **377/377** tests Quality Lab ;
- **2 086 réussis + 2 ignorés** sur la suite backend complète ;
- une seule tête Alembic `c6a1d4e8f2b3` et aucun drift de modèle.

## Commande opérationnelle

```bash
python -m app.offer_graph.backfill --after-raw-id 0 --limit 1000
```

Sans `--apply`, cette commande est en lecture seule. L'écriture exige
`OBSERVATION_SHADOW_ENABLED=true` et `OFFER_GRAPH_SHADOW_ENABLED=true`.

## Limites honnêtes

- Aucun backfill ni writer Offer Graph n'est activé en production.
- Shipping, taxes et coût total restent inconnus.
- Aucune fiabilité marchand n'est calibrée.
- Les datasets Quality Lab humains restent vides ; l'exactitude de
  l'attachement et les taux de faux claims ne sont donc pas mesurables.
- Aucune lecture publique, dual-read ou canary n'est autorisée.
