import concurrent.futures
import os
import statistics
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

import requests


BASE_URL = os.getenv("RAGMIND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = int(os.getenv("RAGMIND_REQUEST_TIMEOUT", "40"))
PROCESSING_TIMEOUT_SECONDS = int(os.getenv("RAGMIND_PROCESSING_TIMEOUT", "240"))


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def timed_request(
    method: str,
    path: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    stream: bool = False,
) -> Tuple[int, float, str, Optional[requests.Response]]:
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            files=files,
            timeout=REQUEST_TIMEOUT,
            stream=stream,
        )
        elapsed = time.perf_counter() - start
        return response.status_code, elapsed, "", response
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return 0, elapsed, str(exc), None


def summarize_phase(name: str, statuses: List[int], durations: List[float], total_time: float) -> Dict[str, Any]:
    success_count = sum(1 for s in statuses if 200 <= s < 400)
    return {
        "phase": name,
        "requests": len(statuses),
        "success": success_count,
        "failures": len(statuses) - success_count,
        "avg_ms": round((statistics.mean(durations) if durations else 0.0) * 1000, 2),
        "p95_ms": round(percentile(durations, 95) * 1000, 2),
        "p99_ms": round(percentile(durations, 99) * 1000, 2),
        "max_ms": round((max(durations) if durations else 0.0) * 1000, 2),
        "throughput_rps": round((len(statuses) / total_time) if total_time > 0 else 0.0, 2),
    }


def run_load_phase(
    *,
    name: str,
    method: str,
    path: str,
    workers: int,
    total_requests: int,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    statuses: List[int] = []
    durations: List[float] = []
    errors: List[str] = []

    def _worker(_: int) -> Tuple[int, float, str]:
        status, elapsed, err, _ = timed_request(
            method=method,
            path=path,
            headers=headers,
            json=json_body,
        )
        return status, elapsed, err

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_worker, i) for i in range(total_requests)]
        for future in concurrent.futures.as_completed(futures):
            status, elapsed, err = future.result()
            statuses.append(status)
            durations.append(elapsed)
            if err:
                errors.append(err)

    total_time = time.perf_counter() - started
    summary = summarize_phase(name=name, statuses=statuses, durations=durations, total_time=total_time)
    summary["non_2xx_statuses"] = sorted({s for s in statuses if s < 200 or s >= 300})
    summary["sample_errors"] = errors[:5]
    return summary


def assert_status(actual: int, expected: Iterable[int], context: str, body: str = "") -> None:
    expected_set = set(expected)
    if actual not in expected_set:
        raise AssertionError(f"{context}: expected one of {sorted(expected_set)}, got {actual}. Body: {body[:500]}")


