import concurrent.futures
from datetime import datetime
from uuid import uuid4

import requests

BASE = "http://127.0.0.1:8000"

suffix = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
username = f"probe_{suffix}"
password = f"ProbePass_{suffix}!"

requests.post(f"{BASE}/auth/signup", json={"username": username, "password": password}, timeout=25)
r = requests.post(f"{BASE}/auth/login", json={"username": username, "password": password}, timeout=25)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

project = requests.post(
    f"{BASE}/projects/",
    headers=headers,
    json={"name": f"Probe Project {suffix}", "description": "429 probe"},
    timeout=25,
).json()
project_id = project["id"]

content = b"Probe document for query pressure. Candidate: Probe Tester."
files = {"file": ("probe.txt", content, "text/plain")}
asset = requests.post(f"{BASE}/projects/{project_id}/documents", headers=headers, files=files, timeout=25).json()
asset_id = asset["id"]

# Wait until completed
for _ in range(120):
    d = requests.get(f"{BASE}/documents/{asset_id}", headers=headers, timeout=25).json()
    if d.get("status") == "completed":
        break
    if d.get("status") == "failed":
        break

payload = {"query": "What is the candidate name?", "language": "en", "top_k": 3}


def do_query(_):
    rr = requests.post(f"{BASE}/projects/{project_id}/query", headers=headers, json=payload, timeout=50)
    return rr.status_code, rr.text[:300]

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    futures = [ex.submit(do_query, i) for i in range(20)]
    for f in concurrent.futures.as_completed(futures):
        results.append(f.result())

codes = [c for c, _ in results]
print("codes", sorted(set(codes)), "count429", codes.count(429))
for c, body in results:
    if c == 429:
        print("sample_429", body)
        break

requests.delete(f"{BASE}/documents/{asset_id}", headers=headers, timeout=25)
requests.delete(f"{BASE}/projects/{project_id}", headers=headers, timeout=25)
