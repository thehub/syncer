import bases, utils, errors

try:
    import json
except ImportError:
    import simplejson as json


class HubSpace(bases.WebApp):
    #loginurl_tmpl = 'http://%s/public/login' # new
    loginurl_tmpl = 'http://%s/login' # old
        
    def makeLoginDict(self, username, password):
       return dict (
            user_name = username,
            password = password, )

    def makeJsonReq(self, url, postdata):
        """
        postdata: dict
        """
        cj, content = self.makeHttpReq(url, postdata)
        ret = json.loads(content)
        if ret['error']:
            errors.raiseError(ret['error'])
        return ret

    #def onLogout(self, username)

    def onUserAdd(self, id):
        url = "http://%s/onuseradd" % (self.domainname)
        d = dict(id = id)
        print "hubspace heard onUserAdd : %s" % d
        print self.makeJsonReq(url, d)
        return True

    def onUserMod(self,id):
        url = "http://%s/onusermod" % (self.domainname)
        d = dict(id = id)
        print "hubspace heard onUserMod : %s" % d
        print self.makeJsonReq(url, d)
        return True

    def onLocationAdd(self, id):
        url = "http://%s/onlocationadd " % (self.domainname)
        d = dict(id = id)
        print "hubspace heard onLocationAdd : %s" % d
        print self.makeJsonReq(url, d)
        return True

    def onLocationRename(self, new_name, old_name):
        url = "http://%s/onlocatiorename" % (self.domainname)
        d = dict(new_name = new_name, old_name = old_name)
        print "hubspace heard onLocationRename : %s" % d
        print self.makeJsonReq(url, d)
        return True
