import sys
import os
import threading
import Pyro

import utils

utils.setupDirs()
utils.setupLogging()
utils.pushToBuiltins("all_subscribers", dict ())
utils.pushToBuiltins("syncer_tls", threading.local())

from bases import *

import transactions
import subscribers

utils.pushToBuiltins("currentTransaction", transactions.currentTransaction)
utils.pushToBuiltins("currentSession", subscribers.sessions.currentSession)

syncer = Syncer()
sessionkeeper = subscribers.sessions.SessionKeeper("sessionkeeper")
sessionkeeper.ignore_old_failures = True
utils.pushToBuiltins("sessions", sessionkeeper)

ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")
ldapwriter.ignore_old_failures = True
transactionmgr = subscribers.trmgr.TransactionMgr("transactionmgr")
transactionmgr.ignore_old_failures = True

hubspace = subscribers.hubspace.HubSpace("hubspace", "space.shons.net:8080")
hubspace.ignore_old_failures = True # TODO

hubplus = subscribers.hubplus.HubPlus("hubplus", "pinax.shons.net:8000")
hubplus.ignore_old_failures = True # TODO

# Transactions
syncer.completeTransactions.addSubscriber(transactionmgr)
syncer.completeTransactions.transactional = False
syncer.rollbackTransactions.addSubscriber(transactionmgr)
syncer.rollbackTransactions.transactional = False

# Signon/off
syncer.onSignon.addSubscriber(sessionkeeper)
syncer.onSignon.addSubscriber(ldapwriter)
syncer.onSignon.addArgsFilter(lambda args, kw: ((args[0], utils.Masked("Secret"), utils.Masked("cookies")), kw))
syncer.onSignon.transactional = False
syncer.onSignon.join = True

syncer.onReceiveAuthcookies.join = True

syncer.onSignoff.addSubscriber(sessionkeeper)
syncer.onSignoff.transactional = False
syncer.onSignoff.join = True

syncer.onUserLogin.addSubscriber(hubspace)
syncer.onUserLogin.addSubscriber(hubplus)
syncer.onUserLogin.transactional = False
syncer.onUserLogin.join = True

# User/Group events
syncer.onServiceAdd.addSubscriber(sessionkeeper)
syncer.onServiceAdd.addSubscriber(ldapwriter)
syncer.onServiceAdd.join = True

syncer.onGroupAdd.addSubscriber(sessionkeeper)
syncer.onGroupAdd.addSubscriber(ldapwriter)
syncer.onGroupAdd.join = True

syncer.onGroupMod.addSubscriber(sessionkeeper)
syncer.onGroupMod.addSubscriber(ldapwriter)
syncer.onGroupMod.join = True

syncer.onUserAdd.addSubscriber(sessionkeeper)
syncer.onUserAdd.addSubscriber(ldapwriter)
syncer.onUserAdd.join = True

syncer.onUserMod.addSubscriber(sessionkeeper)
syncer.onUserMod.addSubscriber(ldapwriter)
syncer.onUserMod.join = True

syncer.onAssignRoles.addSubscriber(sessionkeeper)
syncer.onAssignRoles.addSubscriber(ldapwriter)
syncer.onAssignRoles.join = True

syncer.onRoleAdd.addSubscriber(sessionkeeper)
syncer.onRoleAdd.addSubscriber(ldapwriter)

# Hub events
syncer.onHubAdd.addSubscriber(sessionkeeper)
syncer.onHubAdd.addSubscriber(ldapwriter)
syncer.onHubMod.addSubscriber(sessionkeeper)
syncer.onHubMod.addSubscriber(ldapwriter)

# AccessPolicy events
syncer.onAccesspolicyAdd.addSubscriber(sessionkeeper)
syncer.onAccesspolicyAdd.addSubscriber(ldapwriter)
syncer.onAccesspolicyMod.addSubscriber(sessionkeeper)
syncer.onAccesspolicyMod.addSubscriber(ldapwriter)
syncer.onAccesspolicyDel.addSubscriber(sessionkeeper)
syncer.onAccesspolicyDel.addSubscriber(ldapwriter)

# OpenTimes events
syncer.onOpentimesAdd.addSubscriber(sessionkeeper)
syncer.onOpentimesAdd.addSubscriber(ldapwriter)
syncer.onOpentimesMod.addSubscriber(sessionkeeper)
syncer.onOpentimesMod.addSubscriber(ldapwriter)
syncer.onOpentimesDel.addSubscriber(sessionkeeper)
syncer.onOpentimesDel.addSubscriber(ldapwriter)

# Tariff events
syncer.onTariffAdd.addSubscriber(sessionkeeper)
syncer.onTariffAdd.addSubscriber(ldapwriter)

Pyro.core.initServer()
#Pyro.config.PYRO_TRACELEVEL=3

sslsetup_cmd = "sh %s" % os.path.join(os.getcwd(), "sslsetup.sh")
if os.system(sslsetup_cmd) != 0:
    sys.exit("SSL Setup failed, try sh -x %s manually" % sslsetup_cmd)

daemon = Pyro.core.Daemon(prtcol=config.pyro_protocol)

uri = daemon.connect(syncer, config.apppath)
print"Listening on " , uri

# enter the service loop.
print 'Server started.'

try:
    daemon.requestLoop()
    pass
except KeyboardInterrupt:
    print "^c pressed. Bye."
