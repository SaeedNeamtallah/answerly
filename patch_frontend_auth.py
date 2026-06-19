import re

# 1. Patch auth-store.ts
with open('frontend-next/src/store/auth-store.ts', 'r', encoding='utf-8') as f:
    auth_store = f.read()

# Remove mfaRequired and mfaSetupRequired
auth_store = re.sub(r'    mfaRequired: boolean;\n    mfaSetupRequired: boolean;\n', '', auth_store)
auth_store = re.sub(r'        mfaRequired: false,\n        mfaSetupRequired: false,\n', '', auth_store)
auth_store = re.sub(r'                mfaRequired: false,\n                mfaSetupRequired: false,\n', '', auth_store)
auth_store = re.sub(r'                mfaRequired: data.mfa_required,\n                mfaSetupRequired: data.mfa_setup_required,\n', '', auth_store)

with open('frontend-next/src/store/auth-store.ts', 'w', encoding='utf-8') as f:
    f.write(auth_store)

# 2. Patch lib/api/auth.ts
with open('frontend-next/src/lib/api/auth.ts', 'r', encoding='utf-8') as f:
    api_auth = f.read()

api_auth = re.sub(r'export interface LoginResponse \{.*?\n\}\n', 'export interface LoginResponse {\n  access_token?: string;\n}\n', api_auth, flags=re.DOTALL)
# Delete mfa setup and verify endpoints
api_auth = re.sub(r'export const setupMfa = async \(\) => \{.*?\}\n\n', '', api_auth, flags=re.DOTALL)
api_auth = re.sub(r'export const verifyMfa = async \(code: string\) => \{.*?\}\n\n', '', api_auth, flags=re.DOTALL)
api_auth = re.sub(r'export const disableMfa = async \(\) => \{.*?\}\n', '', api_auth, flags=re.DOTALL)

with open('frontend-next/src/lib/api/auth.ts', 'w', encoding='utf-8') as f:
    f.write(api_auth)
