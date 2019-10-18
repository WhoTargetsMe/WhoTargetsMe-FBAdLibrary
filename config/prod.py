import os

DEBUG=True
SECRET_KEY='prodsecret'
# postgresql://<username>:<userpassword>@<url>/<dbname>
# postgresql://postgres:***REMOVED***@wtm-ad-library-stage.cfhyzec3tjdz.eu-central-1.rds.amazonaws.com/fbadlibraryclone
# SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL']
SQLALCHEMY_DATABASE_URI='postgresql://postgres:***REMOVED***@wtm-ad-library-stage.cfhyzec3tjdz.eu-central-1.rds.amazonaws.com/fbadlibraryclone'
SQLALCHEMY_TRACK_MODIFICATIONS=False
APP_ID='1969644276620014'
APP_SECRET='8f12eb11035256f47ed1be33974967a6'
API_VERSION='3.1'

# How many pages we want to fetch between each storing operation
PAGES_BETWEEN_STORING = 5
# Each page may contain 25-5000 ads, but tests show that they don't permit to fetch 5000
ADS_PER_PAGE = 1000
# Interval of cron job in seconds (if background job is interval)
#INTERVAL = 3600
