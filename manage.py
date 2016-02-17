from flask import url_for
from flask_script import Manager

from main import create_app
from database import db
from api.models import User

app = create_app()
manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    with app.test_request_context():
        db.create_all()

@manager.command
def create_superuser(user):
    ''' create user '''
    with app.test_request_context():
        db.session.add(User(user, 'SuperUser'))
        db.session.commit()

# @manager.command
# def sync_ldap():
#     ''' Perform an LDAP sync '''
#     sync_users()
#     sync_teams()

@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print line

if __name__ == "__main__":
    manager.run()
