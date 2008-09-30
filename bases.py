import cPickle, datetime, threading, time, urllib, urllib2, cookielib, traceback
from Queue import Queue

import twill
import Pyro.core

import errors, config, utils, transactions

picklables = (int, str, dict, tuple, list, Exception, float, long, set, bool, type(None))

class SubscriberBase(object):
    def __init__(self, name):
        self.name = name.replace(" ", "_")
        self.current_tasks = dict()
        self.adminemail = config.subscriber_adminemail
        self.ignore_old_failures = False
        all_subscribers[name] = self

class WebApp(SubscriberBase):
    def __init__(self, domainname, *args, **kw):
        SubscriberBase.__init__(self, *args, **kw)
        self.domainname = domainname

    def makeLoginDict(self, username, password):
        raise NotImplemented

    def onSignon(self, u, p):
        raise NotImplemented

    def onReceiveAuthcookies(self, appname, cookies):
        if appname == self.name:
            session = sessions.current
            if 'authcookies' not in session:
                session['authcookies'] = {appname: cookies}
            else:
                session['authcookies'][appname] = cookies
            return True

    onReceiveAuthcookies.block = True

    def makeHttpReq(self, url, formvars):
        session = sessions.current
        cj = session['authcookies'][self.name]
        params = urllib.urlencode(formvars)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [("Content-type", "application/x-www-form-urlencoded"),
            ("Accept", "text/plain"), ("user-agent", config.user_agent)]
        logger.debug("Opening URL: %s (%s)" % (url, config.user_agent))
        logger.debug("Headers sent: %s" % opener.addheaders)
        r = opener.open(url, params)
        content = r.read()
        r.close()
        logger.debug("authenticate req code: %s" % r.code)
        return cj, content

    def readForm(self, url):
        session = sessions.current
        authcookies = session.get('authcookies', None)
        cj = None
        if authcookies:
            cj = authcookies.get(self.name, None)
        if not cj:
            logger.warn("could not find authcookies for %s" % self.name)
        b = twill.get_browser()
        b.set_agent_string(config.user_agent)
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
        return event

class Event(object):

    def  __init__(self, eventname):
        self.name = eventname
        self.subscribers_s = []
        self.subscribers = []
        self.argsfilterer = lambda args, kw: (args, kw)
        self.join = config.defaults.event_join
        self.transactional = True

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

    def addArgsFilter(self, f):
        self.argsfilterer = f
        
    def runHandler(self, sid, transaction, f, args, kw, subscriber, th_q):
        attempts = getattr(f, 'attempts', 2)
        syncer_tls.transaction = transaction
        syncer_tls.sid = sid
        try:
            for attempt in range(attempts):
                is_last_attempt = ((attempt + 1) == attempts)
                try:
                    ret = f(*args, **kw)
                    if not type(ret) in picklables:
                        err = "Unpicklable result: %s" % ret
                        logger.error(err)
                        raise Exception(err)
                    transaction.results[subscriber.name] = dict(appname = subscriber.name, retcode = errors.success, result = ret)
                    break
                except Exception, err:
                    #raise
                    print '================'
                    try:
                        traceback.print_exc(err)
                    except Exception, err:
                        print err
                    print '================'
                    logger.error("%s %s #%d: failed with error (%s)" % (subscriber.name, self.name, attempt, str(err)))
                    if is_last_attempt:
                        if not type(err) in picklables:
                            err = str(err)
                            logger.warn("Unpicklable exception: %s" % str(err))
                        retcode = (errors.app_write_failed, dict(appname=subscriber.name))
                        transaction.results[subscriber.name] = dict(appname = subscriber.name, retcode = retcode, result = err)
                        break
                    else:
                        print "before attempt #%d sleeping for 2 secs" % (attempt + 1)
                        time.sleep(getattr(f, 'attempt_interval', 2))
        finally:
            transactions.session.remove()
            th_q.get()
            th_q.task_done()

    def runInThread(self, sid, transaction, subscriber, args, kw, th_q, block=False):
        logger.info("%s %s: starting (block=%s)" % (subscriber.name, self.name, block))
        if not (subscriber.ignore_old_failures or not self.transactional) and transactions.hasFailedBefore(subscriber.name):
            err = errors.getError(errors.app_backlog_not_empty, appname = subscriber.name)
            transaction.results[subscriber.name] = dict(retcode = errors.app_backlog_not_empty, appname = subscriber.name, result = err)
            logger.error(errors.err2str(err))
        else:
            f = getattr(subscriber, self.name, getattr(subscriber, "onAnyEvent", None))
            th = threading.Thread(target=self.runHandler, args=(sid, transaction, f, args, kw, subscriber, th_q))
            th_q.put(subscriber.name)
            if block:
                th.run()
                logger.info("%s %s: done\n" % (subscriber.name, self.name))
            else:
                th.start()
        transactions.commit()

    def __call__(self, app_name, sid, *args, **kw):
        logger.info('Syncer publishing event: \"(%s)%s\"' % (app_name, self.name))
        args = [cPickle.loads(arg) for arg in args]
        kw = dict(((cPickle.loads(k), cPickle.loads(v)) for (k,v) in kw.items()))
        th_q = Queue()
        __failed = False

        if not sid:
            sid = sessions.genVisitId(self.name, args, kw)
        
        transactions.commit()
        transaction = transactions.newTransaction(self, *self.argsfilterer(args, kw))
        transactions.commit()

        for subscriber in self.subscribers_s:
            if app_name == subscriber.name: continue
            self.runInThread(sid, transaction, subscriber, args, kw, th_q, True)
            if errors.hasFailed(transaction.results):
                __failed = True
                break
        if not __failed:
            for subscriber in self.subscribers:
                if not app_name == subscriber.name:
                    self.runInThread(sid, transaction, subscriber, args, kw, th_q)

        if self.join:
            print "I'm asked to wait"
            th_q.join()
            print "My wait is over"
            self.onFailure(transaction, th_q, args, kw)
        else:
            threading.Thread(target=self.onFailure, args=(transaction, th_q, args, kw)).start()

        print '========================================'
        for (sid, session) in sessions.items():
            print sid, session['username'], session['ldapconn']
        print transaction.results
        print '========================================'
        transaction.state = 2
        transactions.commit()
        return transaction.t_id, transaction.results

    def onFailure(self, transaction, th_q, args, kw):
        th_q.join()
        results = transaction.results

        if errors.hasFailed(results):
            "failed !!!"
            transaction.state = 2
            eventname = self.name
            failed_apps = dict ()
            username = transaction.owner

            rollback_candidates = [s for s in self.subscribers_s + self.subscribers if not s.ignore_old_failures and s.name in results]
            logger.debug("Begin rollback")

            for subscriber in rollback_candidates:

                f = getattr(subscriber, eventname, getattr(subscriber, "onAnyEvent", None))
                rollback = getattr(f, "rollback", None)
                if rollback:
                    logger.debug("ateempting rollback for %s" % subscriber.name)
                    try:
                        rollback(subscriber, *args, **kw)
                    except Exception, err:
                        logger.error("Rollback failed for %s:%s (%s)" % (subscriber.name, eventname, err))

                if errors.isError(results[subscriber.name]):
                    failed_apps[subscriber.name] = results[subscriber.name]
                    if subscriber.adminemail:
                        recipient = subscriber.adminemail
                        appname = subscriber.name
                        err = utils.sendAlert(locals())
                        if err: logger.warn(err)

        transaction.delete()
