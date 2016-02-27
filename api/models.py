from datetime import date
from database import db


class Cron(db.Model):
    """ Manages pseudo-cron """
    __tablename__ = 'cron'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    date_updated = db.Column(db.Date)

    # _search_on = 'name'

    def __init__(self, name):
        self.name = name
        self.date_updated = date.today()

    def __repr__(self):
        return '<Cron {0}: {1}>'.format(self.name, self.date_updated)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    role = db.Column(db.String(64))
    start = db.Column(db.Date)
    end = db.Column(db.Date)

    # _search_on = 'id'

    def __init__(self, user_id, team_id, role, start, end = None):
        self.user_id = user_id
        self.team_id = team_id
        self.role = role
        self.start = start
        self.end = start if end is None else end

    def get_title(self):
        return "{0}: {1}".format(self.role, self.user.name)

    def to_json(self):
        event = dict(type='events',
                     id=self.id,
                     start=self.start.isoformat(),
                     title=self.get_title(),
                     role=self.role,
                     team_id=self.team_id,
                     user_id=self.user_id)

        if self.end is not None:
            event['end'] = self.end.isoformat()

        return event

    def __repr__(self):
        return '<Event {0} {1} {2} from {3} to {4}>'.format(self.id, self.team_id,
                                                            self.role, self.start,
                                                            self.end)


# TODO: ensure user only exists once?
class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    role = db.Column(db.String(64))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, team, user, role, order):
        self.team_id = team
        self.user_id = user
        self.role = role.capitalize()
        self.order = order

    def get_title(self):
        return "{0}: {1}".format(self.role, self.user.name)

    def to_json(self):
        return dict(type='schedule',
                    id=self.id,
                    order=self.order,
                    role=self.role,
                    team_id=self.team_id,
                    user_id=self.user_id)

    def __repr__(self):
        return '<Schedule {0}:{1} order:{2} role:{3}>'.format(self.team_id,
                                                              self.user_id,
                                                              self.order,
                                                              self.role)

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)

    # _search_on = 'slug'

    def __init__(self, name=None):
        '''
        name - Team name
        '''
        self.name = name

    def to_json(self):
        return dict(type='teams',
                    id=self.id,
                    name=self.name)

    def __repr__(self):
        return '<Team {0}>'.format(self.name)

teams = db.Table('users_to_teams',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('team_id', db.Integer, db.ForeignKey('teams.id'))
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True)
    name = db.Column(db.String(256))
    primary_team = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    contact_card = db.Column(db.Text())
    api_key = db.Column(db.String(256))

    # Not sure why I had this??
    # teams = db.relationship('Team',
    #                         secondary=teams,
    #                         backref=db.backref('users',
    #                                            lazy='dynamic'))
    teams = db.relationship('Team',
                            secondary=teams,
                            backref='users')
    events = db.relationship('Event',
                             backref='user',
                             lazy='dynamic')
    schedule = db.relationship('Schedule',
                               backref='user',
                               lazy='dynamic')


    def __init__(self, username=None, name=None, teams=None):
        '''
        username - username
        name - name
        teams - [team1,team2]
        '''
        self.username = username
        self.name = name
        if not teams is None:
            self.set_teams(teams)
        if len(self.teams) != 0:
            self.primary_team = self.teams[0].id
        else:
            self.primary_team = None
        self.contact_card = ''

    # TODO: Need to decide how to handle appends and single deletes?
    def set_teams(self, myteams):
        self.teams = []

        for team_id in myteams:
            # TODO: error checking if no team comes back
            add = Team.query.filter_by(id = team_id).one()
            self.teams.append(add)

    def to_json(self):
        return dict(type='users',
                    id=self.id,
                    name=self.name,
                    username=self.username,
                    teams=[t.id for t in self.teams])

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.username)

    def __eq__(self, other):
        return type(self) is type(other) and self.username == other.username

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<User {0}>'.format(self.name)
