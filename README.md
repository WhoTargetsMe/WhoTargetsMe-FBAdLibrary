# Facebook Ads Library API clone tool

## Purpose

As part of a transparency effort, Facebook provides an API to review adverts
that have been posted to their platform. Though they provide a UI to look
at this data, it's important for transparency focused organisations, such as
Who Targets Me, to be able to review this in different ways. To that end, we
created this tool.

## Install

### Requirements

Python 3, PostgreSQL, a Facebook developer account

### Install dependencies

- `virtualenv venv`
- `source venv/bin/activate`
- `pip install -r requirements.txt`

### Create Postgres DB to store results

- Create a database and ensure it's details are in you config

### Running the project

The project makes use of `FLASK_ENV` with default of `production` for config
switching. Options are `development` or `production`.

You could `export FLASK_ENV=development` if you want to always use that.

Make sure your details are correct in config/<FLASK_ENV>.py

For the first run, `FLASK_ENV=development flask db upgrade`

Subsequent runs are `FLASK_ENV=development flask run`, which run locally on localhost:5000

## Usage

### Sample calls

- Add/update advertisers

POST, PUT {{url}}/add/advertisers (page_id cannot be updated - POST will raise, PUT will update other details)

Example: {{url}}/add/advertisers
Example body:

```
{"advertisers":
    [
      {"page_id":"164027949687", "page_name": "Labour Party", "country": "GB"}, {"page_id":"8807334278", "page_name": "Conservatives", "country": "GB"}
    ]
}
```

### Load all ads by given advertiser or for country

GET {{url}}/loadall/<country>/<advertiser_id>

Example (load by page_id): {{url}}/loadall/GB/8807334278

Example (load all for country): {{url}}/loadall/GB/all

## Troubleshooting

### psycopg2

Problems installing `psycopg2`?

Make sure you have `pg_client`. Just run that on your CLI to test.

Maybe clang error `library not found for -lssl`? Maybe you installed openssl via
brew, so set env vars for LDFLAGS and CPPFLAGS.

```
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
```
