import os
from pathlib import Path

EXCLUDE_DIRS = {
    "venv",
    ".git",
    "__pycache__",
    "node_modules",
    ".idea",
    "qdrant_data",
    "qdrant_data_test",
    "uploads",
    ".history",
}

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
    ".json",
    ".md",
    ".yml",
}

SPECIAL_FILES = {"Dockerfile", ".env.example"}
SKIP_FILES = {"combine_code.py", "combinecode.py", "all_project_code.txt"}


def combine_code(root_dir: Path, output_file: Path) -> int:
    combined_files = 0

    with output_file.open("w", encoding="utf-8") as outfile:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext not in VALID_EXTENSIONS and filename not in SPECIAL_FILES:
                    continue

                if filename in SKIP_FILES:
                    continue

                filepath = Path(dirpath) / filename
                rel_path = filepath.relative_to(root_dir)

                try:
                    content = filepath.read_text(encoding="utf-8")
                except Exception as exc:
                    print(f"Failed to read {rel_path}: {exc}")
                    continue

                outfile.write(f"\n{'=' * 80}\n")
                outfile.write(f"File: {rel_path}\n")
                outfile.write(f"{'=' * 80}\n\n")
                outfile.write(content)
                outfile.write("\n")
                combined_files += 1

    return combined_files


def main() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    output_dir = root_dir / "tmp"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "all_project_code.txt"
    total = combine_code(root_dir, output_file)
    print(f"Code combined successfully into {output_file} ({total} files)")


if __name__ == "__main__":
    main()
