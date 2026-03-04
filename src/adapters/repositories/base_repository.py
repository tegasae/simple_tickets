from utils.db.connect import Connection


class BaseRepository:
    """
    Base repository providing common database helpers.
    Reduces duplicated DB access logic in concrete repositories.
    """

    def __init__(self, conn: Connection):
        self.conn = conn

    # -------------------------
    # Query helpers
    # -------------------------

    def _get_one(self, sql: str, var: list | None = None, params: dict | None = None):

        with self.conn.create_query(sql, var=var) as q:
            return q.get_one_result(params)

    def _get_many(self, sql: str, var: list | None = None, params: dict | None = None):

        with self.conn.create_query(sql, var=var) as q:
            return q.get_result(params)

    def _execute(self, sql: str, params: dict | None = None):

        with self.conn.create_query(sql) as q:
            return q.set_result(params)

    def _exists(self, sql: str, params: dict | None = None) -> bool:

        with self.conn.create_query(sql) as q:
            row = q.get_one_result(params)

        return bool(row)

