from oncall import db

class Team(db.Model):
    __tablename__ = 'teams'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    members = db.relationship('User', 
                              backref='team',
                              lazy='dynamic')

    def __init__(self, name):
        self.name = name
