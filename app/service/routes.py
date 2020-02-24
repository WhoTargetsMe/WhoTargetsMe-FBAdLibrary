from app import db
from app.fbconnector.ad_downloader import download_ads
from app.s3downloader.media_downloader_selenium import get_and_load_images_to_s3
from app.service import main
from app.service.models import Adverts, Advertisers, Impressions, Tokens, Media
from app.utils.ad_inserter import parse_and_insert
from app.utils.functions import finished_main_scripts
from app.utils.loader import parse_and_load_adverts
from datetime import datetime, timedelta
from flask import current_app as ap
from flask import render_template, request, session, g, jsonify
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import exc, func
from time import sleep
import requests

def get_long_token():
    latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
    return latest_record.long_token

# test that backend is working
@main.route('/test', methods=['GET'])
def get_test_data():
    x = requests.get('https://reqres.in/api/users?page=2') #mock request
    return '<h1> the greeting is: {0} </h1>'.format(x.text)

@main.route('/callloader', methods=['POST'])
def call_loader(country='GB'):
    with ap.app_context():
        print('starting loading job', datetime.now())
        
        # Get config to make request to FB library
        API_VERSION = ap.config['API_VERSION']
        PAGES_BETWEEN_STORING = ap.config['PAGES_BETWEEN_STORING']
        ADS_PER_PAGE = ap.config['ADS_PER_PAGE']
        latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
        LONG_TOKEN = latest_record.long_token

        # get our predefined advertisers
        advertisers = Advertisers.query.all()
        advertiser_ids = [int(a.page_id) for a in advertisers if a.country == country]
        
        # get the most frequent advertisers, based on previously saved adverts
        single_call_lst = []
        adverts = db.session.query(Adverts.page_id, func.count(Adverts.page_id)).group_by(Adverts.page_id).all()
        single_call_lst = [int(a[0]) for a in adverts if a[1] < (ADS_PER_PAGE - 100)]
        ordered_ids = sorted([a for a in adverts], key=lambda k: k[1], reverse=True)
        frequent_advertiser_ids = [int(a[0]) for a in ordered_ids][:2] #50

        # select which advertiser ids set to use, based on... time of day?
        if finished_main_scripts():
            IDS = frequent_advertiser_ids
        else:
            IDS = advertiser_ids

        print('FETCHING IDS ...', IDS)
        print('single_call_lst', single_call_lst)

        for ID in IDS:
            # Iteratively download and store ads
            next_page = 'start'
            page = 0
            single_call = ID in single_call_lst
            while next_page:
                print('...CRON...Starting download from FB library.................', ID, 'time=', datetime.now())
                body, next_page = download_ads(API_VERSION, LONG_TOKEN,\
                    PAGES_BETWEEN_STORING, ADS_PER_PAGE, [ID], country, next_page, single_call)
                
                print('...CRON.....Uploading data to DB....................', ID, 'page=', page, 'time=', datetime.now())
                # parse_and_load_adverts(body, country)
                parse_and_insert(body, country)

                page += 1
            print('...CRON...Finished upload to db.............................', ID, 'time=', datetime.now())
        return '<h1> Advertisers: {0} </h1>'.format(IDS)

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
            return {'Advertiser already exists or name is corrupted': obj.get('page_id', None)}
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
    single_call_lst = []
    # Get config to make request to FB library
    API_VERSION = ap.config['API_VERSION']
    PAGES_BETWEEN_STORING = ap.config['PAGES_BETWEEN_STORING']
    ADS_PER_PAGE = ap.config['ADS_PER_PAGE']
    LONG_TOKEN = get_long_token()

    if advertiser_id != 'all':
        IDS = [advertiser_id]
    else:
        advertisers = Advertisers.query.all()
        IDS = [int(a.page_id) for a in advertisers if a.country == country]
        print(advertisers, IDS)

        adverts = db.session.query(Adverts.page_id, func.count(Adverts.page_id)).group_by(Adverts.page_id).all()
        single_call_lst = [int(a[0]) for a in adverts if a[1] < (ADS_PER_PAGE - 100)]
        print('single_call_lst', single_call_lst)


    for ID in IDS:
        # Iteratively download and store ads
        next_page = 'start'
        page = 0
        single_call = ID in single_call_lst
        while next_page:
            print('...HTTP...Starting download from FB library.................', ID, 'time=', datetime.now())
            body, next_page = download_ads(API_VERSION, LONG_TOKEN,\
                PAGES_BETWEEN_STORING, ADS_PER_PAGE, [ID], country, next_page, single_call)
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
    seconds = details['expires_in']

    latest_record.long_token = details['access_token']
    latest_record.long_last_updated_at = datetime.now()
    latest_record.long_token_expires_on = datetime.now() + timedelta(seconds=seconds)

    db.session.commit()

    return 'OK'

@main.route('/media', methods=['GET'])
def download_media():
    size = 20
    advrts = Adverts.query.filter_by(image_link=None)
    if size >= advrts.count(): size = advrts.count()
    [print(i.post_id) for i in advrts[:size]]
    creds = {
        'long_token': get_long_token(),
        'access_key': ap.config['ACCESS_KEY'],
        'secret_key': ap.config['SECRET_KEY']
    }
    if ap.config['FLASK_ENV'] == 'development':
        driver = webdriver.Chrome()
        login_url = 'https://www.facebook.com'
        driver.get(login_url)
        sleep(40)
        # email = driver.find_element_by_id("email")
        # passwd = driver.find_element_by_id("pass")
        # passwd = driver.find_element_by_id("pass")
        # button.click()

    elif ap.config['FLASK_ENV'] == 'production':
        DRIVER_PATH = '/usr/bin/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument("--remote-debugging-port=9222")
        options.headless = True
        driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)

    for advert in advrts[:size]:
        print('ITEM', advert.post_id)
        aws_links, www_links, ad_info = get_and_load_images_to_s3(advert.post_id, advert.page_id, creds, driver)
        if len(aws_links) == 0 and len(www_links) == 0:
            print('no links for', advert.post_id, advert.page_id)
            continue
        elif len(aws_links) > 0:
            advert.image_link = 'uploaded_to_aws'
        else:
            advert.image_link = 'www_links_only'
        if ad_info:
            advert.ad_info = ad_info
        try:
            item = Media(advert.id, list(www_links), aws_links)
            db.session.add(item)
            db.session.commit()
        except exc.IntegrityError as ex:
            db.session.rollback()
            continue
            #return 'error during media links saving'
    driver.quit()
    return 'OK'
