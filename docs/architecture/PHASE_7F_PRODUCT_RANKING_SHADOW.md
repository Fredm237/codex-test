# FILON — Phase 7F/G Product Ranking shadow et replay

- Date : **1er septembre 2026**
- Migration : `b9e7a1c3d5f8`
- Parent : `a8d6f0b2c4e7`
- Flag : `PRODUCT_RANKING_SHADOW_ENABLED=false`
- Statut : **QUALIFIÉ LOCALEMENT — NON DÉPLOYÉ**

## Expansion additive

La migration ajoute `product_ranking_runs` et `product_ranking_candidates`.
Les lignes sont append-only, reliées aux runs et candidats Constraint Engine et
protégées par des identités uniques. Les contraintes imposent la cohérence entre
statut, rang et utilité et interdisent `raw_context_retained=true`.

Le schéma ne possède aucune colonne d'offre gagnante, marchand ou commission.
Le writer refuse un mapping candidat incomplet, une divergence de digest ou une
réexécution de cardinalité différente.

## Replay borné

Le replay lit au plus 100 runs Constraint Engine et exige un instant UTC fixe,
une verticale supportée et une borne `after_constraint_run_id`. Le dry-run
n'écrit rien. L'apply exige le flag process-local.

La production ne fournit encore aucune des quatre preuves de ranking. Le replay
les marque donc toutes `unknown` et s'abstient. Ce comportement qualifie le
câblage sans faire passer prix, stock ou commission pour une préférence produit.

Les tests locaux prouvent : dry-run sans écriture, premier apply append-only,
replay identique réutilisant les mêmes lignes, divergence fail-closed et absence
de contexte brut.

## Rollback

Le rollback opérationnel consiste à laisser le flag à `false`. Les lecteurs
existants ignorent les deux tables. Aucun downgrade de production n'est requis ;
la migration technique reste réversible en environnement jetable.
