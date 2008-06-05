import os, sys, copy, cPickle
import logging.handlers
import cookielib
import Cookie
import time
import smtplib
import string

import config

class Context(object):
    def __init__(self, results, cred, eventname):
        self.results = results
        self.cred = cred
        self.eventname = eventname
    def __str__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k)) for k in self.__dict__ if k[0] is not '_'))
    def __repr__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k)) for k in self.__dict__ if k[0] is not '_'))
    
def pushToBuiltins(name, val):
    __builtins__[name] = val

def setupLogging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if config.__syncerdebug__:
        formatter = logging.Formatter('%(levelname)-8s: %(funcName)s: %(message)s')
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setFormatter(formatter)
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
    
def getContext(frange=xrange(1,7)):
    for depth in frange:
        frame = sys._getframe(depth)
        context = frame.f_locals.get('context', None)
        #print "search: %s %s" % (frame.f_code.co_name, str([k for k in frame.f_locals]))
        if context: return context

class PList(list):
    def __init__(self, path):
        self.path = path
        list.__init__(self)
        self.load()
    def dump(self):
        file(self.path, 'w').write(cPickle.dumps(list(self), cPickle.HIGHEST_PROTOCOL))
        return True
    def load(self):
        if os.path.exists(self.path):
            data = cPickle.load(file(self.path))
            for x in data:
                self.put(x)
    def put(self, what):
        self.append(what)
        return True
    def hasBacklog(self, appname):
        for tr in self:
            if appname in tr[-1]:
                return True
        return False


# Inspiration => http://docs.turbogears.org/1.0/ConvertCookies

attrs = 'expires', 'path', 'comment', 'domain', 'secure', 'version'
attr_defaults = dict (expires = None, path = None, comment = None, domain = "", secure = None, version = None)

def create_cookies(simple_cookie):
    cookies = []
    attrs_d = dict ()
    for (cname, morsel) in simple_cookie.items():
        name = cname
        value = morsel.value
        for k in attrs:
            v = morsel.get(k, None)
            if isinstance(v, str): v = v.strip()
            if not v: v = attr_defaults[k]
            attrs_d[k] = v
        c = cookielib.Cookie(attrs_d['version'], name, value, None, None, attrs_d['domain'], None, None,
                        attrs_d['path'], None, "", attrs_d['expires'], "", attrs_d['comment'], None, None)
        cookies.append(c)
    return cookies

def create_cookiejar(simple_cookie):
    cj = cookielib.CookieJar()
    for c in create_cookies(simple_cookie):
        cj.set_cookie(c)
    return cj

def create_simple_cookie(cookiejar):
    "Returns a Cookie.SimpleCookie based on cookielib.CookieJar."
    sc = Cookie.SimpleCookie()
    # Doesn't look like Cookie.SimpleCookie allows for nonstandard attributes, so
    # we only deal with the standard ones.
    for path_dict in cookiejar._cookies.values(): #iterate through paths
        for cookie_dict in path_dict.values():
            for name, cookie in cookie_dict.items():
                sc[name] = cookie.value
                for attr in attrs:
                    if getattr(cookie, attr):
                        if attr == 'expires':
                            # Cookies thinks an int expires x seconds in future,
                            # cookielib thinks it is x seconds from epoch,
                            # so doing the conversion to string for Cookies
                            fmt = '%a, %d %b %Y %H:%M:%S GMT'
                            sc[name]['expires'] = time.strftime(fmt,
                                                    time.gmtime(cookie.expires))
                        else:
                            sc[name][attr] = getattr(cookie, attr)
    return sc

def convertCookie(what):
    if isinstance(what, cookielib.CookieJar):
        return create_simple_cookie(what)
    else:
        return create_cookies(what)

def uniq(l):
    l.sort()
    current = l[0]
    ul = [current]
    for next in l:
        if next == current: continue
        ul.append(next)
        if l: current = next
        else: ul.append(next)
    return ul

def mergeSimplecookies(*scs):
    m = Cookie.SimpleCookie()
    for sc in scs:
        m.update(sc)
    return m

class Masked(object):
    def __init__(self, argname="password"):
        self.argname = argname
    def __str__(self):
        return "<%s>" % self.argname
    def __repr__(self):
        return "<%s>" % self.argname

def sendAlert(data):
    smtpserver = 'localhost'
    
    sender = 'syncerdaemon@the-hub.net'
    path = "appadmin_alert.mail"
    locals().update(data)
    body = string.Template(file(path).read()).safe_substitute(data)
    
    session = smtplib.SMTP(smtpserver)

    errstr = ""
    try:
        smtpresult = session.sendmail(sender, [data['recipient']], body)
    except Exception, err:
        smtpresult = None
        errstr = "Error sending mail to %s: %s" % (data['recipient'], str(err))
    
    if smtpresult:
        for recip in smtpresult.keys():
            errstr + "Error sending mail to %s: %s %s %s" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)

    return errstr

def readConfigSafe(path):
    import compiler
    ast = compiler.parseFile("appadmin_alert.mail")
    d = dict()
    for x in ast.asList()[1].asList():
        name = x.asList()[0].name
        if hasattr(x.asList()[1], "value"): value = x.asList()[1].value
        else: value = [n.value for n in x.asList()[1].nodes]
        d[name] = value
    return d


if __name__ == '__main__':
    sc = Cookie.SimpleCookie()
    sc['name'] = 'shon'
    sc['name']['expires'] = '0'
    sc['name']['domain'] = 'foo.net'
    sc['name']['path'] = '/testapp'

    sc1 = Cookie.SimpleCookie()
    sc1['letters'] = 'abc'
    sc1['letters']['expires'] = '100'
    sc1['letters']['domain'] = 'foo.net'
    sc1['letters']['path'] = '/testapp'

    sc = mergeSimplecookies(sc, sc1)

    cl = create_cookies(sc)
    cj = create_cookiejar(sc)

    sc = create_simple_cookie(cj)

    l = [56, 34, 56, 72, 3, 0, 98, 12, 56, 3]
    ul = uniq(l)
