from oncall.database import db

class OncallOrder(db.Model):
	__tablename__ = 'oncall_order'
    id = db.Column('id', db.Integer, primary_key=True)
    

    def __init__(self, name):
        self.name = name
