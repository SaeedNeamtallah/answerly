"""Audit frontend pages for backend-binding drift.

This is intentionally conservative. It flags obvious fake-data terms and reports
route files that do not import from the frontend API layer.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend-next" / "src"
APP_DIR = FRONTEND_SRC / "app"
COMPONENT_DIR = FRONTEND_SRC / "components"

FAKE_DATA_PATTERN = re.compile(
    r"\b(mock|fake|fixture|dummy|hardcoded|sampleData|demoData)\b",
    re.IGNORECASE,
)
API_IMPORT_PATTERN = re.compile(r"@/lib/api/")
ROUTE_PAGE_PATTERN = re.compile(r"page\.tsx$")

STATIC_ALLOWED = {
    "frontend-next/src/app/(company)/onboarding/page.tsx",
    "frontend-next/src/app/forbidden/page.tsx",
    "frontend-next/src/app/not-found.tsx",
    "frontend-next/src/app/error.tsx",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for base in (APP_DIR, COMPONENT_DIR):
        if base.exists():
            files.extend(base.rglob("*.tsx"))
    return sorted(files)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    for path in iter_source_files():
        relative = rel(path)
        text = path.read_text(encoding="utf-8")

        if FAKE_DATA_PATTERN.search(text):
            failures.append(f"{relative}: contains fake-data terminology")

        if ROUTE_PAGE_PATTERN.search(path.name) and relative not in STATIC_ALLOWED:
            if "useQuery" in text or "useMutation" in text:
                if not API_IMPORT_PATTERN.search(text):
                    failures.append(f"{relative}: uses query/mutation without importing from '@/lib/api/'")
            elif "/admin/observability" not in relative:
                warnings.append(f"{relative}: no direct query/mutation detected; verify it is intentionally static")

    print("Frontend/backend binding audit")
    print(f"Checked files: {len(iter_source_files())}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"FAIL: {failure}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
