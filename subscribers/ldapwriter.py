import ldap
import bases, utils

class LDAPWriter(bases.SubscriberBase):

    userdn = 'uid=%s,ou=people,dc=the-hub,dc=net'

    def getConn(self):
        return utils.getContext().session['ldapconn']

    conn = property(getConn)
        
    def onSignon(self, u, p, cookies):
        return "dummy_conn"
        conn = ldap.ldapobject.ReconnectLDAPObject(uri)
        conn.simple_bind_s("cn=%s" & u, p)
        sid = utils.getContext().cred
        session = sessions[sid]
        session['ldapconn'] = conn
        return conn
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
        dn = userdn % username
        for (k, v) in udata.items(): # TODO can we do it in single request?
            self.conn.modify_s(dn, [( ldap.MOD_REPLACE, k, v )])
        return True
    onUserMod.block = True

