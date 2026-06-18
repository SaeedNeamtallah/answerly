from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_db
from backend.database.models import User
from backend.security.auth import get_current_db_user
from backend.security.client_ip import get_optional_client_ip
from backend.security.event_service import log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity
from backend.services.mfa_service import mfa_service
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/auth/mfa", tags=["auth"])

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code_svg: str

class MFAVerifyRequest(BaseModel):
    token: str

class MFAVerifyResponse(BaseModel):
    success: bool
    recovery_codes: List[str] | None = None

class MFARecoveryRequest(BaseModel):
    token: str

@router.get("/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    """Generate a new MFA secret and QR code for the user."""
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled.")

    # Generate new secret (do not save until verified)
    secret = mfa_service.generate_mfa_secret()
    
    # Temporarily store secret on the user object to verify it later.
    # In a real app, this might be cached in redis until verified, but storing it here
    # with mfa_enabled=False works.
    current_user.mfa_secret = secret
    await db.commit()

    provisioning_uri = mfa_service.generate_provisioning_uri(secret, current_user.username)
    qr_code_svg = mfa_service.generate_qr_code_svg(provisioning_uri)

    return MFASetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_code_svg=qr_code_svg
    )

@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa(request: MFAVerifyRequest, current_user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    """Verify the TOTP token to complete MFA setup."""
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA is already enabled.")
    
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA setup not initiated.")

    if not mfa_service.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(status_code=400, detail="Invalid MFA token.")

    # Mark MFA as enabled and generate recovery codes
    current_user.mfa_enabled = True
    recovery_codes = mfa_service.generate_recovery_codes()
    current_user.mfa_recovery_codes = mfa_service.hash_recovery_codes(recovery_codes)
    await db.commit()

    return MFAVerifyResponse(success=True, recovery_codes=recovery_codes)

@router.post("/recovery", response_model=MFAVerifyResponse)
async def regenerate_recovery_codes(
    payload: MFARecoveryRequest,
    request: Request,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate MFA recovery codes after proving possession of TOTP or an unused recovery code."""
    if not current_user.mfa_enabled or not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not enabled.")

    verified = mfa_service.verify_totp(current_user.mfa_secret, payload.token)
    if not verified:
        recovery_accepted, remaining_codes = mfa_service.consume_recovery_code(
            current_user.mfa_recovery_codes,
            payload.token,
        )
        if recovery_accepted:
            current_user.mfa_recovery_codes = remaining_codes
            verified = True
            log_event({
                "event_type": SecurityEventType.MFA_RECOVERY_USED,
                "severity": SecuritySeverity.MEDIUM,
                "user_id": current_user.id,
                "username": current_user.username,
                "ip_address": get_optional_client_ip(request),
                "message": "MFA recovery code used to regenerate recovery codes",
                "metadata": {"username": current_user.username},
            })

    if not verified:
        log_event({
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": current_user.id,
            "username": current_user.username,
            "ip_address": get_optional_client_ip(request),
            "message": "MFA recovery-code regeneration denied",
            "metadata": {"username": current_user.username, "reason": "invalid_mfa_or_recovery_code"},
        })
        raise HTTPException(status_code=401, detail="Invalid MFA token or recovery code.")

    recovery_codes = mfa_service.generate_recovery_codes()
    current_user.mfa_recovery_codes = mfa_service.hash_recovery_codes(recovery_codes)
    await db.commit()
    log_event({
        "event_type": SecurityEventType.MFA_RECOVERY_REGENERATED,
        "severity": SecuritySeverity.MEDIUM,
        "user_id": current_user.id,
        "username": current_user.username,
        "ip_address": get_optional_client_ip(request),
        "message": "MFA recovery codes regenerated",
        "metadata": {"username": current_user.username},
    })

    return MFAVerifyResponse(success=True, recovery_codes=recovery_codes)

@router.post("/disable")
async def disable_mfa(current_user: User = Depends(get_current_db_user), db: AsyncSession = Depends(get_db)):
    """Disable MFA for the user."""
    # For security reasons, this should require a password or MFA token, 
    # but kept simple for the MVP scope
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None
    await db.commit()
    return {"message": "MFA disabled successfully."}
