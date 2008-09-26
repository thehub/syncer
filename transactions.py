import datetime
from sqlalchemy.orm import scoped_session, sessionmaker
from elixir import *

import errors

now = datetime.datetime.now

metadata.bind = "sqlite:///trdb.sqlite"
metadata.bind.echo = True
scoped_session(sessionmaker(autoflush=True, transactional=False, autocommut=True))

max_tid = 1024 * 10

class Transaction(Entity):
    t_id = Field(Integer, unique=True, primary_key=True)
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
 
def newTransaction(event_name, args, kw):
    t_ids = [tr.t_id for tr in Transaction.query.all()]
    if not t_ids:
        t_id = 1
    else:
        t_id = max(t_ids) + 1
        if t_id >= max_tid:
            trs = Transaction.query.filter(time < (now() - datetime.timedelta(180)))
            for tr in trs:
                t_id = tr.t_id
                tr.delete()
                logger.info("Transaction %s is deleted" % t_id)
            if trs:
                t_ids = [tr.id for tr in Transaction.query.all()]
                while xrange(max_tid + 1):
                    if t_id not in t_ids:
                        break
    logger.debug("Transaction %s: Begin" % t_id)
    return Transaction(t_id=t_id, event_name=event_name, args=args, kw=kw, results={})

class RollbackData(Entity):
    subscriber_name = Field(Unicode)
    data = Field(PickleType)
    transaction = ManyToOne("Transaction")
    using_options(tablename="rollbackdata")

def currentTransaction():
    return syncer_tls.transaction

def hasFailedBefore(subscriber_name):
    for tr in Transaction.query.filter(state=2):
        if errors.hasFailed(tr.results[subscriber_name]):
            return True
    return False

setup_all()
create_all()
objectstore.flush()

if __name__ == '__main__':
    tr = newTransaction("someevent", [], {})
    rollback_data = RollbackData(subscriber_name="subscriber1", data={})
    objectstore.flush()
    tr.rollback_data.append(rollback_data)
    rollback_data = RollbackData(subscriber_name="subscriber2", data={})
    tr.rollback_data.append(rollback_data)
    objectstore.flush()
