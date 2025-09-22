import logging
from .exceptions import DBConnectError
from .query import Query

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, connect=None, engine=None):
        self.transaction = False
        self.connect = connect
        self.engine = engine

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

    def begin_transaction(self):  # Better method name
        if not self.transaction:
            self.transaction = True

    def commit(self):  # Better method name
        logger.debug("Commit transaction")
        self.connect.commit()
        if self.transaction:
            self.transaction = False

    def rollback(self):  # Better method name
        logger.debug("Rollback transaction")
        self.connect.rollback()
        if self.transaction:
            self.transaction = False

    def close(self):
        if self.connect:
            self.connect.close()
