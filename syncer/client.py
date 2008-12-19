try:
    import functools
except: # oh, pity you still on python 2.4
    import compat as functools

import cookielib, cPickle

import Pyro.core
import Pyro.errors

import errors, config

class SyncerClient(object):
    def __init__(self, appname, sessiongetter,client_disabled=-1,syncer_uri=-1):
        if client_disabled == -1:
            client_disabled=config.client_disabled
        if syncer_uri == -1:
            syncer_uri=config.syncer_uri
        self.appname = appname
        self.sessiongetter = sessiongetter
        self.syncer_uri = syncer_uri 
        if client_disabled:
            self.publishEvent = lambda *args, **kw: errors.getClientError(errors.syncer_client_disabled)
        else:
            print "SyncerClient initialized for %s:%s -> %s" % (config.host, config.port, config.ldap_uri)

    def getSyncerToken(self):
        return self.sessiongetter().get('syncertoken', None)

    def setSyncerToken(self, syncertoken):
        self.sessiongetter()['syncertoken'] = syncertoken

    def isSyncerRequest(self, user_agent):
        return user_agent == config.user_agent

    def publishEvent(self, eventname, syncertoken, *args, **kw):
        print config.syncer_uri
        syncer = Pyro.core.getProxyForURI(self.syncer_uri)
        args = [cPickle.dumps(arg, -1) for arg in args]
        kw = dict(((cPickle.dumps(k, -1), cPickle.dumps(v, -1)) for (k,v) in kw.items()))
        try:
            return getattr(syncer, eventname)(self.appname, self.getSyncerToken(), *args, **kw)
        except Pyro.errors.ProtocolError:
            return errors.getClientError(errors.syncer_conn_failed)
        except Exception, err:
            return err

    def isSuccessful(self, result):
        return not errors.hasFailed(result)

    def convertCookie(self, what):
        return utils.convertCookie(what)

    def __getattr__(self, eventname):
        return functools.partial(self.publishEvent, eventname, self.getSyncerToken())
