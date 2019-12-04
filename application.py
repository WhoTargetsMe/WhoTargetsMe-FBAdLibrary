from app import create_app, db
from app.fbconnector.ad_downloader import download_ads
from app.service.models import Advertisers, Adverts, Tokens
from app.service.models import Advertisers, Tokens
from app.utils.ad_inserter import parse_and_insert
from app.utils.functions import finished_main_scripts
from app.utils.loader import parse_and_load_adverts
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import current_app as ap
from flask import render_template, request, session, g, jsonify
from sqlalchemy import exc, func
import os
import requests
import sys

def call_loader(country='GB'):
    with application.app_context():
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

# if len(sys.argv) < 2:
#     raise ValueError("Pls provide ENV")

PARAMS = {
    'ENV': os.getenv("ENV", 'prod') # 'dev', 'prod'
}
try:
    for i, arg in enumerate(sys.argv):
        for param in PARAMS.keys():
            if arg.upper().find(param) > -1: PARAMS[param] = sys.argv[i][sys.argv[i].upper().find(param) + len(param) + 1:]
    print('PARAMS', PARAMS)
except:
    pass

application = create_app(PARAMS['ENV'])
#INTERVAL = application.config['INTERVAL']

scheduler = BackgroundScheduler()
# interval style
# scheduler.add_job(func=call_loader, trigger='interval', seconds=INTERVAL, misfire_grace_time=10)
scheduler.add_job(call_loader, 'cron', month='*', day='*', hour='1,7,10,15,19', minute='1')
scheduler.start()

if __name__ == '__main__':
    with application.app_context():
        db.create_all()

        application.run(use_reloader=False)
