from app import db
from app.service.models import Adverts, Advertisers, Impressions, Demographic_distribution, Region_distribution
from app.utils.functions import cast_date, extract_id, parse_bounds, parse_distr, finished_main_scripts
from datetime import datetime
from flask import current_app as app
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import select, text
import sys

# fixed size advert dict for core bulk insert
def advert_dict(fb_ad, country):
    return {   
        'ad_creation_time': fb_ad.get('ad_creation_time', None),
        'ad_creative_body': fb_ad.get('ad_creative_body', None),
        'ad_creative_link_caption': fb_ad.get('ad_creative_link_caption', None),
        'ad_creative_link_description': fb_ad.get('ad_creative_link_description', None),
        'ad_creative_link_title': fb_ad.get('ad_creative_link_title', None),
        'ad_delivery_start_time': fb_ad.get('ad_delivery_start_time', None),
        'ad_delivery_stop_time': fb_ad.get('ad_delivery_stop_time', None),
        'ad_info': fb_ad.get('ad_info', None),
        'ad_snapshot_url': fb_ad.get('ad_snapshot_url', None),
        'country': country,
        'currency': fb_ad.get('currency', None),
        'funding_entity': fb_ad.get('funding_entity', None),
        'image_link': fb_ad.get('image_link', None),
        'page_id': fb_ad.get('page_id', None),
        'page_name': fb_ad.get('page_name', None),
        'post_id': extract_id(fb_ad.get('ad_snapshot_url'))
    }


def bulk_insert_adverts(fb_ads, country):
    # executemany_mode - https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#psycopg2-fast-execution-helpers
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False, executemany_mode='batch')
    connection = engine.connect()

    # BULK INSERT 
    # https://docs.sqlalchemy.org/en/13/_modules/examples/performance/bulk_inserts.html
    # https://github.com/zzzeek/sqlalchemy/blob/master/doc/build/faq/performance.rst#user-content-i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
    #
    # Compose an insert statement we can pass in to execut with a dictionary of items. 
    #   - generic insert: Adverts.__table__.insert(),
    #   - postgres insert: pg_insert(Adverts.__table__).on_conflict_do_nothing(),
    #   - or... insert or update selected columns using posgres ON CONFLICT
    #
    # INSERT INTO advertisers (post_id, country, page_name)
    # VALUES ($1, $2, $3)
    # ON CONFLICT (post_id)
    # DO UPDATE SET
    # 	page_name=$3
    # ;
    statement = pg_insert(Adverts.__table__)
    statement = statement.on_conflict_do_update(
            constraint='adverts_post_id_key',
            set_={
                'ad_delivery_stop_time': statement.excluded.ad_delivery_stop_time,
                'updated_at': datetime.now() # this will always set... do we want that?
            }
        )
    
    # build ads
    ads = []
    for fb_ad in fb_ads:
        ad = advert_dict(fb_ad, country)
        if ad['page_id'] and ad['post_id'] and ad['country']:
            ads.append(ad)

    try:
        connection.execute(
            statement,
            ads
        )

        # executemany in psycopg2 doesn't return the value for all rows (even if you 
        # include a returning statement... like it would in PgSQL... 🤔). 
        # So we need to refetch this inserted data

        # get post_ids to lookup from db... set struct saves removing dupes
        fb_ads_post_ids = { extract_id(ad['ad_snapshot_url']) for ad in fb_ads }
        
        results = connection.execute(
                select(
                    [Adverts.__table__.columns.id, Adverts.__table__.columns.post_id], 
                    Adverts.__table__.columns.post_id.in_(fb_ads_post_ids)
                )
            ).fetchall()

        # reformat to look kinda like you'd expect [{'id':1, 'post_id':234}]
        adverts = [dict(id=r[0], post_id=r[1]) for r in results]

        return adverts

    except:
        e = sys.exc_info()[0]

        print('error inserting ads exception ---->>>', e)
        print('error inserting ads, ads ---->>>', fb_ads)

        return []


def impression_dict(fb_ad, advert_id, country): 
    lower_bound_impressions, upper_bound_impressions = parse_bounds(fb_ad.get('impressions', None))
    lower_bound_spend, upper_bound_spend = parse_bounds(fb_ad.get('spend', None))

    return {
        'advert_id': advert_id,
        'country': country,
        'demographic_distribution': fb_ad.get('demographic_distribution', None),
        'impressions': fb_ad.get('impressions', None),
        'lower_bound_impressions': lower_bound_impressions,
        'lower_bound_spend': lower_bound_spend,
        'page_id': fb_ad.get('page_id', None),
        'post_id': extract_id(fb_ad.get('ad_snapshot_url')),
        'region_distribution': fb_ad.get('region_distribution', None),
        'spend': fb_ad.get('spend', None),
        'upper_bound_impressions': upper_bound_impressions,
        'upper_bound_spend': upper_bound_spend
    }
  
            
