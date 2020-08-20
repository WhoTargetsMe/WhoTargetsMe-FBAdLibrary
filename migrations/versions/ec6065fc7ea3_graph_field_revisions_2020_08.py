"""Graph field revisions 2020-08

Revision ID: ec6065fc7ea3
Revises: 6c6cc9aba03c
Create Date: 2020-08-20 19:48:57.283311

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ec6065fc7ea3"
down_revision = "6c6cc9aba03c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("adverts", sa.Column("potential_reach", sa.JSON(), nullable=True))
    op.add_column(
        "adverts", sa.Column("publisher_platforms", sa.ARRAY(sa.String), nullable=True)
    )


def downgrade():
    op.drop_column("adverts", "potential_reach")
    op.drop_column("adverts", "publisher_platforms")
