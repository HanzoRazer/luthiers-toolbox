#!/usr/bin/env python3
"""
Migration Script: fetch() -> api()

Automatically updates Vue/TypeScript files to use the centralized api() client
instead of raw fetch() calls with relative URLs.

Changes:
  fetch('/api/...') → api('/api/...')

Also adds the import statement if needed.

Usage:
    python scripts/ci/migrate_fetch_to_api.py [--dry-run] [--file PATH]

Options:
    --dry-run    Show what would be changed without modifying files
    --file PATH  Only process a specific file
"""

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLIENT_SRC = REPO_ROOT / "packages" / "client" / "src"

# Pattern to match fetch calls with relative URLs
FETCH_PATTERN = re.compile(
    r'\bfetch\s*\(\s*([\'"`])(/api/[^\'"` ]+)\1',
    re.MULTILINE
)

# Import statement to add
IMPORT_STATEMENT = "import { api } from '@/services/apiBase';"

# Files/directories to skip
SKIP_PATTERNS = [
    "node_modules",
    ".spec.",
    ".test.",
    "__tests__",
    "apiBase.ts",  # Don't modify the source file itself
]


def should_skip(file_path: Path) -> bool:
    """Check if file should be skipped."""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in SKIP_PATTERNS)


def has_api_import(content: str) -> bool:
    """Check if file already imports api from apiBase."""
    return "from '@/services/apiBase'" in content or 'from "@/services/apiBase"' in content


def add_api_import(content: str) -> str:
    """Add api import to file content."""
    if has_api_import(content):
        # Check if api is already imported
        if re.search(r"import\s*{[^}]*\bapi\b[^}]*}\s*from\s*['\"]@/services/apiBase['\"]", content):
            return content
        # Add api to existing import
        content = re.sub(
            r"(import\s*{)([^}]*)(}\s*from\s*['\"]@/services/apiBase['\"])",
            r"\1 api,\2\3",
            content
        )
        return content

    # Find the best place to add the import
    # After other imports, or at the start of the script
    lines = content.split('\n')
    insert_idx = 0

    for i, line in enumerate(lines):
        if line.strip().startswith('import '):
            insert_idx = i + 1
        elif line.strip().startswith('<script'):
            insert_idx = i + 1
            break

    if insert_idx > 0:
        lines.insert(insert_idx, IMPORT_STATEMENT)
        return '\n'.join(lines)

    return content


def migrate_fetch_calls(content: str) -> tuple[str, int]:
    """Replace fetch('/api/...') with api('/api/...')."""
    count = 0

    def replacer(match):
        nonlocal count
        quote = match.group(1)
        url = match.group(2)
        count += 1
        return f"api({quote}{url}{quote}"

    new_content = FETCH_PATTERN.sub(replacer, content)
    return new_content, count


def process_file(file_path: Path, dry_run: bool = False) -> dict:
    """Process a single file and return stats."""
    result = {
        "path": str(file_path),
        "fetch_calls_migrated": 0,
        "import_added": False,
        "modified": False,
        "error": None,
    }

    try:
        content = file_path.read_text(encoding="utf-8")
        original = content

        # Check if there are fetch calls to migrate
        if not FETCH_PATTERN.search(content):
            return result

        # Migrate fetch calls
        content, count = migrate_fetch_calls(content)
        result["fetch_calls_migrated"] = count

        if count > 0:
            # Add import if needed
            if not has_api_import(original) or "api," not in content:
                content = add_api_import(content)
                result["import_added"] = True

            result["modified"] = True

            if not dry_run:
                file_path.write_text(content, encoding="utf-8")

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Migrate fetch() calls to api()")
    parser.add_argument("--dry-run", action="store_true", help="Don't modify files")
    parser.add_argument("--file", type=str, help="Process only this file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = list(CLIENT_SRC.rglob("*.vue")) + list(CLIENT_SRC.rglob("*.ts"))

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Migrating fetch() -> api()...")
    print(f"Scanning {len(files)} files...\n")

    total_migrated = 0
    files_modified = 0

    for file_path in files:
        if should_skip(file_path):
            continue

        result = process_file(file_path, dry_run=args.dry_run)

        if result["error"]:
            print(f"ERROR: {result['path']}: {result['error']}")
            continue

        if result["modified"]:
            files_modified += 1
            total_migrated += result["fetch_calls_migrated"]

            rel_path = file_path.relative_to(REPO_ROOT)
            import_note = " (+import)" if result["import_added"] else ""
            print(f"  {result['fetch_calls_migrated']:3d} calls  {rel_path}{import_note}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary:")
    print(f"  Files modified: {files_modified}")
    print(f"  fetch() calls migrated: {total_migrated}")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
