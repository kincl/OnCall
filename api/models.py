from datetime import date
from database import db


class Cron(db.Model):
    """ Manages pseudo-cron """
    __tablename__ = 'cron'
    name = db.Column(db.String(200), primary_key=True)
    date_updated = db.Column(db.Date)

    _search_on = 'name'

    def __init__(self, name):
        self.name = name
        self.date_updated = date.today()

    def __repr__(self):
        return '<Cron %r: %r>' % (self.name, self.date_updated)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column('id', db.Integer, primary_key=True)
    user_username = db.Column(db.String(200), db.ForeignKey('users.username'))
    team_slug = db.Column(db.Integer, db.ForeignKey('teams.slug'))
    role = db.Column(db.String(200))
    start = db.Column(db.Date)
    end = db.Column(db.Date)

    _search_on = 'id'

    def __init__(self, user_username, team_slug, role, start, end = None):
        self.user_username = user_username
        self.team_slug = team_slug
        self.role = role
        self.start = start
        self.end = start if end is None else end

    def to_json(self):
        r = dict(id=self.id,
                 start=self.start.isoformat(),
                 title="%s: %s" % (self.role, self.user.name),
                 user_username=self.user_username,
                 role=self.role)
        if self.end is not None:
            r['end'] = self.end.isoformat()
        return r

    def __repr__(self):
        return '<Event %s %s %s:%s from %s to %s>' % (self.id, self.team_slug, self.role, self.user_username, self.start, self.end)


# TODO: ensure user only exists once?
class Schedule(db.Model):
    __tablename__ = 'schedule'
    order = db.Column(db.Integer)
    team_slug = db.Column(db.String(200), db.ForeignKey('teams.slug'), primary_key=True)
    role = db.Column(db.String(200), primary_key=True)
    user_username = db.Column(db.String(200), db.ForeignKey('users.username'), primary_key=True)


    def __init__(self, team, user, role, order):
        self.team_slug = team
        self.user_username = user
        self.role = role.capitalize()
        self.order = order

    def __repr__(self):
        return '<Schedule %s:%s position:%s role:%s>' % (self.team_slug, self.user_username, self.order, self.role)

    def get_title(self):
        return "%s: %s" % (self.role, self.user.name)

    def to_json(self):
        return dict(order=self.order, role=self.role, team_slug=self.team_slug, user=self.user.to_json())


class Team(db.Model):
    __tablename__ = 'teams'
    slug = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))

    _search_on = 'slug'

    def __init__(self, name=None):
        '''
        name - Team name
        '''
        self.name = name
        self.slug = None

    def to_json(self):
        return dict(name=self.name,
                    id=self.slug)

    def __repr__(self):
        return '<Team %r>' % self.name

teams = db.Table('users_to_teams',
    db.Column('user_username', db.String(200), db.ForeignKey('users.username')),
    db.Column('team_slug', db.String(200), db.ForeignKey('teams.slug'))
)


class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    primary_team = db.Column(db.String(200), db.ForeignKey('teams.slug'), nullable=True)
    contact_card = db.Column(db.Text())
    api_key = db.Column(db.String(200))

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
            self.primary_team = self.teams[0].slug
        else:
            self.primary_team = None
        self.contact_card = ''

    # TODO: Need to decide how to handle appends and single deletes?
    def set_teams(self, myteams):
        self.teams = []

        for team in myteams:
            # TODO: error checking if no team comes back
            add = Team.query.filter_by(slug = team).one()
            self.teams.append(add)


    def to_json(self):
        return dict(name=self.name, id=self.username, teams=[t.slug for t in self.teams])

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
        return '<User %r>' % self.name
