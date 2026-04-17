"""Authentication service for user signup and credential operations."""
from __future__ import annotations

import re

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User
from backend.security.sanitization import sanitize_text


_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")
_PASSWORD_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class SignupValidationError(ValueError):
    """Raised when signup payload fails validation."""


class DuplicateUsernameError(ValueError):
    """Raised when username already exists."""


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

        user_stmt = (
            select(User)
            .where(func.lower(User.username) == normalized_username)
            .order_by(User.id.asc())
            .limit(1)
        )
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if user is None:
            return None

        if not self._verify_password(sanitized_password, user.hashed_password):
            return None

        return user

    async def signup_user(
        self,
        db: AsyncSession,
        *,
        username: str,
        password: str,
    ) -> User:
        """Create a new user account with bcrypt hashed password."""
        normalized_username = self._normalize_username(username)
        sanitized_password = self._sanitize_password_input(password)
        self._validate_password(sanitized_password)

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
