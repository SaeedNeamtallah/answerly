import re

with open('backend/routes/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove user_requires_privileged_mfa import
content = content.replace(
    '    resolve_roles_for_username,\n    user_requires_privileged_mfa,\n)',
    '    resolve_roles_for_username,\n)'
)

# 2. Remove mfa_token from LoginRequest
content = content.replace(
    '    username: str = Field(..., min_length=1, max_length=128)\n    password: str = Field(..., min_length=1, max_length=256)\n    mfa_token: str | None = None',
    '    username: str = Field(..., min_length=1, max_length=128)\n    password: str = Field(..., min_length=1, max_length=256)'
)

# 3. Remove mfa_required and mfa_setup_required from TokenResponse
content = content.replace(
    '    access_token: str | None = None\n    mfa_required: bool = False\n    mfa_setup_required: bool = False',
    '    access_token: str | None = None'
)

# 4. Remove MFA block from login
# From: `        privileged_mfa_required = user_requires_privileged_mfa(user)`
# To the end of `if privileged_mfa_required and not user.mfa_enabled:` block.
pattern = r"        privileged_mfa_required = user_requires_privileged_mfa\(user\).*?token = create_jwt_access_token\(\n            subject=user\.username,\n            roles=resolved_roles,\n            expires_minutes=settings\.auth_access_token_expire_minutes,\n            extra_claims=\{\"mfa_verified\": mfa_verified\},\n        \)"
replacement = r"""        token = create_jwt_access_token(
            subject=user.username,
            roles=resolved_roles,
            expires_minutes=settings.auth_access_token_expire_minutes,
        )"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('backend/routes/auth.py', 'w', encoding='utf-8') as f:
    f.write(content)