def bulk_insert_impressions(fb_ads, adverts, country):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False, executemany_mode='batch')
    connection = engine.connect()

    # we want existing the ads so we can match up the advert_id
    # this will be much easier if we have a hash table
    post_advert_id_map = {a['post_id']:a['id'] for a in adverts}

    try:
        # build impressions to insert
        impressions = []
        for fb_ad in fb_ads:
            # We stop adding impression data when we have ad_delivery_stop_time
            # FIXME: we need to check the stop time and recording impressions until then
            if not skip_ad(fb_ad):
                post_id = extract_id(fb_ad.get('ad_snapshot_url'))
                ad_id = post_advert_id_map.get(post_id)
                impressions.append(impression_dict(fb_ad, ad_id, country))
            
        connection.execute(
            pg_insert(Impressions.__table__).returning(Impressions.__table__.columns.id),
            impressions
        )
        
        # get result again... would be much simpler if psycopg2 respected returning.
        # we need to do some filtering by latest for these post_ids
        statement = text("""SELECT id, advert_id, post_id, created_at
                        FROM impressions JOIN
                            (SELECT MAX(created_at) created_at, post_id 
                                FROM impressions 
                                WHERE post_id IN :fb_ads_post_ids
                                GROUP BY post_id 
                            ) AS max_date
                        USING (post_id, created_at)""")

        fb_ads_post_ids = { extract_id(ad['ad_snapshot_url']) for ad in fb_ads }

        results = connection.execute(
                statement,
                fb_ads_post_ids=tuple(fb_ads_post_ids) # tuple generates (1,2,3) output for IN
            ).fetchall()

        # reformat to look like you'd expect [{'id':1, 'advert_id':234, ... etc }]
        impressions = []
        for r in results:
            impressions.append(dict(id=r[0], advert_id=r[1], post_id=r[2], created_at=r[3]))
        
        return impressions

    
    except:
        e = sys.exc_info()[0]

        print('error inserting impressions exception ---->>>', e)
        print('error inserting impressions, impressions ---->>>', fb_ads)

        return []

def demographic_distributions_dict(fb_demographic_distribution, impression_id): 
    percentage, age, gender = parse_distr(fb_demographic_distribution, 'dem')
    return {
        'age': age,
        'gender': gender,
        'impression_id': impression_id,
        'percentage': percentage
    }


def bulk_insert_demographic_distributions(fb_ads, impressions):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False, executemany_mode='batch')
    connection = engine.connect()

    post_impression_id_map = {i['post_id']:i['id'] for i in impressions}

    demographic_distributions = []
    for fb_ad in fb_ads:
        if not skip_ad(fb_ad):
            fb_demographic_distribution = fb_ad.get('demographic_distribution', None)
            post_id = extract_id(fb_ad.get('ad_snapshot_url'))
            impression_id = post_impression_id_map.get(post_id)

            # iterate demographic_distribution field
            if fb_demographic_distribution:
                for dd in fb_demographic_distribution:
                    demographic_distributions.append(
                            demographic_distributions_dict(
                                dd, 
                                impression_id
                            )
                        )
    
    connection.execute(
        Demographic_distribution.__table__.insert(),
        demographic_distributions
    )

    # We don't really need return values here
    return 'OK'


def region_distributions_dict(fb_region_distribution, impression_id): 
    percentage, region = parse_distr(fb_region_distribution, 'reg')
    return {
        'impression_id': impression_id,
        'percentage': percentage,
        'region': region
    }

def bulk_insert_region_distributions(fb_ads, impressions):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=False, executemany_mode='batch')
    connection = engine.connect()

    post_impression_id_map = {i['post_id']:i['id'] for i in impressions}

    region_distributions = []
    for fb_ad in fb_ads:
        if not skip_ad(fb_ad):
            fb_region_distribution = fb_ad.get('region_distribution', None)
            post_id = extract_id(fb_ad.get('ad_snapshot_url'))
            impression_id = post_impression_id_map.get(post_id)

            # iterate region_distribution field
            if fb_region_distribution:
                for dd in fb_region_distribution:
                    region_distributions.append(
                            region_distributions_dict(
                                dd, 
                                impression_id
                            )
                        )
    
    connection.execute(
        Region_distribution.__table__.insert(),
        region_distributions
    )

    # We don't really need return values here
    return 'OK'



# utils
def skip_ad(fb_ad):
    should_skip = False

    # check if the ad's run has finished
    # FIXME - this should compare date
    should_skip = bool(fb_ad.get('ad_delivery_stop_time', False))

    return should_skip


# Main
def parse_and_insert(fb_ads, country):

    if not fb_ads or len(fb_ads) is 0: 
        return

    adverts = bulk_insert_adverts(fb_ads, country)

    impressions = bulk_insert_impressions(fb_ads, adverts, country)

    bulk_insert_demographic_distributions(fb_ads, impressions)

    bulk_insert_region_distributions(fb_ads, impressions)

    return
