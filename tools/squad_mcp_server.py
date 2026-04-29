"""Local MCP wrapper for the Squad workflow CLI.

This exposes the repository's Squad intake workflow to MCP clients so they can
init a repo, import a Jira-backed story, and draft a plan from the same place
they already load Copilot/Codex tools.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP


REPO_ROOT = Path(__file__).resolve().parents[1]
SQUAD_EXECUTABLE = os.environ.get("SQUAD_BIN") or shutil.which("squad")

mcp = FastMCP("squad-workflow")


def _run_squad(arguments: list[str]) -> str:
    if not SQUAD_EXECUTABLE:
        raise RuntimeError(
            "Squad CLI is not installed or not on PATH. Install it first or set SQUAD_BIN to the executable path."
        )

    completed = subprocess.run(
        [SQUAD_EXECUTABLE, *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output_parts = []
    if completed.stdout.strip():
        output_parts.append(completed.stdout.strip())
    if completed.stderr.strip():
        output_parts.append(completed.stderr.strip())

    output = "\n".join(output_parts).strip()
    if completed.returncode != 0:
        raise RuntimeError(
            f"Squad command failed with exit code {completed.returncode}.\n{output or 'No output was produced.'}"
        )

    return output or "Squad command completed successfully."


@mcp.tool()
def squad_init() -> str:
    """Initialize Squad intake scaffolding in the current repository."""

    return _run_squad(["init"])


@mcp.tool()
def squad_new_story(story_slug: str, jira_id: str) -> str:
    """Import a Jira story into Squad and write the story intake."""

    story_slug = story_slug.strip()
    jira_id = jira_id.strip()
    if not story_slug:
        raise ValueError("story_slug is required")
    if not jira_id:
        raise ValueError("jira_id is required")

    return _run_squad(["new-story", story_slug, "--id", jira_id])


@mcp.tool()
def squad_new_plan(api: bool = True) -> str:
    """Draft a Squad implementation plan after intake is ready."""

    arguments = ["new-plan"]
    if api:
        arguments.append("--api")
    return _run_squad(arguments)


if __name__ == "__main__":
    mcp.run()