from oncall import db

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
