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

#ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")
#ldapwriter.ignore_old_failures = True
transactionmgr = subscribers.trmgr.TransactionMgr("transactionmgr")
transactionmgr.ignore_old_failures = True

hubspace = subscribers.hubspace.HubSpace("hubspace", "newdev.the-hub.net")
hubspace.ignore_old_failures = True # TODO

hubplus = subscribers.hubplus.HubPlus("hubplus", "plusdev.the-hub.net")
#hubplus = subscribers.hubplus.HubPlus("hubplus", "plus.the-hub.net")
hubplus.ignore_old_failures = True # TODO

# Transactions
syncer.completeTransactions.addSubscriber(transactionmgr)
syncer.completeTransactions.transactional = False
syncer.rollbackTransactions.addSubscriber(transactionmgr)
syncer.rollbackTransactions.transactional = False

# Signon/off
syncer.onSignon.addSubscriber(sessionkeeper)
#syncer.onSignon.addSubscriber(ldapwriter)
syncer.onSignon.addSubscriber(hubspace)
syncer.onSignon.addSubscriber(hubplus)
syncer.onSignon.addArgsFilter(lambda args, kw: ((args[0], utils.Masked("Secret"), utils.Masked("cookies")), kw))
syncer.onSignon.transactional = False
syncer.onSignon.join = True

syncer.onReceiveAuthcookies.join = True

syncer.onUserLogin.addSubscriber(sessionkeeper)
syncer.onUserLogin.addSubscriber(hubspace)
syncer.onUserLogin.addSubscriber(hubplus)
syncer.onUserLogin.transactional = False
syncer.onUserLogin.join = True

# User/Group events
syncer.onUserAdd.addSubscriber(sessionkeeper)
#syncer.onUserAdd.addSubscriber(ldapwriter)
syncer.onUserAdd.addSubscriber(hubplus)
syncer.onUserAdd.addSubscriber(hubspace)
syncer.onUserAdd.join = False

syncer.onUserMod.addSubscriber(sessionkeeper)
#syncer.onUserMod.addSubscriber(ldapwriter)
syncer.onUserMod.addSubscriber(hubplus)
syncer.onUserMod.addSubscriber(hubspace)
syncer.onUserMod.join = False

syncer.onGroupJoin.addSubscriber(sessionkeeper)
syncer.onGroupJoin.addSubscriber(hubplus)
syncer.onGroupJoin.join = False

syncer.onGroupLeave.addSubscriber(sessionkeeper)
syncer.onGroupLeave.addSubscriber(hubplus)
syncer.onGroupLeave.join = False

# Location events
syncer.onLocationAdd.addSubscriber(sessionkeeper)
#syncer.onLocationAdd.addSubscriber(ldapwriter)
syncer.onLocationAdd.addSubscriber(hubspace)

syncer.onLocationMod.addSubscriber(sessionkeeper)
#syncer.onHubMod.addSubscriber(ldapwriter)

Pyro.core.initServer()
#Pyro.config.PYRO_TRACELEVEL=3

#sslsetup_cmd = "sh %s" % os.path.join(os.getcwd(), "sslsetup.sh")
#if os.system(sslsetup_cmd) != 0:
#    sys.exit("SSL Setup failed, try sh -x %s manually" % sslsetup_cmd)

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
