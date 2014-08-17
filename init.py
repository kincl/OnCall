from oncall import db
from oncall.models import Team
from oncall.models import Event
from oncall.models import User
from oncall.models import Cron
from oncall.models import OncallOrder

from datetime import date

#db.create_all()

team1 = Team('Team 1')
team2 = Team('Team 2')
db.session.add(team1)
db.session.add(team2)
db.session.commit()


jkincl = User('jkincl', 'Jason Kincl', team1.slug)
user1 = User('user1', 'Test User', team1.slug)
user2 = User('user2', 'Another User', team1.slug)
user3 = User('user3', 'Byzantine Candor', team1.slug)
db.session.add(jkincl)
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)


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
db.session.add(User('user21', 'RageMaster', team2.slug))
db.session.add(User('user22', 'Return Spring', team2.slug))
db.session.add(User('user23', 'Sneaker Net', team2.slug))
db.session.add(User('user24', 'Short Sheet', team2.slug))
db.session.add(User('user25', 'Seagull Faro', team2.slug))
db.session.add(Event(jkincl.username, team1.slug, "Primary", date(2014,05,12)))
db.session.add(Event(jkincl.username, team1.slug, "Primary", date(2014,05,13), date(2014,05,14)))

db.session.add(OncallOrder(team1.slug, jkincl.username, "Primary", 0))
db.session.add(OncallOrder(team1.slug, user1.username, "Secondary", 0))
db.session.add(OncallOrder(team1.slug, user2.username, "Primary", 1))
db.session.add(OncallOrder(team1.slug, jkincl.username, "Secondary", 1))
db.session.add(OncallOrder(team1.slug, user3.username, "Primary", 2))
db.session.add(OncallOrder(team1.slug, user2.username, "Secondary", 2))
db.session.add(OncallOrder(team1.slug, user1.username, "Primary", 3))
db.session.add(OncallOrder(team1.slug, user3.username, "Secondary", 3))


db.session.commit()
