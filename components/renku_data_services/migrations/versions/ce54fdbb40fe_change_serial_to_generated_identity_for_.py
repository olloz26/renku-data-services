"""change serial to generated identity for primary keys

Revision ID: ce54fdbb40fe
Revises: 46236d8d7cbe
Create Date: 2024-10-18 14:23:21.711427

"""

import sqlalchemy as sa
from alembic import op
from psycopg import sql
from sqlalchemy.schema import CreateSequence

# revision identifiers, used by Alembic.
revision = "ce54fdbb40fe"
down_revision = "46236d8d7cbe"
branch_labels = None
depends_on = None

tables = [
    ("users", "user_preferences", "id"),
    ("users", "users", "id"),
    ("users", "last_keycloak_event_timestamp", "id"),
    ("projects", "projects_repositories", "id"),
    ("common", "entity_slugs", "id"),
    ("common", "entity_slugs_old", "id"),
    ("resource_pools", "users", "id"),
    ("resource_pools", "resource_classes", "id"),
    ("resource_pools", "resource_pools", "id"),
    ("resource_pools", "tolerations", "id"),
    ("resource_pools", "node_affinities", "id"),
    ("events", "events", "id"),
    ("authz", "project_user_authz", "id"),
]


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    connection = op.get_bind()

    for schema, table, column in tables:
        op.execute(sa.text(f"LOCK TABLE {schema}.{table} IN EXCLUSIVE MODE"))
        full_name = sql.Identifier(schema, table)
        statement = sql.SQL("SELECT MAX(id) FROM {}").format(full_name).as_string(connection)  # type: ignore[arg-type]
        res = connection.exec_driver_sql(statement)
        row = res.fetchone()
        next_id = 1
        if row is not None and len(row) > 0 and row[0] is not None:
            next_id = row[0] + 1

        statement = sa.sql.text(f"select pg_get_serial_sequence('{schema}.{table}', '{column}')")
        res = connection.execute(statement)
        row = res.fetchone()
        statement = sa.sql.text(
            f"""
              ALTER TABLE {schema}.{table}
                  ALTER COLUMN {column} DROP DEFAULT;
            """
        )
        connection.execute(statement)
        if row is not None and len(row) > 0 and row[0] is not None:
            sequence_name = row[0]
            statement = sa.sql.text(f"DROP SEQUENCE {sequence_name}")
            connection.execute(statement)

        statement = sa.sql.text(
            f"""
              ALTER TABLE {schema}.{table}
                  ALTER COLUMN {column} SET DATA TYPE integer,
                  ALTER COLUMN {column} ADD GENERATED ALWAYS AS IDENTITY (START WITH {next_id});
            """
        )
        connection.execute(statement)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    connection = op.get_bind()
    for schema, table, column in tables:
        full_name = sql.Identifier(schema, table)
        statement = sql.SQL("SELECT MAX(id) FROM {}").format(full_name).as_string(connection)  # type: ignore[arg-type]
        res = connection.exec_driver_sql(statement)
        row = res.fetchone()
        next_id = 1
        if row is not None and len(row) > 0 and row[0] is not None:
            next_id = row[0] + 1
        connection.execute(
            sa.sql.text(
                f"""
              ALTER TABLE {schema}.{table}
                  ALTER COLUMN {column} DROP IDENTITY;
            """
            )
        )
        op.alter_column(table, column, type_=sa.Integer, schema=schema)
        sequence_name = f"{table}_{column}_seq"
        op.execute(CreateSequence(sa.Sequence(sequence_name, schema=schema, start=next_id), if_not_exists=True))
        op.execute(sa.sql.text(f"ALTER SEQUENCE {schema}.{sequence_name} OWNED BY {schema}.{table}.{column}"))
        connection.execute(
            sa.sql.text(
                f"""
              ALTER TABLE {schema}.{table}
                  ALTER COLUMN {column} SET DEFAULT nextval('"{schema}"."{sequence_name}"');
            """
            )
        )
    # ### end Alembic commands ###
