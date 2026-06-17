from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from backend.database import get_db
from backend.database.models import User, UserRole, UserAccountStatus
from backend.services.auth_service import AuthService
from backend.services.oauth_service import OAuthService
from backend.security.jwt_utils import create_jwt_access_token

router = APIRouter(prefix="/auth", tags=["OAuth & Recovery"])

class GoogleLoginRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/google/login")
async def google_login(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    idinfo = OAuthService.verify_google_token(request.token)
    if not idinfo:
        raise HTTPException(status_code=400, detail="Invalid Google token")
        
    email = idinfo.get("email")
    google_id = idinfo.get("sub")
    name = idinfo.get("name", "")
    
    if not email or not google_id:
        raise HTTPException(status_code=400, detail="Incomplete Google profile")

    # Check if user exists by email or google_id
    result = await db.execute(select(User).where((User.email == email) | (User.google_id == google_id)))
    user = result.scalars().first()
    
    if not user:
        # Create a new user since one doesn't exist
        # Make a safe, unique username
        base_username = email.split('@')[0]
        safe_username = "".join(c for c in base_username if c.isalnum() or c in "_.-")
        if not safe_username or len(safe_username) < 3:
            safe_username = "user_" + str(uuid.uuid4())[:8]
            
        # Ensure username uniqueness
        existing_username = await db.execute(select(User).where(User.username == safe_username))
        if existing_username.scalar_one_or_none():
            safe_username = f"{safe_username}_{str(uuid.uuid4())[:4]}"
            
        user = User(
            username=safe_username,
            email=email,
            hashed_password=None,
            auth_provider="google",
            google_id=google_id,
            role=UserRole.COMPANY_ADMIN.value,
            status=UserAccountStatus.ACTIVE.value
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update existing user if needed
        if not user.google_id:
            user.google_id = google_id
            user.auth_provider = "google"
            await db.commit()
            
    if user.status != UserAccountStatus.ACTIVE.value:
        raise HTTPException(status_code=403, detail="Account is not active")
        
    access_token = create_jwt_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    # We still send success to prevent email enumeration, but we only send email if user exists
    if user:
        token = OAuthService.create_reset_token(user.email)
        OAuthService.send_reset_email(user.email, token)
        
    return {"message": "If that email is in our system, we have sent a reset link."}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = OAuthService.verify_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = AuthService._hash_password(request.new_password)
    user.auth_provider = "local" # Once they reset password, they can login locally
    await db.commit()
    
    return {"message": "Password reset successfully"}
