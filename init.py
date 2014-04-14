from oncall import db
from oncall.models import Team
from oncall.models import User

db.create_all()

team1 = Team('Team 1')
jason = User('Jason Kincl', team1)
db.session.add(team1)
db.session.add(jason)
db.session.commit()