"""Create materialized view for unique adverts

Revision ID: 2212ec124f21
Revises: ec6065fc7ea3
Create Date: 2020-10-01 11:47:32.801222

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2212ec124f21"
down_revision = "ec6065fc7ea3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE MATERIALIZED VIEW mv_unique_adverts_by_date
        AS  SELECT adverts.page_id,
                md5(adverts.ad_creative_body) AS body_hash,
                to_char(adverts.ad_creation_time::date::timestamp with time zone, 'yyyy-mm-dd'::text) AS ad_creation_date
            FROM adverts
            WHERE adverts.ad_creative_body <> '{{product.brand}}'::text AND adverts.ad_creative_body IS NOT NULL
            GROUP BY adverts.page_id, (md5(adverts.ad_creative_body)), (to_char(adverts.ad_creation_time::date::timestamp with time zone, 'yyyy-mm-dd'::text));
    """
    )


def downgrade():
    op.execute("DROP IF EXISTS MATERIALIZED VIEW mv_unique_adverts_by_date;")
