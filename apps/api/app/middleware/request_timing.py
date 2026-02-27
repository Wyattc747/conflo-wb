import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Threshold for slow request warnings (seconds)
SLOW_REQUEST_THRESHOLD = 2.0


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        response.headers["X-Request-Duration"] = f"{duration:.3f}"

        if duration > SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration:.2f}s"
            )

        return response
