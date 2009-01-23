import decimal
import datetime

class TestData():
    """
    """

root_u = "ldapadmin"
root_p = "cL5XgIxJK0"
host_u = "x"
host_p = "x"
hub1 = TestData()
hub1.user1 = TestData()

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

hub1.user1.uid = "shon"
hub1.user1.p = "secret"
hub1.user1.data = [('billingTelephoneNumber', None),
                ('cn', u'Shekhar Tiwatne'),
                ('uid', u'shon'),
                ('publicViewable', None),
                ('operatingSystem', u'Linux'),
                ('gn', u'Shekhar'),
                ('homeHub', 'hubId=1,ou=hubs,o=the-hub.net'),
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
                ('description',
                 u'Just a programmer\n'),
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
                ('hubUserId', 1),
                ('displayName', u'Shekhar Tiwatne'),
                ('labeledURI', None),
                ('mobile', '+91 99222 55300'),
                ('billingProfile', 1),
                ('mailAlso', [u'shon@thisdoesnotexists.net']),
                ('billingFacsimileNumber', None),
                ('sn', u'Tiwatne'),
                ('billingMail', None),
                ('billingReminderKey', u'66cbf1d00bc76b9a34f82388f5c6b85f')]

hub1.user1.moddata = [('title', 'Mr.')]

superuser = TestData()
superuser.uid = "hubspaceadmin"
superuser.p = "secret"
superuser.data = [ ('uid', "hubspaceadmin"),
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

superusergrp.moddata = [('member',['uid=hubspaceadmin,ou=users,o=the-hub.net'])]

