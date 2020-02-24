
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app(config_type):
    application = Flask(__name__)
    
    configuration = os.path.join(os.getcwd(), 'config', config_type + '.py')
    application.config.from_pyfile(configuration)

    db.init_app(application)
    migrate = Migrate(application, db)

    from app.service import main
    application.register_blueprint(main)

    return application

from app.service.routes import call_loader
from apscheduler.schedulers.background import BackgroundScheduler

application = create_app(os.getenv("FLASK_ENV", 'production'))

scheduler = BackgroundScheduler()
scheduler.add_job(call_loader, 'cron', month='*', day='*', hour='1,7,10,15,19', minute='1')
scheduler.start()

if __name__ == '__main__':
    with application.app_context():
        db.create_all()

        application.run()
