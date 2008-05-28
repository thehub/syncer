import os, cPickle, datetime, threading, time, urllib, urllib2, cookielib
from Queue import Queue

import twill
import Pyro.core

import errors, config, utils

picklables = (int, str, dict, tuple, list, Exception, float, long, set)

class SubscriberBase(object):
    def __init__(self, name):
        self.name = name.replace(" ", "_")
        self.current_tasks = dict()
        all_subscribers[name] = self
        self.trusted = False

class WebApp(SubscriberBase):
    def __init__(self, domainname, *args, **kw):
        SubscriberBase.__init__(self, *args, **kw)
        self.domainname = domainname

    def makeLoginDict(self, username, password):
        raise NotImplemented

    def onSignon(self, u, p):
        raise NotImplemented

    def makeHttpReq(self, url, formvars):
        cj = sessions.current['authcookies'][self.name]
        params = urllib.urlencode(formvars)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [("Content-type", "application/x-www-form-urlencoded"), ("Accept", "text/plain")]# ('Cookie', cookie_hdr)]
        logger.debug("Opening URL: %s" % url)
        logger.debug("Headers sent: %s" % opener.addheaders)
        r = opener.open(url, params)
        content = r.read()
        r.close()
        logger.debug("authenticate req code: %s" % r.code)
        return cj, content # If there are more than one name/value pairs we want a list to
        return list(cj), content # If there are more than one name/value pairs we want a list to
                                 # enable caller function perform addition to make a single list
        
    def readForm(self, url):
        cj = sessions.current['authcookies'][self.name]
        b = twill.get_browser()
        for c in cj:
            b.cj.set_cookie(c)
        b.go(url)
        f = b.get_all_forms()[0]
        d = dict()
        for c in f.controls:
            if isinstance(c.value, list):
                if c.value:
                    value = c.value[0]
                else:
                    value = ""
            else:
                value = c.value
            d[c.name] = value
        return d

class Syncer(Pyro.core.ObjBase):

    def __init__(self, *args, **kw):
        Pyro.core.ObjBase.__init__(self, *args, **kw)
        self.events = dict()
    
    def __getattr__(self, eventname):
        if eventname not in self.events:
            event = Event(eventname)
            self.events[eventname] = event
        setattr(self, eventname, event)
        for subscriber in all_subscribers.values():
            if hasattr(subscriber, "onAnyEvent"):
                event.addSubscriber(subscriber)
        return event

class Event(object):

    def  __init__(self, eventname):
        self.name = eventname
        self.subscribers_s = []
        self.subscribers = []
        self.join = config.defaults.event_join

    def addSubscriber(self, subscriber):
        handler = getattr(subscriber, self.name, getattr(subscriber, "onAnyEvent", None))
        if getattr(handler, "block", config.defaults.eventhandler_block):
            self.subscribers_s.append(subscriber)
        else:
            self.subscribers.append(subscriber)

    def removeSubscriber(self, subscriber):
        while subscriber in self.subscribers_s:
            self.subscribers_s.remove(subscriber)
        while subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

    def genVisitId(self):
        return os.urandom(21).encode('hex')
        
    def runHandler(self, f, cred, args, kw, subscriber, results, th_q):
        attempts = getattr(f, 'attempts', 2)
        data = dict()
        eventname = self.name # so that context gets it
        try:
            for attempt in range(attempts):
                is_last_attempt = ((attempt + 1) == attempts)
                try:
                    ret = f(*args, **kw)
                    results[subscriber.name] = dict(appname = subscriber.name, retcode = (errors.success, {}), result = ret)
                    break
                except Exception, err:
                    #raise
                    logger.error("%s %s #%d: failed with error (%s)" % (subscriber.name, self.name, attempt, str(err)))
                    if is_last_attempt:
                        if not type(err) in picklables:
                            err = str(err)
                            logger.warn("Unpicklable exception: %s" % str(err))
                        retcode = (errors.app_write_failed, dict(appname=subscriber.name))
                        results[subscriber.name] = dict(appname = subscriber.name, retcode = retcode, result = err)
                        break
                    else:
                        print "before attempt #%d sleeping for 2 secs" % (attempt + 1)
                        time.sleep(getattr(f, 'attempt_interval', 2))
        finally:
            print "marking %s task over\n" % subscriber.name
            th_q.get()
            th_q.task_done()

    def runInThread(self, cred, subscriber, args, kw, results, th_q, block=False):
        logger.info("%s %s: starting (block=%s)" % (subscriber.name, self.name, block))
        if trdb.hasBacklog(subscriber.name):
            err = errors.getError(errors.app_backlog_not_empty, appname = subscriber.name)
            results[subscriber.name] = dict(retcode = errors.app_backlog_not_empty, appname = subscriber.name, result = err)
            logger.error(errors.err2str(err))
        else:
            f = getattr(subscriber, self.name, getattr(subscriber, "onAnyEvent", None))
            th = threading.Thread(target=self.runHandler, args=(f, cred, args, kw, subscriber, results, th_q))
            th_q.put(subscriber.name)
            if block:
                th.run()
                logger.info("%s %s: done" % (subscriber.name, self.name))
            else:
                th.start()

    def __call__(self, app_name, cred, *args, **kw):
        logger.info('Syncer publishing event: \"(%s)%s\"' % (app_name, self.name))
        args = [cPickle.loads(arg) for arg in args]
        kw = dict(((cPickle.loads(k), cPickle.loads(v)) for (k,v) in kw.items()))
        results = dict ()
        th_q = Queue()
        __failed = False

        if not cred:
            cred = self.genVisitId()
            while cred in sessions:
                cred = self.genVisitId()
        for subscriber in self.subscribers_s:
            if not app_name == subscriber.name:
                self.runInThread(cred, subscriber, args, kw, results, th_q, True)
                if errors.hasFailed(results):
                    __failed = True
                    break
        if not __failed:
            for subscriber in self.subscribers:
                if not app_name == subscriber.name:
                    self.runInThread(cred, subscriber, args, kw, results, th_q)
        if self.join:
            print "I'm asked to wait"
            th_q.join()
            print th_q.queue
            print "My wait is over"
        else:
            def dumpresults(th_q, results):
                th_q.join()
                if __failed or errors.hasFailed(results):
                    trdb.put(results)
                trdb.dump()
            threading.Thread(target=dumpresults, args=(th_q, results)).start()
        return results
