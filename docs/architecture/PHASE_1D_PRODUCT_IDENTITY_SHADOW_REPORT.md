# FILON — Phase 1D Product Identity Shadow Report

- Date : **31 août 2026**
- Statut : **QUALIFIÉ LOCALEMENT — NON DÉPLOYÉ**
- Révision Alembic : `b3e1a7c4d9f2`
- Lecteurs publics : **inchangés**
- Flag : writer couvert par `PRODUCT_GRAPH_SHADOW_ENABLED`, faux par défaut

## Livré

La table expand-only `graph_identity_assertions` conserve chaque fait
d'identité avant une éventuelle promotion canonique. Une assertion porte :

- une clé SHA-256 idempotente ;
- le `RawSourceRecord` et l'Offer d'origine ;
- le type de sujet, le champ, la valeur brute et la valeur normalisée ;
- le namespace et le scope d'identifiant lorsqu'ils existent ;
- la source, l'horodatage, la transformation et sa version ;
- un statut `observed`, `validated`, `conflict` ou `quarantine`.

Aucune colonne ni valeur du Core v1 n'est modifiée et la migration ne lance
aucun backfill.

## Projection Awin v1

| Fait source | Projection | Statut | Promotion |
|---|---|---|---|
| `brand_name` non vide | candidat de nom Brand normalisé | `observed` | aucune |
| EAN/GTIN valide | `gtin`, scope `global` | `validated` | Variant exact via le writer existant |
| EAN/GTIN invalide | valeur brute conservée | `quarantine` | aucune |
| `aw_product_id` | `merchant_sku`, scope `merchant:<id>` | `validated` | aucune fusion inter-marchands |
| valeur absente | aucune assertion | — | aucun unknown inventé |

Family, Model, MPN et attributs de variante ne sont pas fabriqués depuis le
titre Awin. Leur schéma contractuel existe, mais leur writer attend une source
structurée et son benchmark.

## Atomicité et idempotence

Les assertions et la projection exacte Variant s'exécutent dans le savepoint
Product Graph existant, après capture RawSource/Observation. Une panne du
shadow n'annule donc pas l'upsert Core. Un replay du même raw avec la même
version retrouve les clés d'assertion et ne duplique aucune ligne.

Le backfill existant a été étendu sans changer ses garde-fous :

- dry-run par défaut ;
- limite maximale de 10 000 raws ;
- ordre primaire stable et curseur `after_raw_id` ;
- `--apply` exige Observation + Product Graph shadows ;
- compteurs assertions créées/existantes/quarantaines et contexte marchand
  manquant ;
- replay idempotent.

## Preuves locales

La suite ciblée a passé **121 tests**, avec **3 tests PostgreSQL CI ignorés
localement** faute de `TEST_POSTGRES_URL` :

- migration upgrade/head/check et rollback SQLite ;
- tête runtime `b3e1a7c4d9f2` alignée ;
- projection Brand/GTIN/SKU et quarantaine GTIN invalide ;
- idempotence append-only et provenance obligatoire ;
- ingestion Awin sous double flag ;
- backfill dry-run/apply/replay ;
- benchmark exact-product et contrats JSON.

Les tests PostgreSQL opt-in ont été mis à jour pour attendre la nouvelle
table et la nouvelle tête ; ils devront passer en CI avant tout déploiement.

## Rollback

Le rollback opérationnel met `PRODUCT_GRAPH_SHADOW_ENABLED=false` et conserve
la table pour audit. Un ancien binaire ignore l'expansion. Le downgrade
technique vers `a2d7e9f4c1b6` supprime uniquement les assertions shadow ; il
n'est pas la procédure normale de production.

## Limites et gate suivant

Ce lot ne prouve pas encore la distribution des assertions sur les raws de
production. P1E doit :

1. publier et faire passer la CI, dont PostgreSQL ;
2. appliquer la migration dans une fenêtre sans writer ;
3. exécuter un dry-run réel borné ;
4. examiner GTIN résolus/quarantaines, marques observées, SKU scopés et
   contextes manquants ;
5. appliquer un seul lot shadow borné, rejouer le même lot et prouver zéro
   duplication ;
6. conserver les lecteurs v1 inchangés.
