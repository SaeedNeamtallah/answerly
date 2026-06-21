"""JWT authentication helpers and FastAPI dependencies."""
from __future__ import annotations

import base64
import hashlib
import os
import time
from dataclasses import dataclass
from hmac import compare_digest
from pathlib import Path
from typing import List, Optional, Set

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.database.models import User, UserAccountStatus
from backend.security.event_service import log_event
from backend.security.client_ip import get_optional_client_ip
from backend.security.jwt_utils import create_jwt_access_token, decode_jwt_access_token
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.security.sanitization import sanitize_text
from backend.services.auth_service import AuthService


security_scheme = HTTPBearer(auto_error=False)

ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_PLATFORM_OWNER = "platform_owner"
ROLE_COMPANY_ADMIN = "company_admin"
ROLE_SECURITY_ENGINEER = "security_engineer"
ROLE_CYBERSECURITY_ENGINEER = "cybersecurity_engineer"

_ENV_FILE_PATH = Path(__file__).resolve().parents[2] / ".env"
_ENGINEER_USERNAMES_CACHE: Set[str] = set()
_ENGINEER_USERNAMES_CACHE_MTIME: float = -1.0
_ENGINEER_USERNAMES_CACHE_TS: float = 0.0
_ENGINEER_USERNAMES_CACHE_TTL_SECONDS = 2.0


class AuthUser(BaseModel):
    username: str
    roles: List[str]


@dataclass(frozen=True)
class ServiceAccountCredentials:
    username: str
    source: str
    plain_password: str | None = None
    password_hash: str | None = None


def _normalize_username(value: str) -> str:
    return sanitize_text(value, max_length=150, strip_html=True, allow_newlines=False).strip().lower()


def _normalize_role(value: str) -> str:
    clean = sanitize_text(value, max_length=64, strip_html=True, allow_newlines=False).strip().lower()
    return clean or ROLE_USER


def _configured_platform_owner_username() -> str:
    return _normalize_username(settings.platform_owner_username or "")


def get_product_role_for_user(user: User | None) -> str:
    """Return the DB-backed product role used for SaaS authorization."""
    role = sanitize_text(
        str(getattr(user, "role", "") or ""),
        max_length=64,
        strip_html=True,
        allow_newlines=False,
    ).strip().lower()
    if role in {
        ROLE_PLATFORM_OWNER,
        ROLE_COMPANY_ADMIN,
        ROLE_SECURITY_ENGINEER,
        ROLE_CYBERSECURITY_ENGINEER,
    }:
        return role
    return ROLE_COMPANY_ADMIN


async def _sync_bootstrap_platform_owner_role(db: AsyncSession, user: User) -> User:
    configured_username = _configured_platform_owner_username()
    if not configured_username:
        return user

    if _normalize_username(user.username) != configured_username:
        return user

    if get_product_role_for_user(user) == ROLE_PLATFORM_OWNER:
        return user

    user.role = ROLE_PLATFORM_OWNER
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except Exception:
        await db.rollback()
        raise

    return user


def _load_engineer_usernames_from_env_file() -> Set[str]:
    global _ENGINEER_USERNAMES_CACHE, _ENGINEER_USERNAMES_CACHE_MTIME, _ENGINEER_USERNAMES_CACHE_TS

    now = time.monotonic()
    try:
        mtime = _ENV_FILE_PATH.stat().st_mtime
    except OSError:
        return set(_ENGINEER_USERNAMES_CACHE)

    cache_is_fresh = (now - _ENGINEER_USERNAMES_CACHE_TS) < _ENGINEER_USERNAMES_CACHE_TTL_SECONDS
    if cache_is_fresh and mtime == _ENGINEER_USERNAMES_CACHE_MTIME:
        return set(_ENGINEER_USERNAMES_CACHE)

    raw_values: List[str] = []
    try:
        with _ENV_FILE_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.upper().startswith("SECURITY_ENGINEER_USERNAMES="):
                    value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        raw_values.append(value)
                if stripped.upper().startswith("SECURITY_CYBERSECURITY_ENGINEER_USERNAMES="):
                    value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        raw_values.append(value)
    except Exception:
        # Keep previous cache if .env is temporarily unreadable.
        return set(_ENGINEER_USERNAMES_CACHE)

    raw_value = ",".join(raw_values)

    refreshed: Set[str] = set()
    for chunk in raw_value.split(","):
        normalized = _normalize_username(chunk)
        if normalized:
            refreshed.add(normalized)

    _ENGINEER_USERNAMES_CACHE = refreshed
    _ENGINEER_USERNAMES_CACHE_MTIME = mtime
    _ENGINEER_USERNAMES_CACHE_TS = now
    return set(_ENGINEER_USERNAMES_CACHE)


