import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import hashlib
import secrets
from hmac import compare_digest
from typing import List

from backend.config import settings

class MFAService:
    def __init__(self, issuer_name: str = "RAGMind"):
        self.issuer_name = issuer_name

    def generate_mfa_secret(self) -> str:
        """Generate a new base32 secret for TOTP."""
        return pyotp.random_base32()

    def generate_provisioning_uri(self, secret: str, username: str) -> str:
        """Generate a provisioning URI for authenticator apps."""
        return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=self.issuer_name)

    def generate_qr_code_svg(self, provisioning_uri: str) -> str:
        """Generate an SVG QR code for the provisioning URI."""
        img = qrcode.make(provisioning_uri, image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify a TOTP token against a secret."""
        if not secret or not token:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(str(token).strip(), valid_window=1)

    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """Generate a list of secure recovery codes."""
        return [f"{secrets.token_hex(4)}-{secrets.token_hex(4)}" for _ in range(count)]

    def hash_recovery_code(self, code: str) -> str:
        """Hash a recovery code for storage."""
        normalized = self.normalize_recovery_code(code)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"sha256${digest}"

    def hash_recovery_codes(self, codes: List[str]) -> List[str]:
        """Hash generated recovery codes before persisting them."""
        return [self.hash_recovery_code(code) for code in codes]

    def normalize_recovery_code(self, code: str) -> str:
        """Normalize human-entered recovery codes while keeping entropy intact."""
        return str(code or "").strip().lower().replace(" ", "")

    def verify_recovery_code(self, stored_code: str, submitted_code: str) -> bool:
        """Verify a submitted recovery code against a stored hash.

        Plain stored values are accepted for one migration cycle so older codes
        can still be consumed and invalidated.
        """
        normalized = self.normalize_recovery_code(submitted_code)
        stored = str(stored_code or "").strip().lower()
        if not normalized or not stored:
            return False
        if stored.startswith("sha256$"):
            return compare_digest(stored, self.hash_recovery_code(normalized))
        return compare_digest(stored, normalized)

    def consume_recovery_code(self, stored_codes: List[str] | None, submitted_code: str) -> tuple[bool, List[str]]:
        """Return whether a recovery code matched and the remaining stored codes."""
        if not stored_codes:
            return False, []

        remaining: List[str] = []
        consumed = False
        for stored_code in stored_codes:
            if not consumed and self.verify_recovery_code(str(stored_code), submitted_code):
                consumed = True
                continue
            remaining.append(str(stored_code))

        return consumed, remaining

mfa_service = MFAService(issuer_name=settings.auth_mfa_issuer)
