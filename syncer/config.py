import os, datetime, Pyro

use_ssl = False
pyrobasedir = os.path.dirname(os.path.abspath(__file__))
#pyroconf_path = "%s/Pyro.conf" % pyrobasedir
#Pyro.config.setup(pyroconf_path)
Pyro.config.PYRO_HOST = "ldap.the-hub.net"
Pyro.config.PYRO_PORT = 9003
Pyro.config.PYRO_STDLOGGING = 0
Pyro.config.PYRO_LOGFILE = "daemon.log"
Pyro.config.PYRO_TRACELEVEL = 1
Pyro.config.PYROSSL_CERTDIR = "%s/certs" % pyrobasedir

syncer_path = "sync"
if use_ssl:
    syncer_uri =  "PYROLOCSSL://%s:%s/%s" % (Pyro.config.PYRO_HOST, Pyro.config.PYRO_PORT, syncer_path)
    pyro_protocol = "PYROSSL"
else:
    syncer_uri =  "PYROLOC://%s:%s/%s" % (Pyro.config.PYRO_HOST, Pyro.config.PYRO_PORT, syncer_path)
    pyro_protocol = "PYRO"
__syncerdebug__ = True
syncerroot = os.getcwd()
datadir = os.path.join(syncerroot, "data")
logdir = os.path.join(syncerroot, "logs")
user_agent = "syncer"
subscriber_adminemail = ""

ldap_uri = "ldap://ldap.the-hub.net"
ldap_basedn = "dc=the-hub,dc=net"

session_idletimeout = datetime.timedelta(0, 60 * 24 * 60 * 60) # 60 days of inactivity should expire the session

client_disabled = False

class defaults(object):
    event_join = False
    eventhandler_block = False
    eventhandler_attempts = 2 # TODo rename to retries
    eventhandler_attempt_interval = 2 # seconds
    subscriber_adminemail = None 
