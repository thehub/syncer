import Pyro

import utils
from bases import *
import subscribers

utils.setupDirs()
utils.setupLogging()

trdb = PList(os.path.join(config.datadir, "trdb"))
utils.pushToBuiltins("trdb", trdb)
utils.pushToBuiltins("all_subscribers", dict ())

syncer = Syncer()
utils.pushToBuiltins("sessions", subscribers.sessions.SessionKeeper("sessionkeeper"))

#hubspace = subscribers.hubspace.HubSpace("members.the-hub.net", "hubspace")
hubspace = subscribers.hubspace.HubSpace("localhost:8080", "hubspace")
ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")

syncer.onSignon.addSubscriber(ldapwriter)
syncer.onSignon.addSubscriber(hubspace)
syncer.onSignon.join = True

event = syncer.onUserChange
syncer.onUserChange.addSubscriber(hubspace)
syncer.onUserChange.join = True

Pyro.core.initServer()
daemon = Pyro.core.Daemon()

uri = daemon.connect(syncer, config.syncer_path)
print"Listening on " , uri

# enter the service loop.
print 'Server started.'

try:
    daemon.requestLoop()
except KeyboardInterrupt:
    print "^c pressed. Bye."
