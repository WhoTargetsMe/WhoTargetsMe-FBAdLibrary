from app.fbconnector.facebook import GraphAPI, GraphAPIError
from urllib.parse import urlsplit, parse_qs
import os
import sys

# DOCS:
# https://www.facebook.com/ads/library/api/
"""
Each search will return all of the results that match the specified parameters.
Since each page of results can return a maximum of 5,000 ads, please use the link provided at the end of the returned data to view results on the next page.

Rate limiting defines limits on how many API calls can be made within a specified time period.
Application-level rate limits apply to calls made using any access token other than a Page access token and ads APIs calls.
The total number of calls your app can make per hour is 200 times the number of users.
Please note this isn't a per-user limit. Any individual user can make more than 200 calls per hour, as long as the total for all users does not exceed the app maximum.
"""
# https://medium.com/@DrGabrielA81/python-how-making-facebook-api-calls-using-facebook-sdk-ea18bec973c8
# https://medium.com/@DrGabrielA81/python-how-getting-facebook-data-and-insights-using-facebook-sdk-9de14d3c12fb


def build_args(adspp, url=None):
    args = {}
    if url:
        query = urlsplit(url).query
        params = parse_qs(query)
        for k, v in params.items():
            if k == "limit":
                args[k] = adspp
            else:
                args[k] = v[0]
    return args


def download_ads(
    API_VERSION,
    LONG_TOKEN,
    PAGES_BETWEEN_STORING,
    ADS_PER_PAGE,
    IDS,
    country,
    next_page,
    single_call,
):

    graph = GraphAPI(version=API_VERSION)

    args = dict()
    args["access_token"] = LONG_TOKEN
    args["search_terms"] = ""
    args["ad_type"] = "POLITICAL_AND_ISSUE_ADS"
    args["ad_reached_countries"] = [country]
    args[
        "search_page_ids"
    ] = IDS  # list of specific page (advertiser) ids if we know them
    args["ad_active_status"] = "ALL"
    args[
        "fields"
    ] = "ad_creation_time,ad_delivery_start_time,ad_delivery_stop_time,ad_creative_body,ad_creative_link_caption,ad_creative_link_title,ad_creative_link_description,ad_snapshot_url,currency,funding_entity,demographic_distribution,impressions,page_id,page_name,region_distribution,spend"
    args["limit"] = ADS_PER_PAGE
    method = "/ads_archive"
    i = 1
    result = []

    if next_page == "start":
        try:
            r = graph.request(method, args)
            data = r.get("data", [])
            result.extend(data)
            next_page = r.get("paging", {}).get("next")
            print("-------RESULTS----------", "iterations=", i, "len data=", len(data))
            if single_call:
                return result, None

        except Exception as e:
            print("Error -+", e.message)
            print("Error ->", sys.exc_info()[0].message)

    while i < PAGES_BETWEEN_STORING:
        argsi = build_args(ADS_PER_PAGE, url=next_page)
        try:
            print("=======ARGS", argsi["search_page_ids"], argsi["after"])
        except:
            return result, None
        r = graph.request(method, argsi)
        data = r.get("data", [])
        result.extend(data)
        next_page = r.get("paging", {}).get("next", None)
        i += 1
        print("-------RESULTS----------", "iterations=", i, "len data=", len(data))

    return result, next_page
