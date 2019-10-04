import facebook
from flask import current_app as app

API_VERSION = app.config['API_VERSION']
APP_ID = app.config['APP_ID']
APP_SECRET = app.config['APP_SECRET']

graph = facebook.GraphAPI(version=API_VERSION)
token = graph.get_app_access_token(app_id=APP_ID, app_secret=APP_SECRET, offline=True)
