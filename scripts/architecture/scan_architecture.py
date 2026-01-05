#!/usr/bin/env python3
"""
Architecture Scan Harness (v1)

Read-only scanner that detects structural risk signals and basic invariant
violations across selected repository paths.

Outputs:
  reports/architecture_scan.json

Design goals:
- No code execution (parses files as text)
- Deterministic output
- Low false-negative bias (ok to be a bit noisy in v1)
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ----------------------------
# Configuration (v1 defaults)
# ----------------------------

DEFAULT_TARGETS = [
    "services/api/app",
    "client/src",
]

# Only scan these file extensions (v1)
SCAN_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".yml", ".yaml", ".md",
}

# Keyword -> signal tag
KEYWORDS: Dict[str, str] = {
    # Machine-executable output signals
    "gcode": "GCODE",
    "emit_gcode": "GCODE_EMIT",
    ".nc": "GCODE_FILE",
    "dxf": "DXF",
    "ezdxf": "DXF_LIB",

    # Persistence / authority
    "store_artifact": "PERSISTENCE",
    "persist_run": "PERSISTENCE",
    "write_run_artifact": "PERSISTENCE",
    "read_run_artifact": "RMOS_READ",

    # Direct response (bypasses persistence)
    "Response(": "DIRECT_RESPONSE",
    "PlainTextResponse": "DIRECT_RESPONSE",
    "response_class=Response": "DIRECT_RESPONSE",
    "media_type=\"text/plain": "DIRECT_RESPONSE",

    # IDs / authority creation
    "uuid.uuid4": "ID_CREATION",
    "create_run_id": "ID_CREATION",

    # Safety / feasibility
    "risk_bucket": "RISK_EVAL",
    "should_block": "SAFETY_GATE",
    "compute_feasibility": "SAFETY_GATE",

    # Boundary / sandbox
    "_experimental": "EXPERIMENTAL",
}


INVARIANTS = [
    "GCODE_TRACEABLE",
    "AI_NO_AUTHORITY",
    "ADVISORY_ATTACHED",
]

# Heuristic: advisory signal
ADVISORY_KEYWORDS = {"advisory", "advisories", "attach_advisory", "advisory_id", "parent_id"}


@dataclass
class Finding:
    id: str
    type: str
    file: str
    signals: List[str]
    risk: str
    invariant_violated: str | None = None
    note: str | None = None


@dataclass
class ScanReport:
    scan_id: str
    scan_type: str
    mode: str
    timestamp_utc: str
    targets: List[str]
    risk_summary: Dict[str, int]
    invariants_checked: List[str]
    findings: List[Finding]
    findings_count: int
    # Metadata for clarity
    scan_scope: str = "repo_subset"
    targets_scanned: List[str] = None  # type: ignore  # Actual targets that existed
    files_scanned_count: int = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compute_scan_id() -> str:
    # Simple monotonic-ish id based on UTC timestamp (good enough for v1)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"AS-{ts}"


def iter_files(root: Path) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in SCAN_EXTS:
            out.append(p)
    return out


def read_text(path: Path) -> str:
    # Read as utf-8 with replacement to avoid hard failures on odd encodings
    return path.read_text(encoding="utf-8", errors="replace")


def detect_signals(text: str) -> Set[str]:
    signals: Set[str] = set()
    haystack = text  # v1: simple substring search (fast, deterministic)
    for kw, tag in KEYWORDS.items():
        if kw in haystack:
            signals.add(tag)
    return signals


def strip_comments(text: str) -> str:
    """
    Strip comments and docstrings from code for policy signal detection.

    Handles:
    - Python: # comments, '''docstrings''', \"\"\"docstrings\"\"\"
    - JS/TS/Vue: // comments

    This reduces false positives when authority keywords appear only in
    documentation/comments, not in executable code.
    """
    # Phase 1: Strip triple-quoted strings (Python docstrings)
    # Uses non-greedy match to handle multiple docstrings correctly
    # DOTALL flag makes . match newlines
    text = re.sub(r'""".*?"""', '""', text, flags=re.DOTALL)
    text = re.sub(r"'''.*?'''", "''", text, flags=re.DOTALL)

    # Phase 2: Strip line comments
    lines = text.split("\n")
    stripped: List[str] = []

    for line in lines:
        # Skip lines that are pure comments (after stripping whitespace)
        lstripped = line.lstrip()
        if lstripped.startswith("#") or lstripped.startswith("//"):
            continue

        # For mixed lines, try to strip trailing comments
        # (simple heuristic: find # or // not inside quotes)
        result = line
        for marker in ("#", "//"):
            idx = line.find(marker)
            if idx > 0:
                # Check if marker is likely inside a string (crude check)
                before = line[:idx]
                # Count quotes - if odd, marker is inside string
                single_quotes = before.count("'") - before.count("\\'")
                double_quotes = before.count('"') - before.count('\\"')
                if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                    result = line[:idx]
                    break

        stripped.append(result)

    return "\n".join(stripped)


def is_experimental_path(rel: str) -> bool:
    # Detect experimental sandbox areas
    return "/_experimental/" in rel.replace("\\", "/") or rel.replace("\\", "/").startswith("_experimental/")


def looks_like_advisory(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ADVISORY_KEYWORDS)


def risk_for(signals: Set[str], rel: str, text: str, signals_no_comments: Set[str] | None = None) -> str:
    """
    Conservative risk scoring:
      - critical: experimental authority creation OR experimental persistence
      - high: GCODE/DXF direct response without persistence (traceability break)
      - medium: multi-authority signals (>=3 distinct signal categories)
      - low: everything else flagged

    For critical/_experimental decisions, uses signals_no_comments to avoid
    false positives from comments mentioning authority keywords.
    """
    # Use comment-stripped signals for critical policy decisions
    policy_signals = signals_no_comments if signals_no_comments is not None else signals

    if is_experimental_path(rel):
        # CRITICAL only for true authority creation:
        # - persistence (store_artifact, persist_run, write_run_artifact)
        # - RMOS run-id creation (not ephemeral suggestion UUIDs)
        # - explicit enforcement gates (should_block, compute_feasibility)
        if "PERSISTENCE" in policy_signals:
            return "critical"

        # ID_CREATION is critical only if it looks like RMOS authority,
        # not advisory suggestion UUIDs (check in comment-stripped text)
        if "ID_CREATION" in policy_signals:
            text_to_check = strip_comments(text) if signals_no_comments is None else text
            if ("create_run_id" in text_to_check) or ("run_id" in text_to_check.lower()):
                return "critical"

        if "SAFETY_GATE" in policy_signals:
            return "critical"

    # GCODE / DXF traceability break
    machine = ("GCODE" in signals) or ("GCODE_EMIT" in signals) or ("GCODE_FILE" in signals) or ("DXF" in signals) or ("DXF_LIB" in signals)
    direct = "DIRECT_RESPONSE" in signals
    persistence = "PERSISTENCE" in signals
    if machine and direct and not persistence:
        return "high"

    # Advisory attachment heuristic: advisory code without parent_id mention tends to be risky
    if looks_like_advisory(text) and ("parent_id" not in text) and ("attach_advisory" not in text):
        return "medium"

    # Multi-authority heuristic
    if len(signals) >= 3:
        return "medium"

    return "low"


def invariant_violation(signals: Set[str], rel: str, text: str, signals_no_comments: Set[str] | None = None) -> Tuple[str | None, str | None]:
    """
    Return (invariant_id, note) if violated.

    For INV-002 (AI_NO_AUTHORITY), uses signals_no_comments to avoid
    false positives from comments mentioning authority keywords.
    """
    # INV-001: GCODE_TRACEABLE (uses all signals - comments don't affect this)
    machine = ("GCODE" in signals) or ("GCODE_EMIT" in signals) or ("GCODE_FILE" in signals) or ("DXF" in signals) or ("DXF_LIB" in signals)
    direct = "DIRECT_RESPONSE" in signals
    persistence = "PERSISTENCE" in signals
    if machine and direct and not persistence:
        return ("GCODE_TRACEABLE", "Machine-executable output appears to be returned directly without persistence/hash trail.")

    # INV-002: AI_NO_AUTHORITY (uses comment-stripped signals)
    policy_signals = signals_no_comments if signals_no_comments is not None else signals

    if is_experimental_path(rel):
        # Persistence is always a violation
        if "PERSISTENCE" in policy_signals:
            return ("AI_NO_AUTHORITY", "Experimental area appears to persist artifacts (authority creation).")

        # ID_CREATION is a violation only if it looks like RMOS run authority,
        # not ephemeral suggestion/session UUIDs (check in comment-stripped text)
        if "ID_CREATION" in policy_signals:
            text_to_check = strip_comments(text) if signals_no_comments is None else text
            if ("create_run_id" in text_to_check) or ("run_id" in text_to_check.lower()):
                return ("AI_NO_AUTHORITY", "Experimental area appears to create RMOS run IDs (authority creation).")

        # Safety gates are always a violation
        if "SAFETY_GATE" in policy_signals:
            return ("AI_NO_AUTHORITY", "Experimental area appears to make enforcement decisions (authority creation).")

    # INV-003: ADVISORY_ATTACHED (heuristic)
    if looks_like_advisory(text):
        # If it contains advisory but no parent_id / run linkage markers, flag
        tl = text.lower()
        if ("parent_id" not in tl) and ("run_id" not in tl) and ("attach_advisory" not in tl):
            return ("ADVISORY_ATTACHED", "Advisory-related code found without obvious parent run linkage (heuristic).")

    return (None, None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", nargs="*", default=DEFAULT_TARGETS, help="Directories to scan (repo-relative).")
    ap.add_argument("--out", default="reports/architecture_scan.json", help="Output JSON path.")
    ap.add_argument("--max-findings", type=int, default=500, help="Safety cap.")
    args = ap.parse_args()

    repo_root = Path(".").resolve()
    findings: List[Finding] = []

    # risk counts
    risk_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # Track metadata
    targets_scanned: List[str] = []
    files_scanned_count = 0

    fid = 1
    for target in args.targets:
        tpath = (repo_root / target).resolve()
        if not tpath.exists():
            continue

        targets_scanned.append(target)
        for f in iter_files(tpath):
            files_scanned_count += 1
            rel = str(f.relative_to(repo_root)).replace("\\", "/")
            txt = read_text(f)
            sig = detect_signals(txt)

            # Compute comment-stripped signals for policy decisions
            txt_nc = strip_comments(txt)
            sig_nc = detect_signals(txt_nc)

            # Only record files with any interesting signals
            if not sig and not looks_like_advisory(txt):
                continue

            # Use sig_nc for critical/policy decisions, sig for reporting
            risk = risk_for(sig, rel, txt, signals_no_comments=sig_nc)
            inv, note = invariant_violation(sig, rel, txt, signals_no_comments=sig_nc)

            # Only create findings for medium+ risk OR any invariant violation
            if risk in {"medium", "high", "critical"} or inv is not None:
                finding = Finding(
                    id=f"F-{fid:03d}",
                    type="ARCH_SIGNAL" if inv is None else "INVARIANT_VIOLATION",
                    file=rel,
                    signals=sorted(sig),
                    risk=risk,
                    invariant_violated=inv,
                    note=note,
                )
                findings.append(finding)
                risk_summary[risk] += 1
                fid += 1

                if len(findings) >= args.max_findings:
                    break

        if len(findings) >= args.max_findings:
            break

    report = ScanReport(
        scan_id=compute_scan_id(),
        scan_type="architecture",
        mode="read_only",
        timestamp_utc=utc_now(),
        targets=list(args.targets),
        risk_summary=risk_summary,
        invariants_checked=INVARIANTS,
        findings=findings,
        findings_count=len(findings),
        scan_scope="repo_subset",
        targets_scanned=targets_scanned,
        files_scanned_count=files_scanned_count,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                **asdict(report),
                "findings": [asdict(f) for f in findings],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # Console summary (non-blocking usage)
    print(f"[architecture-scan] wrote {out_path}")
    print(f"[architecture-scan] targets_scanned={targets_scanned}")
    print(f"[architecture-scan] files_scanned={files_scanned_count}, findings={len(findings)}")
    print(f"[architecture-scan] risk_summary={risk_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
