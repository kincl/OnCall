import os
import unittest
import json
from flask.ext.testing import TestCase

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

    def test_get_oncall_index(self):
        rv = self.client.get('/')

        assert 'Team 1' in rv.data

    def test_teams_get_post(self):
        # -- get
        rv = self.client.get('/api/v1/teams')
        self.assert200(rv)
        assert 'teams' in rv.json

        # -- post
        newteam = {'team':'Team 3'}
        self.assert200(self.client.post('/api/v1/teams', content_type='application/json', data=json.dumps(newteam)))

        rv = self.client.get('/api/v1/teams/team-3')
        assert 'team-3' in rv.data

    def test_team_get_put_delete(self):
        # -- get
        self.assert200(self.client.get('/api/v1/teams/team-1'))

        # -- put
        updateteam = {'name': 'TEAM 1 CHANGED'}
        self.client.put('/api/v1/teams/team-1', content_type='application/json', data=json.dumps(updateteam))
        rv = self.client.get('/api/v1/teams/team-1')
        assert 'TEAM 1 CHANGED' in rv.data

        # -- delete
        self.client.delete('/api/v1/teams/team-1')
        self.assert404(self.client.get('/api/v1/teams/team-1'))

if __name__ == '__main__':
    unittest.main()
