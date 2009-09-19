# TODO
# mailAlso conversions might swap mail2 / mail3 values
# unicode conversions when ldap -> app

import datetime
import binascii
import base64

username2globaluserdn = lambda user_name: "uid=%s,ou=users,o=the-hub.net" % user_name
globaluserdn2username = lambda dn: dn.split(',')[0].split('=')[1]
hubdn = "hubId=%(hubId)s,ou=hubs,o=the-hub.net"
policydn = "policyId=%(policyId)s,ou=policies," + hubdn
# Posix uid and gid numbers for normal users start with offset 10000 while
# those of special/system users start with offset 9000
posix_uid_offset = 10000
posix_gid_offset = 10000

class AttributeMapper(list):
    def __init__(self, *args):
        super(self.__class__, self).__init__(args)
        app_map = dict ()
        ldap_map = dict ()
        for attr_map in self:
            for app_attr in attr_map.app_attrs:
                app_map[app_attr] = attr_map
            for ldap_attr in attr_map.ldap_attrs:
                ldap_map[ldap_attr] = attr_map
        self.app_map = app_map
        self.ldap_map = ldap_map
        self.all_app_attrs = app_map.keys()
        self.all_ldap_attrs = ldap_map.keys()
    def toApp(self, o, in_attrs):
        attr_maps = []
        for attr in in_attrs:
            if attr in self.all_ldap_attrs:
                attr_maps.append(self.ldap_map[attr])
        attr_maps = tuple(set(attr_maps))
        out_attrs = dict ()
        for attr_map in attr_maps:
            attr_map._toApp(o, in_attrs, out_attrs)
        return out_attrs
    def toLDAP(self, o, in_attrs={}):
        attr_maps = []
        if not in_attrs and o:
            in_attrs = dict([(attr, getattr(o, attr)) for attr in self.all_app_attrs if hasattr(o, attr)])
        for attr in in_attrs:
            if attr in self.all_app_attrs:
                attr_maps.append(self.app_map[attr])
        attr_maps = tuple(set(attr_maps))
        out_attrs = dict ()
        for attr_map in attr_maps:
            attr_map._toLDAP(o, in_attrs, out_attrs)
        return list(out_attrs.items())

class AttributeMapping(object):
    def __init__(self, ldap_attrs, app_attrs=None):
        self.ldap_attrs= isinstance(ldap_attrs, tuple) and ldap_attrs or (ldap_attrs,)
        if app_attrs:
            self.app_attrs = isinstance(app_attrs, tuple) and app_attrs or (app_attrs,)
        else:
            self.app_attrs = self.ldap_attrs
    def _toLDAP(self, o, in_attrs, out_attrs):
        raise NotImplemented
    def _toApp(self, o, in_attrs, out_attrs):
        raise NotImplemented

class SimpleMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        v = in_attrs.get(self.app_attrs[0], None)
        if v is None and o:
            v = getattr(o, self.app_attrs[0])
        out_attrs[self.ldap_attrs[0]] = v
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = in_attrs[self.ldap_attrs[0]]

class posixUidNumberMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs['hubUserId'] = in_attrs[self.app_attrs[0]]
        out_attrs['uidNumber'] = out_attrs['sambaSID'] = posix_uid_offset + in_attrs[self.app_attrs[0]]

class posixGidNumberMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs[self.ldap_attrs[0]] = in_attrs[self.app_attrs[0]]
        out_attrs['gidNumber'] = posix_gid_offset + in_attrs[self.app_attrs[0]]

class Many2OneMapping(AttributeMapping):
    def _toApp(self, o, in_attrs, out_attrs):
        vtuples = zip(self.app_attrs, in_attrs[self.ldap_attrs[0]])
        out_attrs.update(vtuples)
    def _toLDAP(self, o, in_attrs, out_attrs):
        vlist = [v for (k,v) in in_attrs.items() if k in self.app_attrs and v]
        out_attrs[self.ldap_attrs[0]] = vlist

class HubId2dnMapping(AttributeMapping):
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = globaluserdn2username(in_attrs[self.ldap_attrs[0]])
    def _toLDAP(self, o, in_attrs, out_attrs):
        loc_attr = self.app_attrs[0]
        hubId = in_attrs.get(loc_attr, None) or getattr(o, loc_attr, None) and getattr(o, loc_attr).id
        if hubId:
            out_attrs[self.ldap_attrs[0]] = hubdn % locals()

