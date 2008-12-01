import itertools
import datetime
import ldap
import ldap.schema
import bases, utils, transactions
from helpers.ldap import ldapfriendly, ldapSafe

uri = "ldap://localhost"
basedn = "o=the-hub.net"
globaluserdn = "uid=%s,ou=users," + basedn
localuserdn  = "uid=%s,ou=users,hubId=%s,ou=hubs,o=the-hub.net"
hubdn = "hubId=%(hubId)s,ou=hubs," + basedn
leveldn = "level=%(level)s,ou=roles," + hubdn
accesspolicydn = "policyId=%(policyId)s,ou=policies," + hubdn
opentimedn = "openTimeId=%(openTimeId)s," + accesspolicydn

conn = ldap.ldapobject.ReconnectLDAPObject(uri)
conn.simple_bind_s()
subentrydn = conn.search_subschemasubentry_s()
entry = conn.read_subschemasubentry_s(subentrydn)
schema = ldap.schema.SubSchema(entry)

def getAttrs(oc, attrs):
    """
    recursive. returns all attributes for a objectClass object down the hierarchy
    """
    attrs.extend(oc.may + oc.must)
    for oc_name in oc.sup:
        sup_oc = schema.get_obj(ldap.schema.ObjectClass, oc_name)
        getAttrs(sup_oc, attrs)
    return attrs

def addAttrs(*ocnames):
    return tuple(itertools.chain(*[hubocnames_and_attrs[name] for name in ocnames]))

isHubOC = lambda oc: oc.names[0].startswith('hub')
all_ocs = [schema.get_obj(ldap.schema.ObjectClass, oid) for oid in schema.listall(ldap.schema.ObjectClass)]
all_attrs = [schema.get_obj(ldap.schema.AttributeType, oid) for oid in schema.listall(ldap.schema.AttributeType)]
multivalue_attrs = tuple (itertools.chain(*[x.names for x in all_attrs if not x.single_value]))

hub_ocs = [oc for oc in all_ocs if isHubOC(oc)]
hubocnames_and_attrs = dict([(oc.names[0], tuple(getAttrs(oc, []))) for oc in hub_ocs])
#aux_attrs_and_ocnames = dict([(hubocnames_and_attrs[oc.names[0]], oc.names[0]) for oc in hub_ocs if oc.kind == 2])
oc_entries = dict([(oc.names[0], (oc.names + oc.sup)) for oc in hub_ocs])

conn.unbind_s()
del all_ocs, conn, isHubOC, schema, all_attrs

def getLocalUserDNFromUid(conn, uid):
    attrs_d = conn.search_s(basedn, ldap.SCOPE_ONELEVEL, '(%s)' % rdn, ['*'])[0][1]
    return "uid=%s,ou=users,%s" % (uid, attrs_d['homeHub'])

# LDAP Proxy
MOD_ADD, MOD_DELETE, MOD_REPLACE = ldap.MOD_ADD, ldap.MOD_DELETE, ldap.MOD_REPLACE
subscriber_name = "ldapwriter"

class Proxy(object):
    def __init__(self, u, p):
        """
        """
        conn = ldap.ldapobject.ReconnectLDAPObject(uri)
        conn.simple_bind_s(u, p)
        self._conn = conn

    def add_s(self, *args, **kw):
        """
        """
        result = self._conn.add_s(*args, **kw)
        dn, mod_list = args
        rdn, basedn = dn.split(',', 1)
        attrs = list(self._conn.search_s(basedn, ldap.SCOPE_ONELEVEL, '(%s)' % rdn, ['*'])[0][1].items())
        data = ("delete_s", dn, attrs)
        rbdata = transactions.RollbackData(subscriber_name=subscriber_name, data=data, transaction=currentTransaction())
        return result

    def modify_s(self, *args, **kw):
        dn, mod_list = args
        sorter = lambda x: x[1]
        mod_list.sort(key=sorter)
        grouped = itertools.groupby(mod_list, sorter)
        byattrs = dict([(grp[0], list(grp[1])) for  grp in grouped])
        rdn, basedn = dn.split(',', 1)
        
        # 1. Backup old entry if reqd
        if MOD_DELETE in [op[0] for op in mod_list]:
            old_values = self._conn.search_s(basedn, ldap.SCOPE_ONELEVEL, '(%s)' % rdn, ['*'])
            old_values = old_values[0][1]
        # 2. Now actual LDAP operation. If we fail here we don't need rollback data
        result = self._conn.modify_s(*args, **kw)
        # 3. Generate ready to use mod_list based on flags and old/new values
        data = ["modify_s", dn]
        mod_list = []
        for attr, actions in byattrs.items():
            flags = [action[0] for action in actions]
            if MOD_ADD in flags:
                mod_list.append((MOD_DELETE, action[1], action[2]))
            if MOD_DELETE in flags:
                mod_list.append((MOD_ADD, action[1], old_values[attr]))
        data.append(mod_list)
        # 4. save and hope that we will never need it
        rbdata = transactions.RollbackData(subscriber_name=subscriber_name, data=data, transaction=currentTransaction())
        return result

    def delete_s(self, *args, **kw):
        """
        """
        result = self._conn.delete_s(*args, **kw)
        dn, mod_list = args
        rdn, basedn = dn.split(',', 1)
        attrs = list(self._conn.search_s(basedn, ldap.SCOPE_ONELEVEL, '(%s)' % rdn, ['*'])[0][1].items())
        data = ("add_s", dn, attrs)
        rbdata = transactions.RollbackData(subscriber_name=subscriber_name, data=data, transaction=currentTransaction())
        return result

