from oncall import db

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    team_slug = db.Column(db.String(200), db.ForeignKey('teams.slug'))
    events = db.relationship('Event', 
                             backref='user',
                             lazy='dynamic')
    oncallorder = db.relationship('OncallOrder', 
                                  backref='user',
                                  lazy='dynamic')

    def __init__(self, username, name, team_slug = None):
        self.username = username
        self.name = name
        self.team_slug = team_slug

    def to_json(self):
        return dict(name=self.name, id=self.username, team=self.team.name)

    def __eq__(self, other):
        return type(self) is type(other) and self.username == other.username

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<User %r>' % self.name
