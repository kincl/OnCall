from oncall import db

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200))
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'))

    def __init__(self, username, name, team = None):
        self.username = username
        self.name = name
        self.team = team

    def to_json(self):
        return dict(name=self.name, id=self.username, team=self.team.name)

    def __eq__(self, other):
        return type(self) is type(other) and self.username == other.username

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<User %r>' % self.name
