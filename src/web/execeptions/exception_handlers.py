# src/web/core/exception_handlers.py



import importlib
import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


# FastAPI exception handler может быть sync или async.
# Здесь используем async handler, потому что это естественный стиль для FastAPI.
ExceptionHandler = Callable[[Request, Exception], JSONResponse]


class ExceptionHandlerRegistry:
    """
    Centralized registry for FastAPI exception handlers.

    Зачем нужен этот класс:
        - не писать try/except в каждом router endpoint;
        - хранить mapping exception -> HTTP status code в одном месте;
        - регистрировать исключения как явно классами, так и динамически по строкам.

    Пример явной регистрации:

        registry.add_standard_handler(DomainError, 400)
        registry.add_standard_handler(PermissionError, 403)

    Пример динамической регистрации:

        registry.add_all_handlers_from_module(
            module_name="src.domain.exceptions",
            exceptions={
                "DomainOperationError": 400,
                "ItemNotFoundError": 404,
            },
        )
    """

    def __init__(self, app: FastAPI,with_traceback=False,expose_error_type=True,log_error=False):
        self.app = app
        self._handlers: dict[type[Exception], Callable] = {}
        self.with_traceback=with_traceback
        self.log_error=log_error
        self.expose_error_type=expose_error_type

    def add_handler(
        self,
        exception_type: type[Exception],
        handler_func: Callable,
    ) -> None:
        """
        Add a custom handler for a specific exception type.

        Используй этот метод, если для исключения нужна особая логика,
        например специальный JSON body, headers, logging и т.д.
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
        Add a standard JSON handler for exception type.

        Response format:

            {
                "detail": "...",
                "error_type": "DomainOperationError"
            }

        Почему "detail":
            FastAPI сам использует поле "detail" для HTTPException,
            поэтому лучше придерживаться такого же формата.

        expose_error_type:
            True  -> добавить имя класса исключения в response.
            False -> вернуть только detail.

        log_error:
            True  -> логировать exception через logger.exception().
            False -> не логировать, если это ожидаемая бизнес-ошибка.
        """

        self._validate_exception_type(exception_type=exception_type)

        async def handler(request: Request, exc: Exception) -> JSONResponse:
            if self.log_error:
                if self.with_traceback:
                    logger.exception(
                        "Exception on %s %s",
                        request.method,
                        request.url.path,
                        exc_info=exc,
                    )
                logger.error(
                    "Exception on %s %s: %s: %s",
                    request.method,
                    request.url.path,
                    exc.__class__.__name__,
                    exc,
                )


            content: dict[str, Any] = {
                "detail": str(exc),
            }

            if self.expose_error_type:
                content["error_type"] = exc.__class__.__name__

            return JSONResponse(
                status_code=status_code,
                content=content,
            )

        self._handlers[exception_type] = handler

    def add_all_standard_handlers(self,
        *,
        exceptions: dict[type[Exception], int],
        )->None:


        for exception_type, status_code in exceptions.items():
            self.add_standard_handler(exception_type=exception_type, status_code=status_code)




    def add_all_handlers_from_module(
        self,
        *,
        module_name: str,
        exceptions: dict[str, int]
    ) -> None:
        """
        Add handlers for multiple exceptions from one module.

        exceptions example:

            {
                "DomainOperationError": 400,
                "ItemNotFoundError": 404,
                "InvalidCredentialsError": 401,
            }

        module_name example:

            "src.domain.exceptions"

        Этот метод оставляет твою идею mapping-а:
            class name as string -> HTTP status code.
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

    def register_all(self) -> None:
        """
        Register all prepared handlers in FastAPI app.

        Важно:
            Этот метод нужно вызвать один раз при создании приложения.
        """
        for exception_type, handler in self._handlers.items():
            self.app.add_exception_handler(exception_type, handler)

            logger.info(
                "Registered exception handler for %s",
                exception_type.__name__,
            )

    @staticmethod
    def _get_exception_class(
        *,
        module_name: str,
        class_name: str,
    ) -> type[Exception] | None:
        """
        Dynamically import exception class from module.

        Returns:
            exception class if found and valid;
            None otherwise.

        Почему возвращаем None:
            Чтобы один неправильный class name не ломал регистрацию всех handlers.
        """
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logger.exception(
                "Cannot import exception module: %s",
                module_name,
            )
            return None

        try:
            exception_class: Any = getattr(module, class_name)
        except AttributeError:
            logger.exception(
                "Exception class '%s' not found in module '%s'",
                class_name,
                module_name,
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

    @staticmethod
    def _validate_exception_type(exception_type: type[Exception]) -> None:
        """
        Validate manually passed exception type.

        Здесь лучше падать сразу, потому что при явной регистрации
        ошибка программиста должна быть заметна.
        """
        if not isinstance(exception_type, type):
            raise TypeError("exception_type must be an exception class")

        if not issubclass(exception_type, Exception):
            raise TypeError("exception_type must be subclass of Exception")

    @staticmethod
    def _log_exception(
            *,
            request: Request,
            exc: Exception,
            with_traceback: bool,
    ) -> None:
        """
        Log exception.

        If with_traceback=True:
            write full stack trace.

        If with_traceback=False:
            write only short error message.
        """
        if with_traceback:
            logger.exception(
                "Unhandled exception on %s %s",
                request.method,
                request.url.path,
                exc_info=exc,
            )
            return

        logger.error(
            "Unhandled exception on %s %s: %s: %s",
            request.method,
            request.url.path,
            exc.__class__.__name__,
            exc,
        )