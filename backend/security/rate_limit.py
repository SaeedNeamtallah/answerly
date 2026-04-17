"""In-memory rate limiting primitives."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
import time
from typing import Deque, DefaultDict


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


class InMemoryRateLimiter:
    """Simple sliding-window limiter keyed by identity."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._events: DefaultDict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> RateLimitResult:
        now = time.monotonic()

        with self._lock:
            bucket = self._events[key]
            cutoff = now - self.window_seconds

            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                reset_seconds = int(max(1.0, self.window_seconds - (now - bucket[0])))
                return RateLimitResult(allowed=False, remaining=0, reset_seconds=reset_seconds)

            bucket.append(now)
            remaining = max(0, self.max_requests - len(bucket))
            return RateLimitResult(allowed=True, remaining=remaining, reset_seconds=self.window_seconds)
