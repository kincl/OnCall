# These are defaults, set yours somewhere else
class Defaults(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ROLES = ['Primary','Secondary']
    ONCALL_START = 1