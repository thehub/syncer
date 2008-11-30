import sys
import syncer
import syncer.client

session = dict ()
sessiongetter = lambda: session
u = "salfield"
p = "blablablub2"
syncerclient = syncer.client.SyncerClient("hubspace", sessiongetter)

t_id, res = syncerclient.onSignon(u, p, {})
if syncerclient.isSuccessful(res):
    print "Login as %s successful" % u
    syncerclient.setSyncerToken(res['sessionkeeper']['result'])
else:
    sys.exit(1)

udata = dict(title='Mr.')
res = syncerclient.onUserMod('salfield',1,udata.items())
print 'done'
