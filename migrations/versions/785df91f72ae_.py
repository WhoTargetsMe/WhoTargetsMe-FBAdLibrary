"""Add text_search column to adverts

Revision ID: 785df91f72ae
Revises: de807a8d292f
Create Date: 2020-02-05 11:41:08.223905

"""
from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '785df91f72ae'
down_revision = 'de807a8d292f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('adverts', sa.Column('text_search', postgresql.TSVECTOR(), nullable=True))
    op.execute("""
      CREATE OR REPLACE FUNCTION text_to_vector ()
          RETURNS trigger
          LANGUAGE 'plpgsql'
      AS $BODY$
          BEGIN
              NEW."text_search" := to_tsvector(concat(NEW.ad_creative_body, ' ', NEW.ad_creative_link_description, ' ', NEW.ad_creative_link_title));
              RETURN NEW;
          END;
      $BODY$;
    """)
    op.execute("""
      CREATE TRIGGER text_to_vector
        BEFORE INSERT OR UPDATE ON adverts
        FOR EACH ROW
        EXECUTE PROCEDURE text_to_vector ();
    """)
    

def downgrade():
    op.drop_column('adverts', 'text_search')
    op.execute("DROP TRIGGER IF EXISTS text_to_vector ON adverts")
    op.execute("DROP FUNCTION IF EXISTS text_to_vector()")
