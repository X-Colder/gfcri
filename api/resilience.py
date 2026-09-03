from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    """Raised when an external dependency is temporarily open-circuited."""


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float, clock: Callable[[], float] | None = None):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1.0, float(window_seconds))
        self.clock = clock or time.monotonic
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events[key]
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        return events

    def allow(self, key: str) -> bool:
        now = self.clock()
        with self._lock:
            events = self._prune(key, now)
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True

    def retry_after(self, key: str) -> int:
        now = self.clock()
        with self._lock:
            events = self._prune(key, now)
            if not events:
                return 0
            return max(1, int(events[0] + self.window_seconds - now + 0.999))


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_seconds: float = 30,
        clock: Callable[[], float] | None = None,
    ):
        self.failure_threshold = max(1, int(failure_threshold))
        self.recovery_seconds = max(1.0, float(recovery_seconds))
        self.clock = clock or time.monotonic
        self.state = "closed"
        self.failures = 0
        self.opened_at: float | None = None
        self._lock = Lock()

    def _before_call(self) -> None:
        with self._lock:
            if self.state != "open":
                return
            if self.opened_at is not None and self.clock() - self.opened_at >= self.recovery_seconds:
                self.state = "half_open"
                return
            raise CircuitOpenError("External dependency is temporarily unavailable")

    def _record_success(self) -> None:
        with self._lock:
            self.state = "closed"
            self.failures = 0
            self.opened_at = None

    def _record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "open"
                self.opened_at = self.clock()

    def call(self, operation: Callable[[], T]) -> T:
        self._before_call()
        try:
            result = operation()
        except Exception:
            self._record_failure()
            raise
        self._record_success()
        return result
