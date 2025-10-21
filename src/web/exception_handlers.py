# core/exception_handlers.py
import importlib

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from functools import wraps
from typing import Callable, Any, Dict, Optional
import logging

from src.domain.exceptions import AdminError

logger = logging.getLogger(__name__)


class ExceptionHandlerRegistry:
    def __init__(self, app: FastAPI):
        self.app = app
        self._handlers = {}

    def add_handler(self, exception_type, handler_func):
        """Add a handler for specific exception type"""
        self._handlers[exception_type] = handler_func

    def register_all(self):
        """Register all handlers with the FastAPI app"""
        for exception_type, handler in self._handlers.items():
            self.app.exception_handler(exception_type)(handler)

    def add_standard_handler(self, exception_type, code: int):
        self._handlers[exception_type] = lambda request, exc: JSONResponse(status_code=code,
                                                                           content={"error": str(exc)})

    @staticmethod
    def _get_exception_class(module_name: str, class_name: str):
        """
        Get exception class from module by name

        Args:
            module_name: Name of the module (e.g., "domain.exceptions")
            class_name: Name of the exception class (e.g., "AdminAlreadyExistsError")

        Returns:
            Exception class or None if not found
        """
        try:
            # Import the module
            module = importlib.import_module(module_name)
            # Get the class from the module
            exception_class = getattr(module, class_name)

            # Verify it's an exception class
            if issubclass(exception_class, Exception):
                return exception_class
            else:
                print(f"Warning: {class_name} is not an Exception subclass")
                return None

        except ImportError:
            print(f"Error: Module '{module_name}' not found")
            return None
        except AttributeError:
            print(f"Error: Class '{class_name}' not found in module '{module_name}'")
            return None

    def add_all_handler(self, module_name: str, exceptions: Dict):
        """Add handlers for multiple exceptions from a module"""
        successful = 0
        failed = 0

        for class_name, status_code in exceptions.items():
            exception_class = self._get_exception_class(module_name, class_name)
            if exception_class:
                self.add_standard_handler(exception_class, status_code)
                successful += 1
                logger.info(f"Registered handler for {class_name} -> {status_code}")
            else:
                failed += 1
                logger.error(f"Failed to register handler for {class_name}")

        logger.info(f"Exception handlers: {successful} successful, {failed} failed")



