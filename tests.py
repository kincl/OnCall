# import os
# import json

import unittest
from flask_testing import TestCase

from main import create_app
from database import db
from api.models import User, Team

# from datetime import datetime, timedelta
#
# from ldap3 import Server, Connection
#
# from oncall import app, db, ldap_helper
# from oncall.models import Team, User, Cron, Schedule
#
# #_ldap_server = LdapServer({
# #    'bind_dn': 'cn=admin,dc=example,dc=com',
# #    'password': 'pass1',
# #    'base': {'objectclass': ['top', 'organization', 'dcObject'],
# #             'dn': 'dc=example,dc=com',
# #             'attributes': {'dc': 'example'}},
# #    'entries': [
# #        {'objectclass': 'organizationalUnit',
# #         'dn': 'ou=Groups,dc=example,dc=com',
# #         'attributes': {'ou': 'Groups'}},
# #        {'objectclass': ['posixGroup'],
# #         'dn': 'cn=testgroup,ou=Groups,dc=example,dc=com',
# #         'attributes':{'cn': 'testgroup',
# #                       'memberUid': ['ldap_user1', 'user2']}},
# #         {'objectclass': ['posixGroup'],
# #          'dn': 'cn=team-1,ou=Groups,dc=example,dc=com',
# #          'attributes': {'cn': 'team-1',
# #                         'memberUid': ['ldap_user1', 'ldap_user2', 'user2']}},
# #        {'objectclass': 'organizationalUnit',
# #         'dn': 'ou=People,dc=example,dc=com',
# #         'attributes': {'ou': 'People'}},
# #        {'objectclass': ['person', 'inetOrgPerson', 'organizationalPerson', 'posixAccount', 'top'],
# #         'dn': 'uid=ldap_user1,ou=People,dc=example,dc=com',
# #         'attributes': {'uid': 'ldap_user1',
# #                        'loginShell': '/bin/bash',
# #                        'gecos': 'Ldap User1',
# #                        'userPassword': 'chevron',
# #                        'givenName': 'Ldap',
# #                        'cn': 'Ldap',
# #                        'sn': 'User1',
# #                        'mail': 'ldap_user1@example.com',
# #                        'ou': 'People',
# #                        'uidNumber': '501',
# #                        'gidNumber': '1000'}},
# #        {'objectclass': ['person', 'inetOrgPerson', 'organizationalPerson', 'posixAccount', 'top'],
# #         'dn': 'uid=user2,ou=People,dc=example,dc=com',
# #         'attributes': {'uid': 'user2',
# #                        'loginShell': '/bin/bash',
# #                        'gecos': 'User Example',
# #                        'userPassword': 'chevron',
# #                        'givenName': 'User2',
# #                        'cn': 'User2',
# #                        'sn': 'Example',
# #                        'mail': 'user2@example.com',
# #                        'ou': 'People',
# #                        'uidNumber': '503',
# #                        'gidNumber': '1000'}},
# #        {'objectclass': ['person', 'inetOrgPerson', 'organizationalPerson', 'posixAccount', 'top'],
# #         'dn': 'uid=ldap_user2,ou=People,dc=example,dc=com',
# #         'attributes': {'uid': 'ldap_user2',
# #                        'loginShell': '/bin/bash',
# #                        'gecos': 'Ldap User2',
# #                        'userPassword': 'chevron',
# #                        'givenName': 'Ldap',
# #                        'cn': 'Ldap',
# #                        'sn': 'User2',
# #                        'mail': 'ldap_user2@example.com',
# #                        'ou': 'People',
# #                        'uidNumber': '502',
# #                        'gidNumber': '1000'}},
# #    ]
# #})
#
# #def ldap_get_conn():
# #    dn = _ldap_server.config['bind_dn']
# #    pw = _ldap_server.config['password']
# #
# #    srv = Server('localhost', port=_ldap_server.config['port'])
# #    conn = Connection(srv, user=dn, password=pw, auto_bind=True)
# #    return conn


