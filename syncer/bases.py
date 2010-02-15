from __future__ import with_statement
import cPickle, datetime, threading, time, urllib, urllib2, cookielib, traceback
from Queue import Queue
import copy

import Pyro.core
import mechanize

import errors, config, utils, transactions

import cookielib
import urllib
import urllib2
  
picklables = (int, str, dict, tuple, list, float, long, set, bool, type(None))

class SubscriberBase(object):
    def __init__(self, name):
        self.name = name.replace(" ", "_")
        self.current_tasks = dict()
        self.adminemail = config.subscriber_adminemail
        self.ignore_old_failures = False
        all_subscribers[name] = self

class WebApp(SubscriberBase):
    loginurl_tmpl = "http://%s/login"

    def __init__(self, name, domainname, *args, **kw):
        SubscriberBase.__init__(self, name, *args, **kw)
        self.domainname = domainname
        self.login_url = self.loginurl_tmpl % self.domainname
        self.authcookies = []

    def makeHttpReq(self, url, formvars):
        cj = self.authcookies
        params = urllib.urlencode(formvars)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [("Content-type", "application/x-www-form-urlencoded"),
            ("Accept", "text/plain"), ("user-agent", config.user_agent)]
        logger.debug("Opening URL: %s (%s)" % (url, config.user_agent))
        #logger.debug("Headers sent: %s" % opener.addheaders)
        r = opener.open(url, params)
        content = r.read()
        r.close()
        logger.debug("returned http code: %s" % r.code)
        return cj, content

    def onSignonSaveArgs(self, u, p, cookies):
        return (u, utils.masked, utils.masked)


    def onUserLogin(self, u, p, cookies=[]):
        #import ipdb
        #ipdb.set_trace()
        #login_dict = self.makeLoginDict(u, p)
        #post_data = urllib.urlencode(login_dict)
        #headers = {"User-agent": config.user_agent, 
        #           'Accept': 'text/html',
        #           'Host': self.domainname,
        #           'Content-type': "application/x-www-form-urlencoded"}
        #logger.debug("Opening URL: %s (%s)" % (self.login_url, config.user_agent))
        #req = urllib2.Request(self.login_url, post_data, headers)
        #logger.debug("Done Opening URL: %s (%s)" % (self.login_url, config.user_agent))
        cj = self._onUserLogin(u, p, cookies)
        # return True
        return [c for c in cj]

    onUserLogin.block = True
    onUserLogin.saveargs = onSignonSaveArgs
       

    def _onUserLogin(self, u, p, cookies=[]):
        """
        u: username
        p: password
        cookies: list of cookielib.Cookie instances. These cookies would be passed during login attempt.
        Returns list of auth cookies
        """
        b = mechanize.Browser()
        b.addheaders = [ ("User-agent", config.user_agent),
                         ('Accept', 'text/html'),
                         ('Host', self.domainname),
                         ('Content-type', "application/x-www-form-urlencoded"),
                         ]
        cj = b._ua_handlers['_cookies'].cookiejar
        for c in cookies:
            cj.set_cookie(c)
        logger.debug("URL open: %s" % self.login_url)
        b.open(self.login_url)
        login_dict = self.makeLoginDict(u, p)
        forms = list(b.forms())
        for form in forms:
            if set(login_dict.keys()).issubset(set([c.name for c in form.controls])):
                nr = forms.index(form)
                break
        b.select_form(nr=nr)
        for (k,v) in self.makeLoginDict(u, p).items():
            b[k] = v
        b.submit()
        return cj



    def onSignon(self, u, p):
        transaction = currentTransaction()
        session = currentSession()
        if transaction.initiator == self.name:
            self.authcookies = self._onUserLogin(u, p)

    onSignon.block = True
    onUserLogin.saveargs = onSignonSaveArgs

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
        self.join = config.event_join
        self.transactional = True

    def addSubscriber(self, subscriber):
        handler = getattr(subscriber, self.name, getattr(subscriber, "onAnyEvent", None))
        if getattr(handler, "block", config.eventhandler_block):
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
        attempts = getattr(f, 'attempts', config.eventhandler_attempts)
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
                    username = currentSession().get('username', 'anonymous')
                    logger.error("%s %s as (%s) #%d: failed with error (%s)" % (subscriber.name, self.name, username, attempt, str(err)))
                    if is_last_attempt:
                        if not type(err) in picklables or not isinstance(err, picklables):
                            err = str(err)
                            #logger.warn("Unpicklable exception: %s" % str(err))
                            logger.exception("Unpicklable exception")
                        retcode = errors.app_write_failed
                        transaction.results[subscriber.name] = dict(appname = subscriber.name, retcode = retcode, result = err)
                        break
                    else:
                        print "before attempt #%d sleeping for 2 secs" % (attempt + 1)
                        time.sleep(getattr(f, 'attempt_interval', 2))
        finally:
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
                logger.info("%s %s: done" % (subscriber.name, self.name))
            else:
                th.start()

    def __call__(self, initiator, sid, *args, **kw):
        logger.info('Syncer publishing event: \"(%s)%s\"' % (initiator, self.name))
        args = [cPickle.loads(arg) for arg in args]
        kw = dict(((cPickle.loads(k), cPickle.loads(v)) for (k,v) in kw.items()))
        th_q = Queue()
        __failed = False

        if not sid:
            sid = sessions.genVisitId(self.name, args, kw)
        
        with threading.Lock():
            session = transactions.session()
            transaction = transactions.newTransaction(self, initiator, *self.argsfilterer(args, kw))
            if self.transactional:
                session.add(transaction)
            session.commit()
            tr_id = transaction.id
            logger.debug("Transaction (%s): Begin" % transaction.id)

        for subscriber in self.subscribers_s:
            if not initiator == subscriber.name or self.name == 'onSignon':
                self.runInThread(sid, transaction, subscriber, args, kw, th_q, True)
                if errors.hasFailed(transaction.results):
                    __failed = True
                    break

        results = copy.copy(transaction.results)

        if __failed:
            self.onFailure(transaction, th_q, args, kw)
        else:
            for subscriber in self.subscribers:
                if not initiator == subscriber.name:
                    self.runInThread(sid, transaction, subscriber, args, kw, th_q)
            
            def thCleanup(transaction, th_q):
                th_q.join()
                transaction.state = 2
                #transactions.commit()
                session.commit()
                session.close()
                #transactions.session.close()
                logger.debug("dropping session")

            if self.join:
                print "I'm asked to wait"
                threading.Thread(target=thCleanup, args=(transaction, th_q)).run()
                print "My wait is over"
            else:
                threading.Thread(target=thCleanup, args=(transaction, th_q)).start()


        #print '========================================'
        #for (sid, session) in sessions.items():
        #    print sid, session['username'], session
        #print results
        #print '========================================'
        return tr_id, results

    def onFailure(self, transaction, th_q, args, kw):
        th_q.join()
        results = transaction.results

        if errors.hasFailed(results):
            transaction.state = 2
            eventname = self.name
            failed_apps = dict ()

            if self.transactional:
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

        try:
            transaction.delete()
            transactions.commit()
            transactions.session.close()
        except Exception, err:
            logger.warn("TODO %s" % err)
