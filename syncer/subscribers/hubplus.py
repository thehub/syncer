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

    def onUserAdd(self, id, udata=None):
        cj,result = self.post('on_user_add', id=id)
        return True
    onUserAdd.block = False

    def onUserMod(self, id, udata=None):
        cj,result = self.post('on_user_change', id=id)
        return True
    onUserMod.block = True

    def onGroupJoin(self, user_id, group_id, data=None) :
        cj,result = self.post('on_group_join',user_id=user_id,group_id=group_id)
        return True
    onGroupJoin.block = False

    def onGroupLeave(self, user_id, group_id, data=None) :
        cj,result = self.post('on_group_leave',user_id=user_id,group_id=group_id)
        return True
    onGroupLeave.block = False
