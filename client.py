import functools, cookielib, cPickle

import Pyro.core
import Pyro.errors

import errors, config

class SyncerClient(object):
    def __init__(self, appname, authtokengetter):
        self.appname = appname
        self._authtokengetter = authtokengetter

    def publishEvent(self, eventname, syncertoken, *args, **kw):
        syncer = Pyro.core.getProxyForURI(config.syncer_uri)
        args = [cPickle.dumps(arg, -1) for arg in args]
        kw = dict(((cPickle.dumps(k, -1), cPickle.dumps(v, -1)) for (k,v) in kw.items()))
        try:
            return getattr(syncer, eventname)(self.appname, syncertoken, *args, **kw)
        except Pyro.errors.ProtocolError:
            return errors.getError(errors.syncer_conn_failed)
        except Exception, err:
            return err

    def isSuccessful(self, result):
        return not errors.hasFailed(result)

    def getSyncerCred(self):
        return self._authtokengetter()

    def __getattr__(self, eventname):
        return functools.partial(self.publishEvent, eventname, self._authtokengetter())
