from app import db
from app.s3downloader.media_downloader_selenium import get_and_load_images_to_s3
from app.service import main
from app.service.models import Adverts, Advertisers, Tokens, Media
from app.utils.ad_downloader import download_ads
from app.utils.ad_inserter import parse_and_insert
from datetime import datetime, timedelta
from dateutil.parser import parse as dateparse
from flask import current_app as ap
from flask import request
from selenium import webdriver
from sqlalchemy import exc
from sqlalchemy.sql import text
from time import sleep
import requests

# test that backend is working
@main.route("/test", methods=["GET"])
def get_test_data():
    x = requests.get("https://reqres.in/api/users?page=2")  # mock request
    return "<h1> the greeting is: {0} </h1>".format(x.text)


def ads_for_page_id(page_id, country, ad_creation_time_min=False):

    next_page = "start"
    body_count = 0

    print("[{0}] Starting page_id: {1}".format(datetime.now(), page_id))

    while next_page:

        body, next_page = download_ads([page_id], next_page, country=country)
        body_count += len(body)

        parse_and_insert(body, country)

        """
        If the minimum ad_creation_time already stored is later than the last in 
        the body, then we don't need to continue.
        """
        if ad_creation_time_min:
            body_last_ad_creation_time = dateparse(body[-1]["ad_creation_time"])
            if ad_creation_time_min > body_last_ad_creation_time:
                next_page = False

    print(
        "[{0}] Finished page_id: {1}, ad_count: {2}".format(
            datetime.now(), page_id, body_count
        )
    )

    return


@main.route("/callloader", methods=["POST"])
def call_loader(country="US", page_id=False, all_ads=False):

    if request:
        """ 
        Country code has two uses:
        1. Select which advertisers from our db, filtered by country
        2. Use in FB graph as search criteria "ad_reached_countries"
        """
        country = request.form.get("country", country)

        """ Select single advertiser """
        page_id = request.form.get("page_id", page_id)

        """ Collect all historical ads, as opposed to max_ad_creation_time """
        all_ads = request.form.get("all_ads", all_ads)

    with ap.app_context():

        connection = db.engine.connect()
        statement = text(
            """
                SELECT
                    advertisers.page_id,
                    advertisers.country,
                    MAX(adverts.ad_creation_time) AS max_ad_creation_time,
                    COUNT(adverts.id) AS ad_count
                FROM
                    advertisers 
                    LEFT JOIN adverts ON advertisers.page_id = adverts.page_id
                WHERE advertisers.country = :country
                GROUP BY
                    advertisers.page_id,
                    advertisers.country
                ORDER BY
                    ad_count DESC;
            """
        )
        statement.columns(
            Advertisers.__table__.columns.page_id,
            Advertisers.__table__.columns.country,
            Adverts.__table__.columns.ad_creation_time,
            Adverts.__table__.columns.id,
        )
        results = connection.execute(statement, country=country).fetchall()

        for advertiser in results:
            # skip if we're being page_id specific. still got to be in db though
            if page_id and int(page_id) != int(advertiser["page_id"]):
                continue

            ads_for_page_id(
                advertiser["page_id"],
                advertiser["country"],
                ad_creation_time_min=False
                if all_ads
                else advertiser["max_ad_creation_time"],
            )

        return {"message": "success"}


