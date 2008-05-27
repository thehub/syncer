import cookielib
import bases, utils, errors

class HubSpace(bases.WebApp):

    def ls2as(self, u_data):
        s_map = dict (
            Title = "title"
            )
        return dict ((s_map[k],v) for (k, v) in u_data.items())

    def makeLoginDict(self, username, password):
       return dict (
            user_name = username,
            password = password,
            forward_url = "/",
            login = "Login" )
        
    def onSignon(self, u, p, cookies):
        login_url = "http://%s/sync/onSignon" % self.domainname
        cj = cookielib.CookieJar()
        for c in cookies:
            cj.set_cookie(c)
        formvars = self.makeLoginDict(u, p)
        sessions.current.setdefault('authcookies', dict())
        sessions.current['authcookies'][self.name] = cj
        authcookies = self.makeHttpReq(login_url, formvars)[0]
        sessions.current['authcookies'][self.name] = authcookies

        save_url = "http://%s/savesyncertoken" % self.domainname
        formvars = dict(syncertoken = sessions.current["cred"])
        self.makeHttpReq(save_url, formvars)

        return True

    onSignon.block = True

    def onUserChange(self, username, u_data):
        sync_url = "http://%s/hello" % self.domainname
        
        usermod_url = "http://%s/get_widget?widget_name=memberProfileEdit&object_type=User&object_id=%s" % (self.domainname, username)
        d = self.readForm(usermod_url)

        save_url = "http://%s/sync_memberProfileEdit" % self.domainname
        u_data = self.ls2as(u_data)
        d.update(u_data)
        d['id'] = username
        self.makeHttpReq(save_url, d)

        return True
    onUserChange.block = True
