import os, sys, copy
import logging.handlers

import config

class Context(object):
    _context_keys = ('results', 'cred', 'eventname')
    def __init__(self, d):
        for k in self._context_keys:
            setattr(self, k, copy.deepcopy(d[k]))
    def __str__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k, None)) for k in self._context_keys))
    def __repr__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k, None)) for k in self._context_keys))
    
def pushToBuiltins(name, val):
    __builtins__[name] = val

def setupLogging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if config.__syncerdebug__:
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        logger.addHandler(console)

    flog = logging.handlers.RotatingFileHandler(os.path.join(config.logdir + "syncer.log"), 'a', 1024 * 1024, 10)
    flog.setLevel(logging.INFO)
    logger.addHandler(flog)
    pushToBuiltins("logger", logger)

def setupDirs():
    datadir = os.path.join(config.syncerroot, "data")
    logdir = os.path.join(config.syncerroot, "logs")
    for path in (datadir, logdir):
        if not os.path.exists(path): os.makedirs(path)
    
def getContext(frange=xrange(1,5)):
    for depth in frange:
        frame = sys._getframe(depth)
        eventname = frame.f_locals.get('eventname', None)
        if not eventname == None:
            break
    return Context(frame.f_locals)
