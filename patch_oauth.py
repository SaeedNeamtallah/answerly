import re

with open('backend/routes/auth_oauth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove mfa_service import
content = re.sub(r'from backend\.services\.mfa_service import mfa_service\n', '', content)

# Remove user_requires_privileged_mfa import
content = content.replace(', user_requires_privileged_mfa', '')

# Remove mfa_token from GoogleLoginRequest
content = re.sub(r'    mfa_token: str \| None = None\n', '', content)

# Remove MFA verification block from google_login
mfa_block = r"""    privileged_mfa_required = user_requires_privileged_mfa\(user\)
    mfa_verified = False

    if user\.mfa_enabled:
        if not request\.mfa_token:
            return \{"access_token": None, "mfa_required": True\}
        if mfa_service\.verify_totp\(user\.mfa_secret, request\.mfa_token\):
            mfa_verified = True
        else:
            recovery_accepted, remaining_codes = mfa_service\.consume_recovery_code\(
                user\.mfa_recovery_codes,
                request\.mfa_token,
            \)
            if not recovery_accepted:
                log_event\(\{
                    "event_type": SecurityEventType\.LOGIN_FAIL,
                    "severity": SecuritySeverity\.HIGH,
                    "user_id": user\.id,
                    "username": user\.username,
                    "message": "Google login failed: invalid MFA token",
                    "metadata": \{"username": user\.username, "reason": "invalid_mfa"\},
                \}\)
                raise HTTPException\(status_code=status\.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token"\)
            user\.mfa_recovery_codes = remaining_codes
            db\.add\(user\)
            await db\.commit\(\)
            mfa_verified = True

    if privileged_mfa_required and not user\.mfa_enabled:
        setup_token = create_jwt_access_token\(
            subject=user\.username,
            roles=resolved_roles,
            expires_minutes=settings\.auth_access_token_expire_minutes,
            extra_claims=\{"mfa_verified": False, "mfa_setup_pending": True\},
        \)
        return \{"access_token": setup_token, "mfa_setup_required": True\}"""
content = re.sub(mfa_block, '', content)

# Modify create_jwt_access_token call to remove mfa_verified
content = re.sub(r'        extra_claims=\{"mfa_verified": mfa_verified\},\n    \)', r'    )', content)

with open('backend/routes/auth_oauth.py', 'w', encoding='utf-8') as f:
    f.write(content)