# LDAP Events
def rollback(rbdata):
    conn = currentSession()['ldapconn']
    action, dn, modlist = rbdata.data
    f = getattr(conn._conn, action)
    logger.debug("LDAP Rollback: %s %s" % (dn, action))
    try:
        f(dn, modlist)
    except Exception, err:
        msg = "LDAP Rollback: %s %s" % (dn, action)
        logger.error(msg)
        raise


class LDAPWriter(bases.SubscriberBase):

    def getConn(self):
        return currentSession()['ldapconn']

    conn = property(getConn)
        
    def onSignon(self, u, p, cookies):
        u, p = ldapSafe((u, p))
        if u == "ldapadmin":
            dn = "uid=%s,o=the-hub.net" % u
        else:
            dn = globaluserdn % u
        conn = Proxy(dn, p)
        currentSession()['ldapconn'] = conn
        return True
    onSignon.block = True

    @ldapfriendly
    def onUserAdd(self, username, udata):
        # Don't modify `udata` as we may call this method again on failure
        # Add hubGlobalUser record
        user_ocnames = ('hubGlobalUser', 'hubSIP')
        user_all_attrs = addAttrs(*user_ocnames)
        add_record = [('objectClass', tuple(itertools.chain(*[oc_entries[name] for name in user_ocnames])))] + \
                     [(k,v) for (k,v) in udata if k in user_all_attrs]
        self.conn.add_s(globaluserdn % username, add_record)
        # Add hubLocalUser record
        user_ocnames = ('hubLocalUser',)
        user_all_attrs = addAttrs(*user_ocnames)
        if 'homeHub' in udata:
            user_attrs = set(user_all_attrs).intersection(udata.keys())
            if user_attrs:
                localuserdn = "uid=%s,ou=users,%s" % (uid, udata['homeHub'])
                add_record = [('objectClass', tuple(itertools.chain(*[oc_entries[name] for name in user_ocnames])))] + \
                             [(k,v) for (k,v) in udata if k in user_all_attrs]
                self.conn.add_s(localuserdn % (username, hubId), add_record)
        return True
    onUserAdd.block = True
    onUserAdd.rollback = rollback

    @ldapfriendly
    def onUserMod(self, username, udata):
        logger.debug("Modifying %s: %s" % (username, [k[0] for k in udata]))
        user_ocnames = ('hubGlobalUser', 'hubSIP')
        globaluser_all_attrs = addAttrs(*user_ocnames)
        user_ocnames = ('hubLocalUser',)
        localuser_all_attrs = addAttrs(*user_ocnames)
        globaldn = globaluserdn % username
        conn = self.conn
        udata = dict(udata)
        globaluser_attrs = set(globaluser_all_attrs).intersection(udata.keys())
        if globaluser_attrs:
            for k in globaluser_attrs:
                v = udata[k]
                mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
                try:
                    conn.modify_s(globaldn, mod_list)
                except ldap.NO_SUCH_ATTRIBUTE, err:
                    conn.modify_s(globaldn, mod_list[-1:])
        localuser_attrs = set(localuser_all_attrs).intersection(udata.keys())
        if localuser_attrs:
            localdn = getLocalUserDNFromUid(conn, username)
            for k in localuser_attrs:
                v = udata[k]
                mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
                try:
                    conn.modify_s(localdn, mod_list)
                except ldap.NO_SUCH_ATTRIBUTE, err:
                    conn.modify_s(localdn, mod_list[-1:])
        return True
    onUserMod.block = True
    onUserMod.rollback = rollback

    @ldapfriendly
    def onUserDel(self, username):
        #self.conn.delete....
        raise NotImplemented
    onUserDel.block = True
    onUserDel.rollback = rollback

    @ldapfriendly
    def onAssignRoles(self, username, hubId, level):
        """
        When user is assigned new roles
        All previous roles would replaced with new set of roles.
        """
        userdn = globaluserdn % username
        conn = self.conn
        dn = leveldn % locals()
        # Add new roles
        try:
            conn.modify_s(dn, [(ldap.MOD_ADD, "member", userdn)])
        except ldap.TYPE_OR_VALUE_EXISTS, err:
            pass
        # Add role references as globaluser's hubMemberOf attribute
        try:
            conn.modify_s(userdn, [(ldap.MOD_ADD, "hubMemberOf", hubId)])
        except ldap.TYPE_OR_VALUE_EXISTS, err:
            pass
    onAssignRoles.block = True
    onAssignRoles.rollback = rollback

    @ldapfriendly
    def onRevokeRoles(self, username, groupdata):
        raise NotImplemented
    onRevokeRoles.block = True
    onRevokeRoles.rollback = rollback

    @ldapfriendly
    def onHubAdd(self, hubId, hubdata):
        dn = hubdn % locals()
        ocnames = ('hub',)
        all_attrs = addAttrs(*ocnames)
        add_record = [('objectClass', tuple(itertools.chain(*[oc_entries[name] for name in ocnames])))] + \
                     [(k,v) for (k,v) in hubdata if k in all_attrs]
        self.conn.add_s(dn, add_record)
        hub_ous = ['users', 'groups', 'tariffs', 'roles', 'policies']
        oudn = "ou=%s,hubId=%s,ou=hubs,o=the-hub.net"
        for ou in hub_ous:
            dn = oudn % (ou, hubId)
            add_record = [ ('objectClass', 'organizationalUnit'),
                           ('description', "Top level entry for the subtree of this hub's %s" % ou),
                           ('ou', ou) ]
            self.conn.add_s(dn, add_record)
        return True
    onHubAdd.block = True
    onHubAdd.rollback = rollback

    @ldapfriendly
    def onHubMod(self, hubId, hubdata):
        dn = hubdn % locals()
        conn = self.conn
        for (k,v) in hubdata:
            mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
            try:
                conn.modify_s(dn, mod_list)
            except ldap.NO_SUCH_ATTRIBUTE, err:
                conn.modify_s(dn, mod_list[-1:])
        return True
    onHubMod.block = True
    onHubMod.rollback = rollback

    @ldapfriendly
    def onRoleAdd(self, hubId, level, data):
        """
        When a new role is added for a hub, same as new group in HubSpace
        """
        dn = leveldn % locals()
        add_record = [ ('objectClass', 'hubLocalRole'),] + [(k,v) for (k,v) in data]
        self.conn.add_s(dn, add_record)
        return True
    onRoleAdd.block = True
    onRoleAdd.rollback = rollback

    @ldapfriendly
    def onAccesspolicyAdd(self, hubId, mod_list):
        policyId = dict(mod_list)['policyId']
        dn = accesspolicydn % locals()
        add_record = [('objectClass', 'hubLocalPolicy')] + mod_list
        ret = self.conn.add_s(dn, add_record)
    onAccesspolicyAdd.block = True
    onAccesspolicyAdd.rollback = rollback

    @ldapfriendly
    def onAccesspolicyMod(self, policyId, hubId, mod_list):
        dn = accesspolicydn % locals()
        conn.modify_s(dn, mod_list)
    onAccesspolicyMod.block = True
    onAccesspolicyMod.rollback = rollback
    
    @ldapfriendly
    def onOpentimesAdd(self, policyId, hubId, mod_list):
        openTimeId = dict(mod_list)['openTimeId']
        dn = opentimedn % locals()
        add_record = [('objectClass', 'hubLocalOpenTime')] + mod_list
        self.conn.add_s(dn, add_record)
    onOpentimesAdd.block = True
    onOpentimesAdd.rollback = rollback

    @ldapfriendly
    def onOpentimesMod(self, openTimeId, policyId, hubId, mod_list):
        dn = opentimedn % locals()
        conn.modify_s(dn, mod_list)
    onOpentimesMod.block = True
    onOpentimesMod.rollback = rollback
