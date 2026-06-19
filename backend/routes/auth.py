"""Authentication routes for JWT issuance and identity inspection."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.database.models import User, UserAccountStatus
from backend.services.auth_service import (
    AccountStatusError,
    AuthService,
    DuplicateUsernameError,
    SignupValidationError,
)
from backend.services.incident_management_service import IncidentManagementService
from backend.services.login_security_service import (
    FailureRegistration,
    login_security_service,
)
from backend.security.event_service import log_event
from backend.security.auth import (
    get_current_db_user,
    get_product_role_for_user,
    resolve_roles_for_username,
)
from backend.security.client_ip import get_optional_client_ip
from backend.security.jwt_utils import create_jwt_access_token
from backend.security.security_event import SecurityEventType, SecuritySeverity


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# Keep thresholds configurable from env so SOC demos can tune visibility
# without changing route logic.
_BRUTE_FORCE_LOCK_THRESHOLD = max(1, int(settings.security_login_bruteforce_threshold))
_BRUTE_FORCE_SUSPEND_THRESHOLD = _BRUTE_FORCE_LOCK_THRESHOLD + 1
_BRUTE_FORCE_BLOCK_THRESHOLD = max(
    _BRUTE_FORCE_SUSPEND_THRESHOLD + 1,
    _BRUTE_FORCE_SUSPEND_THRESHOLD * 2,
)
_BRUTE_FORCE_SUSPEND_MINUTES = 5
_PROGRESSIVE_FAILURE_DELAYS_SECONDS = {
    1: 0,
    2: 1,
    3: 3,
}


def _format_utc_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None

    normalized = value
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    else:
        normalized = normalized.astimezone(timezone.utc)

    return normalized.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _raise_bruteforce_policy_error(action: Optional[str]) -> None:
    """Map brute-force policy outcomes to explicit HTTP responses.

    Keeping this centralized preserves a single, readable decision point for
    account-state enforcement without scattering security messages in login flow.
    """
    if action == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account is blocked due to repeated failed login attempts. "
                "Please contact support."
            ),
        )

    if action == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your account is temporarily suspended for "
                f"{_BRUTE_FORCE_SUSPEND_MINUTES} minutes due to repeated failed login attempts."
            ),
        )


def _resolve_progressive_login_delay_seconds(failure_state: FailureRegistration) -> int:
    attempts = int(max(0, failure_state.username_failures))
    if attempts >= _BRUTE_FORCE_LOCK_THRESHOLD:
        return 0
    return int(_PROGRESSIVE_FAILURE_DELAYS_SECONDS.get(attempts, 0))


async def _apply_progressive_login_delay(failure_state: FailureRegistration) -> None:
    delay_seconds = _resolve_progressive_login_delay_seconds(failure_state)
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=256)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=256)
    confirm_new_password: str = Field(..., min_length=8, max_length=256)


class TokenResponse(BaseModel):
    access_token: str | None = None


class IdentityResponse(BaseModel):
    id: int
    username: str
    role: str
    roles: list[str]
    status: str
    company_name: str | None = None
    company_website: str | None = None
    created_at: datetime


class SignupResponse(BaseModel):
    message: str


def _extract_client_ip(request: Request) -> str | None:
    return get_optional_client_ip(request)


def _normalize_login_username(username: str) -> str:
    return login_security_service.normalize_username(username)


def _normalize_login_ip(ip_address: str | None) -> str:
    return login_security_service.normalize_ip(ip_address)


def _check_login_block(*, username: str, ip_address: str | None):
    return login_security_service.check_block(username=username, ip_address=ip_address)


def _log_temporary_login_block(*, username: str, ip_address: str | None, retry_after_seconds: int) -> None:
    login_security_service.log_blocked_attempt(
        username=username,
        ip_address=ip_address,
        retry_after_seconds=retry_after_seconds,
    )


def _record_failed_login_event(
    *,
    username: str,
    ip_address: str | None,
    reason: str,
    message: str,
    severity: str = SecuritySeverity.MEDIUM,
) -> FailureRegistration:
    return login_security_service.record_failed_login(
        username=username,
        ip_address=ip_address,
        reason=reason,
        message=message,
        severity=severity,
    )


def _clear_login_failures(*, username: str, ip_address: str | None) -> None:
    login_security_service.clear_success(username=username, ip_address=ip_address)


def _normalize_account_status_label(value: object) -> str:
    normalized = str(value or UserAccountStatus.ACTIVE.value).strip().upper()
    if normalized.startswith("USERACCOUNTSTATUS."):
        normalized = normalized.split(".", 1)[1]
    return normalized


async def _apply_bruteforce_account_policy(
    *,
    db: AsyncSession,
    auth_service: AuthService,
    incident_management_service: IncidentManagementService,
    tracking_username: str,
    failure_state: FailureRegistration,
) -> Optional[str]:
    # This policy upgrades repeated credential abuse to account-level controls:
    # first temporary suspension, then permanent block at a higher threshold.
    username_failures = int(max(0, failure_state.username_failures))
    if username_failures < _BRUTE_FORCE_SUSPEND_THRESHOLD:
        return None

    user_stmt = (
        select(User)
        .where(func.lower(User.username) == str(tracking_username).strip().lower())
        .order_by(User.id.asc())
        .limit(1)
    )
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if user is None:
        return None

    current_status = _normalize_account_status_label(getattr(user, "status", None))
    if username_failures >= _BRUTE_FORCE_BLOCK_THRESHOLD:
        if current_status == UserAccountStatus.BLOCKED.value:
            return "blocked"

        await incident_management_service.block_user(
            user.id,
            reason=f"bruteforce_failed_logins_{username_failures}_within_window",
            actor="system",
            db=db,
            auth_service=auth_service,
        )
        await db.commit()
        return "blocked"

    if current_status in {UserAccountStatus.BLOCKED.value, UserAccountStatus.SUSPENDED.value}:
        return None

    await incident_management_service.suspend_user(
        user.id,
        reason=f"bruteforce_failed_logins_{username_failures}_within_window",
        duration_minutes=_BRUTE_FORCE_SUSPEND_MINUTES,
        actor="system",
        db=db,
        auth_service=auth_service,
    )
    await db.commit()
    return "suspended"


@router.post("/signup", response_model=SignupResponse, status_code=201)
async def signup(
    payload: SignupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    """Create a new user account with username and password."""
    try:
        created_user = await auth_service.signup_user(
            db=db,
            username=payload.username,
            password=payload.password,
        )
        log_event(
            {
                "event_type": SecurityEventType.SIGNUP_SUCCESS,
                "severity": SecuritySeverity.LOW,
                "user_id": created_user.id,
                "username": created_user.username,
                "ip_address": _extract_client_ip(request),
                "message": "User signup succeeded",
                "metadata": {"username": created_user.username},
            }
        )
        return SignupResponse(message="User created successfully")
    except DuplicateUsernameError as exc:
        normalized_username = _normalize_login_username(payload.username)
        log_event(
            {
                "event_type": SecurityEventType.SIGNUP_FAIL,
                "severity": SecuritySeverity.MEDIUM,
                "username": normalized_username,
                "ip_address": _extract_client_ip(request),
                "message": "Signup blocked: duplicate username",
                "metadata": {"username": normalized_username, "reason": str(exc)},
            }
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SignupValidationError as exc:
        normalized_username = _normalize_login_username(payload.username)
        log_event(
            {
                "event_type": SecurityEventType.SIGNUP_FAIL,
                "severity": SecuritySeverity.MEDIUM,
                "username": normalized_username,
                "ip_address": _extract_client_ip(request),
                "message": "Signup blocked: validation failed",
                "metadata": {"username": normalized_username, "reason": str(exc)},
            }
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during signup")
        normalized_username = _normalize_login_username(payload.username)
        log_event(
            {
                "event_type": SecurityEventType.SIGNUP_FAIL,
                "severity": SecuritySeverity.HIGH,
                "username": normalized_username,
                "ip_address": _extract_client_ip(request),
                "message": "Signup failed due to internal error",
                "metadata": {"username": normalized_username},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        ) from exc


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    """Authenticate user credentials and return JWT access token."""
    client_ip = _extract_client_ip(request)
    tracking_username = _normalize_login_username(payload.username)
    tracking_ip = _normalize_login_ip(client_ip)

    try:
        block_status = _check_login_block(
            username=tracking_username,
            ip_address=tracking_ip,
        )
        if block_status.blocked:
            _log_temporary_login_block(
                username=tracking_username,
                ip_address=tracking_ip,
                retry_after_seconds=block_status.retry_after_seconds,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Too many failed login attempts. "
                    f"Please try again in {block_status.retry_after_seconds} seconds."
                ),
            )

        user = await auth_service.authenticate_user(
            db=db,
            username=payload.username,
            password=payload.password,
        )
        if user is None:
            failure_state = _record_failed_login_event(
                username=payload.username,
                ip_address=tracking_ip,
                reason="invalid_credentials",
                message="Login failed: invalid credentials",
            )
            await _apply_progressive_login_delay(failure_state)

            brute_force_action = await _apply_bruteforce_account_policy(
                db=db,
                auth_service=auth_service,
                incident_management_service=incident_management_service,
                tracking_username=tracking_username,
                failure_state=failure_state,
            )
            _raise_bruteforce_policy_error(brute_force_action)

            if failure_state.threshold_exceeded and failure_state.retry_after_seconds > 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Too many failed login attempts. "
                        f"Please try again in {failure_state.retry_after_seconds} seconds."
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        _clear_login_failures(
            username=user.username,
            ip_address=tracking_ip,
        )

        resolved_roles = resolve_roles_for_username(user.username)
        token = create_jwt_access_token(
            subject=user.username,
            roles=resolved_roles,
            expires_minutes=settings.auth_access_token_expire_minutes,
        )
        log_event(
            {
                "event_type": SecurityEventType.LOGIN_SUCCESS,
                "severity": SecuritySeverity.LOW,
                "user_id": user.id,
                "username": user.username,
                "ip_address": tracking_ip,
                "message": "Login succeeded",
                "metadata": {"username": user.username},
            }
        )
        return TokenResponse(access_token=token)
    except SignupValidationError as exc:
        failure_state = _record_failed_login_event(
            username=payload.username,
            ip_address=tracking_ip,
            reason="payload_validation",
            message="Login failed: payload validation error",
        )
        await _apply_progressive_login_delay(failure_state)

        brute_force_action = await _apply_bruteforce_account_policy(
            db=db,
            auth_service=auth_service,
            incident_management_service=incident_management_service,
            tracking_username=tracking_username,
            failure_state=failure_state,
        )
        _raise_bruteforce_policy_error(brute_force_action)

        if failure_state.threshold_exceeded and failure_state.retry_after_seconds > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Too many failed login attempts. "
                    f"Please try again in {failure_state.retry_after_seconds} seconds."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AccountStatusError as exc:
        status_label = exc.account_status.value.lower()
        suspended_until = _format_utc_timestamp(getattr(exc, "suspended_until", None))
        detail_message = "Your account is blocked. Please contact support."
        if exc.account_status.value == "SUSPENDED":
            detail_message = (
                f"Your account is suspended until {suspended_until}. Please try again after this time."
                if suspended_until
                else "Your account is temporarily suspended. Please contact support if this was unexpected."
            )

        log_event(
            {
                "event_type": SecurityEventType.AUTHZ_DENIED,
                "severity": SecuritySeverity.HIGH,
                "username": tracking_username,
                "ip_address": tracking_ip,
                "message": f"Login denied: account is {status_label}",
                "metadata": {
                    "username": tracking_username,
                    "reason": "account_status",
                    "account_status": exc.account_status.value,
                    "suspended_until": suspended_until,
                },
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_message,
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error during login")
        log_event(
            {
                "event_type": SecurityEventType.LOGIN_FAIL,
                "severity": SecuritySeverity.HIGH,
                "username": tracking_username,
                "ip_address": tracking_ip,
                "message": "Login failed due to internal error",
                "metadata": {"username": tracking_username, "reason": "internal_error"},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        ) from exc


@router.get("/me", response_model=IdentityResponse)
async def me(current_user: User = Depends(get_current_db_user)):
    """Return current authenticated user from database."""
    product_role = get_product_role_for_user(current_user)
    roles = [product_role]
    for role in resolve_roles_for_username(current_user.username):
        if role not in roles:
            roles.append(role)
    return IdentityResponse(
        id=current_user.id,
        username=current_user.username,
        role=product_role,
        roles=roles,
        status=_normalize_account_status_label(current_user.status),
        company_name=current_user.company_name,
        company_website=current_user.company_website,
        created_at=current_user.created_at,
    )


@router.post("/change-password", response_model=SignupResponse)
@router.post("/update-password", response_model=SignupResponse)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
):
    """Allow authenticated users to rotate their password securely."""
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirmation do not match",
        )

    try:
        await auth_service.change_password(
            db=db,
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        log_event(
            {
                "event_type": SecurityEventType.PASSWORD_CHANGE_SUCCESS,
                "severity": SecuritySeverity.LOW,
                "user_id": current_user.id,
                "username": current_user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Password changed successfully",
                "metadata": {"username": current_user.username},
            }
        )
        return SignupResponse(message="Password updated successfully")
    except SignupValidationError as exc:
        log_event(
            {
                "event_type": SecurityEventType.PASSWORD_CHANGE_FAIL,
                "severity": SecuritySeverity.MEDIUM,
                "user_id": current_user.id,
                "username": current_user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Password change blocked: validation failed",
                "metadata": {"username": current_user.username, "reason": str(exc)},
            }
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during password change")
        log_event(
            {
                "event_type": SecurityEventType.PASSWORD_CHANGE_FAIL,
                "severity": SecuritySeverity.HIGH,
                "user_id": current_user.id,
                "username": current_user.username,
                "ip_address": _extract_client_ip(request),
                "message": "Password change failed due to internal error",
                "metadata": {"username": current_user.username, "reason": "internal_error"},
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        ) from exc
