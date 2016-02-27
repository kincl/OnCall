# import class and constants
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL

from flask import current_app

from oncall.models import User, Team

# so we can monkey patch for
def get_conn():
    # define the server and the connection
    s = Server(current_app.config['LDAP_HOST'], port = current_app.config['LDAP_PORT'], get_info = ALL)  # define an unsecure LDAP server, requesting info on DSE and schema
    c = Connection(s, auto_bind = True, client_strategy = SYNC, check_names=True)
    #print(s.info) # display info from the DSE. OID are decoded when recognized by the library
    return c

def bind(username, password):
    c = get_conn()
    c.user = 'uid={0},{1},{2}'.format(username,
                                      current_app.config['LDAP_PEOPLE_OU'],
                                      current_app.config['LDAP_BASE_DN'])
    c.password = password
    return c.bind()

def search(filter, attributes):
    c = get_conn()

    c.search(current_app.config['LDAP_BASE_DN'], filter, SUBTREE, attributes = attributes)
    r = c.response
    return r

def sync_users():
    ldap_users = search(current_app.config['LDAP_SYNC_USER_FILTER'], ['uid', 'gecos'])

    for user in ldap_users:
        if type(user['attributes']['gecos']) is list:
            fullname = ''.join(user['attributes']['gecos'])
        else:
            fullname = user['attributes']['gecos']

        found_user = User.query.filter_by(username=user['attributes']['uid'][0]).first()
        if isinstance(found_user, User):
            current_app.logger.info('Updating user: {0}'.format(found_user.username))
            found_user.name = fullname
        else:
            uid = user['attributes']['uid'][0]
            current_app.logger.info('Creating user: {0}'.format(uid))
            current_app.db.session.add(User(uid, fullname))

    current_app.db.session.commit()

def sync_teams():
    ldap_groups = search(current_app.config['LDAP_SYNC_GROUP_FILTER'], ['cn', 'memberUid'])

    for group in ldap_groups:
        group_name = group['attributes']['cn'][0]

        team = Team.query.filter_by(name=group_name).first()
        # if team already exists, replace users
        if isinstance(team, Team):
            team.users = []
            for uid in group['attributes']['memberUid']:
                user = User.query.filter_by(username=uid).first()
                if isinstance(user, User):
                    team.users.append(user)
        # create the team and add the users
        else:
            team = Team(group_name)
            team.users = []
            for uid in group['attributes']['memberUid']:
                user = User.query.filter_by(username=uid).first()
                if isinstance(user, User):
                    team.users.append(user)
            current_app.db.session.add(team)

        current_app.logger.info('LDAP Sync team {0} members: {1}'.format(team.slug, [str(u.username) for u in team.users]))
    current_app.db.session.commit()


