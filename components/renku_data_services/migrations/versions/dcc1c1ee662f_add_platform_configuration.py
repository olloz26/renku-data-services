"""add platform configuration

Revision ID: dcc1c1ee662f
Revises: 9c26ab37ff4c
Create Date: 2024-06-24 14:30:27.671588

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dcc1c1ee662f"
down_revision = "9c26ab37ff4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "config",
        sa.Column("id", sa.Enum("config", name="configid"), nullable=False),
        sa.Column("incident_banner", sa.String(), nullable=False),
        sa.Column("creation_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="platform",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("config", schema="platform")
    op.execute("DROP TYPE configid")
    # ### end Alembic commands ###
