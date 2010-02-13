import datetime, os

import bases, utils, errors, config

class SessionKeeper(dict, bases.SubscriberBase):

    def __init__(self, *args, **kw):
        bases.SubscriberBase.__init__(self, *args, **kw)
        dict.__init__(self)

    def listActiveSession(self):
        return self.items()

    def validate(self, sid):
        return bool(sid) and sid in self

    def destroyThisSession(self):
        del self[syncer_tls.sid]

    def onSignon(self, *args, **kw):
        self.removeStaleSessions()
        existing_session = None # TO BE CHANGED
        if existing_session:
            session = existing_session
        else:
            logger.debug("creating new session")
            sid = syncer_tls.sid
            newsession = dict (sid = sid)
            newsession['last_seen'] = datetime.datetime.now()
            session = newsession
            self[sid] = session
        return session['sid']
    onSignon.block = True

    def onSignoff(self):
        sid = syncer_tls.sid
        if sid in self:
            self.destroyThisSession()
        else:
            logger.warn("session %s does not exist, possibly user has signed out from elsewhere" % sid)

    def onAnyEvent(self, *args, **kw):
        sid = syncer_tls.sid
        if not self.validate(sid):
            errors.raiseError(errors.sessionnotfound)
        return True
    onAnyEvent.block = True

    def genVisitId(self, eventname, args, kw):
        if eventname == "onSignon":
            ses = self.getUserSession(args[0])
            if ses:
                return ses['sid']
            else:
                while True:
                    visit_id = os.urandom(21).encode('hex')
                    if visit_id not in self:
                        return visit_id

    def removeStaleSessions(self):
        now = datetime.datetime.now()
        for (sid, session) in self.items():
            delta = now - session['last_seen']
            if delta > config.session_idletimeout:
                del self[sid]
                logger.info("session %s destroyed" % sid)

    def getUserSession(self, username): # TODO To change to use appnames
        for session in self.values():
            if session.get('username',None) == username:
                return session
        return None

    onAnyEvent.block = True

    def __str__(self):
        return "<sessions: %s>" % super(self.__class__, self).__str__()

    def __repr__(self):
        return "<sessions: %s>" % super(self.__class__, self).__repr__()

def currentSession():
    ses = sessions.get(syncer_tls.sid, None)
    if ses == None:
        logger.warn("no session found as sid is None")
        ses = {}
    return ses
