from oncall import db

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column('id', db.Integer, primary_key=True)
    user_username = db.Column(db.String(200), db.ForeignKey('users.username'))
    team_slug = db.Column(db.Integer, db.ForeignKey('teams.slug'))
    role = db.Column(db.String(200))
    start = db.Column(db.String(100))
    end = db.Column(db.String(100))

    def __init__(self, username, team_slug, role, start, end = None):
		self.user_username = username
		self.team_slug = team_slug
		self.role = role
		self.start = start
		self.end = end

    def to_json(self):
    	r = dict(id=self.id, start=self.start, title="%s: %s" % (self.role, self.user.name))
    	if self.end is not None:
    		r['end'] = self.end
        return r

    def __repr__(self):
        return '<Event %s: %s %s>' % (self.team_slug, self.start, self.end)
