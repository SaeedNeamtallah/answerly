import re

with open('backend/security/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove from AuthUser model
content = content.replace(
    'class AuthUser(BaseModel):\n    username: str\n    roles: List[str]\n    mfa_verified: bool = False\n    mfa_setup_pending: bool = False',
    'class AuthUser(BaseModel):\n    username: str\n    roles: List[str]'
)

# 2. Remove user_requires_privileged_mfa function
pattern_user_requires_mfa = r"def user_requires_privileged_mfa\(user: User \| None\) -> bool:.*?return \(\n.*?has_role\(roles, ROLE_PLATFORM_OWNER\)\n    \)\n\n\n"
content = re.sub(pattern_user_requires_mfa, "", content, flags=re.DOTALL)

# 3. Remove _enforce_privileged_mfa_policy function
pattern_enforce_mfa = r"def _enforce_privileged_mfa_policy\(\*, request: Request, user: User\) -> None:.*?raise HTTPException\(\n            status_code=status\.HTTP_403_FORBIDDEN,\n            detail=\"MFA verification required before privileged access\",\n        \)\n\n\n"
content = re.sub(pattern_enforce_mfa, "", content, flags=re.DOTALL)

# 4. Remove mfa_verified from AuthUser instantiation in _decode_access_token
pattern_authuser_inst = r"    return AuthUser\(\n        username=username,\n        roles=resolved_roles,\n        mfa_verified=bool\(payload\.get\(\"mfa_verified\"\)\),\n        mfa_setup_pending=bool\(payload\.get\(\"mfa_setup_pending\"\)\),\n    \)"
content = re.sub(pattern_authuser_inst, "    return AuthUser(\n        username=username,\n        roles=resolved_roles,\n    )", content, flags=re.DOTALL)

# 5. Remove calls to _enforce_privileged_mfa_policy in the dependency guards
content = content.replace(
    '    _enforce_privileged_mfa_policy(request=request, user=current_user)\n',
    ''
)

with open('backend/security/auth.py', 'w', encoding='utf-8') as f:
    f.write(content)
