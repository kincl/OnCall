from oncall import db
from oncall.models import Team
from oncall.models import Event
from oncall.models import User

from datetime import date

db.create_all()

team1 = Team('Team 1')
jkincl = User('jkincl', 'Jason Kincl', team1.slug)

db.session.add(team1)
db.session.add(jkincl)
db.session.add(User('user1', 'Test User', team1.slug))
db.session.add(User('user2', 'Another User', team1.slug))
db.session.add(User('user3', 'Byzantine Candor', team1.slug))
db.session.add(User('user4', 'Cottonmouth', team1.slug))
db.session.add(User('user5', 'Bacon Ridge', team1.slug))
db.session.add(User('user6', 'Black Pearl', team1.slug))
db.session.add(User('user7', 'Egotistical Goat', team1.slug))
db.session.add(User('user8', 'Egotistical Giraffe', team1.slug))
db.session.add(User('user9', 'Candy Gram', team1.slug))
db.session.add(User('user10', 'Dark Thunder', team1.slug))
db.session.add(User('user11', 'Drop Mire', team1.slug))
db.session.add(User('user12', 'Entourage', team1.slug))
db.session.add(User('user13', 'Flux babbit', team1.slug))
db.session.add(User('user14', 'Firewalk', team1.slug))
db.session.add(User('user15', 'Gopherset', team1.slug))
db.session.add(User('user16', 'Hammer Mill', team1.slug))
db.session.add(User('user17', 'Hollowpoint', team1.slug))
db.session.add(User('user18', 'Iron Chef', team1.slug))
db.session.add(User('user19', 'Jet Plow', team1.slug))
db.session.add(User('user20', 'Island Transport', team1.slug))
db.session.add(Event(jkincl.username, team1.slug, "Primary", date(2014,05,12)))
db.session.add(Event(jkincl.username, team1.slug, "Primary", date(2014,05,13), date(2014,05,14)))
db.session.commit()
