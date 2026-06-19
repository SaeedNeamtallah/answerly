import re

with open('frontend-next/src/lib/auth/session.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the isMfaSetupPendingAccessToken check inside handleAuthenticatedRedirect
content = re.sub(r'  if \(isMfaSetupPendingAccessToken\(state\.accessToken\)\) \{\n    window\.location\.replace\("/mfa/setup"\);\n    return;\n  \}\n\n', '', content)

# Remove isMfaSetupPendingAccessToken function
content = re.sub(r'export function isMfaSetupPendingAccessToken\(token: string \| null\) \{\n  return Boolean\(decodeAccessTokenPayload\(token\)\?\.mfa_setup_pending\);\n\}\n\n', '', content)

# Remove decodeAccessTokenPayload and AccessTokenPayload
content = re.sub(r'interface AccessTokenPayload \{\n  mfa_setup_pending\?: boolean;\n\}\n\nfunction decodeAccessTokenPayload\(token: string \| null\): AccessTokenPayload \| null \{\n  if \(!token\) \{\n    return null;\n  \}\n\n  const \[, payload\] = token\.split\("\."\);\n  if \(!payload\) \{\n    return null;\n  \}\n\n  try \{\n    const normalized = payload\.replace\(/-/g, "\+"\)\.replace\(/_/g, "\/"\);\n    const padded = normalized\.padEnd\(Math\.ceil\(normalized\.length / 4\) \* 4, "="\);\n    return JSON\.parse\(globalThis\.atob\(padded\)\) as AccessTokenPayload;\n  \} catch \{\n    return null;\n  \}\n\}\n\n', '', content)

with open('frontend-next/src/lib/auth/session.ts', 'w', encoding='utf-8') as f:
    f.write(content)
