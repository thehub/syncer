import itertools
import ldap
import ldap.schema
import bases, utils

uri = "ldap://localhost"
globaluserdn = "uid=%s,ou=users,o=the-hub.net"
localuserdn  = "uid=%s,ou=users,hubId=1,ou=hubs,o=the-hub.net"

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
hub_ocs = [oc for oc in all_ocs if isHubOC(oc)]
hubocnames_and_attrs = dict([(oc.names[0], tuple(getAttrs(oc, []))) for oc in hub_ocs])
aux_attrs_and_ocnames = dict([(hubocnames_and_attrs[oc.names[0]], oc.names[0]) for oc in hub_ocs if oc.kind == 2])
oc_entries = dict([(oc.names[0], (oc.names + oc.sup)) for oc in hub_ocs])

conn.unbind_s()
del all_ocs, conn

def removeExtraAttrs(strct_oc, udata):
    valid_aux_ocs = findValidOCs(strct_oc)
    all_attrs = strct_oc.attrs + valid_aux_ocs.attrs
    record = all_attrs.intersection(udata)
    record = addObjectClasses(record)
    return record

class LDAPWriter(bases.SubscriberBase):

    def getConn(self):
        return sessions.current['ldapconn']

    conn = property(getConn)
        
    def onSignon(self, u, p, cookies):
        conn = ldap.ldapobject.ReconnectLDAPObject(uri)
        conn.simple_bind_s(globaluserdn % u, p)
        sessions.current['ldapconn'] = conn
        return True
    onSignon.block = True

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
        # Add global user ref. to appropriate roles.level
        for (k,v) in udata:
            if k is 'groups':
                self.conn.modify_s(globaluserdn % username, [(ldap.MOD_ADD, k, v)])
                break
        return True
    onUserAdd.block = True

    def onUserDel(self, username, udata):
        #self.conn.delete....
        pass
    onUserDel.block = True

    def onUserMod(self, username, udata):
        logger.debug("Modifying %s: %s" % (username, [k[0] for k in udata]))
        dn = globaluserdn % username
        conn = sessions.current['ldapconn']
        for (k,v) in udata:
            mod_list = [(ldap.MOD_DELETE, k, None), (ldap.MOD_ADD, k, v)]
            try:
                conn.modify_s(dn, mod_list)
            except ldap.NO_SUCH_ATTRIBUTE, err:
                conn.modify_s(dn, mod_list[-1:])
        return True
    onUserMod.block = True
