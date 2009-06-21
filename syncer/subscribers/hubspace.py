import bases, utils, errors

class HubSpace(bases.WebApp):

    def makeLoginDict(self, username, password):
       return dict (
            user_name = username,
            password = password )

    def onUserAdd(self, username, udata):
        useradd_url = "http://%s/load_tab?section=addMember&object_id=1&object_type=User" % (self.domainname, username)
        d = self.readForm(usermod_url)

        save_url = "http://%s/create_user" % self.domainname
        d.update(udata)
        d['id'] = username
        self.makeHttpReq(save_url, d)
        return True

    def onUserDel(self, username):
        userdel_url = "http://%s/delete_user" % (self.domainname)
        d = dict (username = username)
        self.makeHttpReq(userdel_url, d)
        return True
       
    def onUserMod(self, username, udata):
        usermod_url = "http://%s/get_widget?widget_name=memberProfileEdit&object_type=User&object_id=%s" % (self.domainname, username)
        d = self.readForm(usermod_url)

        save_url = "http://%s/sync_memberProfileEdit" % self.domainname
        d.update(udata)
        d['id'] = username
        self.makeHttpReq(save_url, d)
        return True

    onUserMod.block = True
