import time
from typing import Dict, Any, Tuple

from .exceptions import DBOperationError


class Query:
    def __init__(self, sql="", var=None, params: dict = None, cursor=None):
        self.sql = sql
        self.params = params
        self.var = var
        self.last_row_id = 0
        self.cur = cursor
        self.result = None
        self.count = 0

    def _execute(self, params: dict = None):
        if params:
            self.params = params

        try:
            if self.params:
                self.cur.execute(self.sql, self.params)
            else:
                self.cur.execute(self.sql)
        except Exception as e:  # Catch broader exception
            raise DBOperationError(str(e))

    def set_result(self, params: dict = None):
        try:

            self.last_row_id = 0
            self.count = 0

            self._execute(params=params)
            self.count = self.cur.rowcount
            if self.cur.lastrowid:
                self.last_row_id = self.cur.lastrowid
            return self.last_row_id
        except Exception as e:
            raise DBOperationError(str(e))

    def get_result(self, params=None):
        try:
            #start_time=time.time()
            self._execute(params=params)
            self.result = self.cur.fetchall()

            if not self.result:
                return []

            if self.var:
                r=[dict(zip(self.var, row)) for row in self.result]
            else:
                r=list(self.result)
            #end_time = time.time()
            #print(end_time - start_time)
            return r


        except Exception as e:  # Catch exceptions from both _execute AND fetchall
            raise DBOperationError(str(e))

    def get_one_result(self, params=None) -> Dict[str | int, Any]:
        try:
            self._execute(params=params)
            self.result = self.cur.fetchone()

            if not self.result:
                return {}  # Empty dict instead of None

            if self.var:
                return dict(zip(self.var, self.result))
            else:
                return dict(enumerate(self.result))  # Convert to dict with index keys

        except Exception as e:  # Catch exceptions from both _execute AND fetchall
            raise DBOperationError(str(e))

    def get_one_result_tuple(self, params=None) -> Tuple:
        """Alternative method that returns empty tuple instead of None"""
        self._execute(params=params)
        self.result = self.cur.fetchone()

        if not self.result:
            return ()  # Empty tuple instead of None

        return self.result

    def close(self):
        if self.cur:
            self.cur.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
