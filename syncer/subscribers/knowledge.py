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

    def onSignon(self, u, p, cookies=[]):
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

    def onUserMod(self,username,data):
        print 'in onUserMod in knowledge'
        #Note that this browser view does not send edit events!
        save_url = 'http://%s/Members/%s/modifyUserBySyncer' % (self.domainname,username)
        self.makeHttpReq(save_url, data)
        #I think we need to check here
        return True

    def onUserAdd(self,username,data):
        print 'in onUserAdd in knowledge'
        data['addUserName'] = username
        add_url = 'http://%s/Members/addUserBySyncer' % (self.domainname)
        self.makeHttpReq(add_url, data)
        #I think we need to check here
        return True

    def onUserDel(self,username):
        print 'in onUserDel in knowledge'
        data = dict(delUserName = username)
        del_url = 'http://%s/Members/delUserBySyncer' % (self.domainname)
        self.makeHttpReq(del_url, data)
        #I think we need to check here
        return True

    onUserMod.block = True
    onUserAdd.block = True
    onUserDel.block = True

    onSignon.block = False
    
    onSignon.saveargs = onSignonSaveArgs