class OtherHubsMapping(AttributeMapping):
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = [hub_dn.split(',')[0].split('=')[1] for hub_dn in in_attrs[self.ldap_attrs[0]]]
    def _toLDAP(self, o, in_attrs, out_attrs):
        tmpl = 'uid=%(user_name)s,ou=users,hubId=%(hub_id)s,ou=hubs,o=the-hub.net'
        out_attrs['homeHub'] = [tmpl % dict (user_name = in_attrs['user_name'], hub_id = hub_id) for hub_id in in_attrs['groups']]

class NameMapping(AttributeMapping):
    def _toApp(self, o, in_attrs, out_attrs):
        if 'cn' in in_attrs:
            out_attrs['first_name'], out_attrs['last_name'] = in_attrs['cn'].split()
        else:
            if 'gn' in in_attrs:
                out_attrs['first_name'] = in_attrs['gn']
            if 'sn' in in_attrs:
                out_attrs['last_name'] = in_attrs['sn']
    def _toLDAP(self, o, in_attrs, out_attrs):
        first_name = in_attrs.get('first_name', None) or getattr(o, 'first_name')
        last_name = in_attrs.get('last_name', None) or getattr(o, 'last_name')
        if 'first_name' in in_attrs:
            out_attrs['gn'] = in_attrs['first_name']
        if 'last_name' in in_attrs:
            out_attrs['sn'] = in_attrs['last_name']
        out_attrs['cn'] = "%(first_name)s %(last_name)s" % locals()

class TariffMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        tariffdn = "tariffId=%(tariff_id)s,ou=tariffs," + hubdn
        out_attrs[self.ldap_attrs[0]] = tariffdn % in_attrs


class RoleMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        level = getattr(o, self.app_attrs[0])
        out_attrs['cn'] = "%s Role" % level.capitalize()
        out_attrs['level'] = level
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs['level'] = in_attrs['level']

class UidMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        user_name = in_attrs.get(self.app_attrs[0]) or (o and getattr(o, self.app_attrs[0]))
        out_attrs['uid'] = user_name
        out_attrs['hubUserReference'] = username2globaluserdn(user_name)
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = in_attrs['uid']

class PasswordMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        hexed_pass = (o and getattr(o, self.app_attrs[0])) or in_attrs[self.app_attrs[0]]
        out_attrs['userPassword'] = "{MD5}%s" % base64.b64encode(binascii.unhexlify(hexed_pass))
        out_attrs['sambaLMPassword'] = o.lanman_hash
        out_attrs['sambaNTPassword'] = o.nt_hash
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = binascii.hexlify(base64.b64decode(in_attrs['userPassword'][4:]))

class UserGroupMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs[self.ldap_attrs[0]] = [username2globaluserdn(o.user.user_name)]
        if isinstance(self.ldap_attrs, (tuple, list)) and len(self.ldap_attrs) > 1:
            out_attrs[self.ldap_attrs[1]] = [o.user.user_name]
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = globaluserdn2username(self.ldap_attrs[0]) # TODO this should be user object

