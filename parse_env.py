import os

env_vars = {}
with open('.env', 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore').replace('\x00', '')

with open('load_env.ps1', 'w', encoding='utf-8') as f:
    for line in content.split('\n'):
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().replace('"', '`"')
            f.write(f'$env:{k}="{v}"\n')
