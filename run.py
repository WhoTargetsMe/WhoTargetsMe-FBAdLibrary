from app import create_app, db
import sys

if len(sys.argv) < 2:
    raise ValueError("Pls provide ENV")

PARAMS = {
    'ENV': 'dev' # 'dev', 'prod'
}

for i, arg in enumerate(sys.argv):
    for param in PARAMS.keys():
        if arg.upper().find(param) > -1: PARAMS[param] = sys.argv[i][sys.argv[i].upper().find(param) + len(param) + 1:]
print('PARAMS', PARAMS)

if __name__ == '__main__':
    flask_app = create_app(PARAMS['ENV'])

    with flask_app.app_context():
        db.create_all()

    flask_app.run()
