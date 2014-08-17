from flask.ext.script import Manager
from oncall import app

from oncall.models import OncallOrder, Event, Team, User, Cron
from oncall import db

manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    db.create_all()
    db.session.commit()

@manager.command
def user():
    ''' Manage Users '''
    raise NotImplementedError

@manager.command
def team():
    ''' Manage Teams '''
    raise NotImplementedError

@manager.command
def cron():
    ''' Manage pseudo-cron '''
    raise NotImplementedError

if __name__ == "__main__":
    manager.run()
