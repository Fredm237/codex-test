# FILON — Phase 7 Product Ranking Final Receipt

- Date : **1er septembre 2026**
- Verdict : **PHASE 7 SHADOW = GO — OUVERTURE PHASE 8 OFFER OPTIMIZATION**
- Lecteurs publics : **INCHANGÉS**
- Activation persistante : **OFF**
- Migration active : `b9e7a1c3d5f8`

## Décision

Product Ranking v1 est qualifié en shadow comme classement produit
vertical-aware, fail-closed et séparé de toute optimisation commerciale. Il ne
consomme que des candidats Phase 6 `ELIGIBLE`, exige quatre dimensions sourcées
et s'abstient dès qu'une preuve manque.

Cette décision ouvre Phase 8 Offer Optimization. Elle n'autorise ni activation
persistante, ni changement de lecteur public, ni assimilation de `BEST PRODUCT`
à `BEST OFFER`, ni introduction de commission dans le classement produit.

## Gates terminales

| Gate | Preuve | Verdict |
|---|---|---:|
| contrat | schéma v1, ADR-012, manifest et exemples synthétiques | **GO** |
| benchmark | 4 608 / 4 608 ; contrôle legacy `UNSAFE` | **GO** |
| sécurité | 0 inéligible classé, 0 unknown classé | **GO** |
| neutralité | 0 échec d'invariance à l'affiliation | **GO** |
| provenance | 100 % sur les résultats connus | **GO** |
| migration | production `b9e7a1c3d5f8`, readiness verte | **GO** |
| CI | run `33522393220`, quatre jobs verts | **GO** |
| replay | dry → create → existing, identité stable | **GO** |
| données sensibles | 0 contexte brut, 0 donnée utilisateur | **GO** |
| validation externe | `NO_EXTERNAL_HUMAN_GROUND_TRUTH` | **NON-BLOQUANT** |
| Cron catalogue | run 22 périmé, récupération requise | **NON-BLOQUANT SHADOW** |

## Publication et production

- PR GitHub : `#399` ;
- commit `main` : `90626475900b88e792f446ecd3ddb8699fe7a97c` ;
- CI GitHub : `33522393220`, Web, Backend, Extension et Mobile verts ;
- déploiement Railway : `a6ec2c1f-d639-43b8-a2fb-25550231dc1f` ;
- PostgreSQL : `ok` ; Redis : `ok` ; readiness : `true` ;
- flags Observation, Product Graph, Entity Resolution, Product Ontology,
  Hybrid Retrieval, Constraint Engine et Product Ranking persistants : `false`.

## Replay P7G

Fenêtre : run Constraint Engine 1, `after_constraint_run_id=0`, `limit=1`,
verticale `smartphones`, instant `2026-09-01T14:57:52Z`.

1. dry-run : 1 candidat `UNRANKABLE`, 0 écriture ;
2. apply : 1 run et 1 candidat créés ;
3. replay identique : 1 run et 1 candidat existants, 0 création ;
4. identité inchangée :
   `sha256:ee50be2ed145bbe499a26904612f1ce06b3b416567e2435fe88357c984904131` ;
5. aucun classement, score de repli ou signal commercial inventé.

## Limites et dette opérationnelle

Le run catalogue 22 est périmé et signalé `recovery_required=true`. Cette dette
reste `CATALOG_CRON_RECOVERY_PENDING` et bloque toute activation persistante de
Product Ranking. Elle ne remet pas en cause la migration, le writer borné,
l'idempotence ou l'ouverture de Phase 8 en shadow ; aucune ingestion catalogue
n'a été lancée ou modifiée pendant la qualification.

Les limites `SINGLE_CONSTRAINT_CANDIDATE_SHADOW_SAMPLE`,
`NO_PRODUCT_RANKING_EVIDENCE_IN_PRODUCTION`,
`NO_EXTERNAL_HUMAN_GROUND_TRUTH` et `NOT_INDEPENDENTLY_VALIDATED` restent
explicites et non bloquantes pour la progression autonome.

## Ouverture Phase 8

Phase 8 peut construire Offer Optimization séparément, à partir d'un produit
déjà classé ou d'une abstention explicite. Elle doit conserver la neutralité du
ranking produit, évaluer prix, disponibilité, fiabilité marchand et valeur
commerciale dans son propre contrat, et rester shadow jusqu'à sa revue terminale.
