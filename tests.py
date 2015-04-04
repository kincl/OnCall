import os
import unittest
import urllib2
from flask.ext.testing import TestCase,LiveServerTestCase

from oncall import app, db

from oncall.models import Team, User

class OncallTesting(TestCase):

    def create_app(self):
        # set up testing config
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'testing'

        return app

    def setUp(self):
        db.create_all()
        db.session.commit()

        team1 = Team('Team 1')
        team2 = Team('Team 2')
        db.session.add(team1)
        db.session.add(team2)

        user1 = User('user1', 'Test User', [team1.slug])
        user2 = User('user2', 'Another User', [team1.slug])
        user3 = User('user3', 'Byzantine Candor', [team2.slug])
        user4 = (User('user4', 'Cottonmouth', [team2.slug]))
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_teams(self):
        response = self.client.get('/api/v1/teams')

        assert 'teams' in response.json

if __name__ == '__main__':
    unittest.main()