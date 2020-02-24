"""Add unique constraints on demographic and regional distributions

Revision ID: 6c6cc9aba03c
Revises: 785df91f72ae
Create Date: 2020-02-05 12:08:21.475859

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c6cc9aba03c'
down_revision = '785df91f72ae'
branch_labels = None
depends_on = None


def upgrade():
    
    op.create_unique_constraint('ix_unique_impression_id_age_gender_percentage', 'demographic_distribution', ['impression_id', 'age', 'gender', 'percentage'])
    op.add_column('impressions', sa.Column('_demographic_distribution_hash', sa.Text(), nullable=True))
    op.add_column('impressions', sa.Column('_region_distribution_hash', sa.Text(), nullable=True))
    op.create_unique_constraint('ix_unique_post_id_impressions_spend_region_demographic', 'impressions', ['post_id', 'impressions', 'spend', '_region_distribution_hash', '_demographic_distribution_hash'])
    op.create_unique_constraint('ix_unique_impression_id_region_percentage', 'region_distribution', ['impression_id', 'region', 'percentage'])
    op.execute("""
      CREATE OR REPLACE FUNCTION serialize_impression_region_demographic ()
          RETURNS TRIGGER
          AS $BODY$
      BEGIN
          NEW._region_distribution_hash = MD5(NEW.region_distribution::text);
          NEW._demographic_distribution_hash = MD5(NEW.demographic_distribution::text);
          RETURN NEW;
      END;
      $BODY$
      LANGUAGE 'plpgsql';
    """)
    op.execute("""
      CREATE TRIGGER serialize_impression_region_demographic
          BEFORE INSERT OR UPDATE ON impressions
          FOR EACH ROW
          EXECUTE PROCEDURE serialize_impression_region_demographic ();
    """)

def downgrade():
    op.drop_constraint('ix_unique_impression_id_region_percentage', 'region_distribution', type_='unique')
    op.drop_constraint('ix_unique_post_id_impressions_spend_region_demographic', 'impressions', type_='unique')
    op.drop_column('impressions', '_region_distribution_hash')
    op.drop_column('impressions', '_demographic_distribution_hash')
    op.drop_constraint('ix_unique_impression_id_age_gender_percentage', 'demographic_distribution', type_='unique')
    op.execute("DROP TRIGGER IF EXISTS serialize_impression_region_demographic ON impressions")
    op.execute("DROP FUNCTION IF EXISTS serialize_impression_region_demographic()")
