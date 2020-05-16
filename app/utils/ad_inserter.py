from app import db
from app.service.models import (
    Adverts,
    Advertisers,
    Impressions,
    Demographic_distribution,
    Region_distribution,
)
from app.utils.functions import (
    cast_date,
    extract_id,
    parse_bounds,
    parse_distr,
    finished_main_scripts,
)
from datetime import datetime, timezone
from flask import current_app as app
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.sql import select, text

# fixed size advert dict for core bulk insert
def advert_dict(fb_ad, country):
    if not country:
        raise Exception("missing country")
    if not extract_id(fb_ad.get("ad_snapshot_url")):
        raise Exception("cannot extract id")

    return {
        "ad_creation_time": fb_ad.get("ad_creation_time", None),
        "ad_creative_body": fb_ad.get("ad_creative_body", None),
        "ad_creative_link_caption": fb_ad.get("ad_creative_link_caption", None),
        "ad_creative_link_description": fb_ad.get("ad_creative_link_description", None),
        "ad_creative_link_title": fb_ad.get("ad_creative_link_title", None),
        "ad_delivery_start_time": fb_ad.get("ad_delivery_start_time", None),
        "ad_delivery_stop_time": fb_ad.get("ad_delivery_stop_time", None),
        "ad_info": fb_ad.get("ad_info", None),
        "ad_snapshot_url": fb_ad.get("ad_snapshot_url", None),
        "country": country,
        "currency": fb_ad.get("currency", None),
        "funding_entity": fb_ad.get("funding_entity", None),
        "image_link": fb_ad.get("image_link", None),
        "page_id": fb_ad["page_id"],
        "page_name": fb_ad["page_name"],
        "post_id": extract_id(fb_ad["ad_snapshot_url"]),
    }


def bulk_insert_adverts(fb_ads, country):
    # executemany_mode - https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#psycopg2-fast-execution-helpers
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], echo=False, executemany_mode="batch"
    )
    connection = engine.connect()

    # BULK INSERT
    # https://docs.sqlalchemy.org/en/13/_modules/examples/performance/bulk_inserts.html
    # https://github.com/zzzeek/sqlalchemy/blob/master/doc/build/faq/performance.rst#user-content-i-m-inserting-400-000-rows-with-the-orm-and-it-s-really-slow
    #
    # Compose an insert statement we can pass to `execute` with a dictionary of items.
    # Options:
    #   1. generic insert: Adverts.__table__.insert(),
    #   2. postgres insert: pg_insert(Adverts.__table__).on_conflict_do_nothing(),
    #   3. or... insert or update selected columns using posgres ON CONFLICT
    #
    # INSERT INTO advertisers (post_id, country, page_name)
    # VALUES ($1, $2, $3)
    # ON CONFLICT (post_id)
    # DO UPDATE SET
    # 	page_name=$3
    # ;
    statement = pg_insert(Adverts.__table__)
    statement = statement.on_conflict_do_update(
        constraint="adverts_post_id_key",
        set_={
            "ad_creative_body": statement.excluded.ad_creative_body,
            "ad_creative_link_caption": statement.excluded.ad_creative_link_caption,
            "ad_creative_link_description": statement.excluded.ad_creative_link_description,
            "ad_creative_link_title": statement.excluded.ad_creative_link_title,
            "ad_delivery_start_time": statement.excluded.ad_delivery_start_time,
            "ad_delivery_stop_time": statement.excluded.ad_delivery_stop_time,
            "ad_snapshot_url": statement.excluded.ad_snapshot_url,
            "updated_at": datetime.now(),
        },
    )

    # build ads
    ads = []
    for fb_ad in fb_ads:
        try:
            ad = advert_dict(fb_ad, country)
            ads.append(ad)
        except Exception as e:
            print("problem adding fb_ad for advert insert", str(e))

    # if there are no ads, e.g. skip_ad condition is always met, then return
    if len(ads) == 0:
        return []

    try:
        connection.execute(statement, ads)

        # executemany in psycopg2 doesn't return the value for all rows (even if you
        # include a returning statement... like it would in PgSQL... 🤔).
        # So we need to refetch this inserted data

        # get post_ids to lookup from db... set struct saves removing dupes
        fb_ads_post_ids = {extract_id(ad["ad_snapshot_url"]) for ad in fb_ads}

        results = connection.execute(
            select(
                [Adverts.__table__.columns.id, Adverts.__table__.columns.post_id],
                Adverts.__table__.columns.post_id.in_(fb_ads_post_ids),
            )
        ).fetchall()

        # reformat to look kinda like you'd expect [{'id':1, 'post_id':234}]
        adverts = [dict(id=r[0], post_id=r[1]) for r in results]

        return adverts

    except Exception as e:
        print("error inserting ads ---->>>", str(e))

        return []


def impression_dict(fb_ad, advert_id, country):
    if not advert_id:
        raise Exception("advert_id required")
    if not country:
        raise Exception("country required")

    lower_bound_impressions, upper_bound_impressions = parse_bounds(
        fb_ad.get("impressions", None)
    )
    lower_bound_spend, upper_bound_spend = parse_bounds(fb_ad.get("spend", None))

    return {
        "advert_id": advert_id,
        "country": country,
        "demographic_distribution": fb_ad.get("demographic_distribution", None),
        "impressions": fb_ad.get("impressions", None),
        "lower_bound_impressions": lower_bound_impressions,
        "lower_bound_spend": lower_bound_spend,
        "page_id": fb_ad["page_id"],
        "post_id": extract_id(fb_ad["ad_snapshot_url"]),
        "region_distribution": fb_ad.get("region_distribution", None),
        "spend": fb_ad.get("spend", None),
        "upper_bound_impressions": upper_bound_impressions,
        "upper_bound_spend": upper_bound_spend,
    }


