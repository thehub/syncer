import os
import logging.handlers
import cookielib
import Cookie
import time
import smtplib
import string
import elixir

import config
   
def pushToBuiltins(name, val):
    __builtins__[name] = val

def setupLogging():
    class TBFilter(logging.Filter):
        def filter(self, rec):
            return "Unpicklable exception" not in rec.msg

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')#, datefmt="%H:%M:%S")

    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    if config.__syncerdebug__:
        console.setLevel(logging.DEBUG)
    console.addFilter(TBFilter())
    logger.addHandler(console)

    flog = logging.handlers.RotatingFileHandler(os.path.join(config.logdir, "syncer.log"), 'a', 1024 * 1024, 10)
    flog.setLevel(logging.INFO)
    if config.__syncerdebug__:
        flog.setLevel(logging.DEBUG)
    flog.setFormatter(formatter)
    logger.addHandler(flog)
    pushToBuiltins("logger", logger)
    logger.info("Syncer Logger initialized")

def setupDirs():
    logdir = os.path.join(config.syncerroot, "logs")
    for path in (logdir,):
        if not os.path.exists(path): os.makedirs(path)
    
# Inspiration => http://docs.turbogears.org/1.0/ConvertCookies

attrs = 'expires', 'path', 'comment', 'domain', 'secure', 'version'
attr_defaults = dict (expires = None, path = "/", comment = None, domain = "", secure = None, version = None)

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
                            if hasattr(cookie, attr):
                                sc[name][attr] = getattr(cookie, attr)
    return sc

def convertCookie(what):
    """
    - list of cookielib.Cookie instances => simple cookie
    - CookieJar -> simple cookie
    - simple cookie -> CookieJar
    """
    if isinstance(what, list):
        cj = cookielib.CookieJar()
        for c in what:
            cj.set_cookie(c)
        return create_simple_cookie(cj)
    elif isinstance(what, cookielib.CookieJar):
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
        logger.info("Alert sent to %s" % str(data['recipient']))
    except Exception, err:
        smtpresult = None
        errstr = "Error sending mail to %s: %s" % (data['recipient'], str(err))
        logger.error(errstr)
    
    if smtpresult:
        for recip in smtpresult.keys():
            errstr + "Error sending mail to %s: %s %s %s" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)
            logger.error(errstr)

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
