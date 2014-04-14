from oncall.database import db

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    role = db.Column(db.String(200))
    team_id = db.Column(db.Integer)
    start = db.Column(db.datetime)
    end = db.Column(db.datetime)

    def __init__(self):
		pass
