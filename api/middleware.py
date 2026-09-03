from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api.resilience import SlidingWindowLimiter


class ResilienceMiddleware(BaseHTTPMiddleware):
    """Protect the single API worker with cheap in-process backpressure."""

    heavy_prefixes = (
        "/api/v1/institutional/analysis-runs",
        "/api/inference",
        "/api/stress-test",
        "/api/reports",
        "/api/causal-discovery",
    )

    def __init__(self, app, general_limit: int = 120, heavy_limit: int = 5):
        super().__init__(app)
        self.general_limiter = SlidingWindowLimiter(general_limit, 60)
        self.heavy_limiter = SlidingWindowLimiter(heavy_limit, 60)
        self.global_slots = asyncio.Semaphore(16)
        self.heavy_slots = asyncio.Semaphore(2)

    @staticmethod
    def _client_key(request: Request) -> str:
        api_key = request.headers.get("x-api-key")
        authorization = request.headers.get("authorization")
        if api_key:
            return "api:" + hashlib.sha256(api_key.encode()).hexdigest()[:24]
        if authorization:
            return "auth:" + hashlib.sha256(authorization.encode()).hexdigest()[:24]
        return "ip:" + (request.client.host if request.client else "unknown")

    @staticmethod
    def _error_response(code: str, message: str, retry_after: int, request_id: str) -> JSONResponse:
        response = JSONResponse(
            status_code=429 if code == "RATE_LIMITED" else 503,
            content={
                "code": code,
                "message": message,
                "retry_after_seconds": retry_after,
                "request_id": request_id,
            },
            headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
        )
        return response

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        path = request.url.path
        if path in {"/api/health", "/api/billing/webhook", "/api/billing/waffo/webhook"}:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        key = self._client_key(request)
        limiter = self.heavy_limiter if path.startswith(self.heavy_prefixes) else self.general_limiter
        if not limiter.allow(key):
            return self._error_response(
                "RATE_LIMITED",
                "Too many requests. Please retry shortly.",
                limiter.retry_after(key),
                request_id,
            )

        heavy = path.startswith(self.heavy_prefixes)
        if self.global_slots.locked() or (heavy and self.heavy_slots.locked()):
            return self._error_response(
                "CAPACITY_LIMIT",
                "The service is busy. Your request was not lost; please retry shortly.",
                5,
                request_id,
            )

        await self.global_slots.acquire()
        if heavy:
            await self.heavy_slots.acquire()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            if heavy:
                self.heavy_slots.release()
            self.global_slots.release()
