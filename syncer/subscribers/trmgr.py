import transactions
import bases
import errors

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
        currentTransaction().owner = currentSession()['username']
    onAnyEvent.block = True

    def completeTransactions(self, tr_list):
        logger.debug("Marking Transaction(s) %s complte" % str(tr_list))
        for t_id in tr_list:
            if not t_id:
                logger.warn("Invalid Transaction ID in Transaction complete request: %s" % t_id)
                continue
            res = list(Transaction.query.filter_by(id=t_id))
            if res:
                res[0].delete()
            else:
                logger.error("No such transaction: %s" % t_id)
                return errors.syncer_transaction_failed
    completeTransactions.block = True

    def rollbackTransactions(self, tr_list):
        for t_id in tr_list:
            trs = list(Transaction.query.filter_by(id=t_id))
            tr = trs[0]
            tr.state = 3
            logger.info("Transaction %s: Begin rollback of event %s" % (t_id, tr.event_name))
            for rbdata in tr.rollback_data:
                logger.info("Transaction %s: attempting rollback for %s(%s)" % (t_id, tr.event_name, rbdata.subscriber_name))
                if not rbdata.subscriber_name in all_subscribers:
                    logger.warn("Transaction %s: subscriber %s could not be instantiated" % (t_id, rbdata.subscriber_name))
                    continue
                subscriber = all_subscribers[rbdata.subscriber_name]
                eventhandler = getattr(subscriber, tr.event_name, None)
                if eventhandler:
                    rbhandler = getattr(eventhandler, 'rollback', None)
                    if rbhandler:
                        try:
                            rbhandler(rbdata)
                        except Exception, err:
                            logger.error("Transaction %s: %s(%s) rollback failed: %s" % (t_id, tr.event_name, rbdata.subscriber_name, err))
                            # TODO alert
            logger.info("Transaction %s: Complete rollback of event %s" % (t_id, tr.event_name))
            for rbdata in tr.rollback_data: # TODO CASCADE
                rbdata.delete()
            tr.delete()
            transactions.commit()
    rollbackTransactions.block = True
