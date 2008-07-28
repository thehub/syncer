import datetime, os

import bases, utils, errors, config

class SessionKeeper(dict, bases.SubscriberBase):

    def __init__(self, *args, **kw):
        bases.SubscriberBase.__init__(self, *args, **kw)
        dict.__init__(self)

    def releaseSession(self, sid):
        if sid in self:
            del self[sid]

    def listActiveSession(self):
        return ((sid, data['user']) for sid, data in self.items())

    def authenticate(self, u, p):
        return True

    def validate(self, sid):
        return bool(sid) and sid in self

    def destroySession(self, sid):
        del self[sid]

    def _onSignon(self, u, p, cookies):
        if not self.authenticate(u, p):
            errors.raiseError(errors.authfailure)

    def rollback(self, *args, **kw):
        context = utils.getContext()
        if context.eventname == "onSignon":
            del self[context.cred]
        
    def onAnyEvent(self, *args, **kw):
        context = utils.getContext()
        username = args[0]
        if context.eventname == "onSignon":
            self.removeStaleSessions()
            ret = self._onSignon(*args[:3])
            existing_session = self.getUserSession(username)
            if existing_session:
                logger.debug("using existing session for %s" % username)
                session = existing_session
            else:
                logger.debug("creating new session for %s" % username)
                cred = context.cred
                newsession = dict (cred = cred, username = args[0])
                newsession['last_seen'] = datetime.datetime.now()
                session = newsession
                self[cred] = session
            return session['cred']
        else:
            if not self.validate(context.cred):
                errors.raiseError(errors.sessionnotfound)
    onAnyEvent.rollback = rollback
    onAnyEvent.block = True

    def genVisitId(self, eventname, args, kw):
        if eventname == "onSignon":
            ses = self.getUserSession(args[0])
            if ses:
                return ses['cred']
        return os.urandom(21).encode('hex')

    def onReceiveAuthcookies(self, appname, username, cookies):
        cj = utils.create_cookiejar(cookies)
        session = self.current
        if not 'authcookies' in session:
            session['authcookies'] = dict()
        self.current['authcookies'][appname] = cj
        self.current['username'] = username

    def getCurrentSession(self):
        context = utils.getContext()
        return self[context.cred]

    def removeStaleSessions(self):
        now = datetime.datetime.now()
        for (sid, session) in self.items():
            delta = now - session['last_seen']
            if delta > config.session_idletimeout:
                del self[sid]
                logger.info("session %s destroyed" % sid)

    def getUserSession(self, username):
        for session in self.values():
            if session.get('username',None) == username:
                return session
        return None

    current = property(getCurrentSession)

    onAnyEvent.block = True
