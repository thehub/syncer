"""
Syncer configuration
To override any value before you initialize client/ daemon
>>> import syncer.config
>>> syncer.config.host = "localhost"
>>> syncer.config.ldap_uri = "ldap://localhost"
>>> syncer.config.reload()
"""
import os, datetime

__syncerdebug__ = True

# syncer global defaults
# Application can override as per the site config
# syncer.config.reload() is only required if syncer client daemon is already initialized before the
# change in configuration
# Suggested use is change the config and then initialize syncer client/daemon.
use_ssl = False
host = "localhost"
port = 9003
basedir = os.path.dirname(os.path.abspath(__file__))
ssl_dir = "%s/certs" % basedir
apppath = "sync"
syncerroot = os.getcwd()
datadir = os.path.join(syncerroot, "data")
logdir = os.path.join(syncerroot, "logs")
user_agent = "syncer"
subscriber_adminemail = ""
ldap_uri = "ldap://localhost"
session_idletimeout = datetime.timedelta(0, 60 * 24 * 60 * 60) # 60 days of inactivity should expire the session
client_disabled = False
pyro_protocol = "PYRO"

# event/ sybscriber defaults. 
# To be overriden in syncer code
event_join = False
eventhandler_block = False
eventhandler_attempts = 2 # TODo rename to retries
eventhandler_attempt_interval = 2 # seconds
subscriber_adminemail = None 

def reload():
    import Pyro
    Pyro.config.PYRO_HOST = host
    Pyro.config.PYRO_PORT = port
    Pyro.config.PYRO_STDLOGGING = 0
    Pyro.config.PYRO_LOGFILE = "daemon.log"
    Pyro.config.PYRO_TRACELEVEL = 1
    Pyro.config.PYROSSL_CERTDIR = ssl_dir
    if use_ssl:
        globals()['syncer_uri'] =  "PYROLOCSSL://%s:%s/%s" % (host, port, apppath)
        globals()['pyro_protocol'] = "PYROSSL"
    else:
        globals()['syncer_uri'] =  "PYROLOC://%s:%s/%s" % (host, port, apppath)
    

    return True

reload()
