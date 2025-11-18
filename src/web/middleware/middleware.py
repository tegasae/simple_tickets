import logging
import time

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure your logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# 1. Define your middleware class
class LoggingMiddlewareOld(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        method = request.method
        url = request.url.path

        # Extract Bearer token from Authorization header
        token = self._extract_bearer_token(request)
        username = await self._get_username_from_token(token) if token else "anonymous"

        logger.info(f"START: User={username}, Method={method}, Path={url}, ClientIP={client_ip}")

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        logger.info(f"END: User={username}, Status={response.status_code}, Duration={process_time:.4f}s")
        return response

    @staticmethod
    def _extract_bearer_token(request: Request) -> str | None:
        """Extract Bearer token from Authorization header"""
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None

    @staticmethod
    async def _get_username_from_token(token: str) -> str:
        """Extract username from JWT token without full validation"""
        try:
            # Decode without verification for logging purposes only

            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "token_without_username")
        except Exception:
            return "invalid_token"




class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)

        client_ip = request.client.host
        method = request.method
        url = request.url.path

        # Extract Bearer token from Authorization header
        token = self._extract_bearer_token(request)
        username = await self._get_username_from_token(token) if token else "anonymous"

        logger.info(f"START: User={username}, Method={method}, Path={url}, ClientIP={client_ip}")

        start_time = time.perf_counter()

        # Custom send function to capture response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Log response completion
                process_time = time.perf_counter() - start_time
                status_code = message["status"]
                logger.info(f"END: User={username}, Status={status_code}, Duration={process_time:.4f}s")
            await send(message)

        await self.app(scope, receive, send_wrapper)

    @staticmethod
    def _extract_bearer_token(request: Request) -> str | None:
        """Extract Bearer token from Authorization header"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None

    @staticmethod
    async def _get_username_from_token(token: str) -> str:
        """Extract username from JWT token without full validation"""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "token_without_username")
        except Exception:
            return "invalid_token"


