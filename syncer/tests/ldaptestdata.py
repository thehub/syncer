import decimal
import datetime

class TestData():
    """
    """

root_u = "ldapadmin"
root_p = "secret"

hub1 = TestData()
hub1.roles = ('superuser', 'director', 'member','host')
hub1.id = 1
hub1.data = [('telephoneNumber', u'0123 456 0000'),
                ('billingVATID', u'456 1111 11'),
                ('bankAccountNumber', u'11111177'),
                ('labeledURI', u'http://members.the-hub.net'),
                ('bankIBAN', u'ABCD CPBK 7777 7777 777777'),
                ('bankName', u'The Bank'),
                ('bankSwiftCode', u'CCCCCC22'),
                ('bankSortCode', u'999299'),
                ('currency', u'GBP'),
                ('hubId', hub1.id),
                ('billingAddress', u'5 Some Street, London'),
                ('billingCompanyNumber', u'5111115'),
                ('timezone', u'Europe/London'),
                ('ou', u'Islington'),
                ('hubImageMimetype', u'image/png'),
                ('billingPaymentTerms', u'15 days')]

hub1.host1 = TestData()
hub1.host1.uid = "hostfn"
hub1.host1.p = "secret"
hub1.host1.hubUserId = 2
hub1.host1.role = "host"
hub1.host1.location = hub1
hub1.host1.data = [('billingTelephoneNumber', None),
                ('cn', u'HostFN HostLN'),
                ('uid', hub1.host1.uid),
                ('publicViewable', None),
                ('operatingSystem', u'Linux'),
                ('gn', u'Host'),
                ('homeHub', 'hubId=%s,ou=hubs,o=the-hub.net' % hub1.id),
                ('hubMemberOf', hub1.id),
                ('quotaStorage', None),
                ('billingOutstanding', decimal.Decimal("0.00")),
                ('title', u'Mr'),
                ('facsimileTelephoneNumber', None),
                ('hubImageMimetype', u'image/png'),
                ('organisation', u'The Hub'),
                ('hubUserReference', u'uid=%s,ou=users,o=the-hub.net' % hub1.host1.uid),
                ('hubIdentitySIPURI', None),
                ('sambaLMPassword', u'7B5F83F76983185A7584248B8D2C9F9E'),
                ('mail', u'shekhar.tiwatne@the-hub.net'),
                ('postalAddress', u'London'),
                ('userPassword', '{MD5}Xr4ilOzQ4PCOq3aQ0qbuaQ=='),
                ('billingCompany', u''),
                ('extensionTelephoneNumber', None),
                ('homeTelephoneNumber', u'+91 20 12345'),
                ('description', u'I m a host'),
                ('storageLocation', None),
                ('dateCreated', datetime.datetime(2009, 1, 1, 18, 17, 20)),
                ('billingReminderCounter', 0),
                ('billingAddress', u'Tower Bridge'),
                ('active', 1),
                ('hubWelcomeSent', 1),
                ('sambaNTPassword', u'46EBAD5FF06F009D8E3A8B7995E38B9D'),
                ('skypeId', u'myskype'),
                ('telephoneNumber', u'None'),
                ('billingVATID', u''),
                ('hubUserId', hub1.host1.hubUserId),
                ('displayName', u'HostFN HostLN'),
                ('labeledURI', None),
                ('mobile', '+91 99222 55300'),
                ('billingProfile', 1),
                ('mailAlso', [u'shon@thisdoesnotexists.net']),
                ('billingFacsimileNumber', None),
                ('sn', u'HostLN'),
                ('billingMail', None),
                ('sambaSID', 10000 + hub1.host1.hubUserId),
                ('uidNumber', 10000 + hub1.host1.hubUserId),
                ('gidNumber', 10001),
                ('homeDirectory', '///filesrv/home/hostfn'),
                ('billingReminderKey', u'66cbf1d00bc76b9a34f82388f5c6b85f')]

hub1.user1 = TestData()
hub1.user1.uid = "shon"
hub1.user1.p = "secret"
hub1.user1.hubUserId = 3
hub1.user1.data = [('billingTelephoneNumber', None),
                ('cn', u'Shekhar Tiwatne'),
                ('uid', hub1.user1.uid),
                ('publicViewable', None),
                ('operatingSystem', u'Linux'),
                ('gn', u'Shekhar'),
                ('homeHub', 'hubId=%s,ou=hubs,o=the-hub.net' % hub1.id),
                ('hubMemberOf', hub1.id),
                ('quotaStorage', None),
                ('billingOutstanding', decimal.Decimal("0.00")),
                ('title', u'Mr'),
                ('facsimileTelephoneNumber', None),
                ('hubImageMimetype', u'image/png'),
                ('organisation', u'Open Coop'),
                ('hubUserReference', u'uid=shon,ou=users,o=the-hub.net'),
                ('hubIdentitySIPURI', None),
                ('sambaLMPassword', u'7B5F83F76983185A7584248B8D2C9F9E'),
                ('mail', u'shekhar.tiwatne@the-hub.net'),
                ('postalAddress', u'Pune'),
                ('userPassword', '{MD5}Xr4ilOzQ4PCOq3aQ0qbuaQ=='),
                ('billingCompany', u''),
                ('extensionTelephoneNumber', None),
                ('homeTelephoneNumber', u'+91 20 12345'),
                ('description', u'Just a programmer\n'),
                ('storageLocation', None),
                ('dateCreated', datetime.datetime(2009, 1, 1, 18, 17, 20)),
                ('billingReminderCounter', 0),
                ('billingAddress', u'Tower Bridge'),
                ('active', 1),
                ('hubWelcomeSent', 1),
                ('sambaNTPassword', u'46EBAD5FF06F009D8E3A8B7995E38B9D'),
                ('skypeId', u'shon___'),
                ('telephoneNumber', u'None'),
                ('billingVATID', u''),
                ('hubUserId', hub1.user1.hubUserId),
                ('displayName', u'Shekhar Tiwatne'),
                ('labeledURI', None),
                ('mobile', '+91 99222 55300'),
                ('billingProfile', 1),
                ('mailAlso', [u'shon@thisdoesnotexists.net']),
                ('billingFacsimileNumber', None),
                ('sn', u'Tiwatne'),
                ('billingMail', None),
                ('sambaSID', 10000 + hub1.user1.hubUserId),
                ('uidNumber', 10000 + hub1.user1.hubUserId),
                ('gidNumber', 10001),
                ('homeDirectory', '///filesrv/home/shon'),
                ('billingReminderKey', u'66cbf1d00bc76b9a34f82388f5c6b85f')]

hub1.user1.moddata = [('title', 'Mr.')]

superuser = TestData()
superuser.uid = "hubspace"
superuser.p = "secret"
superuser.data = [ ('uid', "hubspace"),
                ('gidNumber', 10002),
                ('sn', ['admin']),
                ('active', ['0']),
                ('userPassword', '{MD5}Xr4ilOzQ4PCOq3aQ0qbuaQ=='),
                ('cn', 'Hubspace Admin') ]


superusergrp = TestData()
superusergrp.name = "superusers"
superusergrp.data = [('cn', 'superusers'),
                  ('displayName', 'superusers'),
                  ('hubGroupId', 1),
                  ('gidNumber', 9001),
                  ('dateCreated', datetime.datetime(2009, 1, 1, 18, 17, 20))]

superusergrp.moddata = [('member',['uid=hubspace,ou=services,o=the-hub.net'])]
superusergrp.newmember = [('member', ['uid=%s,ou=,o=the-hub.net' % hub1.user1.uid ])]
