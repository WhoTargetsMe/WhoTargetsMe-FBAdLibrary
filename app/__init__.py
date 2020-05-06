
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import os

scheduler = APScheduler()
db = SQLAlchemy()

def create_app(config_type):
    app = Flask(__name__)

    configuration = os.path.join(os.getcwd(), 'config', config_type + '.py')
    app.config.from_pyfile(configuration)

    sentry_sdk.init(dsn=app.config["SENTRY_DSN"], integrations=[FlaskIntegration()])

    db.init_app(app)
    Migrate(app, db)

    from app.service import main
    app.register_blueprint(main)

    scheduler.init_app(app)
    scheduler.start()
    from app import tasks

    return app

app = create_app(os.getenv("FLASK_ENV", 'production'))

if __name__ == '__main__':
    app.run()