def _configured_cybersecurity_engineer_usernames() -> Set[str]:
    configured_primary = os.getenv("SECURITY_ENGINEER_USERNAMES")
    configured_legacy = os.getenv("SECURITY_CYBERSECURITY_ENGINEER_USERNAMES")
    raw_value = ",".join(
        value.strip()
        for value in (configured_primary, configured_legacy)
        if value and value.strip()
    )

    if not raw_value:
        # Fallback to live .env value so changing .env works without restart.
        env_file_usernames = _load_engineer_usernames_from_env_file()
        if env_file_usernames:
            return env_file_usernames
        raw_value = str(settings.security_cybersecurity_engineer_usernames or "")

    usernames: Set[str] = set()

    for chunk in raw_value.split(","):
        normalized = _normalize_username(chunk)
        if normalized:
            usernames.add(normalized)

    return usernames


def resolve_roles_for_username(username: str) -> List[str]:
    normalized_username = _normalize_username(username)
    resolved_roles: List[str] = []

    if normalized_username and normalized_username == _normalize_username(settings.auth_admin_username):
        resolved_roles.append(ROLE_ADMIN)

    if normalized_username and normalized_username in _configured_cybersecurity_engineer_usernames():
        resolved_roles.append(ROLE_SECURITY_ENGINEER)
        resolved_roles.append(ROLE_CYBERSECURITY_ENGINEER)

    resolved_roles.append(ROLE_USER)

    deduplicated_roles: List[str] = []
    for role in resolved_roles:
        normalized_role = _normalize_role(role)
        if normalized_role not in deduplicated_roles:
            deduplicated_roles.append(normalized_role)

    return deduplicated_roles


def has_role(roles: List[str], required_role: str) -> bool:
    expected = _normalize_role(required_role)
    return any(_normalize_role(role) == expected for role in (roles or []))


def has_security_engineer_role(roles: List[str]) -> bool:
    return has_role(roles, ROLE_SECURITY_ENGINEER) or has_role(roles, ROLE_CYBERSECURITY_ENGINEER)


def _get_request_auth_user(request: Request) -> AuthUser | None:
    auth_user = getattr(getattr(request, "state", None), "auth_user", None)
    return auth_user if isinstance(auth_user, AuthUser) else None


def _extract_client_ip(request: Request | None) -> str | None:
    return get_optional_client_ip(request)


def _verify_pbkdf2_sha256(password: str, encoded_hash: str) -> bool:
    """Verify hashes in format: pbkdf2_sha256$iterations$salt_b64$hash_b64."""
    try:
        algo, iterations_str, salt_b64, digest_b64 = encoded_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False

        iterations = int(iterations_str)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
            dklen=len(expected),
        )
        return compare_digest(computed, expected)
    except Exception:
        return False


def _verify_admin_password(password: str) -> bool:
    if settings.auth_admin_password_hash:
        return _verify_pbkdf2_sha256(password, settings.auth_admin_password_hash)
    return compare_digest(password, settings.auth_admin_password)


def _read_explicit_env_value(name: str) -> str | None:
    raw_value = os.getenv(name)
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    return cleaned or None


def _configured_bot_service_account() -> ServiceAccountCredentials | None:
    username = _read_explicit_env_value("BOT_API_USERNAME")
    password = _read_explicit_env_value("BOT_API_PASSWORD")
    if not username or not password:
        return None

    normalized_username = _normalize_username(username)
    if not normalized_username:
        return None

    return ServiceAccountCredentials(
        username=normalized_username,
        source="bot_api",
        plain_password=password,
    )


def _configured_admin_service_account() -> ServiceAccountCredentials | None:
    password_hash = _read_explicit_env_value("AUTH_ADMIN_PASSWORD_HASH")
    password = _read_explicit_env_value("AUTH_ADMIN_PASSWORD")
    if not password_hash and not password:
        return None

    normalized_username = _normalize_username(settings.auth_admin_username)
    if not normalized_username:
        return None

    return ServiceAccountCredentials(
        username=normalized_username,
        source="auth_admin",
        plain_password=password,
        password_hash=password_hash,
    )


def get_service_account_credentials(username: str) -> ServiceAccountCredentials | None:
    normalized_username = _normalize_username(username)
    if not normalized_username:
        return None

    bot_account = _configured_bot_service_account()
    if bot_account and bot_account.username == normalized_username:
        return bot_account

    admin_account = _configured_admin_service_account()
    if admin_account and admin_account.username == normalized_username:
        return admin_account

    return None


def get_reserved_service_account_usernames() -> Set[str]:
    reserved_usernames: Set[str] = set()
    for account in (_configured_bot_service_account(), _configured_admin_service_account()):
        if account is not None and account.username:
            reserved_usernames.add(account.username)
    return reserved_usernames


