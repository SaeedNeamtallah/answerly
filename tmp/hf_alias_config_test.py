import os
from datetime import datetime
from uuid import uuid4

import requests

base = os.getenv("RAGMIND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
suffix = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
username = f"hfalias_{suffix}"
password = f"AliasPass_{suffix}!"

r = requests.post(f"{base}/auth/signup", json={"username": username, "password": password}, timeout=25)
print("signup", r.status_code)

r = requests.post(f"{base}/auth/login", json={"username": username, "password": password}, timeout=25)
print("login", r.status_code)
token = r.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

r = requests.get(f"{base}/config/providers", timeout=25)
print("get providers", r.status_code)
providers = r.json()

payload = {
    "llm_provider": providers.get("llm_provider", "gemini"),
    "embedding_provider": "hf-bge-m3",
    "vector_db_provider": providers.get("vector_db_provider", "pgvector"),
}
r = requests.post(f"{base}/config/providers", json=payload, headers=headers, timeout=25)
print("post providers with hf-bge-m3", r.status_code, r.text[:300])
