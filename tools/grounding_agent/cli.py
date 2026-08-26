"""Command-line interface for the Grounding Agent.

Usage::

    python -m tools.grounding_agent.cli --request path/to/request.json

Exit codes:

* 0 = MATCH / PROCEED
* 2 = STALE
* 3 = BLOCKED
* 4 = INSUFFICIENT_EVIDENCE
* 5 = malformed request / tool error

The CLI only reads. When ``--output`` is omitted it prints the JSON report to
stdout and writes nothing else.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .adapters.filesystem import FileSystemAdapter
from .adapters.git_repo import GitRepoAdapter
from .adapters.github_api import GitHubAdapter
from .engine import ground
from .models import GroundingRequest, GroundingStatus, MalformedRequestError

EXIT_MATCH = 0
EXIT_STALE = 2
EXIT_BLOCKED = 3
EXIT_INSUFFICIENT = 4
EXIT_TOOL_ERROR = 5

_STATUS_EXIT = {
    GroundingStatus.MATCH: EXIT_MATCH,
    GroundingStatus.STALE: EXIT_STALE,
    GroundingStatus.BLOCKED: EXIT_BLOCKED,
    GroundingStatus.INSUFFICIENT_EVIDENCE: EXIT_INSUFFICIENT,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grounding-agent",
        description="Read-only handoff truth check (Grounding Agent v0.1).",
    )
    parser.add_argument("--request", required=True, help="Path to a grounding request JSON file.")
    parser.add_argument("--output", help="Optional path to write the JSON report to.")
    parser.add_argument("--repo-root", default=".", help="Local git checkout root (default: cwd).")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the JSON report.")
    return parser


def _emit_tool_error(message: str) -> int:
    payload = {
        "schema_version": "grounding_report_v0.1",
        "status": "TOOL_ERROR",
        "decision": "STOP",
        "error": message,
    }
    print(json.dumps(payload), file=sys.stderr)
    return EXIT_TOOL_ERROR


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.request, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        return _emit_tool_error(f"request file not found: {args.request}")
    except json.JSONDecodeError as exc:
        return _emit_tool_error(f"invalid JSON in request: {exc}")
    except OSError as exc:
        return _emit_tool_error(f"could not read request: {exc}")

    try:
        request = GroundingRequest.from_dict(raw)
    except MalformedRequestError as exc:
        return _emit_tool_error(f"malformed request: {exc}")

    git = GitRepoAdapter(repo_root=args.repo_root)
    github = GitHubAdapter()
    fs = FileSystemAdapter()

    report = ground(request, git=git, github=github, fs=fs)
    report_dict = report.to_dict()
    text = json.dumps(report_dict, indent=2 if args.pretty else None, sort_keys=False)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        except OSError as exc:
            return _emit_tool_error(f"could not write output: {exc}")
    else:
        print(text)

    return _STATUS_EXIT[report.status]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
