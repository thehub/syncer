import os, datetime

syncer_path = "sync"
syncer_uri =  "PYROLOC://localhost:9003/%s" % syncer_path
__syncerdebug__ = True
syncerroot = os.getcwd()
datadir = os.path.join(syncerroot, "data")
logdir = os.path.join(syncerroot, "logs")

ldap_uri = "ldap://localhost"
ldap_basedn = "dc=the-hub,dc=net"

session_idletimeout = datetime.timedelta(0, 365 * 24 * 60 * 60)

class defaults(object):
    event_join = False
    eventhandler_block = False
    eventhandler_attempts = 2 # TODo rename to retries
    eventhandler_attempt_interval = 2 # seconds
    subscriber_trust = False

