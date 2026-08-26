"""Security headers and rate-limiting middleware for production hardening (Phase 6)."""

import time
import uuid
from typing import Dict, Tuple
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard production security headers on all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Correlation ID tracking
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        response = await call_next(request)
        
        # Inject standard security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


class LoginRateLimiterMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter to protect auth endpoints from brute-force."""

    def __init__(self, app, max_attempts: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # client_ip -> list of timestamp floats
        self.attempts: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.endswith("/auth/login") and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            
            # Prune old timestamps
            self.attempts[client_ip] = [
                ts for ts in self.attempts[client_ip] if now - ts < self.window_seconds
            ]

            if len(self.attempts[client_ip]) >= self.max_attempts:
                logger.warning(f"rate_limit_exceeded ip={client_ip} path={request.url.path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many login attempts. Please wait 60 seconds before trying again.",
                        "error": "RATE_LIMIT_EXCEEDED",
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )

            self.attempts[client_ip].append(now)

        return await call_next(request)
