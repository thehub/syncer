import bases, utils, errors

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

    def _onSignon(self, u, p):
        if not self.authenticate(u, p):
            errors.raiseError(errors.authfailure)

    def onAnyEvent(self, *args, **kw):
        context = utils.getContext()
        if context.eventname == "onSignon":
            ret = self._onSignon(*args[:2])
            self[context.cred] = dict (cred = context.cred)
            return context.cred
        else:
            if not self.validate(context.cred):
                errors.raiseError(errors.authfailure)

    def getCurrentSession(self):
        context = utils.getContext()
        return self[context.cred]

    current = property(getCurrentSession)

    onAnyEvent.block = True