def bulk_insert_impressions(fb_ads, adverts, country):
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], echo=False, executemany_mode="batch"
    )
    connection = engine.connect()

    # we want existing the ads so we can match up the advert_id
    # this will be much easier if we have a hash table
    post_advert_id_map = {a["post_id"]: a["id"] for a in adverts}

    # build impressions to insert
    impressions = []
    for fb_ad in fb_ads:
        if not skip_ad(fb_ad):
            try:
                post_id = extract_id(fb_ad.get("ad_snapshot_url"))
                ad_id = post_advert_id_map.get(post_id)
                impressions.append(impression_dict(fb_ad, ad_id, country))
            except Exception as e:
                print("problem adding fb_ad for impression insert", str(e))

    # no records to insert? just return then
    if len(impressions) == 0:
        return []

    statement = pg_insert(Impressions.__table__).returning(
        Impressions.__table__.columns.id
    )
    statement = statement.on_conflict_do_nothing()

    try:
        connection.execute(statement, impressions)

        # get result again... would be much simpler if psycopg2 respected returning.
        # we need to do some filtering by latest for these post_ids
        statement = text(
            """SELECT id, advert_id, post_id, created_at
                        FROM impressions JOIN
                            (SELECT MAX(created_at) created_at, post_id 
                                FROM impressions 
                                WHERE post_id IN :fb_ads_post_ids
                                GROUP BY post_id 
                            ) AS max_date
                        USING (post_id, created_at)"""
        )

        fb_ads_post_ids = {extract_id(ad["ad_snapshot_url"]) for ad in fb_ads}

        results = connection.execute(
            statement,
            fb_ads_post_ids=tuple(
                fb_ads_post_ids
            ),  # tuple generates (1,2,3) output for IN
        ).fetchall()

        # reformat to look like you'd expect [{'id':1, 'advert_id':234, ... etc }]
        impressions = []
        for r in results:
            impressions.append(
                dict(id=r[0], advert_id=r[1], post_id=r[2], created_at=r[3])
            )

        return impressions

    except Exception as e:
        print("error inserting impressions ---->>>", str(e))

        return []


def demographic_distributions_dict(fb_demographic_distribution, impression_id):
    if not impression_id:
        raise Exception("impression_id required")

    percentage, age, gender = parse_distr(fb_demographic_distribution, "dem")

    return {
        "age": age,
        "gender": gender,
        "impression_id": impression_id,
        "percentage": percentage,
    }


def region_distributions_dict(fb_region_distribution, impression_id):
    if not impression_id:
        raise Exception("impression_id required")

    percentage, region = parse_distr(fb_region_distribution, "reg")

    return {"impression_id": impression_id, "percentage": percentage, "region": region}


def bulk_insert_distributions(fb_ads, impressions, distribution_type, table):
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], echo=False, executemany_mode="batch"
    )
    connection = engine.connect()

    post_impression_id_map = {i["post_id"]: i["id"] for i in impressions}

    table_dicts = {
        "demographic_distribution": demographic_distributions_dict,
        "region_distribution": region_distributions_dict,
    }

    distributions = []
    for fb_ad in fb_ads:
        if not skip_ad(fb_ad):
            try:
                fb_distribution = fb_ad.get(distribution_type, None)
                post_id = extract_id(fb_ad.get("ad_snapshot_url"))
                impression_id = post_impression_id_map.get(post_id)

                # iterate distribution field
                if fb_distribution:
                    for dd in fb_distribution:
                        distributions.append(
                            table_dicts[distribution_type](dd, impression_id)
                        )
            except Exception as e:
                print("cannot add distribution to insert", e, fb_ad)

    # if there are no distributions, then return
    if len(distributions) == 0:
        return []

    statement = pg_insert(table)
    statement = statement.on_conflict_do_nothing()

    try:
        connection.execute(statement, distributions)

        # We don't really need return values here
        return "OK"

    except Exception as e:
        print("error inserting distributions exception ---->>>", str(e))

        return "NOT OK"


# utils
def skip_ad(fb_ad):
    should_skip = False

    # check if the ad's run has finished
    if fb_ad.get("ad_delivery_stop_time", False):
        ad_delivery_stop_time = cast_date(fb_ad.get("ad_delivery_stop_time"))
        has_finished_run = ad_delivery_stop_time < datetime.now(timezone.utc)
        should_skip = has_finished_run

    return should_skip


# Main
def parse_and_insert(fb_ads, country):

    if not fb_ads or len(fb_ads) == 0:
        return

    adverts = bulk_insert_adverts(fb_ads, country)

    impressions = bulk_insert_impressions(fb_ads, adverts, country)

    bulk_insert_distributions(
        fb_ads,
        impressions,
        "demographic_distribution",
        Demographic_distribution.__table__,
    )
    bulk_insert_distributions(
        fb_ads, impressions, "region_distribution", Region_distribution.__table__
    )

    return
