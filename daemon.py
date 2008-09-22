import sys
import os
import threading
import Pyro

import utils
from bases import *
import subscribers

utils.setupDirs()
utils.setupLogging()

trdb = utils.PList(config.trdbpath)
utils.pushToBuiltins("trdb", trdb)
utils.pushToBuiltins("all_subscribers", dict ())
utils.pushToBuiltins("syncer_tls", threading.local())

syncer = Syncer()
sessionkeeper = subscribers.sessions.SessionKeeper("sessionkeeper")
sessionkeeper.ignore_trdb = True
utils.pushToBuiltins("sessions", sessionkeeper)

#hubspace = subscribers.hubspace.HubSpace("members.the-hub.net", "hubspace")
hubspace = subscribers.hubspace.HubSpace("localhost:8080", "hubspace")
hubspace.adminemail = "shon@localhost"
ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")
ldapwriter.ignore_trdb = True

syncer.onSignon.addSubscriber(sessionkeeper)
syncer.onSignon.addSubscriber(ldapwriter)
syncer.onSignon.addSubscriber(hubspace)
syncer.onSignon.addArgsFilter(lambda args, kw: ((args[0], utils.Masked("Secret"), utils.Masked("cookies")), kw))
syncer.onSignon.ignore_trdb = True
syncer.onSignon.join = True

syncer.onReceiveAuthcookies.join = True

syncer.onUserMod.addSubscriber(sessionkeeper)
syncer.onUserMod.addSubscriber(hubspace)
syncer.onUserMod.addSubscriber(ldapwriter)

syncer.onAssignRoles.addSubscriber(sessionkeeper)
syncer.onAssignRoles.addSubscriber(hubspace)
syncer.onAssignRoles.addSubscriber(ldapwriter)
syncer.onAssignRoles.join = True

syncer.onUserAdd.addSubscriber(sessionkeeper)
#syncer.onUserAdd.addSubscriber(hubspace)
syncer.onUserAdd.addSubscriber(ldapwriter)
syncer.onUserAdd.join = True

syncer.onHubAdd.addSubscriber(sessionkeeper)
syncer.onHubAdd.addSubscriber(hubspace)
syncer.onHubAdd.addSubscriber(ldapwriter)

syncer.onHubMod.addSubscriber(sessionkeeper)
syncer.onHubMod.addSubscriber(hubspace)
syncer.onHubMod.addSubscriber(ldapwriter)

syncer.onRoleAdd.addSubscriber(sessionkeeper)
syncer.onRoleAdd.addSubscriber(hubspace)
syncer.onRoleAdd.addSubscriber(ldapwriter)

Pyro.core.initServer()
#Pyro.config.PYRO_TRACELEVEL=3

sslsetup_cmd = "sh %s" % os.path.join(os.getcwd(), "sslsetup.sh")
if os.system(sslsetup_cmd) != 0:
    sys.exit("SSL Setup failed, try sh -x %s manually" % sslsetup_cmd)

daemon = Pyro.core.Daemon(prtcol=config.pyro_protocol)

uri = daemon.connect(syncer, config.syncer_path)
print"Listening on " , uri

# enter the service loop.
print 'Server started.'

try:
    daemon.requestLoop()
    pass
except KeyboardInterrupt:
    print "^c pressed. Bye."
