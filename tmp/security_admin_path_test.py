import os
from uuid import uuid4

import requests

BASE_URL = os.getenv("RAGMIND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 25


def req(method, path, **kwargs):
    r = requests.request(method, f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs)
    return r.status_code, r


def main():
    admin_username = os.getenv("AUTH_ADMIN_USERNAME", "admin")
    admin_password = f"AdminStrong_{uuid4().hex[:12]}!"

    status, resp = req("POST", "/auth/signup", json={"username": admin_username, "password": admin_password})
    if status == 201:
        print(f"[INFO] Admin user created: {admin_username}")
    elif status == 400:
        print(f"[INFO] Admin username already exists, cannot guarantee password for login path test: {admin_username}")
        print(f"[INFO] signup body: {resp.text[:300]}")
        return
    else:
        print(f"[WARN] Unexpected signup status for admin path test: {status} {resp.text[:300]}")
        return

    status, resp = req("POST", "/auth/login", json={"username": admin_username, "password": admin_password})
    if status != 200:
        print(f"[WARN] Admin login failed: {status} {resp.text[:300]}")
        return

    token = resp.json().get("access_token")
    if not token:
        print("[WARN] Admin login missing token")
        return
    headers = {"Authorization": f"Bearer {token}"}

    for path in ("/security/stats", "/security/events"):
        status, resp = req("GET", path, headers=headers)
        print(f"[RESULT] GET {path} -> {status}")

    status, resp = req("POST", "/security/simulate", headers=headers)
    print(f"[RESULT] POST /security/simulate -> {status}")


if __name__ == "__main__":
    main()
