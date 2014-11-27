from flask.ext.script import Manager, Command, Option
from oncall import app

from oncall.models import OncallOrder, Event, Team, User, Cron
from flask import current_app

import inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute

from tabulate import tabulate

manager = Manager(app)

@manager.command
def init_db():
    ''' Initialize the database '''
    current_app.db.create_all()
    current_app.db.session.commit()


class CRUD(Command):
    def __init__(self, model, choices=['create', 'update', 'delete', 'list', 'debug']):
        self.model = model
        self.choices = choices
        self.attributes = []
        for k,v in self.model.__dict__.items():
            if isinstance(v, InstrumentedAttribute) and \
               k not in self.model._hide_command:
                self.attributes.append(k)
        self.__doc__ = model.__doc__

    def get_options(self):
        opts = [Option('action', choices=self.choices, help="Action to take")]

        # get all of the table columns and add them as options
        for c in self.model.__table__.columns:
            opts.append(Option('--{0}'.format(c.key)))

        # need to get all of the possible attributes that can be modified, seems like
        # I don't need to do the above... --- do need it ---
        for k,v in self.model.__dict__.items():
            if isinstance(v, InstrumentedAttribute):
                if '--{0}'.format(k) not in [opt.args[0] for opt in opts] and \
                   k not in self.model._hide_command:
                    opts.append(Option('--{0}'.format(k)))

        # add selector option
        opts.append(Option('--{0}'.format(self.model.__name__), help="Selector for update/delete functions, search on {0}".format(self.model._search_on)))

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

        if options[self.model.__name__] is None:
            print "Use selector --{0} to select the item to update".format(self.model.__name__)
            return

        querydict = {self.model._search_on: options[self.model.__name__]}
        user = self.model.query.filter_by(**querydict).first()

        if user is None:
            print "No user found"
            return

        print user, options


    def list(self):
        table = []
        for t in self.model.query.all():
            row = []
            for c in self.attributes:
                row.append(getattr(t, c))
            table.append(row)

        print tabulate(table, self.attributes, tablefmt='simple')

    def debug(self):
        #print self.model._hide_command

        print self.model.__mapper__.primary_key

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
manager.add_command('event', CRUD(Event, ['list']))
manager.add_command('oncallorder', CRUD(OncallOrder, ['list']))
manager.add_command('cron', CRUD(Cron, ['list','update']))


if __name__ == "__main__":
    manager.run()
