import re

with open('frontend-next/src/components/layout/RoleGuard.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove isMfaSetupPendingAccessToken import
content = content.replace('isMfaSetupPendingAccessToken, ', '')

# Remove mfa redirect block
content = re.sub(r'    if \(isMfaSetupPendingAccessToken\(accessToken\)\) \{\n      window\.location\.replace\("/mfa/setup"\);\n      return;\n    \}\n\n', '', content)

# Remove mfa loading state block
content = re.sub(r'  if \(isHydrated && accessToken && isMfaSetupPendingAccessToken\(accessToken\)\) \{\n    return <LoadingState label="Preparing MFA setup\.\.\." />;\n  \}\n\n', '', content)

with open('frontend-next/src/components/layout/RoleGuard.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
