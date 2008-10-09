import cookielib
import bases, utils, errors

class Knowledge(bases.WebApp):

    def makeLoginDict(self, username, password):
        vars =  dict (__ac_name = username,
                      __ac_password = password)
        vars.update({'form.submitted':1})
        return vars
        
    def onSignonSaveArgs(self, u, p, cookies):
        return (u, utils.masked, utils.masked)

    def onSignon(self, u, p, cookies):
        print "in Signon in hubspace" 
        login_url = "http://%s/login_form" % self.domainname
        cj = cookielib.CookieJar()
        for c in cookies:
            cj.set_cookie(c)
        formvars = self.makeLoginDict(u, p)
        currentSession().setdefault('authcookies', dict())
        currentSession()['authcookies'][self.name] = cj
        authcookies = self.makeHttpReq(login_url, formvars)[0]
        currentSession()['authcookies'][self.name] = authcookies
        return True

    onSignon.block = False
    onSignon.saveargs = onSignonSaveArgs


