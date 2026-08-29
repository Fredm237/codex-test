"""Normalise les drapeaux historiques des offres sans inventer de valeur.

Revision ID: f4c81a9d2e70
Revises: 3a7f9c2e5b61
Create Date: 2026-08-29 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c81a9d2e70"
down_revision: Union[str, None] = "3a7f9c2e5b61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_EXPECTED_DEFAULTS = {
    "is_canonical": "true",
    "is_adult": "false",
}


def _normalise_default(value: object) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower().replace("'", "").replace("::boolean", "")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # La baseline SQLite est déjà stricte. L'écart corrigé ici provient
        # uniquement de l'ancien rattrapage DDL PostgreSQL en production.
        return

    rows = bind.execute(
        sa.text(
            """
            SELECT
                attribute.attname AS column_name,
                attribute.attnotnull AS not_null,
                pg_get_expr(default_value.adbin, default_value.adrelid) AS default_expr
            FROM pg_attribute AS attribute
            JOIN pg_class AS relation ON relation.oid = attribute.attrelid
            JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
            LEFT JOIN pg_attrdef AS default_value
                ON default_value.adrelid = relation.oid
                AND default_value.adnum = attribute.attnum
            WHERE namespace.nspname = current_schema()
              AND relation.relname = 'offers'
              AND attribute.attname IN ('is_canonical', 'is_adult')
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
            """
        )
    ).mappings()
    states = {row["column_name"]: row for row in rows}
    if set(states) != set(_EXPECTED_DEFAULTS):
        raise RuntimeError(
            "Adoption refusée : les drapeaux offers.is_canonical/is_adult "
            "ne correspondent pas au schéma historique attendu."
        )

    for column_name, expected_default in _EXPECTED_DEFAULTS.items():
        state = states[column_name]
        actual_default = _normalise_default(state["default_expr"])
        if actual_default not in {None, expected_default}:
            raise RuntimeError(
                "Adoption refusée : default inattendu sur "
                f"offers.{column_name}."
            )

        if not state["not_null"]:
            null_count = bind.scalar(
                sa.text(f'SELECT count(*) FROM offers WHERE "{column_name}" IS NULL')
            )
            if null_count:
                raise RuntimeError(
                    "Adoption refusée : "
                    f"offers.{column_name} contient {null_count} valeur(s) NULL."
                )

            constraint_name = f"ck_adopt_offers_{column_name}_not_null"
            op.execute(
                f'ALTER TABLE offers ADD CONSTRAINT "{constraint_name}" '
                f'CHECK ("{column_name}" IS NOT NULL) NOT VALID'
            )
            op.execute(
                f'ALTER TABLE offers VALIDATE CONSTRAINT "{constraint_name}"'
            )
            op.execute(
                f'ALTER TABLE offers ALTER COLUMN "{column_name}" SET NOT NULL'
            )
            op.execute(
                f'ALTER TABLE offers DROP CONSTRAINT "{constraint_name}"'
            )

        if actual_default is not None:
            op.execute(
                f'ALTER TABLE offers ALTER COLUMN "{column_name}" DROP DEFAULT'
            )


def downgrade() -> None:
    # Aucun downgrade structurel : rendre de nouveau ces colonnes nullables et
    # réintroduire des defaults serveur recréerait précisément le drift que
    # cette adoption supprime. Le rollback opérationnel reste applicatif.
    pass
