"""Authentication routes for JWT issuance and identity inspection."""
from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.database.models import User
from backend.services.auth_service import AuthService, DuplicateUsernameError, SignupValidationError
from backend.services.login_security_service import (
    FailureRegistration,
    login_security_service,
)
from backend.security.event_service import log_event
from backend.security.auth import get_current_db_user, resolve_roles_for_username
from backend.security.jwt_utils import create_jwt_access_token
from backend.security.security_event import SecurityEventType, SecuritySeverity


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


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
    access_token: str


class IdentityResponse(BaseModel):
    id: int
    username: str
    role: str
    roles: list[str]
    created_at: datetime


class SignupResponse(BaseModel):
    message: str


def _extract_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip() or None
    if request.client and request.client.host:
        return request.client.host
    return None


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

        token = create_jwt_access_token(
            subject=user.username,
            roles=resolve_roles_for_username(user.username),
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
    roles = resolve_roles_for_username(current_user.username)
    return IdentityResponse(
        id=current_user.id,
        username=current_user.username,
        role=roles[0] if roles else "user",
        roles=roles,
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