# add new advertisers to the db
@main.route("/add/advertisers", methods=["POST", "PUT"])
def add_advertisers():
    body = dict(request.get_json())
    details = body["advertisers"]
    if not details or len(details) == 0:
        return "Pls provide at least one advertiser"
    id_check = [obj.get("page_id", None) for obj in details]
    country_check = [obj.get("country", None) for obj in details]
    if None in id_check or None in country_check:
        return "Pls make sure that all advertisers have page_id"

    if request.method == "POST":
        try:
            for obj in details:
                item = Advertisers(
                    obj.get("page_id", None),
                    obj.get("page_name", None),
                    obj.get("country", None),
                )
                db.session.add(item)
            db.session.commit()
        except exc.IntegrityError as ex:
            db.session.rollback()
            return {
                "Advertiser already exists or name is corrupted": obj.get(
                    "page_id", None
                )
            }
    elif request.method == "PUT":
        for obj in details:
            try:
                exists = Advertisers.query.filter_by(page_id=obj.get("page_id", None))
                if exists:
                    updated = exists.update(
                        {
                            "page_name": obj.get("page_name", None),
                            "country": obj.get("country", None),
                        }
                    )
                else:
                    item = Advertisers(
                        obj.get("page_id", None),
                        obj.get("page_name", None),
                        obj.get("country", None),
                    )
                    db.session.add(item)
                db.session.commit()
            except exc.IntegrityError as ex:
                db.session.rollback()
                return {"Error during update": obj.get("page_id", None)}
    advertisers = Advertisers.query.all()
    return {"advertisers": len(advertisers)}


# Manually add posts by country and load into db
# @main.route("/loadsome/<country>", methods=["POST"])
# def add_advert(country):
#     body = dict(request.get_json())
#     details = body["posts"]
#     if not details or len(details) == 0 or not country:
#         return "Pls provide at least one post and country"
#     parse_and_insert(body, country)
#     return "OK"


@main.route("/refreshtoken", methods=["POST"])
def refresh_token():
    latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
    SHORT_TOKEN = latest_record.short_token
    APP_ID = ap.config["APP_ID"]
    APP_SECRET = ap.config["APP_SECRET"]

    url = (
        "https://graph.facebook.com/v4.0/oauth/access_token?grant_type=fb_exchange_token&client_id="
        + APP_ID
        + "&client_secret="
        + APP_SECRET
        + "&fb_exchange_token="
        + SHORT_TOKEN
    )

    r = requests.get(url)
    details = r.json()
    seconds = details["expires_in"]

    latest_record.long_token = details["access_token"]
    latest_record.long_last_updated_at = datetime.now()
    latest_record.long_token_expires_on = datetime.now() + timedelta(seconds=seconds)

    db.session.commit()

    return "OK"


def get_long_token():
    latest_record = db.session.query(Tokens).order_by(Tokens.id.desc()).first()
    return latest_record.long_token


@main.route("/media", methods=["GET"])
def download_media():
    size = 20
    advrts = Adverts.query.filter_by(image_link=None)
    if size >= advrts.count():
        size = advrts.count()
    [print(i.post_id) for i in advrts[:size]]
    creds = {
        "long_token": get_long_token(),
    }
    if ap.config["FLASK_ENV"] == "development":
        driver = webdriver.Chrome()
        login_url = "https://www.facebook.com"
        driver.get(login_url)
        sleep(40)
        # email = driver.find_element_by_id("email")
        # passwd = driver.find_element_by_id("pass")
        # passwd = driver.find_element_by_id("pass")
        # button.click()

    elif ap.config["FLASK_ENV"] == "production":
        DRIVER_PATH = "/usr/bin/chromedriver"
        options = webdriver.ChromeOptions()
        options.add_argument("--remote-debugging-port=9222")
        options.headless = True
        driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)

    for advert in advrts[:size]:
        print("ITEM", advert.post_id)
        aws_links, www_links, ad_info = get_and_load_images_to_s3(
            advert.post_id, advert.page_id, creds, driver
        )
        if len(aws_links) == 0 and len(www_links) == 0:
            print("no links for", advert.post_id, advert.page_id)
            continue
        elif len(aws_links) > 0:
            advert.image_link = "uploaded_to_aws"
        else:
            advert.image_link = "www_links_only"
        if ad_info:
            advert.ad_info = ad_info
        try:
            item = Media(advert.id, list(www_links), aws_links)
            db.session.add(item)
            db.session.commit()
        except exc.IntegrityError as ex:
            db.session.rollback()
            continue
            # return 'error during media links saving'
    driver.quit()
    return "OK"
