import transactions
import bases

Transaction = transactions.Transaction

class TransactionMgr(bases.SubscriberBase):

    def onSignon(self, *args, **kw):
        """
        Do nothing
        """

    def onSignoff(self, *args, **kw):
        """
        Do nothing
        """

    def onAnyEvent(self, *args, **kw):
        return True
    onAnyEvent.block = True

    def completeTransactions(self, tr_list):
        for t_id in tr_list:
            tr = Transaction.query.filter_by(t_id=t_id)
            tr.delete()
    completeTransactions.block = False

    def rollbackTransactions(self, tr_list):
        for t_id in tr_list:
            tr = Transaction.query.filter_by(t_id=t_id)
            tr.state = 3
            logger.info("Transaction %s: Begin rollback of event %s" % (t_id, tr.event_name))
            for rbdata in tr.rollback_data:
                logger.info("Transaction %s: attempting rollback for %s(%s)" % (t_id, tr.event_name, rbdata.subscriber_name))
                if not rbdata.subscriber_name in subscribers:
                    logger.warn("Transaction %s: subscriber %s could not be instantiated" % (t_id, rbdata.subscriber_name))
                    continue
                subscriber = all_subscribers[rbdata.subscriber_name]
                handler = getattr(getattr(subscriber, tr.event_name), 'rollback')
                try:
                    handler(rbdata)
                except Exception, err:
                    logger.error("Transaction %s: %s(%s) rollback failed: %s" % (t_id, tr.event_name, rbdata.subscriber_name, err))
                    # alert
            logger.info("Transaction %s: Complete rollback of event %s" % (t_id, tr.event_name))
            for rbdata in tr.rollback_data: # TODO CASCADE
                rbdata.delete()
            tr.delete()
    rollbackTransactions.block = False
