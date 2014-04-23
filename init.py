from oncall import db
from oncall.models import Team
from oncall.models import Event
from oncall.models import User

db.create_all()

team1 = Team('Team 1')
jason = User('jkincl', 'Jason Kincl', team1.slug)
event1 = Event(jason.username, team1.slug, "Role 1", "2014-04-12")
event2 = Event(jason.username, team1.slug, "Role 1", "2014-04-13", "2014-04-14")
db.session.add(team1)
db.session.add(jason)
db.session.add(event1)
db.session.add(event2)
db.session.commit()