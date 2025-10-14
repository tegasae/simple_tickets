# core/exception_handlers.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from functools import wraps
from typing import Callable, Any, Dict, Optional
import logging

from src.domain.exceptions import AdminError

logger = logging.getLogger(__name__)


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in route handlers.
    Use this on individual route functions.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Let the global exception handlers deal with it
            logger.debug(f"Exception in {func.__name__}: {str(e)}")
            raise

    return wrapper


class ExceptionHandler:
    """Centralized exception handling"""

    # Map domain exceptions to HTTP status codes
    DOMAIN_EXCEPTION_MAP = {
        "AdminNotFoundError": 404,
        "AdminAlreadyExistsError": 409,
        "AdminValidationError": 400,
        "AdminOperationError": 400,
        "DomainException": 400
    }

    @classmethod
    def register_handlers(cls, app: FastAPI):
        """Register all exception handlers"""

        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return cls._handle_http_exception(request, exc)

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return cls._handle_validation_error(request, exc)

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            return cls._handle_general_exception(request, exc)

        # Register domain exceptions
        from src.domain.exceptions import AdminError
        @app.exception_handler(AdminError)
        async def domain_exception_handler(request: Request, exc: AdminError):
            return cls._handle_domain_exception(request, exc)

    @staticmethod
    def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        logger.warning(
            f"HTTP error: {exc.status_code} - {exc.detail}",
            extra={"path": request.url.path, "method": request.method}
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error",
                    "path": str(request.url.path),
                    "method": request.method
                }
            }
        )

    @staticmethod
    def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors"""
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={"path": request.url.path, "method": request.method}
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": 422,
                    "message": "Request validation failed",
                    "type": "validation_error",
                    "details": exc.errors(),
                    "path": str(request.url.path),
                    "method": request.method
                }
            }
        )

    @staticmethod
    def _handle_domain_exception(request: Request, exc: AdminError) -> JSONResponse:
        """Handle domain exceptions"""
        status_code = ExceptionHandler.DOMAIN_EXCEPTION_MAP.get(
            exc.__class__.__name__, 400
        )

        logger.warning(
            f"Domain exception: {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
            }
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": status_code,
                    "message": exc.message,
                    "type": exc.error_code,
                    "details": exc.details,
                    "path": str(request.url.path),
                    "method": request.method
                }
            }
        )

    @staticmethod
    def _handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other exceptions"""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={"path": request.url.path, "method": request.method},
            exc_info=True
        )

        # Don't expose internal details in production
        error_message = "Internal server error"

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": error_message,
                    "type": "internal_error",
                    "path": str(request.url.path),
                    "method": request.method
                }
            }
        )


# Router-level exception handler (optional)
def with_exception_handling(router):
    """Add exception handling to all routes in a router"""
    for route in router.routes:
        if hasattr(route, 'endpoint'):
            original_endpoint = route.endpoint
            route.endpoint = handle_exceptions(original_endpoint)
    return router