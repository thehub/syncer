import cookielib
import bases, utils, errors

class HubSpace(bases.WebApp):

    def makeLoginDict(self, username, password):
       return dict (
            user_name = username,
            password = password,
            forward_url = "/",
            login = "Login" )
        
    def onSignonSaveArgs(self, u, p, cookies):
        return (u, utils.masked, utils.masked)

    def onSignon(self, u, p, cookies):
        login_url = "http://%s/login" % self.domainname
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

    def onUserAdd(self, username, u_data):
        useradd_url = "http://%s/load_tab?section=addMember&object_id=1&object_type=User" % (self.domainname, username)
        d = self.readForm(usermod_url)

        save_url = "http://%s/create_user" % self.domainname
        d.update(u_data)
        d['id'] = username
        self.makeHttpReq(save_url, d)
        return True

    def onUserDelete(self, username):
        userdel_url = "http://%s/delete_user" % (self.domainname)
        d = dict (username = username)
        self.makeHttpReq(userdel_url, d)
        return True
       
    def onUserChange(self, username, u_data):
        usermod_url = "http://%s/get_widget?widget_name=memberProfileEdit&object_type=User&object_id=%s" % (self.domainname, username)
        d = self.readForm(usermod_url)

        save_url = "http://%s/sync_memberProfileEdit" % self.domainname
        d.update(u_data)
        d['id'] = username
        self.makeHttpReq(save_url, d)
        return True

    onUserChange.block = True
