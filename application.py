from app import create_app, db
from app.service.routes import call_loader
from apscheduler.schedulers.background import BackgroundScheduler
import os
import sys

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

scheduler.add_job(call_loader, 'cron', month='*', day='*', hour='1,7,10,15,19', minute='1')
scheduler.start()

if __name__ == '__main__':
    with application.app_context():
        db.create_all()

        application.run(use_reloader=False)
