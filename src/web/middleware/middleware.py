import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure your logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# 1. Define your middleware class
class LoggingMiddleware(BaseHTTPMiddleware):
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
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub", "token_without_username")
        except Exception:
            return "invalid_token"