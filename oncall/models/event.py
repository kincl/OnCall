from oncall import db

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column('id', db.Integer, primary_key=True)
    user_username = db.Column(db.String(200), db.ForeignKey('users.username'))
    team_slug = db.Column(db.Integer, db.ForeignKey('teams.slug'))
    role = db.Column(db.String(200))
    start = db.Column(db.Date)
    end = db.Column(db.Date)

    def __init__(self, user_username, team_slug, role, start, end = None):
		self.user_username = user_username
		self.team_slug = team_slug
		self.role = role
		self.start = start
		self.end = start if end is None else end

    def to_json(self):
    	r = dict(id=self.id, start=self.start.isoformat(), title="%s: %s" % (self.role, self.user.name))
    	if self.end is not None:
    		r['end'] = self.end.isoformat()
        return r

    def __repr__(self):
        return '<Event %s %s:%s from %s to %s>' % (self.id, self.team_slug, self.user_username, self.start, self.end)