class GroupDiplayName(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs[self.ldap_attrs[0]] = o.group.group_name
    def _toApp(self, o, in_attrs, out_attrs):
        raise NotImplemented

class GroupCreatedDate(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs[self.ldap_attrs[0]] = o.group.created
    def _toApp(self, o, in_attrs, out_attrs):
        raise NotImplemented

class AccessPoliciesMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        import hubspace.model # ugly
        AccessPolicy = hubspace.model.AccessPolicy
        access_policies = getattr(o, self.app_attrs[0])
        out_attrs[self.ldap_attrs[0]] = [policydn % dict(policyId=p, hubId=AccessPolicy.get(p).locationID) for p in access_policies]
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = globaluserdn2username(self.ldap_attrs[0])

class PolicyMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        policy = getattr(o, self.app_attrs[0])
        out_attrs[self.ldap_attrs[0]] = policydn % dict(policyId=policy.id, hubId=policy.locationID)
    def _toApp(self, o, in_attrs, out_attrs):
        raise NotImplemented

class PolicyResourceMapping(AttributeMapping):
    def _toLDAP(self, o, in_attrs, out_attrs):
        out_attrs[self.ldap_attrs[0]] = o.policy_resource.id
    def _toApp(self, o, in_attrs, out_attrs):
        out_attrs[self.app_attrs[0]] = globaluserdn2username(self.ldap_attrs[0])

def ldapSafe(x):
    if isinstance(x, unicode):
        x = x.encode('utf-8') # http://www.mail-archive.com/python-ldap-dev@lists.sourceforge.net/msg00040.html
    elif isinstance(x, (bool, int, long)):
        x = str(int(x))
    elif x == None:
        x = ''
    elif isinstance(x, (datetime.date, datetime.time)):
        try:
            x = x.strftime("%Y%m%d%H%M%S") + '+0000'
        except ValueError:
            if isinstance(x, datetime.date):
                x = "%s%s%s000000+0000" % (str(x.year).zfill(4), str(x.month).zfill(2), str(x.day).zfill(2))
            elif isinstance(x, datetime.time):
                x = "00000000%s%s%s+0000" % (str(x.hour).zfill(2), str(x.minute).zfill(2), str(x.second).zfill(2))
            else:
                raise
    elif isinstance(x, (list, tuple)):
        x = [ldapSafe(i) for i in x if i]
    return x

def makeArgLDAPFriendly(o):
    if isinstance(o, (list, tuple)):
        out = []
        for (k, v) in o:
            iterable = hasattr(v, '__iter__')
            if not iterable: v = [v]
            v_friendly = []
            for x in v:
                x = ldapSafe(x)
                v_friendly.append(x)
            if not iterable:
                v_friendly = v_friendly[0]
            if v_friendly:
                out.append((ldapSafe(k), v_friendly))
        return out
    return ldapSafe(o)

def ldapfriendly(f):
    def safeFn(*args, **kw):
        args = [makeArgLDAPFriendly(arg) for arg in args]
        return f(*args, **kw)
    return safeFn

object_maps = dict (
    user = AttributeMapper (
        UidMapping(('uid', 'hubUserReference'), 'user_name'),
        SimpleMapping('mail', 'email_address'),
        SimpleMapping('active'),
        SimpleMapping('displayName', 'display_name'),
        NameMapping(('gn', 'cn', 'sn'), ('first_name', 'last_name')),
        SimpleMapping('title'),
        SimpleMapping('organisation'),
        SimpleMapping('mobile'),
        SimpleMapping('telephoneNumber', 'work'),
        SimpleMapping('homeTelephoneNumber', 'home'),
        SimpleMapping('facsimileTelephoneNumber', 'fax'),
        SimpleMapping('dateCreated', 'created'),
        PasswordMapping('userPassword', ('password', 'unix_hash', 'lanman_hash', 'nt_hash')),
        Many2OneMapping('mailAlso', ('email2', 'email3')),
        SimpleMapping('postalAddress', 'address'),
        SimpleMapping('skypeId', 'skype_id'),
        SimpleMapping('hubIdentitySIPURI', 'sip_id'),
        posixUidNumberMapping(('hubUserId', 'uidNumber'), 'id'),
        SimpleMapping('labeledURI', 'website'),
        HubId2dnMapping('homeHub', 'homeplaceID'),
        AccessPoliciesMapping('policyReference', 'access_policies'),
        SimpleMapping('extensionTelephoneNumber', 'ext'),
        SimpleMapping('quotaStorage', 'gb_storage'),
        SimpleMapping('operatingSystem', 'os'),
        SimpleMapping('storageLocation','storage_loc'),
        SimpleMapping('homeDirectory','storage_loc'),
        SimpleMapping('description'),
        SimpleMapping('billingId', 'billto_id'),
        SimpleMapping('billingProfile', 'bill_to_profile'),
        SimpleMapping('billingCompany', 'bill_to_company'),
        SimpleMapping('billingAddress', 'billingaddress'),
        SimpleMapping('billingTelephoneNumber', 'bill_phone'),
        SimpleMapping('billingFacsimileNumber', 'bill_fax'),
        SimpleMapping('billingMail', 'bill_email'),
        SimpleMapping('bill_company_no', 'billingCompanyNumber'),
        SimpleMapping('billingVATID', 'bill_vat_no'),
        SimpleMapping('billingOutstanding', 'outstanding'),
        SimpleMapping('billingReminderCounter','reminder_counter'),
        SimpleMapping('last_reminder', 'billingLastReminder'),
        SimpleMapping('billingReminderKey', 'reminderkey'),
        SimpleMapping('hubImageMimetype', 'image_mimetype'),
        SimpleMapping('hubWelcomeSent', 'welcome_sent'),
        SimpleMapping('hubSignedUpBy', 'signedby_id'),
        SimpleMapping('hubHostContact', 'hostcontact_id'),
        SimpleMapping('publicViewable', 'public_field'),
        SimpleMapping('postalCode', 'postcode'),
        SimpleMapping('businessCategory', 'biz_type'),
        TariffMapping('tariffReference', 'tariff_id'),
        ),
    hub = AttributeMapper (
        SimpleMapping('hubId', 'id'),
        SimpleMapping('ou', 'name'),
        SimpleMapping('active'),
        SimpleMapping('currency', 'currency'),
        SimpleMapping('billingAddress', 'billing_address'),
        SimpleMapping('openingTime', 'opens'),
        SimpleMapping('closingTime', 'closes'),
        SimpleMapping('timezone'),
        SimpleMapping('billingCompanyNumber', 'company_no'),
        SimpleMapping('labeledURI', 'url'),
        SimpleMapping('billingVATID', 'vat_no'),
        SimpleMapping('telephoneNumber', 'telephone'),
        SimpleMapping('bankAccountNumber', 'account_no'),
        SimpleMapping('bankName', 'bank'),
        SimpleMapping('bankSortCode', 'sort_code'),
        SimpleMapping('bankIBAN', 'iban_no'),
        SimpleMapping('bankSwiftCode', 'swift_no'),
        SimpleMapping('billingPaymentTerms', 'payment_terms'),
        SimpleMapping('hubImageMimetype', 'logo_mimetype'),
        ),
    role = AttributeMapper (
        RoleMapping(('cn', 'level'), 'level'),
        posixGidNumberMapping(('roleId', 'gidNumber'), 'id'),
        UserGroupMapping('member', 'user')
        ),
    group = AttributeMapper (
        GroupDiplayName('displayName', 'id'),
        GroupCreatedDate('dateCreated', 'id'),
        posixGidNumberMapping(('hubGroupId', 'gidNumber'), 'id'),
        UserGroupMapping(('member', 'memberUid'), 'user'),
        ),

    policy = AttributeMapper (
        HubId2dnMapping('policyLocation', 'locationID'),
        SimpleMapping('policyPrecedence', 'precedence'),
        SimpleMapping('policyStartDate', 'policyStartDate'),
        SimpleMapping('policyEndDate', 'policyEndDate'),
        SimpleMapping('policyId', 'id'),
        PolicyResourceMapping('policyResource', 'policy_resource'),
        ),
    opentimes = AttributeMapper (
        SimpleMapping('openTimeId', 'id'),
        SimpleMapping('openTimeStartDate'),
        SimpleMapping('openTimeDay'),
        SimpleMapping('openTimeStart'),
        SimpleMapping('openTimeEnd'),
        SimpleMapping('openTimeDate'),
        PolicyMapping('policyReference', 'policy'),
        ),
    tariff = AttributeMapper (
        SimpleMapping('tariffId', 'id'),
        )
    )

if __name__ == '__main__':

    class NameRelated(AttributeMapping):
        def _toLDAP(self, o, in_attrs, out_attrs):
            out_attrs['cn'] = "%(fn)s %(ln)s" % in_attrs
        def _toApp(self, o, in_attrs, out_attrs):
            out_attrs['fn'], out_attrs['ln'] = in_attrs['cn'].split()
    
    class NickRelated(SimpleMapping):
        def _toLDAP(self, o, in_attrs, out_attrs):
            out_attrs['pet'] = in_attrs['nick']
        def _toApp(self, o, in_attrs, out_attrs):
            nick = in_attrs.get('altname', in_attrs.get('nick', None))
            if nick:
                out_attrs['nick'] = nick
    
    mapper = AttributeMapper (
         NameRelated("cn", ("fn", "ln")),
         NickRelated("pet", "nick")
         )
    print mapper.toLDAP(None, dict(fn = "Shekhar", ln = "Tiwatne"))
    print mapper.toLDAP(None, dict(fn = "Shekhar", ln = "Tiwatne", nick = "Shon"))
    print mapper.toApp (None, dict(cn = "Shekhar Tiwatne", pet = "Shon", altname = "Shon"))

    class location:
        id = 1
    mapper = object_maps['user']
    in_attrs = {
 'active': 0,
 'address': '',
 'billto': None,
 'description': '',
 'display_name': u'Myfn Lnmine',
 'email2': u'mail2@mycomp.org',
 'email3': u'mail3@mycomp.org',
 'email_address': u'mail@mycomp.org',
 'ext': None,
 'fax': None,
 'first_name': u'Myfn',
 'frank_pin': None,
 'gb_storage': u'100',
 'handset': None,
 'home': None,
 'homeplace': location,
 'last_name': u'Lnmine',
 'mobile': u'+91 112233',
 'organisation': '',
 'os': u'my_computer_type',
 'password': u'71ad1dbaca01b78687d6fe620349091e',
 'sip_id': None,
 'skype_id': '',
 'storage_loc': '',
 'title': u'Mr.',
 'user_name': u'usertest',
 'website': None,
 'work': None}
    print in_attrs
    ldap_list = mapper.toLDAP(None, in_attrs)
    print ldap_list
    print mapper.toApp(None, dict(ldap_list))
