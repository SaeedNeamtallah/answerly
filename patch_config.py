import re

with open('backend/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the line `    auth_mfa_issuer: str = ...` or `    auth_mfa_issuer: str = Field(default="RAGMind", alias="AUTH_MFA_ISSUER")`
content = re.sub(r'    auth_mfa_issuer: str = Field\(default="RAGMind", alias="AUTH_MFA_ISSUER"\)\n', '', content)
content = re.sub(r'    auth_mfa_issuer: str = "RAGMind"\n', '', content)

with open('backend/config.py', 'w', encoding='utf-8') as f:
    f.write(content)
