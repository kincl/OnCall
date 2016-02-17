from flask import current_app
from flask_login import LoginManager

from api.models import User

login_manager = LoginManager()
login_manager.login_view = '/login'


@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(username=userid).first()


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.args.get('api_key')
    if api_key:
        if api_key == current_app.config['ADMIN_TOKEN']:
            return User('AdminToken', 'Admin Token')
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user


def init_login(app):
    login_manager.init_app(app)
