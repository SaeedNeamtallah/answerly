"""Encryption and hashing helpers for stored integration secrets."""
from __future__ import annotations

import hashlib

from cryptography.fernet import Fernet, InvalidToken

from backend.config import settings


class SecretConfigurationError(RuntimeError):
    """Raised when a required encryption setting is missing or invalid."""


class TokenCryptoService:
    """Encrypt Telegram bot tokens and store only deterministic token hashes."""

    def __init__(self, key: str | None = None):
        self._key = (key if key is not None else settings.bot_token_encryption_key).strip()
        if not self._key:
            raise SecretConfigurationError("BOT_TOKEN_ENCRYPTION_KEY is required")
        try:
            self._fernet = Fernet(self._key.encode("utf-8"))
        except Exception as exc:
            raise SecretConfigurationError("BOT_TOKEN_ENCRYPTION_KEY must be a valid Fernet key") from exc

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode("utf-8")

    def encrypt_token(self, token: str) -> str:
        clean_token = str(token or "").strip()
        if not clean_token:
            raise ValueError("Telegram bot token is required")
        return self._fernet.encrypt(clean_token.encode("utf-8")).decode("utf-8")

    def decrypt_token(self, encrypted_token: str) -> str:
        try:
            return self._fernet.decrypt(str(encrypted_token or "").encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretConfigurationError("Stored token cannot be decrypted with the configured key") from exc

