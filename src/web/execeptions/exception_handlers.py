# src/web/core/exception_handlers.py

from __future__ import annotations

import importlib
import logging
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


ExceptionHandler = Callable[
    [Request, Exception],
    JSONResponse | Awaitable[JSONResponse],
]


class ExceptionHandlerRegistry:
    """
    Centralized registry for FastAPI exception handlers.

    Responsibilities:
        - keep exception -> HTTP status mapping in one place;
        - register handlers explicitly by exception class;
        - register handlers dynamically by module name and class name;
        - optionally log handled exceptions;
        - optionally write traceback to logs;
        - optionally expose error type / traceback in JSON response.

    Important:
        This class does NOT automatically register handler for Exception.

        If you want catch-all behavior, register it explicitly:

            registry.add_unhandled_handler()

        or:

            registry.add_unhandled_handler(
                exception_type=Exception,
                status_code=500,
                detail="Internal server error",
            )
    """

    def __init__(
        self,
        app: FastAPI,
        *,
        with_traceback: bool = False,
        expose_traceback: bool = False,
        expose_error_type: bool = True,
        log_error: bool = False,
    ) -> None:
        self.app = app
        self._handlers: dict[type[Exception], ExceptionHandler] = {}

        # If True, traceback is written to console/logs when logging is enabled.
        self.with_traceback = with_traceback

        # If True, traceback is included into JSON response.
        # Usually should be False in production.
        self.expose_traceback = expose_traceback

        # If True, JSON response contains:
        #   "error_type": "SomeExceptionName"
        self.expose_error_type = expose_error_type

        # If True, handled exceptions are logged.
        self.log_error = log_error

    # ---------------------------------------------------------------------
    # Public registration API
    # ---------------------------------------------------------------------

    def add_handler(
        self,
        exception_type: type[Exception],
        handler_func: ExceptionHandler,
    ) -> None:
        """
        Add custom handler for a specific exception type.

        Use this when standard JSON response is not enough.
        """
        self._validate_exception_type(exception_type)
        self._handlers[exception_type] = handler_func

    def add_standard_handler(
        self,
        *,
        exception_type: type[Exception],
        status_code: int,
    ) -> None:
        """
        Add standard JSON handler for expected exceptions.

        This handler returns str(exc) as "detail".

        Good for:
            - domain errors;
            - validation errors;
            - auth errors;
            - permission errors.

        Be careful with:
            Exception

        Because for unexpected errors you usually do NOT want to expose str(exc)
        to the client.
        """
        self._validate_exception_type(exception_type)

        async def handler(request: Request, exc: Exception) -> JSONResponse:
            if self.log_error:
                self._log_exception(
                    request=request,
                    exc=exc,
                    message="Handled exception",
                )

            return JSONResponse(
                status_code=status_code,
                content=self._make_error_content(
                    exc=exc,
                    detail=str(exc),
                ),
            )

        self._handlers[exception_type] = handler


    def add_all_standard_handlers(
        self,
        *,
        exceptions: dict[type[Exception], int],
    ) -> None:
        """
        Add many handlers using exception classes directly.

        Example:

            registry.add_all_standard_handlers(
                exceptions={
                    DomainError: 400,
                    PermissionError: 403,
                }
            )
        """
        for exception_type, status_code in exceptions.items():
            self.add_standard_handler(
                exception_type=exception_type,
                status_code=status_code,
            )

    def add_all_handlers_from_module(
        self,
        *,
        module_name: str,
        exceptions: dict[str, int],
    ) -> None:
        """
        Add handlers for multiple exceptions from one module.

        Example:

            registry.add_all_handlers_from_module(
                module_name="src.domain.exceptions",
                exceptions={
                    "DomainOperationError": 400,
                    "ItemNotFoundError": 404,
                    "ItemValidationError": 400,
                },
            )
        """
        successful = 0
        failed = 0

        for class_name, status_code in exceptions.items():
            exception_class = self._get_exception_class(
                module_name=module_name,
                class_name=class_name,
            )

            if exception_class is None:
                failed += 1
                continue

            self.add_standard_handler(
                exception_type=exception_class,
                status_code=status_code,
            )

            successful += 1

            logger.info(
                "Prepared exception handler: %s.%s -> HTTP %s",
                module_name,
                class_name,
                status_code,
            )

        logger.info(
            "Exception handlers prepared from %s: %s successful, %s failed",
            module_name,
            successful,
            failed,
        )

    def add_all_handler(
        self,
        module_name: str,
        exceptions: dict[str, int],
    ) -> None:
        """
        Backward-compatible wrapper.

        Allows old style:

            registry.add_all_handler(
                "src.domain.exceptions",
                handlers,
            )
        """
        self.add_all_handlers_from_module(
            module_name=module_name,
            exceptions=exceptions,
        )

    def register_all(self) -> None:
        """
        Register all prepared handlers in FastAPI app.

        Call this once during application startup.
        """
        for exception_type, handler in self._handlers.items():
            self.app.add_exception_handler(exception_type, handler)

            logger.info(
                "Registered exception handler for %s",
                exception_type.__name__,
            )

    # ---------------------------------------------------------------------
    # Dynamic import
    # ---------------------------------------------------------------------

    def _get_exception_class(
        self,
        *,
        module_name: str,
        class_name: str,
    ) -> type[Exception] | None:
        """
        Dynamically import exception class from module.

        We return None instead of raising because one wrong class name
        should not break registration of all other handlers.
        """
        try:
            module = importlib.import_module(module_name)

        except ImportError as exc:
            self._log_registry_error(
                message=f"Cannot import exception module: {module_name}",
                exc=exc,
            )
            return None

        try:
            exception_class: Any = getattr(module, class_name)

        except AttributeError as exc:
            self._log_registry_error(
                message=(
                    f"Exception class '{class_name}' not found "
                    f"in module '{module_name}'"
                ),
                exc=exc,
            )
            return None

        if not isinstance(exception_class, type):
            logger.error(
                "%s.%s is not a class",
                module_name,
                class_name,
            )
            return None

        if not issubclass(exception_class, Exception):
            logger.error(
                "%s.%s is not an Exception subclass",
                module_name,
                class_name,
            )
            return None

        return exception_class

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def _validate_exception_type(
        exception_type: type[Exception],
    ) -> None:
        """
        Validate manually passed exception type.
        """
        if not isinstance(exception_type, type):
            raise TypeError("exception_type must be an exception class")

        if not issubclass(exception_type, Exception):
            raise TypeError("exception_type must be subclass of Exception")

    def _make_error_content(
        self,
        *,
        exc: Exception,
        detail: str,
    ) -> dict[str, Any]:
        """
        Build JSON response body.

        self.expose_error_type:
            Adds exception class name.

        self.expose_traceback:
            Adds traceback list.
            Usually should be False in production.
        """
        content: dict[str, Any] = {
            "detail": detail,
        }

        if self.expose_error_type:
            content["error_type"] = exc.__class__.__name__

        if self.expose_traceback:
            content["traceback"] = traceback.format_exception(
                type(exc),
                exc,
                exc.__traceback__,
            )

        return content

    def _log_exception(
        self,
        *,
        request: Request,
        exc: Exception,
        message: str,
    ) -> None:
        """
        Log exception.

        If self.with_traceback=True:
            write full traceback.

        If self.with_traceback=False:
            write only short error message.

        Important:
            We do not use logger.exception(), because logger.exception()
            always prints traceback.
        """
        if self.with_traceback:
            logger.error(
                "%s on %s %s",
                message,
                request.method,
                request.url.path,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            return

        logger.error(
            "%s on %s %s: %s: %s",
            message,
            request.method,
            request.url.path,
            exc.__class__.__name__,
            exc,
        )

    def _log_registry_error(
        self,
        *,
        message: str,
        exc: Exception,
    ) -> None:
        """
        Log registry configuration/import errors.

        If self.with_traceback=True:
            write full traceback.

        If self.with_traceback=False:
            write only short error message.
        """
        if self.with_traceback:
            logger.error(
                "%s",
                message,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
            return

        logger.error(
            "%s: %s: %s",
            message,
            exc.__class__.__name__,
            exc,
        )