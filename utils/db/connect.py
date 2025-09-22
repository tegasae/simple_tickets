import logging
from .exceptions import DBConnectError, DBOperationError
from .query import Query

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, connect=None, engine=None):
        self._in_transaction = False
        self.connect = connect
        self.engine = engine
        self._is_closed = False

    @classmethod
    def create_connection(cls, url="", engine=None) -> 'Connection':
        if not url or not engine:
            raise DBConnectError("URL and engine must be provided")

        if not hasattr(engine, 'connect'):
            raise DBConnectError("Engine must have a connect method")

        try:
            connect = engine.connect(url)
            return cls(connect=connect, engine=engine)
        except Exception as e:
            raise DBConnectError(f"Failed to connect to {url}: {str(e)}")

    def create_query(self, sql="", var=None, params=None) -> Query:
        if self._is_closed:
            raise DBConnectError("Connection is closed")

        if not self.connect:
            raise DBConnectError("No active connection")

        return Query(sql=sql, var=var, params=params, cursor=self.connect.cursor())

    def begin_transaction(self) -> bool:
        """Returns True if transaction started, False if already in transaction"""
        if self._is_closed:
            raise DBConnectError("Connection is closed")

        if not self._in_transaction:
            try:
                self.connect.execute("BEGIN TRANSACTION")
                self._in_transaction = True
                logger.debug("Transaction started")
                return True
            except Exception as e:
                raise DBOperationError(f"Failed to begin transaction: {str(e)}")
        return False

    def commit(self) -> bool:
        """Returns True if committed, False if no transaction was active"""
        if self._is_closed:
            raise DBConnectError("Connection is closed")

        if self._in_transaction:
            try:
                self.connect.commit()
                self._in_transaction = False
                logger.debug("Transaction committed")
                return True
            except Exception as e:
                raise DBOperationError(f"Failed to commit transaction: {str(e)}")
        else:
            logger.warning("No active transaction to commit")
            return False

    def rollback(self) -> bool:
        """Returns True if rolled back, False if no transaction was active"""
        if self._is_closed:
            raise DBConnectError("Connection is closed")

        if self._in_transaction:
            try:
                self.connect.rollback()
                self._in_transaction = False
                logger.debug("Transaction rolled back")
                return True
            except Exception as e:
                raise DBOperationError(f"Failed to rollback transaction: {str(e)}")
        else:
            logger.warning("No active transaction to rollback")
            return False

    def close(self) -> bool:
        """Returns True if closed successfully, False if already closed"""
        if self._is_closed:
            return False

        if self.connect:
            try:
                if self._in_transaction:
                    self.rollback()
                self.connect.close()
                self._is_closed = True
                logger.debug("Connection closed")
                return True
            except Exception as e:
                raise DBConnectError(f"Failed to close connection: {str(e)}")
        return False

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return not self._is_closed and self.connect is not None

    def in_transaction(self) -> bool:
        """Check if currently in transaction"""
        return self._in_transaction

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
