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
    teams = db.relationship('Team',
                            secondary=teams, 
                            backref=db.backref('users', 
                                               lazy='dynamic'))
    events = db.relationship('Event', 
                             backref='user',
                             lazy='dynamic')
    oncallorder = db.relationship('OncallOrder', 
                                  backref='user',
                                  lazy='dynamic')

    def __init__(self, username, name, team_slug = None):
        self.username = username
        self.name = name
        self.teams.append(Team.query.filter_by(slug = team_slug).first()) 

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
