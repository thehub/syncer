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

class AddUser1AsRoot(AddUser):
    pass

class AddUser1AsSuperuser(AddUser):
    pass

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

class ModUserAsMember(ModUser):
    pass

def main():
    setupLogging()
    conns = SyncerConns()
    signOnAsRoot = SignOnAsRoot(testdata.root_u, testdata.root_p)
    signOnAsSuperUser = SignOnAsSuperUser(testdata.superuser.uid, testdata.superuser.p)
    signOnAsUser1 = SignOnAsUser1(testdata.hub1.user1.uid, testdata.hub1.user1.p)
    conns.root_conn = signOnAsRoot()
    addSuperuserGroup = AddSuperuserGroup(conns.root_conn, testdata.superusergrp)
    addSuperuser = AddSuperuser(conns.root_conn, testdata.superuser)
    addHubspaceadminToSuperusers = AddHubspaceadminToSuperusers(conns.root_conn, testdata.superusergrp)
    addSuperuserGroup()
    addSuperuser()
    addHubspaceadminToSuperusers()
    conns.su_conn = signOnAsSuperUser()
    addHub1AsSuperuser = AddHubAsSuperUser(conns.su_conn, testdata.hub1)
    #addUser1AsRoot = AddUser1AsRoot(conns.root_conn, testdata.hub1.user1)
    addUser1AsSuperuser = AddUser1AsSuperuser(conns.su_conn, testdata.hub1.user1)
    addHub1AsSuperuser()
    #addUser1AsRoot()
    addUser1AsSuperuser()
    conns.user1_conn = signOnAsUser1()
    modUserAsMember = ModUserAsMember(conns.user1_conn, testdata.hub1.user1)
    modUserAsMember()


if __name__ == '__main__':
    main()

