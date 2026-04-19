"""Service layer for login abuse detection and related security event logging."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
import time

from backend.config import settings
from backend.security.event_service import log_event
from backend.security.sanitization import sanitize_text
from backend.security.security_event import SecurityEventType, SecuritySeverity


@dataclass
class BruteForceStatus:
    blocked: bool
    retry_after_seconds: int = 0


@dataclass
class FailureRegistration:
    threshold_exceeded: bool
    threshold_crossed: bool
    newly_blocked: bool
    retry_after_seconds: int
    username_failures: int
    ip_failures: int
    scope: str


class _LoginAttemptTracker:
    """Tracks failed logins by username and IP with temporary block support."""

    def __init__(
        self,
        *,
        enabled: bool,
        threshold: int,
        window_seconds: int,
        block_seconds: int,
    ) -> None:
        self.enabled = bool(enabled)
        self.threshold = max(1, int(threshold))
        self.window_seconds = max(1, int(window_seconds))
        self.block_seconds = max(0, int(block_seconds))

        self._failed_by_username: dict[str, deque[float]] = {}
        self._failed_by_ip: dict[str, deque[float]] = {}
        self._blocked_username_until: dict[str, float] = {}
        self._blocked_ip_until: dict[str, float] = {}
        self._lock = Lock()

    def _cleanup_bucket(self, bucket: deque[float], *, now: float) -> None:
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def _purge_expired_blocks(self, *, now: float) -> None:
        expired_usernames = [
            key for key, blocked_until in self._blocked_username_until.items() if blocked_until <= now
        ]
        for key in expired_usernames:
            self._blocked_username_until.pop(key, None)

        expired_ips = [key for key, blocked_until in self._blocked_ip_until.items() if blocked_until <= now]
        for key in expired_ips:
            self._blocked_ip_until.pop(key, None)

    def check_block(self, *, username_key: str, ip_key: str) -> BruteForceStatus:
        if not self.enabled:
            return BruteForceStatus(blocked=False, retry_after_seconds=0)

        now = time.monotonic()
        with self._lock:
            self._purge_expired_blocks(now=now)
            username_retry_after = int(
                max(0.0, self._blocked_username_until.get(username_key, 0.0) - now)
            )
            ip_retry_after = int(max(0.0, self._blocked_ip_until.get(ip_key, 0.0) - now))
            retry_after = max(username_retry_after, ip_retry_after)

        if retry_after <= 0:
            return BruteForceStatus(blocked=False, retry_after_seconds=0)
        return BruteForceStatus(blocked=True, retry_after_seconds=max(1, retry_after))

    def register_failure(self, *, username_key: str, ip_key: str) -> FailureRegistration:
        if not self.enabled:
            return FailureRegistration(
                threshold_exceeded=False,
                threshold_crossed=False,
                newly_blocked=False,
                retry_after_seconds=0,
                username_failures=0,
                ip_failures=0,
                scope="none",
            )

        now = time.monotonic()
        with self._lock:
            self._purge_expired_blocks(now=now)

            username_bucket = self._failed_by_username.setdefault(username_key, deque())
            ip_bucket = self._failed_by_ip.setdefault(ip_key, deque())

            self._cleanup_bucket(username_bucket, now=now)
            self._cleanup_bucket(ip_bucket, now=now)

            username_failures_before = len(username_bucket)
            ip_failures_before = len(ip_bucket)

            username_bucket.append(now)
            ip_bucket.append(now)

            username_failures = len(username_bucket)
            ip_failures = len(ip_bucket)

            username_triggered = username_failures >= self.threshold
            ip_triggered = ip_failures >= self.threshold
            threshold_exceeded = username_triggered or ip_triggered
            threshold_crossed = (
                (username_failures_before < self.threshold <= username_failures)
                or (ip_failures_before < self.threshold <= ip_failures)
            )

            scope = "none"
            if username_triggered and ip_triggered:
                scope = "username_and_ip"
            elif username_triggered:
                scope = "username"
            elif ip_triggered:
                scope = "ip"

            newly_blocked = False
            retry_after_seconds = 0

            if threshold_exceeded and self.block_seconds > 0:
                block_until = now + self.block_seconds

                if username_triggered:
                    previous = self._blocked_username_until.get(username_key, 0.0)
                    if previous <= now:
                        newly_blocked = True
                    self._blocked_username_until[username_key] = max(previous, block_until)

                if ip_triggered:
                    previous = self._blocked_ip_until.get(ip_key, 0.0)
                    if previous <= now:
                        newly_blocked = True
                    self._blocked_ip_until[ip_key] = max(previous, block_until)

                username_retry_after = int(
                    max(0.0, self._blocked_username_until.get(username_key, 0.0) - now)
                )
                ip_retry_after = int(max(0.0, self._blocked_ip_until.get(ip_key, 0.0) - now))
                retry_after_seconds = max(username_retry_after, ip_retry_after)

        return FailureRegistration(
            threshold_exceeded=threshold_exceeded,
            threshold_crossed=threshold_crossed,
            newly_blocked=newly_blocked,
            retry_after_seconds=max(0, retry_after_seconds),
            username_failures=username_failures,
            ip_failures=ip_failures,
            scope=scope,
        )

    def clear_success(self, *, username_key: str, ip_key: str) -> None:
        if not self.enabled:
            return

        with self._lock:
            self._failed_by_username.pop(username_key, None)
            self._failed_by_ip.pop(ip_key, None)
            self._blocked_username_until.pop(username_key, None)
            self._blocked_ip_until.pop(ip_key, None)


class LoginSecurityService:
    """Security service for logging and tracking login failures from auth routes."""

    def __init__(self) -> None:
        self._tracker = _LoginAttemptTracker(
            enabled=settings.security_login_bruteforce_enabled,
            threshold=settings.security_login_bruteforce_threshold,
            window_seconds=settings.security_login_bruteforce_window_seconds,
            block_seconds=settings.security_login_bruteforce_block_seconds,
        )

    @staticmethod
    def normalize_username(username: str) -> str:
        clean = sanitize_text(
            username,
            max_length=150,
            strip_html=True,
            allow_newlines=False,
        ).lower()
        return clean or "unknown"

    @staticmethod
    def normalize_ip(ip_address: str | None) -> str:
        clean = str(ip_address or "").strip()
        return clean[:128] if clean else "unknown"

    def check_block(self, *, username: str, ip_address: str | None) -> BruteForceStatus:
        return self._tracker.check_block(
            username_key=self.normalize_username(username),
            ip_key=self.normalize_ip(ip_address),
        )

    def log_blocked_attempt(
        self,
        *,
        username: str,
        ip_address: str | None,
        retry_after_seconds: int,
    ) -> None:
        normalized_username = self.normalize_username(username)
        normalized_ip = self.normalize_ip(ip_address)

        log_event(
            {
                "event_type": SecurityEventType.LOGIN_FAIL,
                "severity": SecuritySeverity.MEDIUM,
                "username": normalized_username,
                "ip_address": normalized_ip,
                "message": "Login blocked due to repeated failed attempts",
                "metadata": {
                    "username": normalized_username,
                    "reason": "temporary_block",
                    "retry_after_seconds": int(max(1, retry_after_seconds)),
                },
            }
        )

    def record_failed_login(
        self,
        *,
        username: str,
        ip_address: str | None,
        reason: str,
        message: str,
        severity: str = SecuritySeverity.MEDIUM,
    ) -> FailureRegistration:
        normalized_username = self.normalize_username(username)
        normalized_ip = self.normalize_ip(ip_address)

        log_event(
            {
                "event_type": SecurityEventType.LOGIN_FAIL,
                "severity": severity,
                "username": normalized_username,
                "ip_address": normalized_ip,
                "message": message,
                "metadata": {
                    "username": normalized_username,
                    "reason": reason,
                },
            }
        )

        failure_state = self._tracker.register_failure(
            username_key=normalized_username,
            ip_key=normalized_ip,
        )

        if failure_state.threshold_crossed or failure_state.newly_blocked:
            log_event(
                {
                    "event_type": SecurityEventType.BRUTE_FORCE,
                    "severity": SecuritySeverity.HIGH,
                    "username": normalized_username,
                    "ip_address": normalized_ip,
                    "message": "Multiple failed login attempts detected",
                    "metadata": {
                        "username": normalized_username,
                        "reason": reason,
                        "scope": failure_state.scope,
                        "threshold": self._tracker.threshold,
                        "window_seconds": self._tracker.window_seconds,
                        "block_seconds": self._tracker.block_seconds,
                        "retry_after_seconds": failure_state.retry_after_seconds,
                        "username_failures": failure_state.username_failures,
                        "ip_failures": failure_state.ip_failures,
                    },
                }
            )

        return failure_state

    def clear_success(self, *, username: str, ip_address: str | None) -> None:
        self._tracker.clear_success(
            username_key=self.normalize_username(username),
            ip_key=self.normalize_ip(ip_address),
        )


login_security_service = LoginSecurityService()
