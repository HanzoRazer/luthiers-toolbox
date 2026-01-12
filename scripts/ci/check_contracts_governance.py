#!/usr/bin/env python3
"""
Contracts Governance Gate (Scenario B)

Enforces:
  1) sha256 file format = single 64-hex line (lowercase required)
  2) if any contract schema/hash changes => contracts/CHANGELOG.md must change
     and must mention each changed contract stem
  3) if contracts are publicly released => *_v1.schema.json and *_v1.schema.sha256 are immutable

This is deliberately "repo-local":
  - Uses git diff against a base ref
  - No GitHub API calls
  - No cross-repo fetch

Exit codes:
  0 pass
  1 violations
  2 execution error
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class Violation:
    code: str
    message: str


def run_git(args: List[str], cwd: Path) -> str:
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{p.stdout}\n{p.stderr}")
    return p.stdout.strip()


def changed_files(repo_root: Path, base_ref: str) -> List[str]:
    # Use three-dot to compare merge-base(base_ref, HEAD)..HEAD (typical PR diff)
    out = run_git(["diff", "--name-only", f"{base_ref}...HEAD"], cwd=repo_root)
    files = [x.strip() for x in out.splitlines() if x.strip()]
    return files


def read_contracts_version(repo_root: Path) -> Tuple[bool, str]:
    """
    contracts/CONTRACTS_VERSION.json:
      { "public_released": true/false, "tag": "..." }
    Missing file => treat as not released (safe default).
    """
    fp = repo_root / "contracts" / "CONTRACTS_VERSION.json"
    if not fp.exists():
        return (False, "")
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to parse {fp}: {e}")
    public = bool(data.get("public_released", False))
    tag = str(data.get("tag", "")) if data.get("tag") is not None else ""
    return (public, tag)


def is_contract_schema(path: str) -> bool:
    return path.startswith("contracts/") and path.endswith(".schema.json")


def is_contract_sha(path: str) -> bool:
    return path.startswith("contracts/") and path.endswith(".schema.sha256")


def contract_stem(path: str) -> str:
    # contracts/foo_v1.schema.json -> foo_v1
    name = Path(path).name
    if name.endswith(".schema.json"):
        return name[: -len(".schema.json")]
    if name.endswith(".schema.sha256"):
        return name[: -len(".schema.sha256")]
    return name


def is_v1_contract(path: str) -> bool:
    # matches *_v1.schema.json or *_v1.schema.sha256
    return bool(re.search(r"_v1\.schema\.(json|sha256)$", path))


def check_sha256_format(repo_root: Path) -> List[Violation]:
    v: List[Violation] = []
    contracts_dir = repo_root / "contracts"
    if not contracts_dir.exists():
        return v
    for fp in contracts_dir.glob("*.schema.sha256"):
        raw = fp.read_text(encoding="utf-8").strip()
        if not HEX64_RE.match(raw):
            v.append(
                Violation(
                    "SHA256_FORMAT",
                    f"{fp.as_posix()} must contain exactly one 64-lowercase-hex line; got: {raw!r}",
                )
            )
    return v


def check_changelog_required(repo_root: Path, changed: List[str], base_ref: str) -> List[Violation]:
    v: List[Violation] = []

    contract_changes = [p for p in changed if is_contract_schema(p) or is_contract_sha(p)]
    if not contract_changes:
        return v

    if "contracts/CHANGELOG.md" not in changed:
        v.append(
            Violation(
                "CHANGELOG_REQUIRED",
                "Contract schema/hash changed but contracts/CHANGELOG.md was not updated.",
            )
        )
        return v

    # Require stems to appear in the diff for this PR (not anywhere in file history)
    diff = run_git(["diff", f"{base_ref}...HEAD", "--", "contracts/CHANGELOG.md"], cwd=repo_root)
    stems = sorted({contract_stem(p) for p in contract_changes})
    missing = [s for s in stems if s not in diff]

    if missing:
        v.append(
            Violation(
                "CHANGELOG_MISSING_MENTIONS",
                "contracts/CHANGELOG.md diff must mention each changed contract: "
                + ", ".join(missing),
            )
        )

    return v


def check_v1_immutability(repo_root: Path, changed: List[str]) -> List[Violation]:
    v: List[Violation] = []
    public, tag = read_contracts_version(repo_root)
    if not public:
        return v

    v1_touched = [p for p in changed if (is_contract_schema(p) or is_contract_sha(p)) and is_v1_contract(p)]
    if v1_touched:
        v.append(
            Violation(
                "V1_IMMUTABLE",
                "Contracts are marked public_released=true "
                f"(tag={tag or '<none>'}). The following v1 contracts are immutable: "
                + ", ".join(sorted(v1_touched)),
            )
        )
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Repo root (default: .)")
    ap.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base ref for diff (default: origin/main). For PRs use origin/main or the PR base branch.",
    )
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()

    try:
        changed = changed_files(repo_root, args.base_ref)
    except Exception as e:
        print(f"[contracts-gov] ERROR: {e}", file=sys.stderr)
        return 2

    violations: List[Violation] = []
    try:
        violations.extend(check_sha256_format(repo_root))
        violations.extend(check_changelog_required(repo_root, changed, args.base_ref))
        violations.extend(check_v1_immutability(repo_root, changed))
    except Exception as e:
        print(f"[contracts-gov] ERROR: {e}", file=sys.stderr)
        return 2

    if not violations:
        print("[contracts-gov] PASS")
        return 0

    print(f"[contracts-gov] FAIL ({len(violations)} violations)", file=sys.stderr)
    for vi in violations:
        print(f"  - [{vi.code}] {vi.message}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
