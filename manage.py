# from flask.ext.script import Manager
# from oncall import app
# from oncall.ldap_helper import sync_users, sync_teams
# from flask import current_app
#
# from oncall.models import User
#
# manager = Manager(app)
#
# @manager.command
# def init_db():
#     ''' Initialize the database '''
#     current_app.db.create_all()
#     current_app.db.session.commit()
#
# @manager.command
# def create_superuser(user):
#     ''' create user '''
#     current_app.db.session.add(User(user, 'SuperUser'))
#     current_app.db.session.commit()
#
# @manager.command
# def sync_ldap():
#     ''' Perform an LDAP sync '''
#     sync_users()
#     sync_teams()
#
# @manager.command
# def list_routes():
#     import urllib
#     output = []
#     for rule in app.url_map.iter_rules():
#
#         options = {}
#         for arg in rule.arguments:
#             options[arg] = "[{0}]".format(arg)
#
#         methods = ','.join(rule.methods)
#         url = url_for(rule.endpoint, **options)
#         line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
#         output.append(line)
#
#     for line in sorted(output):
#         print line
#
# if __name__ == "__main__":
#     manager.run()
