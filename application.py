from app import create_app, db
from app.service.models import Advertisers, Tokens

import sys
from apscheduler.schedulers.background import BackgroundScheduler
from app.fbconnector.ad_downloader import download_ads
from app.service.models import Advertisers, Tokens
from app.utils.loader import parse_and_load_adverts
from flask import render_template, request, session, g, jsonify
from flask import current_app as ap
from sqlalchemy import exc
import requests
from datetime import datetime

def call_loader(country='GB'):
    with application.app_context():
        print('starting loading job', datetime.now())

        advertisers = Advertisers.query.all()
        IDS = [int(a.page_id) for a in advertisers if a.country == country]
        print('FETCHING IDS ...', IDS)

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
            while page < 2: #next_page:
                print('...CRON...Starting download from FB library.................', ID, 'time=', datetime.now())
                body, next_page = download_ads(API_VERSION, LONG_TOKEN,\
                    PAGES_BETWEEN_STORING, ADS_PER_PAGE, [ID], country, next_page)
                print('...CRON.....Uploading data to DB....................', ID, 'page=', page, 'time=', datetime.now())
                parse_and_load_adverts(body, country)
                page += 1
            print('...CRON...Finished upload to db.............................', ID, 'time=', datetime.now())
        return '<h1> Advertisers: {0} </h1>'.format(IDS)

if len(sys.argv) < 2:
    raise ValueError("Pls provide ENV")

PARAMS = {
    'ENV': 'dev' # 'dev', 'prod'
}

for i, arg in enumerate(sys.argv):
    for param in PARAMS.keys():
        if arg.upper().find(param) > -1: PARAMS[param] = sys.argv[i][sys.argv[i].upper().find(param) + len(param) + 1:]
print('PARAMS', PARAMS)
application = create_app(PARAMS['ENV'])
INTERVAL = application.config['INTERVAL']

scheduler = BackgroundScheduler()
scheduler.add_job(func=call_loader, trigger='interval', seconds=INTERVAL, misfire_grace_time=10)
scheduler.start()


with application.app_context():
    db.create_all()

    application.run(use_reloader=False)
