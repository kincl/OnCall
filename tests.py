import os
import unittest
import json
from flask.ext.testing import TestCase

from mock import patch
from ldap_test import LdapServer
from ldap3 import Server, Connection

from oncall import app, db, ldap_helper
from oncall.models import Team, User

_ldap_server = LdapServer({
    'bind_dn': 'cn=admin,dc=example,dc=com',
    'password': 'pass1',
    'base': {'objectclass': ['top', 'organization', 'dcObject'],
             'dn': 'dc=example,dc=com',
             'attributes': {'dc': 'example'}},
    'entries': [
        {'objectclass': 'organizationalUnit',
         'dn': 'ou=People,dc=example,dc=com',
         'attributes': {'ou': 'People'}},
        {'objectclass': ['person', 'inetOrgPerson', 'organizationalPerson', 'posixAccount', 'top'],
         'dn': 'uid=user,ou=People,dc=example,dc=com',
         'attributes': {'uid': 'user',
                        'loginShell': '/bin/bash',
                        'gecos': 'User Example',
                        'userPassword': 'chevron',
                        'givenName': 'User',
                        'cn': 'User',
                        'sn': 'Example',
                        'mail': 'user@example.com',
                        'ou': 'People',
                        'uidNumber': '501',
                        'gidNumber': '1000'}},
    ]
})

def ldap_get_conn():
    dn = _ldap_server.config['bind_dn']
    pw = _ldap_server.config['password']

    srv = Server('localhost', port=_ldap_server.config['port'])
    conn = Connection(srv, user=dn, password=pw, auto_bind=True)
    return conn


class OncallTesting(TestCase):

    def create_app(self):
        # set up testing config
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'testing'
        app.config['LDAP_HOST'] = 'dummy'
        app.config['LDAP_PORT'] = 'dummy'
        app.config['LDAP_BASE_DN'] = 'dc=example,dc=com'
        app.config['LDAP_PEOPLE_OU'] = 'ou=People'

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

        _ldap_server.start()
        # monkey patch our connection helper
        ldap_helper.get_conn = ldap_get_conn

    def tearDown(self):
        db.session.remove()
        db.drop_all()

        _ldap_server.stop()

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

    def test_ldap(self):
        rv = ldap_helper.search('(uid=user)', ['uid', 'cn'])
        assert 'uid=user,ou=People,dc=example,dc=com' in rv[0].values()

    def test_ldap_bind(self):
        bind = ldap_helper.bind('user', 'chevron')
        assert bind is True

if __name__ == '__main__':
    unittest.main()
