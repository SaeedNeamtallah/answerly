"""Dependency providers for FastAPI routes."""

from .auth import CurrentUser, get_current_user

__all__ = ["CurrentUser", "get_current_user"]
