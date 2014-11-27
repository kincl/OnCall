from oncall import db

from team import Team

teams = db.Table('users_to_teams',
    db.Column('user_username', db.String(200), db.ForeignKey('users.username')),
    db.Column('team_slug', db.String(200), db.ForeignKey('teams.slug'))
)

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    primary_team = db.Column(db.String(200), db.ForeignKey('teams.slug'))
    contact_card = db.Column(db.Text())
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
    oncallorder = db.relationship('OncallOrder',
                                  backref='user',
                                  lazy='dynamic')

    _hide_command = ['contact_card', 'events', 'oncallorder']
    _search_on = 'username'

    def __init__(self, username, name, teams = None):
        '''
        username - username
        name - name
        teams - team1,team2
        '''
        self.username = username
        self.name = name
        self.set_teams(teams)
        if teams:
            self.primary_team = self.teams[0]
        else:
            self.primary_team = None
        self.contact_card = ''

    # TODO: Need to decide how to handle appends and single deletes?
    def set_teams(self, teams):
        new_teams = []
        # TODO: HAX?
        if isinstance(teams, str):
            teams = teams.split(',')

        for team in teams:
            new_teams.append(Team.query.filter_by(slug = team).first())
        self.teams = new_teams

    def to_json(self):
        return dict(name=self.name, id=self.username)

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
