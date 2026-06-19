import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

EXCLUDE_DIRS = {
    "venv",
    ".venv",
    ".git",
    ".agents",
    "__pycache__",
    "node_modules",
    ".idea",
    "qdrant_data",
    "qdrant_data_test",
    "assets",
    "docs",
    "specs",
    "uploads",
    ".history",
    "tmp",
    ".next",
    ".playwright-cli",
    "grafana_data",
    "dist",
    "build",
}

EXCLUDE_PATH_TOKENS = (
    "tmp/",
)

VALID_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".tsx",
    ".jsx",
    ".sql",
    ".sh",
    ".bat",
    ".cmd",
    ".ps1",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".ini",
    ".mako",
    ".toml",
    ".cfg",
    ".conf",
}

SPECIAL_FILES = {"Dockerfile", ".env.example", "README", "README.md", "AGENTS.md"}
DEFAULT_IMPORTANT_FILES = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path(".env.example"),
    Path("docker/docker-compose.yml"),
    Path("scripts/dev/setup.bat"),
    Path("scripts/dev/start.bat"),
    Path("scripts/dev/newstart.bat"),
    Path("scripts/dev/stop.bat"),
    Path("app_config.json"),
    Path("bot_config.json"),
)
SKIP_FILES = {
    "combine_code.py",
    "combinecode.py",
    "all_project_code.txt",
    "database_code.txt",
    "runtime_code.txt",
    "tempCodeRunnerFile.bat",
}

MAX_FILE_BYTES = 512 * 1024


@dataclass(frozen=True)
class FocusProfile:
    name: str
    description: str
    output_name: str
    path_tokens: tuple[str, ...]
    patterns: tuple[str, ...]
    context_lines: int = 12
    max_matches_per_file: int = 8
    excluded_extensions: tuple[str, ...] = ()


DATABASE_PROFILE = FocusProfile(
    name="database",
    description=(
        "Extract the important database, storage, and SaaS support paths for the backend, "
        "vector store, Telegram bot integrations, and Docker wiring."
    ),
    output_name="database_code.txt",
    path_tokens=(
        "backend/database/",
        "backend/alembic/",
        "backend/providers/vectordb/",
        "backend/routes/auth.py",
        "backend/routes/projects.py",
        "backend/routes/documents.py",
        "backend/routes/query.py",
        "backend/routes/bot_integrations.py",
        "backend/routes/conversations.py",
        "backend/routes/telegram_webhook.py",
        "backend/routes/admin_console.py",
        "backend/tasks/file_processing.py",
        "backend/tasks/data_indexing.py",
        "backend/tasks/process_workflow.py",
        "backend/tasks/maintenance.py",
        "backend/services/bot_integration_service.py",
        "backend/services/conversation_service.py",
        "backend/services/telegram_webhook_service.py",
        "backend/services/customer_bot_query_service.py",
        "backend/services/admin_service.py",
        "backend/services/telegram_api_service.py",
        "backend/services/token_crypto_service.py",
        "backend/security/auth.py",
        "backend/security/jwt_utils.py",
        "backend/services/query_service.py",
        "backend/routes/app_config.py",
        "backend/routes/bot_config.py",
        "backend/routes/health.py",
        "backend/routes/stats.py",
        "backend/runtime_config.py",
        "backend/config.py",
        "backend/celery_app.py",
        "telegram_bot/config.py",
        "telegram_bot/handlers.py",
        "docker/docker-compose.yml",
        "docker/backend.Dockerfile",
        "app_config.json",
        "bot_config.json",
        ".env.example",
        "backend/alembic/alembic.ini",
        "backend/alembic/env.py",
        "backend/alembic/init-db.sql",
        "backend/alembic/script.py.mako",
    ),
    patterns=(
        r"\bdatabase\b",
        r"\bpostgres\b",
        r"\bpgvector\b",
        r"\bqdrant\b",
        r"\bvector_db_provider\b",
        r"\bDATABASE_URL\b",
        r"\bget_db\b",
        r"\binit_db\b",
        r"\bowner_id\b",
        r"\bactive_project_id\b",
        r"\bBOT_ACTIVE_PROJECT_ID\b",
        r"\bbot_config\.json\b",
        r"\bapp_config\.json\b",
        r"\bupdate_runtime_config\b",
        r"\bcreate_collection\b",
        r"\badd_vectors\b",
        r"\bsearch\(",
        r"\bembedding\b",
        r"\bchunks\b",
        r"\busers\b",
        r"\bprojects\b",
        r"\bassets\b",
        r"\bcelery_task_executions\b",
        r"\bbot_integrations\b",
        r"\bconversations\b",
        r"\bconversation_messages\b",
        r"\btelegram_customers\b",
        r"\bplatform_owner\b",
        r"\bcompany_admin\b",
    ),
)

