"""User Controller.
Business logic for user CRUD operations used by auth flow.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import User


class UserController:
    """Controller for user operations."""

    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> User:
        """Create a new user record.

        Raises:
            ValueError: If email already exists.
        """
        try:
            user = User(
                email=email.strip().lower(),
                password_hash=password_hash,
                role=role,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError as exc:
            await db.rollback()
            # users.email is unique; expose a clean domain error for callers.
            raise ValueError("Email already exists") from exc
        except Exception:
            await db.rollback()
            raise

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Fetch user by normalized email."""
        stmt = select(User).where(User.email == email.strip().lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        """Fetch user by primary key user_id."""
        stmt = select(User).where(User.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
