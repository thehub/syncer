import os

import Pyro

import utils
from bases import *
import subscribers

utils.setupDirs()
utils.setupLogging()

trdb = utils.PList(os.path.join(config.datadir, "trdb"))
utils.pushToBuiltins("trdb", trdb)
utils.pushToBuiltins("all_subscribers", dict ())

syncer = Syncer()
sessionkeeper = subscribers.sessions.SessionKeeper("sessionkeeper")
utils.pushToBuiltins("sessions", sessionkeeper)

#hubspace = subscribers.hubspace.HubSpace("members.the-hub.net", "hubspace")
hubspace = subscribers.hubspace.HubSpace("localhost:8080", "hubspace")
#hubspace2 = subscribers.hubspace.HubSpace("localhost:8081", "hubspace2")
ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")

syncer.onSignon.addSubscriber(ldapwriter)
#syncer.onSignon.addSubscriber(hubspace2)
syncer.onSignon.addSubscriber(hubspace)
syncer.onSignon.addArgsFilter(lambda args, kw: ((args[0], utils.Masked(), utils.Masked("cookies")), kw))
#syncer.onSignon.ignore_trdb = True
syncer.onSignon.join = False

syncer.onReceiveAuthcookies.join = True

event = syncer.onUserChange
syncer.onUserChange.addSubscriber(hubspace)
#syncer.onUserChange.addSubscriber(hubspace2)
syncer.onUserChange.join = True

Pyro.core.initServer()
daemon = Pyro.core.Daemon()

uri = daemon.connect(syncer, config.syncer_path)
print"Listening on " , uri

# enter the service loop.
print 'Server started.'

try:
    daemon.requestLoop()
    pass
except KeyboardInterrupt:
    print "^c pressed. Bye."
