from flask.ext.script import Manager
from oncall import app
from flask import current_app

manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    current_app.db.create_all()
    current_app.db.session.commit()

if __name__ == "__main__":
    manager.run()