class OncallTesting(TestCase):

    def create_app(self):
        app = create_app()
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/testing_oncall.db'

        # http://stackoverflow.com/questions/26647032/py-test-to-test-flask-register-assertionerror-popped-wrong-request-context
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return app

    def setUp(self):
        db.create_all()
        db.session.commit()

        team1 = Team('Team 1')
        team2 = Team('Team 2')
        db.session.add(team1)
        db.session.add(team2)

        # so primary key gets populated
        db.session.flush()

        user1 = User('user1', 'Test User', [team1.id])
        user2 = User('user2', 'Another User', [team1.id])
        user3 = User('user3', 'Byzantine Candor', [team1.id, team2.id])
        user4 = (User('user4', 'Cottonmouth', [team1.id, team2.id]))
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.add(user4)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    # def test_login_logout(self):
    #     rv = self.login('user1', 'test')
    #     assert 'You were logged in' in rv.data
    #     rv = self.logout()
    #     assert 'You were logged out' in rv.data
    #     rv = self.login('adminx', 'default')
    #     assert 'Invalid username' in rv.data
    #     rv = self.login('admin', 'defaultx')
    #     assert 'Invalid password' in rv.data

    def test_teams_users_get(self):
        self.login('user1', 'test')
        rv = self.client.get('/api/v1/users')
        # print rv.data
        self.assert200(rv)
        assert 'users' in rv.data

        rv = self.client.get('/api/v1/teams')
        # print rv.data
        self.assert200(rv)
        assert 'teams' in rv.data

    def test_team_members_get(self):
        self.login('user1', 'test')
        rv = self.client.get('/api/v1/teams/1/members')
        # print rv.data
        self.assert200(rv)
        assert 'teams' in rv.data




#         # -- post
#         newteam = {'team':'Team 3'}
#         self.assert200(self.client.post('/api/v1/teams', content_type='application/json', data=json.dumps(newteam)))
#
#         rv = self.client.get('/api/v1/teams/team-3')
#         assert 'team-3' in rv.data
#
#     def test_team_get_put_delete(self):
#         # -- get
#         self.assert200(self.client.get('/api/v1/teams/team-1'))
#
#         # -- put
#         updateteam = {'name': 'TEAM 1 CHANGED'}
#         self.client.put('/api/v1/teams/team-1', content_type='application/json', data=json.dumps(updateteam))
#         rv = self.client.get('/api/v1/teams/team-1')
#         assert 'TEAM 1 CHANGED' in rv.data
#
#         # -- delete
#         self.client.delete('/api/v1/teams/team-1')
#         self.assert404(self.client.get('/api/v1/teams/team-1'))
#
# #    def test_ldap(self):
# #        rv = ldap_helper.search('(uid=user2)', ['uid', 'cn'])
# #        assert 'uid=user2,ou=People,dc=example,dc=com' in rv[0].values()
# #
# #    def test_ldap_bind(self):
# #        bind = ldap_helper.bind('user2', 'chevron')
# #        assert bind is True
# #
# #    def test_ldap_sync(self):
# #        ldap_helper.sync_users()
# #        assert User.query.filter_by(username="ldap_user1").first() is not None
# #
# #        ldap_helper.sync_teams()
# #        assert 'ldap_user1' in [u.username for u in Team.query.filter_by(slug='team-1').first().users]
# #        self.assert200(self.client.get('/api/v1/teams/testgroup'))
#
#     def test_pseudocron(self):
#         db.session.add(Schedule('team-1', 'user1', "Primary", 0))
#         db.session.add(Schedule('team-1', 'user2', "Secondary", 0))
#         db.session.add(Schedule('team-1', 'user3', "Primary", 1))
#         db.session.add(Schedule('team-1', 'user1', "Secondary", 1))
#         db.session.add(Schedule('team-1', 'user2', "Primary", 2))
#         db.session.add(Schedule('team-1', 'user3', "Secondary", 2))
#
#         db.session.add(Schedule('team-2', 'user3', "Primary", 0))
#         db.session.add(Schedule('team-2', 'user4', "Secondary", 0))
#         db.session.add(Schedule('team-2', 'user4', "Primary", 1))
#         db.session.add(Schedule('team-2', 'user3', "Secondary", 1))
#
#         #print self.client.get('api/v1/teams/team-1/schedule').data
#         #c = User.query.filter_by(name='oncall_rotate')
#         c = Cron('oncall_rotate')
#         c.date_updated = datetime.now() - timedelta(7)
#         db.session.add(c)
#         db.session.commit()
#
#         team1_sched = json.loads(self.client.get('api/v1/teams/team-1/schedule').data)
#         assert 'user3' in team1_sched['schedule']['Primary'][0]['user']['id']
#         assert 'user1' in team1_sched['schedule']['Secondary'][0]['user']['id']
#
#         self.client.get('schedule/rotate')
#
#         team2_sched = json.loads(self.client.get('api/v1/teams/team-2/schedule').data)
#         assert 'user4' in team2_sched['schedule']['Primary'][0]['user']['id']
#         assert 'user3' in team2_sched['schedule']['Secondary'][0]['user']['id']


if __name__ == '__main__':
    unittest.main()
