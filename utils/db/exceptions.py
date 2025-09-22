class DBException(Exception):
    """Base exception for database operations"""
    def __init__(self, message=""):
        super().__init__(f"The DBException occurred: {message}")


class DBConnectError(DBException):
    def __init__(self, message=''):
        super().__init__(f"The connection isn't established: {message}")


class DBOperationError(DBException):
    def __init__(self, message=''):
        super().__init__(f"The operation error is: {message}")
