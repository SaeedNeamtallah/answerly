"""Provider-specific exceptions with user-safe messages."""

from __future__ import annotations


class ProviderError(RuntimeError):
    """Base error for external AI provider failures."""

    default_message = "AI provider request failed."

    def __init__(self, message: str | None = None, *, provider: str | None = None):
        self.provider = provider
        super().__init__(message or self.default_message)


class ProviderUnavailableError(ProviderError):
    """Provider network/service is temporarily unavailable."""

    default_message = "AI provider is temporarily unavailable. Please try again later."


class ProviderAuthError(ProviderError):
    """Provider credentials are missing, invalid, or unauthorized."""

    default_message = "AI provider authentication failed. Check provider credentials."


class ProviderRateLimitError(ProviderError):
    """Provider rate limit or quota was exceeded."""

    default_message = "AI provider rate limit was reached. Please try again later."


class ProviderTimeoutError(ProviderError):
    """Provider request timed out."""

    default_message = "AI provider request timed out. Please try again later."


def provider_error_payload(exc: BaseException) -> dict[str, str]:
    """Return a JSON-safe task/API payload for provider errors."""

    if isinstance(exc, ProviderError):
        return {
            "error": exc.__class__.__name__,
            "message": str(exc),
            "provider": exc.provider or "unknown",
        }
    return {
        "error": exc.__class__.__name__,
        "message": "Document processing failed. Check server logs for details.",
        "provider": "unknown",
    }
