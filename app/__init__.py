import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

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
