"""Initial setup

Revision ID: de807a8d292f
Revises: 
Create Date: 2020-02-05 10:53:05.723121

"""
from alembic import op
from app.service.models import JSONEncodedDict
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'de807a8d292f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('advertisers',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('page_id', sa.String(length=25), nullable=False),
      sa.Column('page_name', sa.Text(), nullable=True),
      sa.Column('country', sa.String(length=10), nullable=False),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('page_id')
    )
    op.create_index(op.f('ix_advertisers_page_name'), 'advertisers', ['page_name'], unique=False)

    op.create_table('adverts',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('page_id', sa.String(length=25), nullable=False),
      sa.Column('page_name', sa.Text(), nullable=True),
      sa.Column('post_id', sa.String(length=25), nullable=False),
      sa.Column('country', sa.String(length=10), nullable=False),
      sa.Column('ad_creation_time', sa.DateTime(timezone=True), nullable=True),
      sa.Column('ad_creative_body', sa.Text(), nullable=True),
      sa.Column('ad_creative_link_caption', sa.Text(), nullable=True),
      sa.Column('ad_creative_link_description', sa.Text(), nullable=True),
      sa.Column('ad_creative_link_title', sa.Text(), nullable=True),
      sa.Column('ad_delivery_start_time', sa.DateTime(timezone=True), nullable=True),
      sa.Column('ad_delivery_stop_time', sa.DateTime(timezone=True), nullable=True),
      sa.Column('ad_snapshot_url', sa.Text(), nullable=True),
      sa.Column('image_link', sa.Text(), nullable=True),
      sa.Column('currency', sa.String(length=10), nullable=True),
      sa.Column('funding_entity', sa.Text(), nullable=True),
      sa.Column('ad_info', JSONEncodedDict(), nullable=True),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('post_id')
    )
    op.create_index(op.f('ix_adverts_ad_delivery_start_time'), 'adverts', ['ad_delivery_start_time'], unique=False)
    op.create_index(op.f('ix_adverts_funding_entity'), 'adverts', ['funding_entity'], unique=False)
    op.create_index(op.f('ix_adverts_page_name'), 'adverts', ['page_name'], unique=False)

    op.create_table('tokens',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('short_token', sa.Text(), nullable=False),
      sa.Column('long_token', sa.Text(), nullable=True),
      sa.Column('short_last_updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('long_last_updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('long_token_expires_on', sa.DateTime(timezone=True), nullable=True),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('long_token'),
      sa.UniqueConstraint('short_token')
    )

    op.create_table('impressions',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('advert_id', sa.Integer(), nullable=False),
      sa.Column('page_id', sa.String(length=25), nullable=False),
      sa.Column('post_id', sa.String(length=25), nullable=False),
      sa.Column('country', sa.String(length=10), nullable=False),
      sa.Column('demographic_distribution', sa.JSON(), nullable=True),
      sa.Column('region_distribution', sa.JSON(), nullable=True),
      sa.Column('impressions', JSONEncodedDict(), nullable=True),
      sa.Column('spend', JSONEncodedDict(), nullable=True),
      sa.Column('lower_bound_impressions', sa.String(length=25), nullable=True),
      sa.Column('upper_bound_impressions', sa.String(length=25), nullable=True),
      sa.Column('lower_bound_spend', sa.String(length=25), nullable=True),
      sa.Column('upper_bound_spend', sa.String(length=25), nullable=True),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.ForeignKeyConstraint(['advert_id'], ['adverts.id'], ),
      sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_impressions_advert_id'), 'impressions', ['advert_id'], unique=False)
    op.create_index(op.f('ix_impressions_page_id'), 'impressions', ['page_id'], unique=False)
    op.create_index(op.f('ix_impressions_post_id'), 'impressions', ['post_id'], unique=False)

    op.create_table('media',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('advert_id', sa.Integer(), nullable=False),
      sa.Column('www_links', sa.JSON(), nullable=True),
      sa.Column('aws_links', sa.JSON(), nullable=True),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.ForeignKeyConstraint(['advert_id'], ['adverts.id'], ),
      sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_advert_id'), 'media', ['advert_id'], unique=False)

    op.create_table('demographic_distribution',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('impression_id', sa.Integer(), nullable=False),
      sa.Column('percentage', sa.Float(), nullable=True),
      sa.Column('age', sa.String(length=10), nullable=True),
      sa.Column('gender', sa.String(length=10), nullable=True),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.ForeignKeyConstraint(['impression_id'], ['impressions.id'], ),
      sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demographic_distribution_impression_id'), 'demographic_distribution', ['impression_id'], unique=False)
    
    op.create_table('region_distribution',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('impression_id', sa.Integer(), nullable=False),
      sa.Column('percentage', sa.Float(), nullable=True),
      sa.Column('region', sa.String(length=255), nullable=True),
      sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
      sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
      sa.ForeignKeyConstraint(['impression_id'], ['impressions.id'], ),
      sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_region_distribution_impression_id'), 'region_distribution', ['impression_id'], unique=False)
    op.create_index(op.f('ix_region_distribution_region'), 'region_distribution', ['region'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_region_distribution_region'), table_name='region_distribution')
    op.drop_index(op.f('ix_region_distribution_impression_id'), table_name='region_distribution')
    op.drop_table('region_distribution')
    op.drop_index(op.f('ix_demographic_distribution_impression_id'), table_name='demographic_distribution')
    op.drop_table('demographic_distribution')
    op.drop_index(op.f('ix_media_advert_id'), table_name='media')
    op.drop_table('media')
    op.drop_index(op.f('ix_impressions_post_id'), table_name='impressions')
    op.drop_index(op.f('ix_impressions_page_id'), table_name='impressions')
    op.drop_index(op.f('ix_impressions_advert_id'), table_name='impressions')
    op.drop_table('impressions')
    op.drop_table('tokens')
    op.drop_index(op.f('ix_adverts_page_name'), table_name='adverts')
    op.drop_index(op.f('ix_adverts_funding_entity'), table_name='adverts')
    op.drop_index(op.f('ix_adverts_ad_delivery_start_time'), table_name='adverts')
    op.drop_table('adverts')
    op.drop_index(op.f('ix_advertisers_page_name'), table_name='advertisers')
    op.drop_table('advertisers')
    # ### end Alembic commands ###
