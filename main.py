from flask import Flask

from database import db
from login import init_login

from api.views import api_app
from cal.views import calendar_app

def create_app():
    app = Flask(__name__)
    db.init_app(app)
    app.register_blueprint(api_app)
    app.register_blueprint(calendar_app)

    app.config.from_object('config.Defaults')

    # TODO remove this
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'asdf'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

    init_login(app)

    @app.after_request
    def add_header(response):
        """
        Do not cache json query responses
        """
        if response.mimetype == 'application/json':
            response.headers['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = 'Fri, 01 Jan 1990 00:00:00 GMT'
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
