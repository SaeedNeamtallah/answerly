import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import secrets
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
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def generate_recovery_codes(self, count: int = 10) -> List[str]:
        """Generate a list of secure recovery codes."""
        # Generates a code like "a1b2c3d4"
        return [secrets.token_hex(4) for _ in range(count)]

mfa_service = MFAService(issuer_name=settings.auth_mfa_issuer)
