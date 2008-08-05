import ldap
import bases, utils

uri = "ldap://localhost"
userdn = "uid=%s,ou=users,o=the-hub.net"

class LDAPWriter(bases.SubscriberBase):

    def getConn(self):
        return utils.getContext().session['ldapconn']

    conn = property(getConn)
        
    def onSignon(self, u, p, cookies):
        conn = ldap.ldapobject.ReconnectLDAPObject(uri)
        conn.simple_bind_s(userdn % u, p)
        sessions.current['ldapconn'] = conn
        return True
    onSignon.block = True

    def onUserAdd(self, username, udata):
        add_record = [
         ('objectclass', ['organizationalperson','inetorgperson']),
         ('uid', [username]),
         ('cn', [username] ),
         ('sn', [udata['sn']] ),
         ('userpassword', udata['userpassword']),
         ('ou', ['people'])
        ] # TODO: schema dependent
        self.conn.add_s(self.userdn % username, add_record)
        return True
    onUserAdd.block = True

    def onUserDel(self, username, udata):
        #self.conn.delete....
        pass
    onUserDel.block = True

    def onUserMod(self, username, udata):
        logger.debug("Modifying %s: %s" % (username, [k[0] for k in udata]))
        dn = userdn % username
        conn = sessions.current['ldapconn']
        mod_list = [(ldap.MOD_REPLACE, k, v) for (k,v) in udata]
        for (k, v) in udata: # TODO do it in single request
            if isinstance(v, unicode):
                v = v.encode('utf-8') # http://www.mail-archive.com/python-ldap-dev@lists.sourceforge.net/msg00040.html
            elif isinstance(v, bool):
                v = str(int(v))
            else:
                v = str(v)
            conn.modify_s(dn, [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, [v])])
        return True
    onUserMod.block = True
