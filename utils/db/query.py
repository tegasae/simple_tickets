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
        self.last_row_id = 0
        self.count = 0

        try:
            self._execute(params=params)
            self.count = self.cur.rowcount
            if self.cur.lastrowid:
                self.last_row_id = self.cur.lastrowid
        except Exception as e:
            raise DBOperationError(str(e))

        return self.last_row_id

    def get_result(self, params=None):
        self._execute(params=params)
        self.result = self.cur.fetchall()

        if not self.result:
            return []

        if self.var:
            return [dict(zip(self.var, row)) for row in self.result]
        else:
            return list(self.result)

    def get_one_result(self, params=None) -> Dict[str|int, Any]:
        self._execute(params=params)
        self.result = self.cur.fetchone()

        if not self.result:
            return {}  # Empty dict instead of None

        if self.var:
            return dict(zip(self.var, self.result))
        else:
            return dict(enumerate(self.result))  # Convert to dict with index keys

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
