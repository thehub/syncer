import itertools
import datetime
import ldap
import ldap.schema
import bases, utils, transactions
from helpers.ldap import ldapfriendly, ldapSafe

uri = "ldap://localhost"
globaluserdn = "uid=%s,ou=users,o=the-hub.net"
localuserdn  = "uid=%s,ou=users,hubId=1,ou=hubs,o=the-hub.net"
hubdn = "hubId=%s,ou=hubs,o=the-hub.net"
leveldn = "level=%s,ou=roles,hubId=%s,ou=hubs,o=the-hub.net"

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

# LDAP Proxy
MOD_ADD, MOD_DELETE, MOD_REPLACE = ldap.MOD_ADD, ldap.MOD_DELETE, ldap.MOD_REPLACE
subscriber_name = "ldapwriter"

class RBMap:
    add_s = "delete_s"
    delete_s = "add_s"
    modify_s = "modify_s"
    MOD_ADD = MOD_DELETE
    MOD_DELETE = MOD_ADD
    MOD_REPLACE = MOD_REPLACE
    def __getitem__(self, k):
        return getattr(self, k)

rev_map = RBMap()

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
        result = ldap.add_s(*args, **kw)
        dn, mod_list = args
        rdn, basedn = dn.split(',', 1)
        rbdata = (rev_map.add_s, dn)
        currentTransaction().rollback_data.append(rbdata)
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
        data = [rev_map.modify_s, dn]
        mod_list = []
        for attr, actions in byattrs.items():
            flags = [action[0] for action in actions]
            if MOD_ADD in flags:
                mod_list.append((rev_map.MOD_ADD, action[1], action[2]))
            if MOD_DELETE in flags:
                mod_list.append((rev_map.MOD_DELETE, action[1], old_values[attr]))
        # 4. save and hope that we will never need it
        rbdata = transactions.RollbackData(subscriber_name=subscriber_name, data=data)
        currentTransaction().rollback_data.append(rbdata)
        return result

    def delete_s(self, *args, **kw):
        """
        """
        result = self._conn.delete_s(*args, **kw)
        dn, mod_list = args
        rdn, basedn = dn.split(',', 1)
        data = list(self._conn.search_s(basedn, ldap.SCOPE_ONELEVEL, '(%s)' % rdn, ['*'])[0][1].items())
        rbdata = (rev_map.delete_s, dn, data)
        currentTransaction().rollback_data.append(rbdata)
        return result

# LDAP Events
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

    def rollback(self, rbdata):
        print rbdata
        rb_errs = []
        for entry in rbdata:
            action, dn, modlist = entry
            f = getattr(self.conn._conn, action)
            logger.debug("LDAP Rollback: %s %s" % (dn, action))
            try:
                f(dn, modlist)
            except Exception, err:
                msg = "LDAP Rollback: %s %s" % (dn, action)
                logger.error(msg)
                rb_errs.append(msg)
        if rb_errs:
            raise Exception(rb_errs)

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
        add_record = [('objectClass', tuple(itertools.chain(*[oc_entries[name] for name in user_ocnames])))] + \
                     [(k,v) for (k,v) in udata if k in user_all_attrs]
        self.conn.add_s(localuserdn % username, add_record)
        return True
    onUserAdd.block = True

    @ldapfriendly
    def onUserMod(self, username, udata):
        logger.debug("Modifying %s: %s" % (username, [k[0] for k in udata]))
        user_ocnames = ('hubGlobalUser', 'hubSIP')
        globaluser_all_attrs = addAttrs(*user_ocnames)
        user_ocnames = ('hubLocalUser',)
        localuser_all_attrs = addAttrs(*user_ocnames)
        globaldn = globaluserdn % username
        localdn = localuserdn % username
        conn = self.conn
        for (k,v) in udata:
            if k in globaluser_all_attrs:
                mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
                try:
                    conn.modify_s(globaldn, mod_list)
                except ldap.NO_SUCH_ATTRIBUTE, err:
                    conn.modify_s(globaldn, mod_list[-1:])
            elif k in localuser_all_attrs:
                mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
                try:
                    conn.modify_s(localdn, mod_list)
                except ldap.NO_SUCH_ATTRIBUTE, err:
                    conn.modify_s(localdn, mod_list[-1:])
        return True
    onUserMod.block = True

    @ldapfriendly
    def onUserDel(self, username, udata):
        #self.conn.delete....
        raise NotImplemented
    onUserDel.block = True

    @ldapfriendly
    def onAssignRoles(self, username, hub_id, level):
        """
        When user is assigned new roles
        All previous roles would replaced with new set of roles.
        """
        print username, hub_id, level
        userdn = globaluserdn % username
        conn = self.conn
        dn = leveldn % (level, hub_id)
        # Add new roles
        try:
            conn.modify_s(dn, [(ldap.MOD_ADD, "member", userdn)])
        except ldap.TYPE_OR_VALUE_EXISTS, err:
            pass
        # Add role references as globaluser's hubMemberOf attribute
        try:
            conn.modify_s(userdn, [(ldap.MOD_ADD, "hubMemberOf", hub_id)])
        except ldap.TYPE_OR_VALUE_EXISTS, err:
            pass
    onAssignRoles.block = True

    @ldapfriendly
    def onRevokeRoles(self, username, groupdata):
        raise NotImplemented
    onRevokeRoles.block = True

    @ldapfriendly
    def onHubAdd(self, hubid, hubdata):
        dn = hubdn % hubid
        ocnames = ('hub',)
        all_attrs = addAttrs(*ocnames)
        add_record = [('objectClass', tuple(itertools.chain(*[oc_entries[name] for name in ocnames])))] + \
                     [(k,v) for (k,v) in hubdata if k in all_attrs]
        self.conn.add_s(dn, add_record)
        hub_ous = ['users', 'groups', 'tariffs', 'roles', 'policies']
        oudn = "ou=%s,hubId=%s,ou=hubs,o=the-hub.net"
        for ou in hub_ous:
            dn = oudn % (ou, hubid)
            add_record = [ ('objectClass', 'organizationalUnit'),
                           ('description', "Top level entry for the subtree of this hub's %s" % ou),
                           ('ou', ou) ]
            self.conn.add_s(dn, add_record)
        return True
    onHubAdd.block = True

    @ldapfriendly
    def onHubMod(self, hubid, hubdata):
        dn = hubdn % hubid
        conn = self.conn
        for (k,v) in hubdata:
            mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
            try:
                conn.modify_s(dn, mod_list)
            except ldap.NO_SUCH_ATTRIBUTE, err:
                conn.modify_s(dn, mod_list[-1:])
        return True
    onHubMod.block = True

    @ldapfriendly
    def onRoleAdd(self, hubid, level, data):
        """
        When a new role is added for a hub, same as new group in HubSpace
        """
        print data
        dn = leveldn % (level, hubid)
        add_record = [ ('objectClass', 'hubLocalRole'),] + [(k,v) for (k,v) in data]
        print dn, add_record
        self.conn.add_s(dn, add_record)
        return True
    onRoleAdd.block = True
