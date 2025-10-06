# services/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
import logging

from src.services.uow.uowsqlite import AbstractUnitOfWork

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Base service class with common functionality
    All services should inherit from this
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, *args, **kwargs) -> T:
        """Main execution method - must be implemented by subclasses"""
        raise NotImplementedError

    def _validate_input(self, **kwargs) -> None:
        """Common input validation - can be overridden by subclasses"""
        for key, value in kwargs.items():
            if value is None:
                raise ValueError(f"Parameter '{key}' cannot be None")

    def _log_operation(self, operation: str, **details) -> None:
        """Structured logging for service operations"""
        self.logger.info(f"{operation} - {details}")