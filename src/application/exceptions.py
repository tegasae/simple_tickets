"""Domain Exceptions Module.

This module defines custom exception classes for domain-related errors
in the application. All exceptions inherit from DomainError for consistent
error handling and reporting.
"""




class ApplicationError(Exception):

    def __init__(self, message: str):

        self.message = message
        super().__init__(self.message)



class ApplicationValidateError(ApplicationError):
    """"""


class ApplicationStoreError(ApplicationError):
    """"""

