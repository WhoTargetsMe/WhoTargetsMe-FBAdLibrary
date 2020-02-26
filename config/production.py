import os
from config.aws import _ACCESS_KEY, _SECRET_KEY, _SQLALCHEMY_DATABASE_URI, _APP_ID, _APP_SECRET

DEBUG=True
ACCESS_KEY=_ACCESS_KEY
SECRET_KEY=_SECRET_KEY
# postgresql://<username>:<userpassword>@<url>/<dbname>
# SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL']
SQLALCHEMY_DATABASE_URI=_SQLALCHEMY_DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS=False
APP_ID=_APP_ID
APP_SECRET=_APP_SECRET
API_VERSION='3.1'
FLASK_ENV='production'

# How many pages we want to fetch between each storing operation
PAGES_BETWEEN_STORING = 5
# Each page may contain 25-5000 ads, but tests show that they don't permit to fetch 5000
ADS_PER_PAGE = 1000
# Interval of cron job in seconds (if background job is interval)
#INTERVAL = 3600
