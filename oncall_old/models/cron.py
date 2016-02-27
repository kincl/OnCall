from oncall import db
from datetime import date

class Cron(db.Model):
    """ Manages pseudo-cron """
    __tablename__ = 'cron'
    name = db.Column(db.String(200), primary_key=True)
    date_updated = db.Column(db.Date)

    _hide_command = []
    _search_on = 'name'

    def __init__(self, name):
        self.name = name
        self.date_updated = date.today()

    def __repr__(self):
        return '<Cron %r: %r>' % (self.name, self.date_updated)
