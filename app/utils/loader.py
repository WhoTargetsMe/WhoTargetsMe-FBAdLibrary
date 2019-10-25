from flask import render_template, request, session, g, jsonify
from sqlalchemy import exc
import psycopg2
import json
from app.utils.functions import cast_date, extract_id, parse_bounds, parse_distr
from app import db
from app.service.models import Adverts, Advertisers, Impressions,\
    Demographic_distribution, Region_distribution


# func to parse downloaded fblib objects and store them in the DB
def parse_and_load_adverts(details, country):
    try:
        for obj in details:
            post_id = extract_id(obj.get('ad_snapshot_url', None))
            if post_id is None:
                print('Error extracting post_id', obj.get('ad_snapshot_url', None), obj.get('page_id', None))
                continue
            else:
                exists = Adverts.query.filter_by(post_id=post_id).first()
                page_id = obj.get('page_id', None)

                # preparing data for Impressions table
                lower_bound_impressions, upper_bound_impressions = parse_bounds(obj.get('impressions', None))
                lower_bound_spend, upper_bound_spend = parse_bounds(obj.get('spend', None))

                demographic_distribution = obj.get('demographic_distribution', None)
                region_distribution = obj.get('region_distribution', None)
                impressions = obj.get('impressions', None)
                spend = obj.get('spend', None)

                impression = Impressions(
                    'placeholder',
                    page_id,
                    post_id,
                    country,
                    demographic_distribution, #raw string
                    region_distribution, #raw string
                    impressions, #raw string
                    lower_bound_impressions,
                    upper_bound_impressions,
                    spend, #raw string
                    lower_bound_spend,
                    upper_bound_spend)

                ad_delivery_stop_time = cast_date(obj.get('ad_delivery_stop_time', None))

                if exists:
                    impression.advert_id = exists.id
                    if exists.ad_delivery_stop_time is None and ad_delivery_stop_time:
                        # print('Updating ad_delivery_stop_time to', ad_delivery_stop_time, "id=", exists.id)
                        exists.ad_delivery_stop_time = ad_delivery_stop_time
                    elif exists.ad_delivery_stop_time is not None:
                        # print('Ad is closed: ad_delivery_stop_time=', ad_delivery_stop_time, "id=", exists.id)
                        continue
                    db.session.add(impression)
                    db.session.commit()
                else: # create advert first; then get its id and load impressions
                    ad_creation_time = cast_date(obj.get('ad_creation_time', None))
                    ad_delivery_start_time = cast_date(obj.get('ad_delivery_start_time', None))
                    image_link = None
                    ad_info = None

                    item = Adverts(
                        obj.get('page_id', None),
                        obj.get('page_name', None),
                        post_id,
                        country,
                        ad_creation_time,
                        obj.get('ad_creative_body', None),
                        obj.get('ad_creative_link_caption', None),
                        obj.get('ad_creative_link_description', None),
                        obj.get('ad_creative_link_title', None),
                        ad_delivery_start_time,
                        ad_delivery_stop_time,
                        obj.get('ad_snapshot_url', None),
                        image_link,
                        obj.get('currency', None),
                        obj.get('funding_entity', None),
                        ad_info)
                    db.session.add(item)
                    db.session.commit()
                    created_advert = db.session.query(Adverts).order_by(Adverts.id.desc()).first()
                    impression.advert_id = created_advert.id
                    db.session.add(impression)
                    db.session.commit()

                # preparing data for Demographic_distribution and Region_distribution table
                created_impr = db.session.query(Impressions).order_by(Impressions.id.desc()).first()
                impression_id = created_impr.id
                demograph_lst = []
                region_lst = []
                if demographic_distribution:
                    for it in demographic_distribution:
                        percentage, age, gender = parse_distr(it, 'dem')
                        dem = Demographic_distribution(
                            impression_id, percentage, age, gender
                        )
                        demograph_lst.append(dem)
                    db.session.add_all(demograph_lst)
                if region_distribution:
                    for it in region_distribution:
                        percentage, region = parse_distr(it, 'reg')
                        reg = Region_distribution(
                            impression_id, percentage, region
                        )
                        region_lst.append(reg)
                    db.session.add_all(region_lst)
                db.session.commit()

    except exc.IntegrityError as ex:
        db.session.rollback()
        print('Error inside add_adverts', obj)
        return {'error': 'Error inside add_adverts'}

    i = Impressions.query.all()
    a = Adverts.query.all()
    return {'Impressions': len(i), 'Adverts': len(a)}
