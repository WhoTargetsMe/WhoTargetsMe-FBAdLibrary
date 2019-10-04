from flask import Flask
from flask_script import Manager, Command, Option
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db

flask_app = create_app('dev')

migrate = Migrate(flask_app, db)
manager = Manager(flask_app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
