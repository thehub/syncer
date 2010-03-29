import sys
import syncer
import syncer.client

session = dict ()
sessiongetter = lambda: session
u = "shon"
p = "123"
syncerclient = syncer.client.SyncerClient("hubspace", sessiongetter)

t_id, res = syncerclient.onSignon(u, p, {})
if syncerclient.isSuccessful(res):
    print "Login as %s successful" % u
    syncerclient.setSyncerToken(res['sessionkeeper']['result'])
else:
    sys.exit(1)

print syncerclient.onUserMod(1)
print 'done'
