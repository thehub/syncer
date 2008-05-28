import datetime

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
        if sid and sid in self:
            return True
        return False

    def destroySession(self, sid):
        del self[sid]

    def _onSignon(self, u, p):
        if not self.authenticate(u, p):
            errors.raiseError(errors.authfailure)

    def rollback(self, *args, **kw):
        print self
        context = utils.getContext()
        if context.eventname == "onSignon":
            del self[context.cred]
        print self
        
    def onAnyEvent(self, *args, **kw):
        context = utils.getContext()
        if context.eventname == "onSignon":
            self.removeStaleSessions()
            ret = self._onSignon(*args[:2])
            newsession = dict (cred = context.cred)
            newsession['last_seen'] = datetime.datetime.now()
            self[context.cred] = newsession
            return context.cred
        else:
            if not self.validate(context.cred):
                errors.raiseError(errors.authfailure)
    onAnyEvent.rollback = rollback

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

    current = property(getCurrentSession)

    onAnyEvent.block = True
