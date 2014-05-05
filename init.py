from oncall import db
from oncall.models import Team
from oncall.models import Event
from oncall.models import User

from datetime import date

db.create_all()

team1 = Team('Team 1')
jkincl = User('jkincl', 'Jason Kincl', team1.slug)
user1 = User('user1', 'Test User', team1.slug)
user2 = User('user2', 'Another User', team1.slug)
user3 = User('user3', 'Again User', team1.slug)
user4 = User('user4', 'Wow User', team1.slug)

db.session.add(team1)
db.session.add(jkincl)
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.add(user4)
db.session.add(Event(jkincl.username, team1.slug, "Role 1", date(2014,05,12)))
db.session.add(Event(jkincl.username, team1.slug, "Role 1", date(2014,05,13), date(2014,05,14)))
db.session.commit()
