# ADR-008 — Offer Truth v1, faits temporels sourcés

- Statut : **accepté pour shadow**
- Date : **1er septembre 2026**
- Portée : Phase 3 Offer Truth
- Contrat : `contracts/offer-truth/v1`
- Lecteurs publics : **inchangés**

## Contexte

Le Core v1 possède des offres, des snapshots de prix et un premier Offer Graph
append-only. Ce socle prouve déjà le couple argent/devise, le stock tri-state,
le lien marchand et la provenance du raw. Il ne représente pas encore
uniformément livraison, retours, garantie, identité marchand et fraîcheur par
claim ; les données absentes ne doivent jamais devenir zéro, gratuit,
disponible ou favorable.

## Décision

1. Une offre shadow porte sept claims fermés : prix, stock, livraison,
   retours, garantie, marchand et fraîcheur.
2. Chaque claim possède `state`, `value` et une liste de preuves versionnées.
3. Un prix ou coût de livraison est une chaîne décimale non négative associée
   atomiquement à une devise ISO explicite.
4. `unknown` et `invalid` exigent `value=null`. `stale` peut conserver la
   dernière valeur observée uniquement pour audit ; elle n'est jamais courante.
5. `VERIFIED` exige une Variant, un prix connu, un stock connu, un marchand
   connu et une fraîcheur `fresh`. Livraison, retours et garantie peuvent
   rester explicitement inconnus.
6. `QUARANTINED` exige une identité Variant non résolue.
7. Une preuve connue cite le raw, la source, le champ, l'horodatage, la
   transformation et sa version.
8. La confiance reste qualitative : `observed_direct`,
   `derived_deterministic` ou `not_calibrated`. Aucun nombre ne devient une
   probabilité sans calibration externe.
9. Le statut marchand utilise le roster fermé `INDEXED`, `AFFILIATED`,
   `DIRECT_PARTNER`, `MARKETPLACE`, `UNVERIFIED` ; l'affiliation ne signifie
   pas automatiquement partenariat direct.
10. Le contrat reste shadow-only jusqu'au replay production, au benchmark et à
    la revue de sortie Phase 3.

## Invariants

- aucune devise de fallback ;
- aucune livraison gratuite par défaut ;
- aucune disponibilité positive par défaut ;
- aucune valeur future ou stale présentée comme actuelle ;
- aucun claim connu sans provenance ;
- aucun score opaque capable de lever un état inconnu, invalide ou stale ;
- aucun changement des endpoints et clients v1 pendant la qualification.

## Alternatives refusées

- réutiliser seulement `offers.updated_at` : ce timestamp applicatif n'est pas
  une preuve de prix ou de stock ;
- stocker l'argent en flottant : la représentation n'est pas exacte ;
- rendre livraison/retours/garantie obligatoirement connus : le feed réel peut
  ne pas les fournir et le contrat doit s'abstenir honnêtement ;
- produire une note de confiance marchand : aucune ground truth externe ne la
  calibre à ce stade.

## Rollback

Le contrat n'active aucun writer ni lecteur. Son rollback immédiat consiste à
ne pas adopter sa future projection. Les migrations P3 devront rester
expand-only et les writers seront coupés par un flag dédié sans effacement de
preuve.
