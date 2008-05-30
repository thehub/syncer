from string import Template

import Pyro

default_err_tmpl = "Syncer error#$intcode"

success = (0, "Success")
authfailure = (1, "Authentication failed")
sessionnotfound = (2, "Expired Or Invalid Session")
syncer_conn_failed = (3, "Syncer connection failed")
app_conn_failed = (5, "$appname connection failed")
app_write_failed = (7, "$appname modification failed")
app_backlog_not_empty = (8, "$appname sync not attempted as previous sync(s) failed")

def raiseError(err_tuple, **errdata):
    raise Exception(err_tuple, errdata)

def getError(err_tuple, **errdata):
    return Exception(err_tuple, errdata)

def hasFailed(result):
    if isinstance(result, Exception):
        return True
    for handler_res in result.values():
        try:
            if handler_res['retcode'][0] != success:
                return True
        except:
            return True
    return False

def err2str(err):
    print err
    if isinstance(err, Exception):
        print '============================='
        print ''.join(Pyro.util.getPyroTraceback(err))
        print '============================='
        return "Remote eception"
    err_tuple, errdata = err['retcode']
    errdata.update(intcode=err_tuple[0])
    try:
        template = err_tuple[1]
    except IndexError:
        template = default_err_tmpl
    return "%-12s %s" % ("(%s)" % err['appname'], Template(template).safe_substitute(errdata))
