try:
    import functools
    import hashlib
except:
    import compat as functools
    hashlib = functools

import cookielib, cPickle

import Pyro.core
import Pyro.errors

import errors, config

h = hashlib.sha1("hubplus")
h.update(file("/proc/cpuinfo").read())
apptoken = h.hexdigest()

class SyncerClient(object):
    def __init__(self, appname, sessiongetter):
        self.appname = appname
        self.sessiongetter = sessiongetter

    def getSyncerToken(self):
        return self.sessiongetter().get('syncertoken', None)

    def setSyncerToken(self, syncertoken):
        self.sessiongetter()['syncertoken'] = syncertoken

    def isSyncerRequest(self, user_agent):
        return user_agent == config.user_agent

    def exchangeTokens(self):
        return self.onReceiveApptoken(self.appname, apptoken)

    def publishEvent(self, eventname, syncertoken, *args, **kw):
        syncer = Pyro.core.getProxyForURI(config.syncer_uri)
        args = [cPickle.dumps(arg, -1) for arg in args]
        kw = dict(((cPickle.dumps(k, -1), cPickle.dumps(v, -1)) for (k,v) in kw.items()))
        try:
            return getattr(syncer, eventname)(self.appname, self.getSyncerToken(), *args, **kw)
        except Pyro.errors.ProtocolError:
            return errors.getError(errors.syncer_conn_failed)
        except Exception, err:
            return err

    def isSuccessful(self, result):
        return not errors.hasFailed(result)

    def convertCookie(self, what):
        return utils.convertCookie(what)

    def __getattr__(self, eventname):
        return functools.partial(self.publishEvent, eventname, self.getSyncerToken())
