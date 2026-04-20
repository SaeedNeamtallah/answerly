"""Security middleware for API rate limiting."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from threading import Lock
from typing import Optional, Pattern

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.config import settings
from backend.security.jwt_utils import decode_jwt_access_token
from backend.security.event_service import log_event
from backend.security.rate_limit import InMemoryRateLimiter, RateLimitResult
from backend.security.security_event import SecurityEventType, SecuritySeverity


logger = logging.getLogger(__name__)


@dataclass
class EndpointRateRule:
    """Per-endpoint throttling rule."""

    name: str
    methods: set[str]
    path_pattern: Pattern[str]
    limiter: InMemoryRateLimiter
    max_in_flight: int = 0


class SecurityRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply configurable, endpoint-focused throttling for abuse-sensitive actions."""

    def __init__(self, app):
        super().__init__(app)

        self._global_limiter: Optional[InMemoryRateLimiter] = None
        if settings.security_rate_limit_global_enabled:
            self._global_limiter = InMemoryRateLimiter(
                max_requests=settings.security_rate_limit_requests_per_window,
                window_seconds=settings.security_rate_limit_window_seconds,
            )

        self._rules: list[EndpointRateRule] = []
        if settings.security_rate_limit_chat_requests_per_window > 0:
            self._rules.append(
                EndpointRateRule(
                    name="chat",
                    methods={"POST"},
                    path_pattern=re.compile(r"^/projects/\d+/query(?:/stream)?/?$"),
                    limiter=InMemoryRateLimiter(
                        max_requests=settings.security_rate_limit_chat_requests_per_window,
                        window_seconds=settings.security_rate_limit_chat_window_seconds,
                    ),
                    max_in_flight=max(0, settings.security_rate_limit_chat_max_in_flight),
                )
            )

        if settings.security_rate_limit_upload_requests_per_window > 0:
            self._rules.append(
                EndpointRateRule(
                    name="upload",
                    methods={"POST"},
                    path_pattern=re.compile(r"^/projects/\d+/documents/?$"),
                    limiter=InMemoryRateLimiter(
                        max_requests=settings.security_rate_limit_upload_requests_per_window,
                        window_seconds=settings.security_rate_limit_upload_window_seconds,
                    ),
                    max_in_flight=max(0, settings.security_rate_limit_upload_max_in_flight),
                )
            )

        if settings.security_rate_limit_project_create_requests_per_window > 0:
            self._rules.append(
                EndpointRateRule(
                    name="project_create",
                    methods={"POST"},
                    path_pattern=re.compile(r"^/projects/?$"),
                    limiter=InMemoryRateLimiter(
                        max_requests=settings.security_rate_limit_project_create_requests_per_window,
                        window_seconds=settings.security_rate_limit_project_create_window_seconds,
                    ),
                    max_in_flight=max(0, settings.security_rate_limit_project_create_max_in_flight),
                )
            )

        if settings.security_rate_limit_login_requests_per_window > 0:
            self._rules.append(
                EndpointRateRule(
                    name="auth_login",
                    methods={"POST"},
                    path_pattern=re.compile(r"^/auth/login/?$"),
                    limiter=InMemoryRateLimiter(
                        max_requests=settings.security_rate_limit_login_requests_per_window,
                        window_seconds=settings.security_rate_limit_login_window_seconds,
                    ),
                    max_in_flight=max(0, settings.security_rate_limit_login_max_in_flight),
                )
            )

        self._exempt_paths = [
            item.strip()
            for item in settings.security_rate_limit_exempt_paths.split(",")
            if item.strip()
        ]
        self._in_flight: dict[str, int] = {}
        self._in_flight_lock = Lock()

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    @staticmethod
    def _identity_key(request: Request, fallback_ip: str) -> str:
        """Use JWT subject when present to avoid shared-IP bottlenecks."""
        authorization = request.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            if token:
                try:
                    payload = decode_jwt_access_token(token)
                    subject = str(payload.get("sub", "")).strip()
                    if subject:
                        return f"user:{subject}"
                except Exception:
                    # Keep throttling functional even for invalid/malformed tokens.
                    logger.debug("Could not derive rate-limit identity from bearer token", exc_info=True)
        return f"ip:{fallback_ip}"

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._exempt_paths)

    @staticmethod
    def _matches(rule: EndpointRateRule, method: str, path: str) -> bool:
        return method in rule.methods and bool(rule.path_pattern.match(path))

    @staticmethod
    def _rate_limit_message(rule_name: str) -> str:
        if rule_name == "chat":
            return "Too many chatbot messages. Please slow down and retry."
        if rule_name == "upload":
            return "Too many upload attempts. Please wait before uploading more files."
        if rule_name == "project_create":
            return "Too many project creation attempts. Please retry later."
        if rule_name == "auth_login":
            return "Too many login attempts. Please wait and try again."
        return "Rate limit exceeded. Please retry later."

    @staticmethod
    def _concurrency_message(rule_name: str) -> str:
        if rule_name == "upload":
            return "Too many simultaneous uploads. Please wait for current uploads to finish."
        if rule_name == "chat":
            return "Too many simultaneous chatbot requests. Please wait and retry."
        if rule_name == "project_create":
            return "Too many simultaneous project creation requests. Please wait and retry."
        if rule_name == "auth_login":
            return "Too many simultaneous login attempts. Please wait and retry."
        return "Too many simultaneous requests. Please retry shortly."

    @staticmethod
    def _rate_limit_response(detail: str, retry_after: int, rule_name: str) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": detail},
            headers={
                "Retry-After": str(max(1, retry_after)),
                "X-RateLimit-Rule": rule_name,
            },
        )

    @staticmethod
    def _event_type_for_rule(rule_name: str) -> str:
        if rule_name == "auth_login":
            return SecurityEventType.BRUTE_FORCE
        return SecurityEventType.RATE_LIMITED

    @staticmethod
    def _severity_for_rule(rule_name: str) -> str:
        if rule_name == "auth_login":
            return SecuritySeverity.HIGH
        if rule_name == "upload":
            return SecuritySeverity.MEDIUM
        return SecuritySeverity.MEDIUM

    def _log_rate_limit_event(
        self,
        *,
        request: Request,
        client_ip: str,
        identity_key: str,
        rule_name: str,
        detail: str,
        retry_after: int,
        event_type: Optional[str] = None,
    ) -> None:
        log_event(
            {
                "event_type": event_type or self._event_type_for_rule(rule_name),
                "severity": self._severity_for_rule(rule_name),
                "ip_address": client_ip,
                "message": detail,
                "metadata": {
                    "path": request.url.path,
                    "method": request.method,
                    "rule": rule_name,
                    "identity_key": identity_key,
                    "retry_after": max(1, int(retry_after)),
                },
            }
        )

    def _try_acquire_in_flight(self, key: str, max_in_flight: int) -> bool:
        if max_in_flight <= 0:
            return True
        with self._in_flight_lock:
            current = self._in_flight.get(key, 0)
            if current >= max_in_flight:
                return False
            self._in_flight[key] = current + 1
            return True

    def _release_in_flight(self, key: str) -> None:
        with self._in_flight_lock:
            current = self._in_flight.get(key, 0)
            if current <= 1:
                self._in_flight.pop(key, None)
            else:
                self._in_flight[key] = current - 1

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        if not settings.security_rate_limit_enabled or self._is_exempt(path):
            return await call_next(request)

        client_ip = self._client_ip(request)
        identity_key = self._identity_key(request, client_ip)
        matched_rules = [rule for rule in self._rules if self._matches(rule, method, path)]

        global_result: Optional[RateLimitResult] = None
        if self._global_limiter:
            global_result = self._global_limiter.check(f"global:{identity_key}")
            if not global_result.allowed:
                detail = self._rate_limit_message("global")
                self._log_rate_limit_event(
                    request=request,
                    client_ip=client_ip,
                    identity_key=identity_key,
                    rule_name="global",
                    detail=detail,
                    retry_after=global_result.reset_seconds,
                    event_type=SecurityEventType.RATE_LIMITED,
                )
                return self._rate_limit_response(
                    detail=detail,
                    retry_after=global_result.reset_seconds,
                    rule_name="global",
                )

        per_rule_results: list[tuple[EndpointRateRule, RateLimitResult]] = []
        for rule in matched_rules:
            rule_result = rule.limiter.check(f"{rule.name}:{identity_key}")
            if not rule_result.allowed:
                detail = self._rate_limit_message(rule.name)
                self._log_rate_limit_event(
                    request=request,
                    client_ip=client_ip,
                    identity_key=identity_key,
                    rule_name=rule.name,
                    detail=detail,
                    retry_after=rule_result.reset_seconds,
                )
                return self._rate_limit_response(
                    detail=detail,
                    retry_after=rule_result.reset_seconds,
                    rule_name=rule.name,
                )
            per_rule_results.append((rule, rule_result))

        acquired_locks: list[str] = []
        for rule in matched_rules:
            if rule.max_in_flight <= 0:
                continue
            lock_key = f"{rule.name}:{identity_key}"
            if not self._try_acquire_in_flight(lock_key, rule.max_in_flight):
                for acquired in acquired_locks:
                    self._release_in_flight(acquired)
                detail = self._concurrency_message(rule.name)
                self._log_rate_limit_event(
                    request=request,
                    client_ip=client_ip,
                    identity_key=identity_key,
                    rule_name=rule.name,
                    detail=detail,
                    retry_after=1,
                )
                return self._rate_limit_response(
                    detail=detail,
                    retry_after=1,
                    rule_name=rule.name,
                )
            acquired_locks.append(lock_key)

        try:
            response = await call_next(request)
        finally:
            for lock_key in acquired_locks:
                self._release_in_flight(lock_key)

        if per_rule_results:
            primary_rule, primary_result = per_rule_results[0]
            response.headers["X-RateLimit-Rule"] = primary_rule.name
            response.headers["X-RateLimit-Limit"] = str(primary_rule.limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(primary_result.remaining)
            response.headers["X-RateLimit-Reset"] = str(primary_result.reset_seconds)
        elif global_result:
            response.headers["X-RateLimit-Rule"] = "global"
            response.headers["X-RateLimit-Limit"] = str(self._global_limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(global_result.remaining)
            response.headers["X-RateLimit-Reset"] = str(global_result.reset_seconds)

        return response
