import logging
from .exceptions import DBConnectError, DBOperationError
from .query import Query

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, connect=None, engine=None):
        self.transaction = False
        self.connect = connect
        self.engine = engine
        self._in_transaction = False

    @classmethod
    def create_connection(cls, url="", engine=None):
        if not url or not engine:
            raise DBConnectError("URL and engine must be provided")

        if not hasattr(engine, 'connect'):
            raise DBConnectError("Engine must have a connect method")

        try:
            connect = engine.connect(url)
        except Exception as e:  # Catch broader exception
            raise DBConnectError(str(e))

        return cls(connect=connect, engine=engine)

    def create_query(self, sql="", var=None, params=None):
        return Query(sql=sql, var=var, params=params, cursor=self.connect.cursor())

    def begin_transaction(self):
        if not self._in_transaction:
            try:
                self.connect.execute("BEGIN TRANSACTION")  # Execute begin transaction
                self._in_transaction = True
                logger.debug("Transaction started")
            except Exception as e:
                raise DBOperationError(f"Failed to begin transaction: {str(e)}")

    def commit(self):
        if self._in_transaction:
            try:
                self.connect.commit()
                self._in_transaction = False
                logger.debug("Transaction committed")
            except Exception as e:
                raise DBOperationError(f"Failed to commit transaction: {str(e)}")
        else:
            logger.warning("No active transaction to commit")

    def rollback(self):
        if self._in_transaction:
            try:
                self.connect.rollback()
                self._in_transaction = False
                logger.debug("Transaction rolled back")
            except Exception as e:
                raise DBOperationError(f"Failed to rollback transaction: {str(e)}")
        else:
            logger.warning("No active transaction to rollback")

    def close(self):
        if self.connect:
            try:
                if self._in_transaction:
                    self.rollback()  # Auto-rollback on close
                self.connect.close()
                logger.debug("Connection closed")
            except Exception as e:
                raise DBConnectError(f"Failed to close connection: {str(e)}")

        # Context manager support

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
