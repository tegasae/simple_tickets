import logging
import time
from fastapi import FastAPI, Request
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

        # Try to get user from request state (set by the dependency)
        user = getattr(request.state, 'user', None)
        username = user.name if user else "anonymous"

        request_id = f"{method}_{url}_{int(time.time())}"

        # Log with username
        logger.info(f"START Request: User={username}, IP={client_ip}, Method={method}, Path={url}")

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        # Log completion with username
        logger.info(f"END Request: User={username}, Status={response.status_code}, Duration={process_time:.4f}s")

        return response