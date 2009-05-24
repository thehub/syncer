# LDAP Tests
# * ACL tests
import sys
import unittest
import logging
import logging.handlers

import syncer
import syncer.client
import syncer.config
import syncer.errors
syncer.config.host = "localhost"
syncer.config.ldap_uri = "ldap://localhost"
syncer.config.reload()

import ldaptestdata as testdata

class SyncerConn(object):
    def __init__(self, u):
        self.username = u
        self.session = dict ()
        session_getter = lambda : self.session
        self.clnt = syncer.client.SyncerClient("LDAPTest", session_getter)

trs_list = []

def setUpModule():
    print "setting up.. "

class SyncerTestCase(unittest.TestCase):
    short_dscr = ""
    def __call__(self):
        try:
            ret = self._run()
            logger.info(self.__class__.__name__)
            return ret
        except Exception, err:
            msg = "(%s) %s" % (self.__class__.__name__, str(err))
            logger.error(msg)
            sys.exit(1)

class SignOn(SyncerTestCase):
    e_ret = True
    def __init__(self, u, p):
        self.u = u
        self.p = p
    def _run(self):
        conn = SyncerConn(self.u)
        ret = conn.clnt.onSignon(self.u, self.p)
        tr_id, res = ret
        if not conn.clnt.isSuccessful(res):
            msg = syncer.errors.res2errstr(res, ", ")
            self.fail(msg)
        conn.clnt.setSyncerToken(res['sessionkeeper']['result'])
        return conn

class AddHub(SyncerTestCase):
    e_ret = False
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onHubAdd(self.data.id, self.data.data)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res, ", "))
        for (i, role) in enumerate(self.data.roles):
            data = [('cn', '%s Role' % role.capitalize()), ('level', role), ('roleId', i+1)]
            tr_id, res = self.conn.clnt.onRoleAdd(self.data.id, role, data)
            if not self.conn.clnt.isSuccessful(res):
                self.fail(syncer.errors.res2errstr(res))

class AddHubAsSuperUser(AddHub):
    e_ret = True

class TearDownModule():
    pass

def setupLogging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s', datefmt="%Y.%m.%d %H:%M:%S")

    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    flog = logging.handlers.RotatingFileHandler("syncertests.log", 'a', 1024 * 1024, 10)
    flog.setLevel(logging.DEBUG)
    flog.setFormatter(formatter)
    logger.addHandler(flog)
    globals()["logger"] = logger

class SignOnAsRoot(SignOn):
    pass

class SignOnAsUser1(SignOn):
    pass

class SignOnAsHost1(SignOn):
    pass

class SignOnAsSuperUser(SignOn):
    pass

class AddUser(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onUserAdd(self.data.uid, self.data.data)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res))

class AddUser1AsRoot(AddUser): pass
class AddUser1AsSuperuser(AddUser): pass
class AddUser1AsHost(AddUser): pass
class AddHost1AsSuperuser(AddUser): pass

class AssignRole(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        data = self.data
        tr_id, res = self.conn.clnt.onAssignRoles(data.uid, data.location.id, data.role)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res, ", "))

class AddSuperuserGroup(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onGroupAdd(self.data.name, self.data.data)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res, ", "))

class AddHubspaceadminToSuperusers(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onGroupMod(self.data.name, self.data.moddata)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res, ", "))

class AddSuperuser(AddUser):
    pass

class AddService(AddUser):
    def _run(self):
        tr_id, res = self.conn.clnt.onServiceAdd(self.data.uid, self.data.data)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res))


class SyncerConns(object):
    """I do nothing"""

class ModUser(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onUserMod(self.data.uid, self.data.moddata)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res))

class ModGlobalGroup(SyncerTestCase):
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data
    def _run(self):
        tr_id, res = self.conn.clnt.onGroupMod(self.data.name, self.data.newmember)
        if not self.conn.clnt.isSuccessful(res):
            self.fail(syncer.errors.res2errstr(res))

def main():
    setupLogging()
    conns = SyncerConns()
    signOnAsRoot = SignOnAsRoot(testdata.root_u, testdata.root_p)
    signOnAsSuperUser = SignOnAsSuperUser(testdata.superuser.uid, testdata.superuser.p)
    signOnAsUser1 = SignOnAsUser1(testdata.hub1.user1.uid, testdata.hub1.user1.p)
    conns.root_conn = signOnAsRoot()
    addSuperuserGroup = AddSuperuserGroup(conns.root_conn, testdata.superusergrp)
    addService = AddService(conns.root_conn, testdata.superuser)
    addHubspaceadminToSuperusers = AddHubspaceadminToSuperusers(conns.root_conn, testdata.superusergrp)
    addSuperuserGroup()
    addService()
    addHubspaceadminToSuperusers()
    conns.su_conn = signOnAsSuperUser()
    addHub1AsSuperuser = AddHubAsSuperUser(conns.su_conn, testdata.hub1)
    addHost1AsSuperuser  = AddHost1AsSuperuser(conns.su_conn, testdata.hub1.host1)
    assignHostRole = AssignRole(conns.su_conn, testdata.hub1.host1)
    signOnAsHost1 = SignOnAsHost1(testdata.hub1.host1.uid, testdata.hub1.host1.p)
    addHub1AsSuperuser()
    addHost1AsSuperuser()
    assignHostRole()
    conns.host_conn = signOnAsHost1()
    modGlobalGroup = ModGlobalGroup(conns.su_conn, testdata.superusergrp)
    addUser1AsHost = AddUser1AsHost(conns.host_conn, testdata.hub1.user1)
    addUser1AsHost()
    conns.user1_conn = signOnAsUser1()
    modUserAsSuperuser = ModUser(conns.su_conn, testdata.hub1.user1)
    modUserAsMember = ModUser(conns.user1_conn, testdata.hub1.user1)
    modUserAsMember()
    modUserAsSuperuser()
    modGlobalGroup()


if __name__ == '__main__':
    main()

