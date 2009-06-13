import datetime
from elixir import *

import errors
import config

now = datetime.datetime.now

metadata.bind = config.dburl
#metadata.bind = "postgres://shon:e@localhost/trdb"
#metadata.bind.echo = True

def commit():
    try:
        session.flush()
        session.commit()
    except:
        pass

max_tid = 1024 * 10

class Transaction(Entity):
    time = Field(DateTime, default=now)
    state = Field(Integer, default=1) # 1: Running, 2: Complete, 3: Rolling back
    owner = Field(Unicode)
    is_complete = Field(Boolean, default=False)
    event_name = Field(Unicode)
    args = Field(PickleType)
    kw = Field(PickleType)
    results = Field(PickleType, default={})
    rollback_data = OneToMany('RollbackData') # ondelete='CASCADE')
    using_options(tablename="transactions")
    def __str__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k)) for k in self.__dict__ if k[0] is not '_'))
    def __repr__(self):
        return '\n'.join(("%-10s:%s" % (k, getattr(self, k)) for k in self.__dict__ if k[0] is not '_'))

class DummyTransaction(object):
    def __init__(self, **kw):
        self.id = 0
        self.__dict__.update(kw)
    def delete(self): pass
 
def newTransaction(event, args, kw):
    if event.transactional:
        factory = Transaction
        trs = Transaction.query.filter(Transaction.time < (now() - datetime.timedelta(180)))
        for tr in trs:
            t_id = tr.id
            tr.delete()
            logger.info("Transaction %s is deleted" % t_id)
    else:
        factory = DummyTransaction
    tr = factory(event_name=event.name, args=args, kw=kw, results={})
    return tr

class RollbackData(Entity):
    subscriber_name = Field(Unicode)
    data = Field(PickleType)
    transaction = ManyToOne("Transaction")
    using_options(tablename="rollbackdata")

def currentTransaction():
    return syncer_tls.transaction

def hasFailedBefore(subscriber_name):
    for tr in Transaction.query.filter_by(state=2):
        ret = tr.results.get(subscriber_name, None)
        if ret and errors.isError(tr.results[subscriber_name]):
            return True
    return False

setup_all()
create_all()
commit()

if __name__ == '__main__':
    tr = newTransaction("someevent", [], {})
    rollback_data = RollbackData(subscriber_name="subscriber1", data={})
    objectstore.flush()
    tr.rollback_data.append(rollback_data)
    rollback_data = RollbackData(subscriber_name="subscriber2", data={})
    tr.rollback_data.append(rollback_data)
