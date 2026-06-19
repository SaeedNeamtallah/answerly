import re

with open('frontend-next/src/app/(auth)/login/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove mfa state variables
content = re.sub(r'  const \[mfaRequired, setMfaRequired\] = useState\(false\);\n  const \[mfaToken, setMfaToken\] = useState\(""\);\n', '', content)

# Remove mfa_setup_pending redirect
content = re.sub(r'      if \(isMfaSetupPendingAccessToken\(accessToken\)\) \{\n        router\.replace\("/mfa/setup"\);\n        return;\n      \}\n', '', content)

# Remove isMfaSetupPendingAccessToken import
content = re.sub(r'isMfaSetupPendingAccessToken, ', '', content)

# Remove mfa login response handling
mfa_login_resp = r"""      if \(payload\.mfa_required\) \{
        setMfaRequired\(true\);
        return;
      \}
      if \(payload\.mfa_setup_required\) \{
        setAccessToken\(payload\.access_token as string\);
        toast\.message\("MFA setup is required before privileged access"\);
        router\.push\("/mfa/setup"\);
        return;
      \}
"""
content = re.sub(mfa_login_resp, '', content)

# Remove mfa input form block
mfa_input = r"""          \{mfaRequired && \(
            <div className="space-y-1\.5">
              <label className="text-sm font-medium text-slate-700">MFA Token</label>
              <Input
                placeholder="123456"
                className="h-11"
                value=\{mfaToken\}
                onChange=\{\(e\) => setMfaToken\(e\.target\.value\)\}
              />
            </div>
          \)\}\n\n"""
content = re.sub(mfa_input, '', content)

# Update Login Button
old_btn = r'<Button type="button" onClick=\{\(\) => mutation\.mutate\(\{ \.\.\.form\.getValues\(\), mfa_token: mfaToken \|\| undefined \}\)\} className="h-11 w-full rounded-lg bg-blue-600 hover:bg-blue-700" disabled=\{mutation\.isPending\}>\n            \{mutation\.isPending \? <Loader2 className="mr-2 size-4 animate-spin" /> : null\}\n            \{mfaRequired \? "Verify MFA" : "Login"\}\n          </Button>'
new_btn = r'<Button type="submit" className="h-11 w-full rounded-lg bg-blue-600 hover:bg-blue-700" disabled={mutation.isPending}>\n            {mutation.isPending ? <Loader2 className="mr-2 size-4 animate-spin" /> : null}\n            Login\n          </Button>'
content = re.sub(old_btn, new_btn, content)

# Update Google Login
google_mfa = r"""                      if \(payload\.mfa_required\) \{
                          toast\.error\("Google login currently does not support MFA"\);
                          return;
                      \}
                      if \(payload\.mfa_setup_required\) \{
                          setAccessToken\(payload\.access_token as string\);
                          router\.push\("/mfa/setup"\);
                          return;
                      \}
"""
content = re.sub(google_mfa, '', content)

with open('frontend-next/src/app/(auth)/login/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
