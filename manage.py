from flask.ext.script import Manager, Command, Option
from oncall import app

from oncall.models import OncallOrder, Event, Team, User, Cron
from oncall import db

import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute

manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    db.create_all()
    db.session.commit()


class CRUD(Command):
    def __init__(self, model):
        self.model = model

    def get_options(self):
        opts = [Option('action', choices=['create', 'update', 'delete', 'list', 'debug'], help="Action to take")]

        # get all of the table columns and add them as options
        for c in self.model.__table__.columns:
            opts.append(Option('--{0}'.format(c.key)))

        # need to get all of the possible attributes that can be modified, seems like
        # I don't need to do the above... TODO: fix?
        for k,v in self.model.__dict__.items():
            if isinstance(v, InstrumentedAttribute):
                if '--{0}'.format(k) not in [opt.args[0] for opt in opts] and \
                   k not in self.model._hide_command:
                    opts.append(Option('--{0}'.format(k)))

        return opts

    def create(self, options):
        #print options
        #print inspect.getargspec(self.model.__init__)
        print self.model.__init__.__doc__

        args = dict()
        for o in options.keys():
            if o in inspect.getargspec(self.model.__init__)[0]:
                # TODO: only if no defaults are set?
                if options[o] is None:
                    print "{0} is required and connot be null".format(o)
                    raise Exception
                args[o] = options[o]

        db.session.add(self.model(**args))
        db.session.commit()

    def update(self, options):
        # TODO: updating single entries is easy, need to handle things like user.teams
        print options

    def list(self):
        col = self.model.__table__.columns
        for c in col:
            print c.key,
        print

        for t in self.model.query.all():
            for c in col:
                print getattr(t, c.key),
            print

    def debug(self):
        print self.model._hide_command
        pass
        # for t in self.model.query.all():
        #     print t
        #     for i in inspect.getmembers(t):
        #         print i

    def run(self, action, **options):
        print action
        if action == 'list':
            self.list()
        if action == 'create':
            self.create(options)
        if action == 'update':
            self.update(options)
        if action == 'debug':
            self.debug()


manager.add_command('user', CRUD(User))
manager.add_command('team', CRUD(Team))


if __name__ == "__main__":
    manager.run()