def main() -> None:
    print(f"[INFO] High intensive endpoint test started against {BASE_URL}")

    suffix = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    username = f"intensive_{suffix}"
    password = f"IntensePass_{suffix}!"
    new_password = f"IntensePass_{suffix}_new!"

    token: Optional[str] = None
    auth_headers: Optional[Dict[str, str]] = None
    project_id: Optional[int] = None
    asset_id: Optional[int] = None

    phase_summaries: List[Dict[str, Any]] = []

    try:
        # Public endpoints
        st, t, err, res = timed_request("GET", "/")
        assert_status(st, {200}, "GET /")

        st, t, err, res = timed_request("GET", "/health")
        assert_status(st, {200}, "GET /health", res.text if res else "")

        st, t, err, res = timed_request("GET", "/stats/")
        assert_status(st, {200}, "GET /stats/", res.text if res else "")

        # Auth flow
        st, t, err, res = timed_request(
            "POST",
            "/auth/signup",
            json={"username": username, "password": password},
        )
        assert_status(st, {201}, "POST /auth/signup", res.text if res else "")

        st, t, err, res = timed_request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert_status(st, {200}, "POST /auth/login", res.text if res else "")
        token = (res.json() if res else {}).get("access_token")
        if not token:
            raise AssertionError("Login did not return access_token")
        auth_headers = {"Authorization": f"Bearer {token}"}

        st, t, err, res = timed_request("GET", "/auth/me", headers=auth_headers)
        assert_status(st, {200}, "GET /auth/me", res.text if res else "")

        st, t, err, res = timed_request(
            "POST",
            "/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": password,
                "new_password": new_password,
                "confirm_new_password": new_password,
            },
        )
        assert_status(st, {200}, "POST /auth/change-password", res.text if res else "")

        st, t, err, res = timed_request(
            "POST",
            "/auth/login",
            json={"username": username, "password": new_password},
        )
        assert_status(st, {200}, "POST /auth/login after password change", res.text if res else "")
        token = (res.json() if res else {}).get("access_token")
        auth_headers = {"Authorization": f"Bearer {token}"}

        st, t, err, res = timed_request(
            "POST",
            "/auth/update-password",
            headers=auth_headers,
            json={
                "current_password": new_password,
                "new_password": password,
                "confirm_new_password": password,
            },
        )
        assert_status(st, {200}, "POST /auth/update-password", res.text if res else "")

        # Refresh token after reverting password
        st, t, err, res = timed_request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert_status(st, {200}, "POST /auth/login after revert", res.text if res else "")
        token = (res.json() if res else {}).get("access_token")
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Project endpoints
        st, t, err, res = timed_request(
            "POST",
            "/projects/",
            headers=auth_headers,
            json={
                "name": f"Intensive Project {suffix}",
                "description": "High intensive endpoint test",
                "metadata": {"source": "tmp/high_intensive_endpoints_test.py"},
            },
        )
        assert_status(st, {201}, "POST /projects/", res.text if res else "")
        project_id = (res.json() if res else {}).get("id")
        if not project_id:
            raise AssertionError("Project creation did not return id")

        st, t, err, res = timed_request("GET", "/projects/?skip=0&limit=10", headers=auth_headers)
        assert_status(st, {200}, "GET /projects/", res.text if res else "")

        st, t, err, res = timed_request("GET", f"/projects/{project_id}", headers=auth_headers)
        assert_status(st, {200}, "GET /projects/{id}", res.text if res else "")

        st, t, err, res = timed_request(
            "PUT",
            f"/projects/{project_id}",
            headers=auth_headers,
            json={"description": "Updated by intensive test"},
        )
        assert_status(st, {200}, "PUT /projects/{id}", res.text if res else "")

        st, t, err, res = timed_request("GET", f"/projects/{project_id}/stats", headers=auth_headers)
        assert_status(st, {200}, "GET /projects/{id}/stats", res.text if res else "")

        st, t, err, res = timed_request(
            "POST",
            f"/projects/{project_id}/index",
            headers=auth_headers,
            json={"do_reset": False},
        )
        assert_status(st, {200}, "POST /projects/{id}/index", res.text if res else "")

        # Document endpoints
        file_payload = {
            "file": (
                "intensive_test.txt",
                (
                    "RAGMind intensive test content.\n"
                    "Candidate: Intensive Tester.\n"
                    "Location: Cairo.\n"
                    "Skill: retrieval augmented generation.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        }
        st, t, err, res = timed_request(
            "POST",
            f"/projects/{project_id}/documents",
            headers=auth_headers,
            files=file_payload,
        )
        assert_status(st, {201}, "POST /projects/{id}/documents", res.text if res else "")
        asset_id = (res.json() if res else {}).get("id")
        if not asset_id:
            raise AssertionError("Document upload did not return id")

        st, t, err, res = timed_request("GET", f"/projects/{project_id}/documents", headers=auth_headers)
        assert_status(st, {200}, "GET /projects/{id}/documents", res.text if res else "")

        st, t, err, res = timed_request("GET", f"/documents/{asset_id}", headers=auth_headers)
        assert_status(st, {200}, "GET /documents/{asset_id}", res.text if res else "")

        # Wait for processing completion
        deadline = time.time() + PROCESSING_TIMEOUT_SECONDS
        last_status = None
        while time.time() < deadline:
            st, t, err, res = timed_request("GET", f"/documents/{asset_id}", headers=auth_headers)
            assert_status(st, {200}, "GET /documents/{asset_id} polling", res.text if res else "")
            payload = res.json() if res else {}
            last_status = payload.get("status")
            if last_status == "completed":
                break
            if last_status == "failed":
                raise AssertionError(f"Document processing failed: {payload}")
            time.sleep(2)
        else:
            raise AssertionError(f"Timeout waiting for processing completion. Last status: {last_status}")

        st, t, err, res = timed_request("POST", f"/documents/{asset_id}/process", headers=auth_headers)
        assert_status(st, {200}, "POST /documents/{asset_id}/process", res.text if res else "")
        process_task_id = (res.json() if res else {}).get("task_id")

        st, t, err, res = timed_request(
            "POST",
            f"/documents/{asset_id}/process-and-index",
            headers=auth_headers,
            json={"do_reset": False},
        )
        assert_status(st, {200}, "POST /documents/{asset_id}/process-and-index", res.text if res else "")
        workflow_task_id = (res.json() if res else {}).get("workflow_task_id")

        if process_task_id:
            st, t, err, res = timed_request("GET", f"/tasks/{process_task_id}", headers=auth_headers)
            assert_status(st, {200}, "GET /tasks/{process_task_id}", res.text if res else "")

        if workflow_task_id:
            st, t, err, res = timed_request("GET", f"/tasks/{workflow_task_id}", headers=auth_headers)
            # Keep as data point; some implementations may intentionally deny if owner map is not registered.
            assert_status(st, {200, 403}, "GET /tasks/{workflow_task_id}", res.text if res else "")
            print(f"[INFO] Workflow task ownership status code: {st}")

        # Query endpoints
        query_body = {"query": "What is the candidate name?", "language": "en", "top_k": 3}
        st, t, err, res = timed_request(
            "POST",
            f"/projects/{project_id}/query",
            headers=auth_headers,
            json=query_body,
        )
        assert_status(st, {200}, "POST /projects/{id}/query", res.text if res else "")

        st, t, err, res = timed_request(
            "POST",
            f"/projects/{project_id}/query/stream",
            headers=auth_headers,
            json=query_body,
            stream=True,
        )
        assert_status(st, {200}, "POST /projects/{id}/query/stream", res.text if res else "")
        stream_line_count = 0
        if res is not None:
            for raw_line in res.iter_lines(decode_unicode=True):
                if raw_line:
                    stream_line_count += 1
                if stream_line_count >= 3:
                    break
            res.close()
        if stream_line_count == 0:
            raise AssertionError("Streaming query returned no data lines")

        # App config / bot config endpoints
        st, t, err, res = timed_request("GET", "/config/providers")
        assert_status(st, {200}, "GET /config/providers", res.text if res else "")
        providers_payload = res.json() if res else {}

        update_payload = {
            "llm_provider": providers_payload.get("llm_provider", "gemini"),
            "embedding_provider": providers_payload.get("embedding_provider", "gemini"),
            "vector_db_provider": providers_payload.get("vector_db_provider", "pgvector"),
            "retrieval_top_k": providers_payload.get("retrieval_top_k", 4),
        }
        st, t, err, res = timed_request("POST", "/config/providers", headers=auth_headers, json=update_payload)
        assert_status(st, {200, 401}, "POST /config/providers", res.text if res else "")

        st, t, err, res = timed_request("GET", "/bot/config")
        assert_status(st, {200}, "GET /bot/config", res.text if res else "")

        st, t, err, res = timed_request("POST", "/bot/config", headers=auth_headers, json={"active_project_id": project_id})
        assert_status(st, {200, 401}, "POST /bot/config", res.text if res else "")

        # Bot profile may fail due missing Telegram token in env; treat as optional behavior.
        st, t, err, res = timed_request(
            "POST",
            "/bot/profile",
            headers=auth_headers,
            files={"name": (None, "RAGMind Test Bot")},
        )
        assert_status(st, {200, 401, 500}, "POST /bot/profile", res.text if res else "")

        # Security endpoints (expected 403 for non-admin/non-cybersecurity users)
        st, t, err, res = timed_request("GET", "/security/stats", headers=auth_headers)
        assert_status(st, {200, 403}, "GET /security/stats", res.text if res else "")

        st, t, err, res = timed_request("GET", "/security/events", headers=auth_headers)
        assert_status(st, {200, 403}, "GET /security/events", res.text if res else "")

        st, t, err, res = timed_request("POST", "/security/simulate", headers=auth_headers)
        assert_status(st, {200, 403}, "POST /security/simulate", res.text if res else "")

        st, t, err, res = timed_request("GET", "/security/events/stream", headers=auth_headers, stream=True)
        assert_status(st, {200, 403}, "GET /security/events/stream", res.text if res else "")
        if res is not None:
            res.close()

        # Load phases
        phase_summaries.append(
            run_load_phase(
                name="health_heavy",
                method="GET",
                path="/health",
                workers=40,
                total_requests=400,
            )
        )
        phase_summaries.append(
            run_load_phase(
                name="stats_heavy",
                method="GET",
                path="/stats/",
                workers=20,
                total_requests=200,
            )
        )
        phase_summaries.append(
            run_load_phase(
                name="projects_list_heavy",
                method="GET",
                path="/projects/?skip=0&limit=10",
                workers=20,
                total_requests=200,
                headers=auth_headers,
            )
        )
        phase_summaries.append(
            run_load_phase(
                name="documents_get_heavy",
                method="GET",
                path=f"/documents/{asset_id}",
                workers=20,
                total_requests=200,
                headers=auth_headers,
            )
        )
        phase_summaries.append(
            run_load_phase(
                name="query_moderate",
                method="POST",
                path=f"/projects/{project_id}/query",
                workers=5,
                total_requests=20,
                headers=auth_headers,
                json_body=query_body,
            )
        )

        print("\n[RESULT] Endpoint load summaries")
        for summary in phase_summaries:
            print(summary)

        print("\n[OK] High intensive endpoint test completed")

    finally:
        if asset_id is not None and auth_headers is not None:
            st, _, _, _ = timed_request("DELETE", f"/documents/{asset_id}", headers=auth_headers)
            print(f"[CLEANUP] DELETE /documents/{asset_id} -> {st}")
        if project_id is not None and auth_headers is not None:
            st, _, _, _ = timed_request("DELETE", f"/projects/{project_id}", headers=auth_headers)
            print(f"[CLEANUP] DELETE /projects/{project_id} -> {st}")


if __name__ == "__main__":
    main()
