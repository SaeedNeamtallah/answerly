"""Validate AGENTS route documentation against mounted FastAPI routers.

Usage:
    python tools/check_agents_sync.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "backend" / "main.py"
AGENTS_PATH = ROOT / "AGENTS.md"
ROUTES_DIR = ROOT / "backend" / "routes"


def _parse_mounted_route_files(main_text: str) -> Set[str]:
    mounted_aliases = set(re.findall(r"app\.include_router\((\w+)\.router\)", main_text))
    return {f"backend/routes/{alias}.py" for alias in mounted_aliases}


def _extract_agents_route_section(agents_text: str) -> str:
    section_match = re.search(r"### Route Layer\n(.*?)(?:\n### |\Z)", agents_text, flags=re.S)
    if not section_match:
        return ""
    return section_match.group(1)


def _parse_agents_route_entries(route_section: str) -> Set[str]:
    entries = set(re.findall(r"- `([^`]*backend/routes/[^`]+\.py)`", route_section))
    return {entry.replace("\\", "/") for entry in entries}


def _route_note_lines(route_section: str) -> Dict[str, List[str]]:
    lines = route_section.splitlines()
    notes_by_file: Dict[str, List[str]] = {}
    current_file: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        file_match = re.match(r"- `([^`]*backend/routes/[^`]+\.py)`", line)
        if file_match:
            current_file = file_match.group(1).replace("\\", "/")
            notes_by_file.setdefault(current_file, [])
            continue

        if current_file and line.startswith("- "):
            notes_by_file[current_file].append(line)

    return notes_by_file


def main() -> int:
    if not MAIN_PATH.exists():
        print(f"ERROR: Missing file: {MAIN_PATH}")
        return 1
    if not AGENTS_PATH.exists():
        print(f"ERROR: Missing file: {AGENTS_PATH}")
        return 1

    main_text = MAIN_PATH.read_text(encoding="utf-8")
    agents_text = AGENTS_PATH.read_text(encoding="utf-8")

    mounted_routes = _parse_mounted_route_files(main_text)
    route_section = _extract_agents_route_section(agents_text)
    if not route_section:
        print("ERROR: Could not find '### Route Layer' section in AGENTS.md")
        return 1

    documented_routes = _parse_agents_route_entries(route_section)
    note_lines = _route_note_lines(route_section)

    errors: List[str] = []

    missing_in_agents = sorted(mounted_routes - documented_routes)
    if missing_in_agents:
        errors.append("Mounted routes missing from AGENTS route section:")
        errors.extend([f"  - {path}" for path in missing_in_agents])

    stale_in_agents = sorted(
        path for path in documented_routes if not (ROOT / path).exists()
    )
    if stale_in_agents:
        errors.append("AGENTS route section contains non-existent route files:")
        errors.extend([f"  - {path}" for path in stale_in_agents])

    alerts_path = "backend/routes/alerts.py"
    if alerts_path in documented_routes:
        alerts_notes = " ".join(note_lines.get(alerts_path, [])).lower()
        if "not mounted" not in alerts_notes:
            errors.append(
                "AGENTS should explicitly state that backend/routes/alerts.py is not mounted in backend/main.py"
            )

    if "/projects/{project_id}/query" not in agents_text:
        errors.append(
            "AGENTS runtime flow is missing '/projects/{project_id}/query' endpoint path"
        )

    if errors:
        print("AGENTS sync check: FAILED")
        for item in errors:
            print(item)
        return 1

    print("AGENTS sync check: PASSED")
    print(f"Mounted routes checked: {len(mounted_routes)}")
    print(f"Documented route files: {len(documented_routes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
