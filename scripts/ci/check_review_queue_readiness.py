#!/usr/bin/env python3
"""
Review queue architecture readiness check.

Answers: *are the declared operational prerequisites of the review-queue subsystem present
in this repository?* — deterministically, from repository evidence.

    python scripts/ci/check_review_queue_readiness.py --format text
    python scripts/ci/check_review_queue_readiness.py --format json --output report.json
    python scripts/ci/check_review_queue_readiness.py --report-only        # CI rollout mode

There is deliberately **no flag that lets a caller assert readiness**. Readiness is derived
from findings; that is the whole point of replacing the historical TD-2 design, which
recorded whatever readiness a caller claimed.

Exit codes — enforcement mode (default):

    READY                -> 0
    READY_WITH_WARNINGS  -> 0
    NOT_READY            -> 1
    EVALUATOR_ERROR      -> 2

Exit codes — ``--report-only`` (current CI rollout mode):

    READY / READY_WITH_WARNINGS / NOT_READY -> 0
    EVALUATOR_ERROR                         -> 2

An evaluator defect is never reported as a readiness verdict, in either mode. Report-only
suppresses *enforcement of known gaps*, never the truth of the report or a real failure.

Note on exit code 2: argparse also exits 2 for usage errors (an unknown ``--format``, for
instance). That overlap is intentional — both cases mean "no readiness verdict was
produced", which is precisely the distinction callers must be able to make. What must never
happen is a usage error or an evaluator defect being reported as READY or NOT_READY.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "services" / "api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from app.cam.review_queue_readiness import (  # noqa: E402
    AggregateReadiness,
    ReadinessEvaluationError,
    ReadinessStatus,
    ReviewQueueReadinessContext,
    ReviewQueueReadinessReport,
)
from app.cam.review_queue_readiness_evaluator import (  # noqa: E402
    evaluate_review_queue_readiness,
)
from app.cam.review_queue_readiness_evidence import (  # noqa: E402
    collect_readiness_evidence,
)
from app.cam.review_queue_readiness_requirements import get_requirements  # noqa: E402

EXIT_OK = 0
EXIT_NOT_READY = 1
EXIT_EVALUATOR_ERROR = 2

_STATUS_MARK = {
    ReadinessStatus.SATISFIED: "PASS",
    ReadinessStatus.UNSATISFIED: "FAIL",
    ReadinessStatus.UNRESOLVED_RUNTIME_VALIDATION_REQUIRED: "UNRESOLVED",
    ReadinessStatus.NOT_APPLICABLE: "N/A",
    ReadinessStatus.DEFERRED_BY_POLICY: "DEFERRED",
}


def readiness_exit_code(report: ReviewQueueReadinessReport) -> int:
    """Enforcement-mode exit code for a successfully produced report."""
    if report.aggregate is AggregateReadiness.NOT_READY:
        return EXIT_NOT_READY
    return EXIT_OK


def render_readiness_json(report: ReviewQueueReadinessReport) -> str:
    """Deterministic machine-readable output.

    Stable field names and ordering, an explicit schema version, and no timestamps,
    host-specific paths, or generated ids — the same tree always renders byte-identically.
    """
    return json.dumps(report.to_dict(), indent=2, sort_keys=False) + "\n"


def render_readiness_text(report: ReviewQueueReadinessReport, *, report_only: bool) -> str:
    """Stable human-readable output. Blocking findings first."""
    lines: List[str] = []
    lines.append("=" * 68)
    lines.append("Review Queue Architecture Readiness")
    lines.append("=" * 68)
    lines.append("")
    lines.append(f"Status: {report.aggregate.value}")
    if report_only:
        lines.append("Enforcement: DISABLED (--report-only) — findings do not fail this check.")
    else:
        lines.append("Enforcement: ENABLED — blocking findings fail this check.")
    lines.append("")

    blocking = report.blocking_failures
    if blocking:
        lines.append(f"Blocking ({len(blocking)}):")
        for f in blocking:
            lines.append(f"  [{_STATUS_MARK[f.status]}] {f.requirement_id} — {f.title}")
            lines.append(f"      {f.detail}")
            for src in f.evidence_sources:
                lines.append(f"      evidence: {src}")
        lines.append("")

    warnings = report.warnings
    if warnings:
        lines.append(f"Warnings ({len(warnings)}):")
        for f in warnings:
            lines.append(f"  [{_STATUS_MARK[f.status]}] {f.requirement_id} — {f.title}")
            lines.append(f"      {f.detail}")
        lines.append("")

    satisfied = [f for f in report.findings if f.status is ReadinessStatus.SATISFIED]
    if satisfied:
        lines.append(f"Satisfied ({len(satisfied)}):")
        for f in satisfied:
            lines.append(f"  [PASS] {f.requirement_id} — {f.title}")
        lines.append("")

    lines.append("-" * 68)
    lines.append(report.notice)
    lines.append("-" * 68)
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_review_queue_readiness",
        description="Evaluate review-queue architecture readiness from repository evidence.",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format."
    )
    parser.add_argument("--output", type=Path, default=None, help="Write output to a file.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help=(
            "Report findings without failing on known readiness gaps. Evaluator errors "
            "still fail. Used during the CI rollout phase."
        ),
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        context = ReviewQueueReadinessContext(
            requirements=get_requirements(),
            evidence=collect_readiness_evidence(),
        )
        report = evaluate_review_queue_readiness(context)
    except ReadinessEvaluationError as exc:
        print(f"EVALUATOR ERROR: {exc}", file=sys.stderr)
        return EXIT_EVALUATOR_ERROR
    except Exception as exc:  # noqa: BLE001 - any collector/contract failure is a defect
        print(f"EVALUATOR ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return EXIT_EVALUATOR_ERROR

    rendered = (
        render_readiness_json(report)
        if args.format == "json"
        else render_readiness_text(report, report_only=args.report_only)
    )

    if args.output is not None:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            # A user-input problem, not an evaluator defect — no stack trace.
            print(f"ERROR: cannot write --output {args.output}: {exc}", file=sys.stderr)
            return EXIT_EVALUATOR_ERROR
    else:
        sys.stdout.write(rendered)

    if args.report_only:
        return EXIT_OK
    return readiness_exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
