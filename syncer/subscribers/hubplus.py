import bases, utils, errors

import simplejson as json

# XXX following shouldn't be hardwired in
url_base = 'http://plusdev-app.the-hub.net:8000/synced/'

class HubPlus(bases.WebApp):

    loginurl_tmpl = 'http://%s/login/'

    def makeLoginDict(self, username, password):
       return dict (
            username = username,
            password = password )


    def post(self, event, **kwargs) :
        # this is a placeholder 
        # to-do
        # handle if error comes back ({'OK':False,'msg':'error message'})
        print "received %s" % event
        xs = self.makeHttpReq(url_base+event+'/', {'json':json.dumps(kwargs)})
        print xs
        return xs

    def onUserCreate(self, username, udata=None):
        cj,result = self.post('on_user_create', username=username)
        return True
    onUserCreate.block = True

    def onUserMod(self, username, udata=None):
        cj,result = self.post('on_user_change', username=username)
        return True
    onUserMod.block = True

    def onGroupJoin(self, username, group_id, data=None) :
        cj,result = self.post('on_group_join',username=username,group_id=group_id)
        return True
    onGroupJoin.block = True

    def onGroupLeave(self, username, group_id, data=None) :
        cj,result = self.post('on_group_leave',username=username,group_id=group_id)
        return True
    onGroupLeave.block = True
