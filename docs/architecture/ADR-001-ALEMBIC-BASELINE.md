# ADR-001 — Baseline Alembic et fin des DDL implicites

- Statut : **accepté**
- Date : 28 août 2026
- Décisionnaires : architecture FILON
- Révision de baseline : `b9db07b15986`

## Contexte

Le backend créait les tables avec `Base.metadata.create_all()` puis exécutait
des `ALTER TABLE` et `CREATE INDEX` tolérants aux erreurs à chaque démarrage.
Cette approche ne fournissait ni ordre de migration, ni version de schéma, ni
preuve de rollback. Une erreur pouvait en outre être ignorée alors que le service
continuait sur un schéma incomplet.

## Décision

1. Alembic devient l'unique mécanisme normal de changement du schéma.
2. La baseline `b9db07b15986` photographie les 14 tables Core et Intelligence,
   leurs clés étrangères, contraintes, index partiels et index trigramme
   PostgreSQL.
3. Une base neuve est construite avec `alembic upgrade head`.
4. Une base existante et prouvée conforme est adoptée avec `alembic stamp` :
   la baseline ne rejoue jamais des `CREATE TABLE` sur la production existante.
5. `DATABASE_SCHEMA_MODE=alembic` est le mode par défaut. Le service vérifie la
   révision et n'exécute aucune DDL au démarrage ou avant une ingestion.
6. `DATABASE_SCHEMA_MODE=legacy` conserve temporairement l'ancien comportement
   comme rollback opérationnel de la première bascule. Son activation doit être
   explicite, limitée dans le temps et journalisée.
7. Les migrations futures suivent expand/shadow/contract. Aucun `DROP`, renommage
   destructif ou contrainte bloquante n'entre dans la même livraison que le
   basculement des lecteurs.

## Conséquences

- La migration devient une étape de déploiement obligatoire avant le service.
- Un schéma absent, non estampillé ou en retard est signalé explicitement.
- La CI reconstruit une base vide, contrôle le drift, adopte une base existante,
  exécute le downgrade et restaure un snapshot avec conservation des données.
- Le downgrade de la baseline supprime toutes les tables applicatives. Il est
  autorisé uniquement sur une base éphémère ou vide ; en production, le retour
  arrière se fait par rollback applicatif et restauration du snapshot.
- L'extension `pg_trgm` est conservée lors du downgrade, car elle peut être
  partagée avec d'autres schémas.

## Preuves

- Migration : `filon-backend/alembic/versions/b9db07b15986_baseline_v1.py`
- Tests : `filon-backend/tests/test_migrations.py`
- Procédure opérationnelle : `DATABASE_MIGRATION_RUNBOOK.md`
