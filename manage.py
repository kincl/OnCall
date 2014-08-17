from flask.ext.script import Manager
from oncall import app

manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    from oncall import db
    from oncall.models import Team
    from oncall.models import Event
    from oncall.models import User
    from oncall.models import Cron
    from oncall.models import OncallOrder

    db.create_all()
    db.session.commit()

if __name__ == "__main__":
    manager.run()