RUNTIME_PROFILE = FocusProfile(
    name="runtime",
    description=(
        "Extract application code plus Docker, environment, startup, Prometheus, "
        "and Telegram bot files while skipping docs and generated artifacts."
    ),
    output_name="runtime_code.txt",
    path_tokens=(
        "backend/",
        "frontend-next/",
        "telegram_bot/",
        "tools/",
        "docker/",
        "scripts/dev/setup.bat",
        "scripts/dev/start.bat",
        "scripts/dev/newstart.bat",
        "scripts/dev/stop.bat",
        "AGENTS.md",
        "README.md",
        ".env.example",
    ),
    patterns=(),
    excluded_extensions=(".md",),
)

PROFILES = {
    DATABASE_PROFILE.name: DATABASE_PROFILE,
    RUNTIME_PROFILE.name: RUNTIME_PROFILE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine full project code or extract focused snippets for a profile."
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        help="Named focus profile. Example: --profile database",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Extra regex pattern to match. Repeat to add more patterns.",
    )
    parser.add_argument(
        "--context",
        type=int,
        help="Context lines around each match. Defaults to the profile setting.",
    )
    parser.add_argument(
        "--max-matches-per-file",
        type=int,
        default=None,
        help="Maximum matched windows to keep from each file.",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path. Defaults to tmp/all_project_code.txt or the profile output.",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Collect absolutely all files, ignoring VALID_EXTENSIONS, SKIP_FILES, and EXCLUDE_PATH_TOKENS filters.",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available focus profiles and exit.",
    )
    return parser.parse_args()


def list_profiles() -> None:
    for profile in PROFILES.values():
        print(f"{profile.name}: {profile.description}")


def iter_source_files(root_dir: Path, include_all: bool = False) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)

        for filename in sorted(filenames):
            if not include_all:
                if filename != ".env.example" and (filename == ".env" or filename.startswith(".env.")):
                    continue
            ext = Path(filename).suffix.lower()
            if not include_all:
                is_docker = "dockerfile" in filename.lower()
                if ext not in VALID_EXTENSIONS and filename not in SPECIAL_FILES and not is_docker:
                    continue
                if filename in SKIP_FILES:
                    continue
            path = Path(dirpath) / filename
            rel_posix = path.relative_to(root_dir).as_posix()
            if not include_all and any(token in rel_posix for token in EXCLUDE_PATH_TOKENS):
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES and filename not in SPECIAL_FILES:
                    continue
            except OSError:
                continue
            yield path


def get_default_bundle_files(root_dir: Path, include_all: bool = False) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()

    if not include_all:
        for rel_path in DEFAULT_IMPORTANT_FILES:
            full_path = root_dir / rel_path
            if full_path.exists() and full_path.is_file():
                ordered.append(full_path)
                seen.add(full_path.resolve())

    for path in iter_source_files(root_dir, include_all=include_all):
        resolved = path.resolve()
        if resolved in seen:
            continue
        ordered.append(path)
        seen.add(resolved)

    return ordered


