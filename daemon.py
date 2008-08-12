import Pyro

import utils
from bases import *
import subscribers

utils.setupDirs()
utils.setupLogging()

trdb = utils.PList(config.trdbpath)
utils.pushToBuiltins("trdb", trdb)
utils.pushToBuiltins("all_subscribers", dict ())

syncer = Syncer()
sessionkeeper = subscribers.sessions.SessionKeeper("sessionkeeper")
sessionkeeper.ignore_trdb = True
utils.pushToBuiltins("sessions", sessionkeeper)

#hubspace = subscribers.hubspace.HubSpace("members.the-hub.net", "hubspace")
hubspace = subscribers.hubspace.HubSpace("localhost:8080", "hubspace")
hubspace.adminemail = "shon@localhost"
#hubspace2 = subscribers.hubspace.HubSpace("localhost:8081", "hubspace2")
ldapwriter = subscribers.ldapwriter.LDAPWriter("ldapwriter")
ldapwriter.ignore_trdb = True

syncer.onSignon.addSubscriber(sessionkeeper)
syncer.onSignon.addSubscriber(ldapwriter)
#syncer.onSignon.addSubscriber(hubspace2)
syncer.onSignon.addSubscriber(hubspace)
syncer.onSignon.addArgsFilter(lambda args, kw: ((args[0], utils.Masked("Secret"), utils.Masked("cookies")), kw))
#syncer.onSignon.ignore_trdb = True
syncer.onSignon.join = True

syncer.onReceiveAuthcookies.join = True

syncer.onUserMod.addSubscriber(sessionkeeper)
syncer.onUserMod.addSubscriber(hubspace)
syncer.onUserMod.addSubscriber(ldapwriter)
syncer.onUserMod.join = True

syncer.onUserAdd.addSubscriber(sessionkeeper)
#syncer.onUserAdd.addSubscriber(hubspace)
syncer.onUserAdd.addSubscriber(ldapwriter)
syncer.onUserAdd.join = True

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
