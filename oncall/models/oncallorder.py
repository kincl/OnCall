from oncall import db

# TODO: ensure user only exists once?
class OncallOrder(db.Model):
    __tablename__ = 'oncall_order'
    order = db.Column(db.Integer, primary_key=True)
    team_slug = db.Column(db.String(200), db.ForeignKey('teams.slug'), primary_key=True)
    role = db.Column(db.String(200), primary_key=True)
    user_username = db.Column(db.String(200), db.ForeignKey('users.username'))

    def __init__(self, team, user, role, order):
        self.team_slug = team
        self.user_username = user
        self.role = role
        self.order = order

    def __repr__(self):
        return '<Oncall Order %s:%s position:%s role:%s>' % (self.team_slug, self.user_username, self.order, self.role)

    def get_title(self):
        return "%s: %s" % (self.role, self.user.name)

    def to_json(self):
        return dict(order=self.order, role=self.role, team_slug=self.team_slug, user=self.user.to_json())