def compile_patterns(patterns: Sequence[str]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        compiled.append(re.compile(pattern, re.IGNORECASE))
    return compiled


def merge_ranges(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
        else:
            prev_start, prev_end = merged[-1]
            merged[-1] = (prev_start, max(prev_end, end))
    return merged


def find_match_ranges(
    lines: Sequence[str],
    patterns: Sequence[re.Pattern[str]],
    context_lines: int,
    max_matches_per_file: int,
) -> list[tuple[int, int]]:
    if not patterns:
        return [(1, len(lines))] if lines else []

    matched_line_numbers: list[int] = []
    for idx, line in enumerate(lines, start=1):
        if any(pattern.search(line) for pattern in patterns):
            matched_line_numbers.append(idx)
            if len(matched_line_numbers) >= max_matches_per_file:
                break

    ranges = []
    for line_no in matched_line_numbers:
        start = max(1, line_no - context_lines)
        end = min(len(lines), line_no + context_lines)
        ranges.append((start, end))
    return merge_ranges(ranges)


def path_matches_profile(rel_path: Path, profile: FocusProfile | None) -> bool:
    if profile is None:
        return True
    rel_posix = rel_path.as_posix()
    return any(token in rel_posix for token in profile.path_tokens)


def write_full_file(outfile, rel_path: Path, content: str) -> None:
    outfile.write(f"\n{'=' * 80}\n")
    outfile.write(f"File: {rel_path.as_posix()}\n")
    outfile.write(f"{'=' * 80}\n\n")
    outfile.write(content)
    if not content.endswith("\n"):
        outfile.write("\n")


def write_snippet_file(
    outfile,
    rel_path: Path,
    lines: Sequence[str],
    ranges: Sequence[tuple[int, int]],
) -> None:
    outfile.write(f"\n{'=' * 80}\n")
    outfile.write(f"File: {rel_path.as_posix()}\n")
    outfile.write(f"Ranges: {', '.join(f'{start}-{end}' for start, end in ranges)}\n")
    outfile.write(f"{'=' * 80}\n\n")

    for range_index, (start, end) in enumerate(ranges):
        if range_index:
            outfile.write("...\n\n")
        for line_no in range(start, end + 1):
            outfile.write(f"{line_no:04d}: {lines[line_no - 1]}\n")
    outfile.write("\n")


def combine_code(root_dir: Path, output_file: Path, include_all: bool = False) -> int:
    combined_files = 0

    with output_file.open("w", encoding="utf-8") as outfile:
        outfile.write("Bundle: default\n")
        outfile.write("Notes:\n")
        outfile.write("- Includes current repo code and runtime files.\n")
        outfile.write("- Includes the current Next.js frontend under frontend-next/.\n")
        outfile.write("- Includes important project context files and Windows startup scripts first.\n\n")

        for filepath in get_default_bundle_files(root_dir, include_all=include_all):
            rel_path = filepath.relative_to(root_dir)

            try:
                content = filepath.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"Failed to read {rel_path}: {exc}")
                continue

            write_full_file(outfile, rel_path, content)
            combined_files += 1

    return combined_files


def combine_focus_code(
    root_dir: Path,
    output_file: Path,
    *,
    profile: FocusProfile,
    extra_patterns: Sequence[str],
    context_lines: int | None,
    max_matches_per_file: int | None,
    include_all: bool = False,
) -> int:
    combined_files = 0
    patterns = compile_patterns([*profile.patterns, *extra_patterns])
    context = profile.context_lines if context_lines is None else max(0, context_lines)
    max_matches = profile.max_matches_per_file if max_matches_per_file is None else max(1, max_matches_per_file)

    with output_file.open("w", encoding="utf-8") as outfile:
        outfile.write(f"Profile: {profile.name}\n")
        outfile.write(f"Description: {profile.description}\n")
        outfile.write(f"Context lines: {context}\n")
        outfile.write(f"Max matches per file: {max_matches}\n")
        if extra_patterns:
            outfile.write(f"Extra patterns: {', '.join(extra_patterns)}\n")
        outfile.write("\n")

        for filepath in iter_source_files(root_dir, include_all=include_all):
            rel_path = filepath.relative_to(root_dir)
            if not path_matches_profile(rel_path, profile):
                continue
            if filepath.suffix.lower() in profile.excluded_extensions:
                continue

            try:
                content = filepath.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"Failed to read {rel_path}: {exc}")
                continue

            lines = content.splitlines()
            ranges = find_match_ranges(lines, patterns, context, max_matches)
            if not ranges:
                continue

            write_snippet_file(outfile, rel_path, lines, ranges)
            combined_files += 1

    return combined_files


def main() -> None:
    args = parse_args()
    if args.list_profiles:
        list_profiles()
        return

    root_dir = Path(__file__).resolve().parents[1]
    output_dir = root_dir / "tmp"
    output_dir.mkdir(exist_ok=True)

    if args.profile:
        profile = PROFILES[args.profile]
        output_file = Path(args.output) if args.output else output_dir / profile.output_name
        total = combine_focus_code(
            root_dir,
            output_file,
            profile=profile,
            extra_patterns=args.query,
            context_lines=args.context,
            max_matches_per_file=args.max_matches_per_file,
            include_all=args.all_files,
        )
        print(f"Focused code combined into {output_file} ({total} files)")
        return

    output_file = Path(args.output) if args.output else output_dir / "all_project_code.txt"
    total = combine_code(root_dir, output_file, include_all=args.all_files)
    print(f"Code combined successfully into {output_file} ({total} files)")


if __name__ == "__main__":
    main()
