"""Compatibility wrapper for bot-token encryption terminology used by specs."""
from __future__ import annotations

from backend.services.token_crypto_service import SecretConfigurationError, TokenCryptoService


class TokenEncryptionService(TokenCryptoService):
    """Alias around TokenCryptoService with encrypt/decrypt/hash_secret names."""

    def encrypt_secret(self, value: str) -> str:
        return self.encrypt_token(value)

    def decrypt_secret(self, value: str) -> str:
        return self.decrypt_token(value)

    def hash_secret(self, value: str) -> str:
        return self.hash_token(value)


__all__ = ["SecretConfigurationError", "TokenEncryptionService"]

