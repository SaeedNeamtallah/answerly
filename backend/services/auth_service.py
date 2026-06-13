"""Authentication service for user signup and credential operations."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import User, UserAccountStatus
from backend.security.sanitization import sanitize_text

_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")
_PASSWORD_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class SignupValidationError(ValueError):
    """Raised when signup payload fails validation."""


class DuplicateUsernameError(ValueError):
    """Raised when username already exists."""


class AccountStatusError(ValueError):
    """Raised when account is blocked or suspended."""

    def __init__(
        self,
        account_status: UserAccountStatus,
        *,
        suspended_until: datetime | None = None,
    ):
        self.account_status = account_status
        self.suspended_until = suspended_until

        if account_status == UserAccountStatus.SUSPENDED and suspended_until is not None:
            detail = f"Account is suspended until {suspended_until.isoformat()}"
        elif account_status == UserAccountStatus.BLOCKED:
            detail = "Account is blocked"
        else:
            detail = f"Account is {account_status.value.lower()}"

        super().__init__(detail)


class AuthService:
    """Service layer for authentication related operations."""

    @staticmethod
    def _normalize_username(username: str) -> str:
        cleaned = sanitize_text(
            username,
            max_length=150,
            strip_html=True,
            allow_newlines=False,
        ).lower()

        if not cleaned:
            raise SignupValidationError("Username is required")

        if not _USERNAME_RE.match(cleaned):
            raise SignupValidationError(
                "Username must be 3-50 chars and contain only lowercase letters, numbers, ., _, or -"
            )

        return cleaned

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise SignupValidationError("Password must be at least 8 characters")

        # bcrypt accepts up to 72 bytes; limit before hashing to avoid silent truncation.
        if len(password.encode("utf-8")) > 72:
            raise SignupValidationError("Password is too long")

        if password != password.strip():
            raise SignupValidationError("Password cannot start or end with spaces")

        if _PASSWORD_CONTROL_CHAR_RE.search(password):
            raise SignupValidationError("Password contains invalid control characters")

    @staticmethod
    def _sanitize_password_input(password: str) -> str:
        if password is None:
            raise SignupValidationError("Password is required")

        cleaned = str(password)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        if not cleaned:
            raise SignupValidationError("Password is required")

        if _PASSWORD_CONTROL_CHAR_RE.search(cleaned):
            raise SignupValidationError("Password contains invalid control characters")

        return cleaned

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def _verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            return False

    @staticmethod
    def _get_reserved_service_account_usernames() -> set[str]:
        from backend.security.auth import get_reserved_service_account_usernames

        return get_reserved_service_account_usernames()

    @staticmethod
    def _get_service_account_credentials(username: str):
        from backend.security.auth import get_service_account_credentials

        return get_service_account_credentials(username)

    @staticmethod
    def _verify_service_account_password(service_account, password: str) -> bool:
        from backend.security.auth import verify_service_account_password

        return verify_service_account_password(service_account, password)

    async def _get_user_by_normalized_username(
        self,
        db: AsyncSession,
        *,
        normalized_username: str,
    ) -> User | None:
        user_stmt = (
            select(User)
            .where(func.lower(User.username) == normalized_username)
            .order_by(User.id.asc())
            .limit(1)
        )
        user_result = await db.execute(user_stmt)
        return user_result.scalar_one_or_none()

    async def _sync_service_account_user(
        self,
        db: AsyncSession,
        *,
        normalized_username: str,
        password: str,
        existing_user: User | None,
    ) -> User:
        managed_password_hash = self._hash_password(password)
        user = existing_user

        if user is None:
            user = User(
                username=normalized_username,
                hashed_password=managed_password_hash,
            )
        else:
            user.username = normalized_username
            user.hashed_password = managed_password_hash

        db.add(user)

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            user = await self._get_user_by_normalized_username(
                db,
                normalized_username=normalized_username,
            )
            if user is None:
                raise

            if not self._verify_password(password, user.hashed_password):
                user.hashed_password = self._hash_password(password)
                db.add(user)
                try:
                    await db.commit()
                except Exception:
                    await db.rollback()
                    raise

            await db.refresh(user)
            return user
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    def _normalize_account_status(value: UserAccountStatus | str | None) -> UserAccountStatus:
        if isinstance(value, UserAccountStatus):
            return value

        raw = str(value or UserAccountStatus.ACTIVE.value).strip().upper()
        try:
            return UserAccountStatus(raw)
        except ValueError:
            return UserAccountStatus.ACTIVE

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_datetime_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _normalize_status_reason(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = sanitize_text(
            value,
            max_length=255,
            strip_html=True,
            allow_newlines=False,
        ).strip()
        return cleaned or None

    @staticmethod
    def _normalize_status_changed_by(value: int | str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, int):
            return str(value)

        cleaned = sanitize_text(
            str(value),
            max_length=64,
            strip_html=True,
            allow_newlines=False,
        ).strip()
        return cleaned or None

    async def evaluate_user_status(
        self,
        db: AsyncSession,
        *,
        user: User,
        allow_auto_restore: bool = True,
    ) -> tuple[UserAccountStatus, datetime | None, bool]:
        """Return effective status and optionally auto-restore expired suspensions."""
        account_status = self._normalize_account_status(getattr(user, "status", None))
        suspended_until = self._normalize_datetime_utc(getattr(user, "suspended_until", None))

        if account_status == UserAccountStatus.SUSPENDED:
            is_expired = (
                suspended_until is not None
                and self._now_utc() > suspended_until
            )
            if allow_auto_restore and is_expired:
                user.status = UserAccountStatus.ACTIVE
                user.suspended_until = None
                user.status_reason = "suspension_expired_auto_restore"
                user.status_updated_at = self._now_utc()
                user.status_changed_by = "system"
                db.add(user)
                await db.flush()
                return UserAccountStatus.ACTIVE, None, True
            return account_status, suspended_until, False

        # Ensure non-suspended users do not keep stale suspension timestamps.
        if suspended_until is not None:
            user.suspended_until = None
            db.add(user)
            await db.flush()

        return account_status, None, False

    async def authenticate_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
    ) -> User | None:
        """Authenticate a user against stored bcrypt credentials."""
        normalized_username = self._normalize_username(username)
        sanitized_password = self._sanitize_password_input(password)

        user = await self._get_user_by_normalized_username(
            db,
            normalized_username=normalized_username,
        )

        suspension_expired = False
        if user is not None:
            account_status, suspended_until, _ = await self.evaluate_user_status(
                db,
                user=user,
                allow_auto_restore=False,
            )

            suspension_expired = (
                account_status == UserAccountStatus.SUSPENDED
                and suspended_until is not None
                and self._now_utc() > suspended_until
            )

            if account_status == UserAccountStatus.BLOCKED:
                raise AccountStatusError(account_status)

            if account_status == UserAccountStatus.SUSPENDED and not suspension_expired:
                raise AccountStatusError(
                    account_status,
                    suspended_until=suspended_until,
                )

            if self._verify_password(sanitized_password, user.hashed_password):
                # Apply automatic suspension lift only after successful credential validation.
                if suspension_expired:
                    user.status = UserAccountStatus.ACTIVE
                    user.suspended_until = None
                    user.status_reason = "suspension_expired_after_successful_login"
                    user.status_updated_at = self._now_utc()
                    user.status_changed_by = "system"
                    db.add(user)
                    await db.flush()

                return user

        service_account = self._get_service_account_credentials(normalized_username)
        if service_account is None:
            return None

        if not self._verify_service_account_password(service_account, sanitized_password):
            return None

        if user is not None and suspension_expired:
            user.status = UserAccountStatus.ACTIVE
            user.suspended_until = None
            user.status_reason = "suspension_expired_after_successful_login"
            user.status_updated_at = self._now_utc()
            user.status_changed_by = "system"
            db.add(user)
            await db.flush()

        return await self._sync_service_account_user(
            db,
            normalized_username=normalized_username,
            password=sanitized_password,
            existing_user=user,
        )

    async def signup_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
        role: str = "company_admin",
        parent_id: int | None = None,
    ) -> User:
        """Create a new user account with bcrypt hashed password."""
        normalized_username = self._normalize_username(username)
        sanitized_password = self._sanitize_password_input(password)
        self._validate_password(sanitized_password)

        if normalized_username in self._get_reserved_service_account_usernames():
            raise SignupValidationError(
                "Username is reserved for a configured service account"
            )

        existing_stmt = (
            select(User.id)
            .where(func.lower(User.username) == normalized_username)
            .order_by(User.id.asc())
            .limit(1)
        )
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
            raise DuplicateUsernameError("Username already exists")

        user = User(
            username=normalized_username,
            hashed_password=self._hash_password(sanitized_password),
            role=role,
            parent_id=parent_id,
            status=UserAccountStatus.ACTIVE,
        )
        db.add(user)

        try:
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError as exc:
            await db.rollback()
            raise DuplicateUsernameError("Username already exists") from exc
        except Exception:
            await db.rollback()
            raise

    async def set_user_status(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: UserAccountStatus,
        suspension_minutes: int | None = None,
        suspended_until: datetime | None = None,
        status_reason: str | None = None,
        status_changed_by: int | str | None = None,
    ) -> User:
        """Update user account status without committing the transaction."""
        user_stmt = select(User).where(User.id == int(user_id)).limit(1)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        normalized_status = self._normalize_account_status(status)
        user.status = normalized_status
        user.status_updated_at = self._now_utc()
        user.status_changed_by = self._normalize_status_changed_by(status_changed_by) or "system"

        if normalized_status == UserAccountStatus.SUSPENDED:
            resolved_expiry = self._normalize_datetime_utc(suspended_until)
            if resolved_expiry is None:
                resolved_minutes = (
                    int(suspension_minutes)
                    if suspension_minutes is not None
                    else int(settings.security_user_suspension_default_minutes)
                )
                if resolved_minutes <= 0:
                    raise ValueError("Suspension duration must be a positive number of minutes")
                resolved_expiry = self._now_utc() + timedelta(minutes=resolved_minutes)

            if resolved_expiry <= self._now_utc():
                raise ValueError("Suspension expiry must be in the future")

            user.suspended_until = resolved_expiry
            user.status_reason = (
                self._normalize_status_reason(status_reason)
                or "temporary_security_suspension"
            )
        else:
            # ACTIVE and BLOCKED do not carry temporary suspension windows.
            user.suspended_until = None
            if normalized_status == UserAccountStatus.BLOCKED:
                user.status_reason = (
                    self._normalize_status_reason(status_reason)
                    or "confirmed_malicious_activity"
                )
            else:
                user.status_reason = self._normalize_status_reason(status_reason)

        db.add(user)
        await db.flush()
        return user

    async def change_password(
        self,
        db: AsyncSession,
        *,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change an existing user's password after validating current credentials."""
        sanitized_current_password = self._sanitize_password_input(current_password)
        sanitized_new_password = self._sanitize_password_input(new_password)
        self._validate_password(sanitized_new_password)

        if self._normalize_username(user.username) in self._get_reserved_service_account_usernames():
            raise SignupValidationError(
                "Password for this account is managed by service-account configuration"
            )

        if not self._verify_password(sanitized_current_password, user.hashed_password):
            raise SignupValidationError("Current password is incorrect")

        if self._verify_password(sanitized_new_password, user.hashed_password):
            raise SignupValidationError("New password must be different from current password")

        user.hashed_password = self._hash_password(sanitized_new_password)
        db.add(user)

        try:
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()
            raise
