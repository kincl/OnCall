# import class and constants
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL

from flask import current_app

# so we can monkey patch for
def get_conn():
    # define the server and the connection
    s = Server('localhost', port = 389, get_info = ALL)  # define an unsecure LDAP server, requesting info on DSE and schema
    c = Connection(s, auto_bind = False, client_strategy = SYNC, check_names=True)
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
    # response = c.response
    # result = c.result
    # for r in response:
    #     print(r['dn'], r['attributes']) # return unicode attributes
    #     #print(r['dn'], r['raw_attributes']) # return raw (bytes) attributes
    # print(result)
    r = c.response
    c.unbind()
    return r
