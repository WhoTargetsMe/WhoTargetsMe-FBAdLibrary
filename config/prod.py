import os

DEBUG=False
SECRET_KEY='prodsecret'
# postgresql://<username>:<userpassword>@<url>/<dbname>
# postgresql://postgres:***REMOVED***@wtm-ad-library-stage.cfhyzec3tjdz.eu-central-1.rds.amazonaws.com/fbadlibraryclone
SQLALCHEMY_DATABASE_URI=os.environ['DATABASE_URL']
SQLALCHEMY_TRACK_MODIFICATIONS=False
APP_ID='1969644276620014'
APP_SECRET='8f12eb11035256f47ed1be33974967a6'
API_VERSION='3.1'
# should be moved to db
LONG_TOKEN='EAAbZCYYtxGu4BAJy9FubXICjw6eYrY3vw6YVGU5t3haccscdDEcMF8NvEf9vCcLHE1gHdxfp4R51LLF5kdde4qv6zIP7uu6MPiclQaMCcr6f98XEVqyAvPZBNhZAIobrp5dOf5cgJtMXCQSRdVZBIf1MM3i7ZAYGvFvuIIBuUnwZDZD'
LONG_TOKEN_EXPIRES_IN=5184000

# How many pages we want to fetch between each storing operation
PAGES_BETWEEN_STORING = 10
# Each page may contain 25-5000 ads, but tests show that they don't permit to fetch 5000
ADS_PER_PAGE = 500
# Interval of cron job in seconds
INTERVAL = 3600*24
