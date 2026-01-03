"""
Endpoint Truth Gate
-------------------
CI guard that enforces your canonical endpoint map against the actual FastAPI app.

Usage:
  cd services/api
  python -m app.ci.endpoint_truth_gate check

Config (env):
  ENDPOINT_TRUTH_MAP_PATH:
    Path to ENDPOINT_TRUTH_MAP.md. If not set, we try a few common candidates.
  ENDPOINT_TRUTH_EXTRA_ALLOWLIST:
    Comma-separated list of METHOD:PATH entries to allow (e.g. "GET:/health,GET:/api/ping").
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple


MethodPath = Tuple[str, str]  # (METHOD, /path)


_BULLET_RE = re.compile(
    r"""^\s*(?:[-*]\s*)?(GET|POST|PUT|PATCH|DELETE|OPTIONS)\s+`?(/[^`\s]+)`?\s*$""",
    re.IGNORECASE,
)

_TABLE_RE = re.compile(
    r"""^\s*\|\s*(GET|POST|PUT|PATCH|DELETE|OPTIONS)\s*\|\s*`?(/[^`\s|]+)`?\s*\|""",
    re.IGNORECASE,
)


def _norm_path(path: str) -> str:
    # Keep "/" as-is, strip trailing slash elsewhere for stable comparisons.
    if path != "/" and path.endswith("/"):
        return path[:-1]
    return path


def _parse_method_path_token(token: str) -> Optional[MethodPath]:
    """
    Parse METHOD:PATH token from allowlist env.
    Example: "GET:/api/rmos/runs"
    """
    token = token.strip()
    if not token:
        return None
    if ":" not in token:
        return None
    m, p = token.split(":", 1)
    m = m.strip().upper()
    p = _norm_path(p.strip())
    if not p.startswith("/"):
        return None
    if m not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}:
        return None
    return (m, p)


def parse_expected_endpoints(markdown_text: str) -> Set[MethodPath]:
    """
    Extract expected endpoints from ENDPOINT_TRUTH_MAP.md.

    Supported formats:
      - Bullets or plain lines:
          GET /api/rmos/runs
          - POST `/api/rmos/runs`
      - Markdown tables:
          | GET | /api/rmos/runs | ...
    """
    expected: Set[MethodPath] = set()
    for line in markdown_text.splitlines():
        line = line.rstrip()
        if not line:
            continue

        m = _BULLET_RE.match(line)
        if m:
            method = m.group(1).upper()
            path = _norm_path(m.group(2))
            expected.add((method, path))
            continue

        t = _TABLE_RE.match(line)
        if t:
            method = t.group(1).upper()
            path = _norm_path(t.group(2))
            expected.add((method, path))
            continue

    return expected


def _default_truth_map_candidates() -> List[Path]:
    """
    Run from services/api, but support alternate working directories.
    """
    cwd = Path.cwd()

    # Typical locations (relative to services/api):
    candidates = [
        cwd / "ENDPOINT_TRUTH_MAP.md",
        cwd / "../ENDPOINT_TRUTH_MAP.md",
        cwd / "../../ENDPOINT_TRUTH_MAP.md",
        cwd / "docs/ENDPOINT_TRUTH_MAP.md",
        cwd / "../docs/ENDPOINT_TRUTH_MAP.md",
        cwd / "../../docs/ENDPOINT_TRUTH_MAP.md",
        cwd / "docs/governance/ENDPOINT_TRUTH_MAP.md",
        cwd / "../docs/governance/ENDPOINT_TRUTH_MAP.md",
        cwd / "../../docs/governance/ENDPOINT_TRUTH_MAP.md",
    ]

    # Also: repo-provided path env may be absolute.
    env_path = os.getenv("ENDPOINT_TRUTH_MAP_PATH")
    if env_path:
        candidates.insert(0, Path(env_path))

    # De-dup while preserving order.
    seen: Set[str] = set()
    out: List[Path] = []
    for p in candidates:
        rp = p.resolve() if p.exists() else p
        key = str(rp)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def load_truth_map_text() -> Tuple[Path, str]:
    """
    Locate and read ENDPOINT_TRUTH_MAP.md.
    """
    for candidate in _default_truth_map_candidates():
        try:
            if candidate.exists() and candidate.is_file():
                return (candidate, candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
    tried = "\n".join(str(p) for p in _default_truth_map_candidates())
    raise FileNotFoundError(
        "Could not locate ENDPOINT_TRUTH_MAP.md. "
        "Set ENDPOINT_TRUTH_MAP_PATH explicitly.\n"
        f"Tried:\n{tried}"
    )


def list_actual_endpoints() -> Set[MethodPath]:
    """
    Introspect FastAPI app routes and return a set of (METHOD, PATH).
    """
    # Import inside function so this module can be imported without side effects.
    from app.main import app  # type: ignore

    actual: Set[MethodPath] = set()

    # We only care about user endpoints, not docs/openapi.
    ignored_prefixes = (
        "/openapi.json",
        "/docs",
        "/redoc",
    )

    # APIRoute is the common case, but we avoid importing FastAPI internals directly.
    for r in getattr(app, "routes", []):
        path = getattr(r, "path", None)
        if not isinstance(path, str) or not path.startswith("/"):
            continue
        path = _norm_path(path)

        if any(path == p or path.startswith(p + "/") for p in ignored_prefixes):
            continue

        methods = getattr(r, "methods", None)
        if not methods:
            continue

        for m in methods:
            m_up = str(m).upper()
            # HEAD is typically auto-provided for GET; enforce GET only.
            if m_up == "HEAD":
                continue
            if m_up not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}:
                continue
            actual.add((m_up, path))

    return actual


def load_extra_allowlist() -> Set[MethodPath]:
    raw = os.getenv("ENDPOINT_TRUTH_EXTRA_ALLOWLIST", "").strip()
    if not raw:
        return set()
    out: Set[MethodPath] = set()
    for token in raw.split(","):
        mp = _parse_method_path_token(token)
        if mp:
            out.add(mp)
    return out


@dataclass(frozen=True)
class GateResult:
    truth_path: Path
    expected_count: int
    actual_count: int
    missing: List[MethodPath]
    unexpected: List[MethodPath]

    @property
    def ok(self) -> bool:
        return not self.missing and not self.unexpected


def run_check() -> GateResult:
    truth_path, text = load_truth_map_text()
    expected = parse_expected_endpoints(text)
    if not expected:
        raise RuntimeError(
            f"Parsed 0 endpoints from truth map: {truth_path}. "
            "Ensure it contains lines like `GET /api/...` or a table `| GET | /api/... |`."
        )

    actual = list_actual_endpoints()
    extra_allow = load_extra_allowlist()

    # Apply extra allowlist only to 'unexpected' outcomes.
    missing = sorted(expected - actual)
    unexpected = sorted((actual - expected) - extra_allow)

    return GateResult(
        truth_path=truth_path,
        expected_count=len(expected),
        actual_count=len(actual),
        missing=list(missing),
        unexpected=list(unexpected),
    )


def _fmt(mp: MethodPath) -> str:
    return f"{mp[0]} {mp[1]}"


def main(argv: Sequence[str]) -> int:
    if len(argv) < 2 or argv[1] not in {"check"}:
        print("Usage: python -m app.ci.endpoint_truth_gate check")
        return 2

    try:
        res = run_check()
    except Exception as e:
        print(f"[endpoint_truth_gate] ERROR: {e}")
        return 2

    print("[endpoint_truth_gate] Truth map:", res.truth_path)
    print(f"[endpoint_truth_gate] Expected: {res.expected_count} | Actual: {res.actual_count}")

    if res.missing:
        print("\n[endpoint_truth_gate] Missing endpoints (expected but not mounted):")
        for mp in res.missing[:200]:
            print("  -", _fmt(mp))
        if len(res.missing) > 200:
            print(f"  ... and {len(res.missing) - 200} more")

    if res.unexpected:
        print("\n[endpoint_truth_gate] Unexpected endpoints (mounted but not in truth map):")
        for mp in res.unexpected[:200]:
            print("  -", _fmt(mp))
        if len(res.unexpected) > 200:
            print(f"  ... and {len(res.unexpected) - 200} more")

    if res.ok:
        print("\n[endpoint_truth_gate] OK: app routes match ENDPOINT_TRUTH_MAP.md")
        return 0

    print("\n[endpoint_truth_gate] FAIL")
    print("Hints:")
    print("  - If ENDPOINT_TRUTH_MAP.md is missing routes, update it (truth source).")
    print("  - If the app is mounting legacy or debug routes you don't want, remove them or add shadow aliases.")
    print("  - For temporary exceptions, set ENDPOINT_TRUTH_EXTRA_ALLOWLIST='GET:/path,POST:/path2'")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