def verify_service_account_password(
    service_account: ServiceAccountCredentials,
    password: str,
) -> bool:
    if service_account.password_hash:
        return _verify_pbkdf2_sha256(password, service_account.password_hash)
    if service_account.plain_password is None:
        return False
    return compare_digest(password, service_account.plain_password)


def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin credentials from environment settings."""
    service_account = get_service_account_credentials(username)
    if service_account is None or service_account.source != "auth_admin":
        return False
    return verify_service_account_password(service_account, password)


def create_access_token(username: str, roles: Optional[List[str]] = None) -> str:
    """Create short-lived JWT access token."""
    return create_jwt_access_token(
        subject=username,
        roles=roles or ["admin"],
        expires_minutes=settings.auth_access_token_expire_minutes,
    )


def _decode_access_token(token: str) -> AuthUser:
    try:
        payload = decode_jwt_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_TOKEN_INVALID,
                "severity": SecuritySeverity.MEDIUM,
                "message": "Rejected expired access token",
                "metadata": {"reason": "expired"},
            }
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.PyJWTError as exc:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_TOKEN_INVALID,
                "severity": SecuritySeverity.MEDIUM,
                "message": "Rejected invalid access token",
                "metadata": {"reason": "jwt_error"},
            }
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    username = str(payload.get("sub") or "").strip()
    roles_raw = payload.get("roles")

    if not username:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_TOKEN_INVALID,
                "severity": SecuritySeverity.MEDIUM,
                "message": "Rejected token without subject claim",
                "metadata": {"reason": "missing_sub"},
            }
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    if not isinstance(roles_raw, list) or not roles_raw:
        resolved_roles = resolve_roles_for_username(username)
    else:
        resolved_roles = []
        for role in roles_raw:
            normalized_role = _normalize_role(str(role))
            if normalized_role not in resolved_roles:
                resolved_roles.append(normalized_role)

        if ROLE_USER not in resolved_roles:
            resolved_roles.append(ROLE_USER)

    return AuthUser(
        username=username,
        roles=resolved_roles,
    )


async def _get_user_for_token_subject(
    *,
    db: AsyncSession,
    request: Request,
    token_user: AuthUser,
) -> User:
    """Resolve DB user from token subject using normalized, case-insensitive lookup."""
    normalized_username = _normalize_username(token_user.username)
    user_stmt = (
        select(User)
        .where(func.lower(User.username) == normalized_username)
        .order_by(User.id.asc())
        .limit(1)
    )
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_TOKEN_INVALID,
                "severity": SecuritySeverity.MEDIUM,
                "ip_address": _extract_client_ip(request),
                "message": "Token subject does not map to an existing user",
                "metadata": {"username": token_user.username, "path": request.url.path},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await _sync_bootstrap_platform_owner_role(db, user)


async def _enforce_account_status_policy(
    *,
    db: AsyncSession,
    request: Request,
    auth_service: AuthService,
    user: User,
) -> None:
    user_status, suspended_until, auto_restored = await auth_service.evaluate_user_status(
        db,
        user=user,
        allow_auto_restore=True,
    )

    if auto_restored:
        log_event(
            {
                "event_type": "ACCOUNT_AUTO_RESTORED",
                "severity": SecuritySeverity.LOW,
                "user_id": user.id,
                "username": user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Suspended account automatically restored after expiry",
                "metadata": {
                    "path": request.url.path,
                    "method": request.method,
                    "account_status": UserAccountStatus.ACTIVE.value,
                    "auto_restore": True,
                },
            }
        )

    if user_status == UserAccountStatus.BLOCKED:
        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "user_id": user.id,
                "username": user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Access denied for blocked account",
                "metadata": {
                    "path": request.url.path,
                    "method": request.method,
                    "account_status": user_status.value,
                    "suspended_until": (
                        suspended_until.isoformat() if suspended_until else None
                    ),
                },
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account blocked due to security violation",
        )

    if user_status == UserAccountStatus.SUSPENDED:
        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "user_id": user.id,
                "username": user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Access denied for temporarily suspended account",
                "metadata": {
                    "path": request.url.path,
                    "method": request.method,
                    "account_status": user_status.value,
                    "suspended_until": (
                        suspended_until.isoformat() if suspended_until else None
                    ),
                },
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account temporarily suspended",
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
) -> AuthUser:
    """Require and decode bearer token."""
    if credentials is None:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_REQUIRED,
                "severity": SecuritySeverity.LOW,
                "ip_address": _extract_client_ip(request),
                "message": "Authentication required but bearer token is missing",
                "metadata": {"path": request.url.path, "method": request.method},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_user = _decode_access_token(credentials.credentials)
    user = await _get_user_for_token_subject(
        db=db,
        request=request,
        token_user=token_user,
    )
    await _enforce_account_status_policy(
        db=db,
        request=request,
        auth_service=auth_service,
        user=user,
    )
    request.state.auth_user = token_user

    return token_user


async def get_current_db_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
) -> User:
    """Require bearer token, validate JWT, and fetch current user from database."""
    if credentials is None:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_REQUIRED,
                "severity": SecuritySeverity.LOW,
                "ip_address": _extract_client_ip(request),
                "message": "Authentication required but bearer token is missing",
                "metadata": {"path": request.url.path, "method": request.method},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_user = _decode_access_token(credentials.credentials)
    user = await _get_user_for_token_subject(
        db=db,
        request=request,
        token_user=token_user,
    )
    await _enforce_account_status_policy(
        db=db,
        request=request,
        auth_service=auth_service,
        user=user,
    )
    request.state.auth_user = token_user

    return user


async def require_mutation_auth_if_enabled(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[AuthUser]:
    """Conditionally enforce auth on write operations via environment flag."""
    if not settings.security_require_auth_for_mutations:
        return None

    if credentials is None:
        log_event(
            {
                "event_type": SecurityEventType.AUTH_REQUIRED,
                "severity": SecuritySeverity.LOW,
                "ip_address": _extract_client_ip(request),
                "message": "Mutation endpoint requires authentication",
                "metadata": {"path": request.url.path, "method": request.method},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _decode_access_token(credentials.credentials)


async def require_security_center_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    """Allow Security Center access only for Cybersecurity Engineer, Admin, and Platform Owner users."""
    roles = resolve_roles_for_username(current_user.username)
    product_role = get_product_role_for_user(current_user)
    if product_role not in roles:
        roles.append(product_role)

    if has_security_engineer_role(roles) or has_role(roles, ROLE_ADMIN) or has_role(roles, ROLE_PLATFORM_OWNER):
        return current_user

    log_event(
        {
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": current_user.id,
            "username": current_user.username,
            "ip_address": _extract_client_ip(request),
            "message": "Security Center access denied",
            "metadata": {
                "path": request.url.path,
                "method": request.method,
                "required_roles": [ROLE_SECURITY_ENGINEER, ROLE_ADMIN, ROLE_PLATFORM_OWNER],
                "user_roles": roles,
            },
        }
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Security Center access is restricted to security_engineer, admin, and platform_owner roles",
    )


async def require_incident_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    """Allow incidents access only for security_engineer, admin, and platform_owner roles."""
    roles = resolve_roles_for_username(current_user.username)
    product_role = get_product_role_for_user(current_user)
    if product_role not in roles:
        roles.append(product_role)

    if has_security_engineer_role(roles) or has_role(roles, ROLE_ADMIN) or has_role(roles, ROLE_PLATFORM_OWNER):
        return current_user

    log_event(
        {
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": current_user.id,
            "username": current_user.username,
            "ip_address": _extract_client_ip(request),
            "message": "Incidents access denied",
            "metadata": {
                "path": request.url.path,
                "method": request.method,
                "required_roles": [ROLE_SECURITY_ENGINEER, ROLE_ADMIN, ROLE_PLATFORM_OWNER],
                "user_roles": roles,
            },
        }
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Incidents access is restricted to security_engineer, admin, and platform_owner roles",
    )


async def require_admin_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    """Allow admin endpoints only for admin role users."""
    roles = resolve_roles_for_username(current_user.username)
    product_role = get_product_role_for_user(current_user)
    if product_role not in roles:
        roles.append(product_role)

    if has_role(roles, ROLE_ADMIN):
        return current_user

    log_event(
        {
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": current_user.id,
            "username": current_user.username,
            "ip_address": _extract_client_ip(request),
            "message": "Admin access denied",
            "metadata": {
                "path": request.url.path,
                "method": request.method,
                "required_roles": [ROLE_ADMIN],
                "user_roles": roles,
            },
        }
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access is restricted to admin role",
    )


async def require_platform_owner_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    """Allow /admin product endpoints only for platform_owner users."""
    product_role = get_product_role_for_user(current_user)
    if product_role == ROLE_PLATFORM_OWNER:
        return current_user

    log_event(
        {
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": current_user.id,
            "username": current_user.username,
            "ip_address": _extract_client_ip(request),
            "message": "Platform owner access denied",
            "metadata": {
                "path": request.url.path,
                "method": request.method,
                "required_roles": [ROLE_PLATFORM_OWNER],
                "user_role": product_role,
            },
        }
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Platform owner access is restricted to platform_owner role",
    )


async def require_company_dashboard_access(
    current_user: User = Depends(get_current_db_user),
) -> User:
    """Require an active dashboard user for company-scoped product endpoints."""
    # Account status enforcement already ran in get_current_db_user.
    return current_user
