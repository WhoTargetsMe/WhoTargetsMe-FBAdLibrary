import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand


db = SQLAlchemy()

def create_app(config_type):
    app = Flask(__name__)
    configuration = os.path.join(os.getcwd(), 'config', config_type + '.py')
    app.config.from_pyfile(configuration)

    db.init_app(app)
    migrate = Migrate(app, db)

    from app.service import main
    app.register_blueprint(main)

    return app
