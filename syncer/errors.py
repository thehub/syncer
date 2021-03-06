from string import Template

import Pyro

default_err_tmpl = "Syncer error#$intcode"

success = (0, "Success")
authfailure = (1, "Authentication failed")
sessionnotfound = (2, "Expired Or Invalid Session")
syncer_conn_failed = (3, "Syncer connection failed")
syncer_client_disabled = (4, "Syncer client disabled")
syncer_transaction_failed = (5, "Trasaction failure")
app_conn_failed = (5, "$appname connection failed")
app_write_failed = (7, "$appname modification failed")
app_backlog_not_empty = (8, "$appname sync not attempted as previous sync(s) failed")

def raiseError(err_tuple, **errdata):
    raise Exception(err_tuple, errdata)

def getError(err_tuple, **errdata):
    return Exception(err_tuple, errdata)

def getClientError(err_tuple, **errdata):
    d = dict (appname = 'syncerclient')
    d['retcode'] = err_tuple
    d['result'] = getError(err_tuple, **errdata)
    return -1, dict (clienterror = d)

def isError(status):
    try:
        if status['retcode'] != success:
            return True
    except:
        return True

def hasFailed(result):
    if isinstance(result, Exception):
        return True
    if isinstance(result, dict):
        result = result.values()
    for handler_res in result:
        if isError(handler_res):
            return True
    return False

def res2errstr(result, sep="\n"):
    if isinstance(result, Exception):
        return "Remote exception" + ''.join(Pyro.util.getPyroTraceback(result))
    return sep.join([err2str(handler_res) for handler_res in result.values() if handler_res['retcode'] != success])

def err2str(err):
    if isinstance(err, (Exception, str)):
        return "Remote exception" + ''.join(Pyro.util.getPyroTraceback(err))
    err_tuple = err['retcode']
    err.update(intcode=err_tuple[0])
    try:
        template = err_tuple[1]
    except IndexError:
        template = default_err_tmpl
    return "%-12s %s: %s" % ("(%s)" % err['appname'], Template(template).safe_substitute(err), err['result'] or "")
