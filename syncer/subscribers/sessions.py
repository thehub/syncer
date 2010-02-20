import datetime, os

import bases, utils, errors, config

def removeCurrentSession(*args, **kw):
    session = currentSession()
    sid = session.get('sid', None)
    if sid and sid in sessions:
        del sessions[sid]
    
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
        print 'begin onSignon', `self.items()`
        self.removeStaleSessions()
        username = currentTransaction().initiator
        existing_session = self.getUserSession(username)
        if existing_session:
            session = existing_session
        else:
            logger.debug("creating new session")
            print `syncer_tls.sid`
            sid = syncer_tls.sid
            newsession = dict (sid = sid)
            newsession['last_seen'] = datetime.datetime.now()
            newsession['username'] = username
            session = newsession
            self[sid] = session
        print "end onSignon", `self.items()`    
        return session['sid']
    onSignon.block = True
    onSignon.rollback = removeCurrentSession

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
