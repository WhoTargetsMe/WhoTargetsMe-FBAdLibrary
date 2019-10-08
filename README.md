FB LIB CLONE TOOL

1. Install python 3.6.5 (pip should be installed authomatically)
2. Install virtualenv

3. Create and activate virtualenv: from root directory:
virtualenv myenv
source myenv/bin/active
cd myenv
git clone repo to myenv

4. Install libraries
pip install -r requirements.txt

5. Create Postgres DB
- Install postgres
- Create postgres admin and password

- Log as admin
psql postgres -U admin

- Create database
CREATE DATABASE dbname

6. Init DB and set track for migrations
TEMPORARILY: change line 6 in manage.py to
```
flask_app = create_app('prod')
```
if intend to run with prod config. Default config is 'dev'

7. Run the project
python run.py ENV=dev

- locally will run on localhost:5000

8. Sample calls

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

- Load all ads by given advertiser or for country

GET {{url}}/loadall/<country>/<advertiser_id>

Example (load by page_id): {{url}}/loadall/GB/8807334278

Example (load all for country): {{url}}/loadall/GB/all


9. After any schema change in the app need to migrate

- python manage.py db init
- python manage.py db migrate
- python manage.py db upgrade

For help:
- python manage.py db --help
