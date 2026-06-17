"""OAuth and password reset services."""
import logging
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from datetime import datetime, timedelta, timezone

from backend.config import settings

logger = logging.getLogger(__name__)

class OAuthService:
    @staticmethod
    def verify_google_token(token: str) -> Optional[dict]:
        """Verify Google ID token and return user info if valid."""
        try:
            # Specify the CLIENT_ID of the app that accesses the backend
            client_id = settings.google_client_id
            if not client_id:
                logger.warning("GOOGLE_CLIENT_ID is not configured. OAuth will fail.")
                return None
                
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
            return idinfo
        except ValueError as e:
            logger.warning(f"Invalid Google token: {e}")
            return None

    @staticmethod
    def create_reset_token(email: str) -> str:
        """Create a short-lived JWT for password reset."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode = {"sub": email, "exp": expire, "type": "password_reset"}
        encoded_jwt = jwt.encode(to_encode, settings.auth_jwt_secret_key, algorithm=settings.auth_jwt_algorithm)
        return encoded_jwt

    @staticmethod
    def verify_reset_token(token: str) -> Optional[str]:
        """Verify reset token and return email if valid."""
        try:
            payload = jwt.decode(token, settings.auth_jwt_secret_key, algorithms=[settings.auth_jwt_algorithm])
            if payload.get("type") != "password_reset":
                return None
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            logger.warning("Reset token expired.")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid reset token.")
            return None

    @staticmethod
    def send_reset_email(email: str, token: str):
        """Send password reset email."""
        reset_link = f"{settings.public_webhook_base_url.replace('/api', '')}/reset-password?token={token}"
        
        if settings.brevo_api_key:
            import httpx
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": settings.brevo_api_key,
                "content-type": "application/json"
            }
            data = {
                "sender": {"email": settings.smtp_from_email, "name": "RAGMind"},
                "to": [{"email": email}],
                "subject": "Reset Your Password - RAGMind",
                "htmlContent": f"<p>Click the following link to reset your password:</p><p><a href='{reset_link}'>{reset_link}</a></p><p>If you did not request this, please ignore this email.</p>"
            }
            try:
                # Fire and forget or block briefly
                with httpx.Client() as client:
                    response = client.post(url, headers=headers, json=data)
                    response.raise_for_status()
                logger.info(f"Reset email sent to {email} via Brevo API")
                return
            except Exception as e:
                logger.error(f"Failed to send reset email to {email} via Brevo API: {e}")
                return
                
        if not settings.smtp_server or not settings.smtp_username:
            logger.info("SMTP is not configured. Printing reset link to console:")
            logger.info(f"--- PASSWORD RESET LINK FOR {email} ---")
            logger.info(reset_link)
            logger.info("---------------------------------------")
            return
            
        import smtplib
        from email.message import EmailMessage
        
        msg = EmailMessage()
        msg.set_content(f"Click the following link to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.")
        msg["Subject"] = "Reset Your Password - RAGMind"
        msg["From"] = settings.smtp_from_email
        msg["To"] = email
        
        try:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            logger.info(f"Reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send reset email to {email}: {e}")
