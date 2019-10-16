from app.service import main
# from app.fbconnector.ad_downloader import download_ads
from app import db
from app.service.models import Adverts, Advertisers, Impressions, Tokens
from app.utils.loader import parse_and_load_adverts

from flask import render_template, request, session, g, jsonify
from flask import current_app as ap
from sqlalchemy import exc
import requests
from datetime import datetime

# test that backend is working
@main.route('/test', methods=['GET'])
def get_test_data():
    x = requests.get('https://reqres.in/api/users?page=2') #mock request
    return '<h1> the greeting is: {0} </h1>'.format(x.text)

# add new advertisers to the db
@main.route('/add/advertisers', methods=['POST', 'PUT'])
def add_advertisers():
    body = dict(request.get_json())
    details = body['advertisers']
    if not details or len(details) == 0:
        return 'Pls provide at least one advertiser'
    id_check = [obj.get('page_id', None) for obj in details]
    country_check = [obj.get('country', None) for obj in details]
    if None in id_check or None in country_check:
        return 'Pls make sure that all advertisers have page_id'

    if request.method == 'POST':
        try:
            for obj in details:
                item = Advertisers(obj.get('page_id', None), obj.get('page_name', None), obj.get('country', None))
                db.session.add(item)
            db.session.commit()
        except exc.IntegrityError as ex:
            db.session.rollback()
            return 'Advertiser already exists'
    elif request.method == 'PUT':
        for obj in details:
            try:
                exists = Advertisers.query.filter_by(page_id=obj.get('page_id', None))
                if exists:
                    updated = exists.update({'page_name': obj.get('page_name', None), 'country': obj.get('country', None)})
                else:
                    item = Advertisers(obj.get('page_id', None), obj.get('page_name', None), obj.get('country', None))
                    db.session.add(item)
                db.session.commit()
            except exc.IntegrityError as ex:
                db.session.rollback()
                return {'Error during update': obj.get('page_id', None)}
    advertisers = Advertisers.query.all()
    return {'advertisers': len(advertisers)}

# MAIN LOOP
# load advertisers by country or country+ID
@main.route('/loadall/<country>/<advertiser_id>', methods=['GET'])
def load_data_from_archive(country, advertiser_id):
    if advertiser_id != 'all':
        IDS = [advertiser_id]
    else:
        advertisers = Advertisers.query.all()
        IDS = [int(a.page_id) for a in advertisers if a.country == country]
        print(advertisers, IDS)

    # Get config to make request to FB library
    API_VERSION = ap.config['API_VERSION']
    PAGES_BETWEEN_STORING = ap.config['PAGES_BETWEEN_STORING']
    ADS_PER_PAGE = ap.config['ADS_PER_PAGE']
    latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
    LONG_TOKEN = latest_record.long_token

    for ID in IDS:
        # Iteratively download and store ads
        next_page = 'start'
        page = 0
        while next_page:
            print('...HTTP...Starting download from FB library.................', ID, 'time=', datetime.now())
            # body, next_page = download_ads(API_VERSION, LONG_TOKEN,\
            #     PAGES_BETWEEN_STORING, ADS_PER_PAGE, [ID], country, next_page)
            print('...HTTP.....Uploading data to DB....................', ID, 'page=', page, 'time=', datetime.now())
            parse_and_load_adverts(body, country)
            page += 1
        print('...HTTP...Finished upload to db.............................', ID, 'time=', datetime.now())
    return '<h1> Advertisers: {0} </h1>'.format(IDS)

# Mock main loop for testing purposes
# manually add posts by country and load into db
@main.route('/loadsome/<country>', methods=['POST'])
def add_advert(country):
    body = dict(request.get_json())
    details = body['posts']
    if not details or len(details) == 0 or not country:
        return 'Pls provide at least one post and country'
    parse_and_load_adverts(body, country)
    return 'OK'

@main.route('/refreshtoken', methods=['GET'])
def refresh_token():
    latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
    SHORT_TOKEN = latest_record.short_token
    APP_ID = ap.config['APP_ID']
    APP_SECRET = ap.config['APP_SECRET']

    url = "https://graph.facebook.com/v4.0/oauth/access_token?grant_type=fb_exchange_token&client_id=" +\
        APP_ID + "&client_secret=" + APP_SECRET +\
        "&fb_exchange_token=" + SHORT_TOKEN
    r = requests.get(url)
    details = r.json()
    LONG_TOKEN = details['access_token']
    seconds = details['expires_in']
    expires_on = datetime.now() + timedelta(seconds=seconds)
    item = Tokens(
        SHORT_TOKEN,
        LONG_TOKEN,
        latest_record.short_last_updated_at,
        datetime.now(),
        expires_on
        )
    db.session.add(item)
    db.session.commit()
