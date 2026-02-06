#!/usr/bin/env python3
"""
Close a measurement session: hash the JSONL ledger, write session_close.json, optionally zip.

Usage:
    python scripts/session_close.py --session-dir ./out/session_S_20251228_A --operator "Ross"
    python scripts/session_close.py --session-dir ./out/session_S_20251228_A --operator "Ross" --zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED


def utc_now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl_count(path: Path) -> Tuple[int, int]:
    """
    Returns (line_count, parseable_count). JSONL may contain blank lines or partial last line.
    We'll count lines, and also count parseable JSON objects.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    line_count = 0
    parseable = 0
    for ln in lines:
        if not ln.strip():
            continue
        line_count += 1
        try:
            json.loads(ln)
            parseable += 1
        except Exception:
            # Ignore malformed line; a partial last line can happen after crashes.
            pass
    return line_count, parseable


def scan_jsonl_lines(path: Path) -> Tuple[List[str], int, int, Optional[int]]:
    """
    Returns:
      lines: original lines (including blank lines)
      nonblank_count: number of non-blank lines
      parseable_count: number of non-blank lines that parse as JSON
      last_bad_idx: index into `lines` of the last non-blank line that failed JSON parse, else None
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nonblank = 0
    ok = 0
    last_bad_idx: Optional[int] = None

    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        nonblank += 1
        try:
            json.loads(ln)
            ok += 1
        except Exception:
            last_bad_idx = i

    return lines, nonblank, ok, last_bad_idx


def get_jsonl_context(lines: list[str], bad_idx: int, n_prev: int) -> list[dict[str, Any]]:
    """
    Returns up to n_prev preceding NON-BLANK lines before bad_idx, with their original indexes.
    Ordered from oldest->newest.
    """
    out: list[dict[str, Any]] = []
    if n_prev <= 0:
        return out

    i = bad_idx - 1
    while i >= 0 and len(out) < n_prev:
        if lines[i].strip():
            out.append({"idx": i, "line": lines[i]})
        i -= 1

    out.reverse()
    return out


def classify_malformed_jsonl_line(line: str) -> str:
    """
    Rough, dependency-free classification for a malformed JSONL line.
    Tags are heuristic — meant to quickly diagnose common corruption modes.
    """
    s = line

    # Encoding/BOM oddities
    if s.startswith("\ufeff"):
        return "BOM/ENCODING"

    # Strip leading/trailing whitespace for classification
    t = s.strip()
    if not t:
        return "BLANK/WHITESPACE"

    # High proportion of non-printable control chars often indicates binary / encoding damage
    nonprint = sum(1 for ch in t if (ord(ch) < 32 and ch not in "\t\r\n"))
    if len(t) > 0 and (nonprint / len(t)) > 0.10:
        return "BINARY/ENCODING_NOISE"

    # Obvious "should be JSON but cut off" patterns
    if t.startswith("{") or t.startswith("["):
        # If it starts like JSON but doesn't end like JSON, likely truncated
        if not (t.endswith("}") or t.endswith("]")):
            return "TRUNCATED_JSON"
        # Ends properly but still doesn't parse: could be quoting/escape damage
        return "JSON_SYNTAX_ERROR"

    # JSONL should usually start with '{' (object per line); if not, probably garbage
    # But detect common cases:
    if t[0] in "\"'":
        return "STRING_LINE_NOT_OBJECT"
    if t[0].isdigit() or t.startswith("-"):
        return "NUMBER_LINE_NOT_OBJECT"
    if t.lower().startswith(("true", "false", "null")):
        return "LITERAL_LINE_NOT_OBJECT"

    # If it contains lots of braces but doesn't start with one, could be prefixed junk
    if "{" in t or "[" in t:
        return "PREFIXED_OR_GARBLED_JSON"

    return "NON_JSON_GARBAGE"


def suggest_action_for_tag(tag: str) -> str:
    """
    Returns a one-line suggested action for a given malformed line classification tag.
    """
    tag = (tag or "").strip().upper()

    suggestions = {
        "TRUNCATED_JSON": "Likely partial write/crash at EOF → try --repair-ledger (safe only if malformed line is last non-blank).",
        "JSON_SYNTAX_ERROR": "JSON-looking but invalid → inspect the line; compare with prior context (--show-bad-line-context) and consider regenerating that entry.",
        "BOM/ENCODING": "UTF-8 BOM/encoding anomaly → rewrite file as UTF-8 without BOM; avoid mixed editors; re-run scan.",
        "BINARY/ENCODING_NOISE": "Looks like binary/control chars → file corruption or wrong encoding; restore from backup (.bak) if available.",
        "PREFIXED_OR_GARBLED_JSON": "Line may have junk prefix/suffix → inspect surrounding context; search for log prefixes; consider stripping known prefixes at write-time.",
        "NON_JSON_GARBAGE": "Not JSON-like → inspect context lines; determine source (log spam, accidental append); fix generator before repair.",
        "STRING_LINE_NOT_OBJECT": "Ledger line is a string literal → verify writer; JSONL entries should be objects; inspect generator and context.",
        "NUMBER_LINE_NOT_OBJECT": "Ledger line is numeric → verify writer; JSONL entries should be objects; inspect generator and context.",
        "LITERAL_LINE_NOT_OBJECT": "Ledger line is true/false/null → verify writer; JSONL entries should be objects; inspect generator and context.",
        "BLANK/WHITESPACE": "Blank line is usually harmless → ignore unless your tooling forbids it; keep parseability threshold based on non-blank lines.",
    }

    return suggestions.get(tag, "Inspect the malformed line and nearby context; decide whether repair is safe or restore from backup.")


def scan_all_malformed_jsonl_indexes(path: Path, sample_k: int = 0, keep_full: bool = False) -> Dict[str, Any]:
    """
    Returns summary + list of malformed line indexes (0-based file line index).
    If sample_k > 0, includes a sample prefix for each malformed line.
    If keep_full is True, includes the full line text for classification.
    """
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nonblank = 0
    ok = 0
    bad_indexes: list[int] = []
    bad_samples: list[dict[str, Any]] = []

    k = max(0, int(sample_k))
    need_full = bool(keep_full)

    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        nonblank += 1
        try:
            json.loads(ln)
            ok += 1
        except Exception:
            bad_indexes.append(i)
            if k > 0 or need_full:
                s_prefix = (ln[:k] + ("…" if len(ln) > k else "")) if k > 0 else None
                rec: dict[str, Any] = {"idx": i}
                if s_prefix is not None:
                    rec["sample"] = s_prefix
                if need_full:
                    rec["full_line"] = ln
                bad_samples.append(rec)

    return {
        "ledger_path": path.as_posix(),
        "total_lines_in_file": len(lines),
        "nonblank_lines": nonblank,
        "parseable_lines": ok,
        "malformed_count": len(bad_indexes),
        "malformed_indexes": bad_indexes,
        "malformed_samples": bad_samples if (k > 0 or need_full) else None,
        "sample_k": k if k > 0 else None,
    }


def repair_ledger_truncate_last_bad_line(path: Path, backup_suffix: str = ".bak") -> Dict[str, Any]:
    """
    Repairs by truncating the last malformed non-blank line if (and only if) it is the LAST non-blank line.
    Creates a backup first. Returns a dict describing what happened.
    """
    lines, nonblank, ok, last_bad_idx = scan_jsonl_lines(path)

    if nonblank == 0:
        return {"repaired": False, "reason": "ledger_empty"}

    if last_bad_idx is None:
        return {"repaired": False, "reason": "no_malformed_lines"}

    # Find last non-blank line index
    last_nonblank_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_nonblank_idx = i
            break

    if last_nonblank_idx is None:
        return {"repaired": False, "reason": "ledger_all_blank"}

    # Only safe to truncate if the malformed line is the last non-blank line (classic partial write).
    if last_bad_idx != last_nonblank_idx:
        return {
            "repaired": False,
            "reason": "malformed_not_last_line",
            "last_bad_idx": last_bad_idx,
            "last_nonblank_idx": last_nonblank_idx,
        }

    # Backup
    backup_path = path.with_suffix(path.suffix + backup_suffix) if path.suffix else path.with_name(path.name + backup_suffix)
    backup_path.write_bytes(path.read_bytes())

    # Truncate: remove that last malformed line, preserve earlier lines exactly.
    repaired_lines = lines[:last_bad_idx]  # drop the bad line
    # Preserve trailing newline in the output for cleanliness
    repaired_text = "\n".join(repaired_lines).rstrip("\n") + "\n" if repaired_lines else ""
    path.write_text(repaired_text, encoding="utf-8")

    # Re-scan post repair
    _, nonblank2, ok2, last_bad2 = scan_jsonl_lines(path)

    return {
        "repaired": True,
        "reason": "truncated_last_malformed_line",
        "backup_path": backup_path.as_posix(),
        "dropped_line_index": last_bad_idx,
        "before": {"nonblank_lines": nonblank, "parseable_lines": ok},
        "after": {"nonblank_lines": nonblank2, "parseable_lines": ok2, "last_bad_idx": last_bad2},
    }


def ledger_has_blank_lines(path: Path) -> bool:
    """Returns True if the ledger contains any blank or whitespace-only lines."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return any((ln == "" or ln.strip() == "") for ln in lines)


def auto_repair_ledger_if_tag(
    ledger_path: Path,
    *,
    required_tag: str,
    backup_suffix: str,
    max_drop: int = 1,
    require_no_blank_lines: bool = False,
) -> Dict[str, Any]:
    """
    Auto-repair strategy:
      - Scan all malformed lines and classify them.
      - Only proceed if:
          (a) malformed lines exist
          (b) EVERY malformed line has classify == required_tag
          (c) ALL malformed lines are confined to the end-of-file region (i.e., they are the last non-blank lines)
          (d) count of trailing malformed non-blank lines <= max_drop
      - Repair action:
          truncate those trailing malformed non-blank lines
      - Always writes backup first.
    Returns a dict describing what happened.
    """
    req = (required_tag or "").strip().upper()
    if not req:
        return {"repaired": False, "reason": "no_required_tag"}

    if require_no_blank_lines and ledger_has_blank_lines(ledger_path):
        return {
            "repaired": False,
            "reason": "blank_lines_present_refusing_auto_repair",
            "required_tag": req,
        }

    lines = ledger_path.read_text(encoding="utf-8", errors="replace").splitlines()

    # Gather non-blank line indexes and parseability
    nonblank_indexes: list[int] = [i for i, ln in enumerate(lines) if ln.strip()]
    if not nonblank_indexes:
        return {"repaired": False, "reason": "ledger_empty_or_all_blank"}

    malformed: list[dict[str, Any]] = []
    for i in nonblank_indexes:
        ln = lines[i]
        try:
            json.loads(ln)
        except Exception:
            tag = classify_malformed_jsonl_line(ln)
            malformed.append({"idx": i, "tag": tag, "line": ln})

    if not malformed:
        return {"repaired": False, "reason": "no_malformed_lines"}

    # Check all tags match required
    bad_tags = sorted({m["tag"] for m in malformed if m["tag"] != req})
    if bad_tags:
        return {
            "repaired": False,
            "reason": "tags_not_all_match",
            "required_tag": req,
            "other_tags": bad_tags,
            "malformed_count": len(malformed),
        }

    # Identify trailing non-blank region
    # We only allow malformed lines that are the final non-blank lines.
    trailing_malformed_idxs: list[int] = []
    for idx in reversed(nonblank_indexes):
        # if this non-blank line is malformed, keep counting
        if any(m["idx"] == idx for m in malformed):
            trailing_malformed_idxs.append(idx)
        else:
            break  # hit first good line; stop trailing scan

    trailing_malformed_idxs = list(reversed(trailing_malformed_idxs))  # oldest->newest

    if not trailing_malformed_idxs:
        return {"repaired": False, "reason": "no_trailing_malformed_lines"}

    # Ensure there are NO malformed lines outside trailing region
    trailing_set = set(trailing_malformed_idxs)
    outside = [m["idx"] for m in malformed if m["idx"] not in trailing_set]
    if outside:
        return {
            "repaired": False,
            "reason": "malformed_not_confined_to_eof",
            "outside_malformed_indexes": sorted(outside),
            "trailing_malformed_indexes": trailing_malformed_idxs,
        }

    max_drop = max(1, int(max_drop))
    if len(trailing_malformed_idxs) > max_drop:
        return {
            "repaired": False,
            "reason": "too_many_trailing_malformed_lines",
            "trailing_malformed_count": len(trailing_malformed_idxs),
            "max_drop": max_drop,
            "trailing_malformed_indexes": trailing_malformed_idxs,
        }

    # Backup
    backup_path = ledger_path.with_suffix(ledger_path.suffix + backup_suffix) if ledger_path.suffix else ledger_path.with_name(ledger_path.name + backup_suffix)
    backup_path.write_bytes(ledger_path.read_bytes())

    # Truncate: remove those trailing malformed lines (preserve others)
    drop_set = set(trailing_malformed_idxs)
    kept_lines = [ln for i, ln in enumerate(lines) if i not in drop_set]

    repaired_text = "\n".join(kept_lines).rstrip("\n") + "\n"
    ledger_path.write_text(repaired_text, encoding="utf-8")

    # Post-scan summary
    post = scan_all_malformed_jsonl_indexes(ledger_path, sample_k=0, keep_full=False)

    return {
        "repaired": True,
        "reason": "auto_repair_truncated_trailing_malformed",
        "required_tag": req,
        "backup_path": backup_path.as_posix(),
        "dropped_line_indexes": trailing_malformed_idxs,
        "after": {
            "malformed_count": post["malformed_count"],
            "nonblank_lines": post["nonblank_lines"],
            "parseable_lines": post["parseable_lines"],
        },
    }


def get_last_malformed_line_preview(path: Path, context_n: int = 0) -> Dict[str, Any]:
    """
    Returns a preview dict:
      - can_truncate: bool (only if malformed line is the last non-blank line)
      - last_bad_idx, last_nonblank_idx
      - bad_line (string) if present
      - context_prev: list of preceding non-blank lines (if context_n > 0)
      - reason if not safe
    """
    lines, nonblank, ok, last_bad_idx = scan_jsonl_lines(path)

    if nonblank == 0:
        return {"can_truncate": False, "reason": "ledger_empty"}

    if last_bad_idx is None:
        return {"can_truncate": False, "reason": "no_malformed_lines"}

    last_nonblank_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            last_nonblank_idx = i
            break

    if last_nonblank_idx is None:
        return {"can_truncate": False, "reason": "ledger_all_blank"}

    if last_bad_idx != last_nonblank_idx:
        ctx = get_jsonl_context(lines, last_bad_idx, context_n)
        return {
            "can_truncate": False,
            "reason": "malformed_not_last_line",
            "last_bad_idx": last_bad_idx,
            "last_nonblank_idx": last_nonblank_idx,
            "bad_line": lines[last_bad_idx],
            "context_prev": ctx,
        }

    ctx = get_jsonl_context(lines, last_bad_idx, context_n)
    return {
        "can_truncate": True,
        "reason": "truncatable_last_malformed_line",
        "last_bad_idx": last_bad_idx,
        "last_nonblank_idx": last_nonblank_idx,
        "bad_line": lines[last_bad_idx],
        "context_prev": ctx,
    }


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def strip_nulls(x: Any) -> Any:
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            vv = strip_nulls(v)
            if vv is None:
                continue
            out[k] = vv
        return out
    if isinstance(x, list):
        return [strip_nulls(v) for v in x]
    return x


def parse_percent(s: str) -> float:
    """Parse a percent string like '100%' or '99.5%' into a float 0-100."""
    s = s.strip()
    if s.endswith("%"):
        s = s[:-1].strip()
    try:
        v = float(s)
    except Exception:
        raise ValueError(f"Invalid percent value: {s!r} (expected like 100% or 99.5%)")
    if v < 0.0 or v > 100.0:
        raise ValueError(f"Percent out of range: {v} (expected 0..100)")
    return v


def zip_dir(
    src_dir: Path,
    dst_zip: Path,
    *,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> None:
    """
    Zips the session directory with relative paths.
    Patterns use simple suffix matching and substring checks (kept minimal + dependency-free).
    """
    dst_zip.parent.mkdir(parents=True, exist_ok=True)

    def included(rel: str) -> bool:
        if exclude_patterns:
            for p in exclude_patterns:
                if p in rel:
                    return False
        if not include_patterns:
            return True
        for p in include_patterns:
            if rel.endswith(p) or p in rel:
                return True
        return False

    with ZipFile(dst_zip, "w", compression=ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(src_dir).as_posix()
            if included(rel):
                zf.write(p, arcname=rel)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="session_close",
        description="Close a measurement session: hash the JSONL ledger, write session_close.json, optionally zip.",
    )
    ap.add_argument("--session-dir", required=True, help="Path to session_<id>/ directory.")
    ap.add_argument("--session-id", default=None, help="Session id (if omitted, derived from folder name).")
    ap.add_argument("--operator", default=os.getenv("USER") or os.getenv("USERNAME") or None, help="Signer/operator name.")
    ap.add_argument("--signer", default=None, help="Optional distinct signer name (defaults to operator).")

    ap.add_argument("--ledger", default="session_manifest.jsonl", help="Ledger filename within session dir.")
    ap.add_argument("--calibration", default="session_calibration.json", help="Calibration filename within session dir.")
    ap.add_argument("--close-out", default="session_close.json", help="Close file name to write within session dir.")

    ap.add_argument("--zip", action="store_true", help="If set, produce a session_<id>.zip archive.")
    ap.add_argument("--zip-out", default=None, help="Optional output path for zip. Default: <session_dir>/../session_<id>.zip")

    # Safety knobs
    ap.add_argument(
        "--zip-exclude",
        action="append",
        default=[],
        help="Exclude pattern substring (repeatable). Example: --zip-exclude .venv --zip-exclude __pycache__",
    )
    ap.add_argument(
        "--require-ledger-parseable",
        default=None,
        help="Fail unless at least this percent of non-blank JSONL lines parse as JSON. Examples: 100%%, 95%%, 99.5%%",
    )
    ap.add_argument(
        "--repair-ledger",
        action="store_true",
        help="Attempt to repair ledger JSONL by truncating the last malformed non-blank line. Creates a .bak backup. Explicit only.",
    )
    ap.add_argument(
        "--repair-backup-suffix",
        default=".bak",
        help="Backup suffix to use when repairing (default: .bak).",
    )
    ap.add_argument(
        "--auto-repair-if",
        type=str,
        default=None,
        help="Auto-attempt repair only if ALL malformed lines classify as this TAG and are safely truncatable at EOF (e.g., TRUNCATED_JSON).",
    )
    ap.add_argument(
        "--auto-repair-max-drop",
        type=int,
        default=1,
        help="Maximum number of trailing malformed non-blank lines allowed to drop during auto-repair (default 1).",
    )
    ap.add_argument(
        "--auto-repair-if-only",
        action="store_true",
        help="Stricter auto-repair: refuse to auto-repair if the ledger contains ANY blank/whitespace-only lines.",
    )
    ap.add_argument(
        "--repair-dry-run",
        action="store_true",
        help="Dry-run ledger repair: report what would be truncated (and show the last malformed line) without modifying files.",
    )
    ap.add_argument(
        "--show-bad-line-context",
        type=int,
        default=0,
        help="When reporting a malformed JSONL line, also print N preceding non-blank lines for context (default 0).",
    )
    ap.add_argument(
        "--scan-all-malformed",
        action="store_true",
        help="Scan the ledger and list every malformed non-blank JSONL line index (no file modifications).",
    )
    ap.add_argument(
        "--scan-all-malformed-max",
        type=int,
        default=50,
        help="Maximum malformed line indexes to print (default 50).",
    )
    ap.add_argument(
        "--scan-all-malformed-with-sample",
        type=int,
        default=0,
        help="When scanning malformed lines, also print the first K characters of each malformed line (default 0 = off).",
    )
    ap.add_argument(
        "--scan-all-malformed-classify",
        action="store_true",
        help="When scanning malformed lines with samples, print a rough classification tag per line (no deps).",
    )
    ap.add_argument(
        "--scan-all-malformed-suggest-action",
        action="store_true",
        help="When scanning malformed lines with classify, also print a one-line suggested action per tag.",
    )
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    session_dir = Path(args.session_dir).expanduser().resolve()
    if not session_dir.exists() or not session_dir.is_dir():
        raise SystemExit(f"ERROR: session-dir not found or not a dir: {session_dir}")

    session_id = args.session_id or session_dir.name.replace("session_", "")
    operator = args.operator or "unknown"
    signer = args.signer or operator

    ledger_path = session_dir / args.ledger
    if not ledger_path.exists():
        raise SystemExit(f"ERROR: ledger not found: {ledger_path}")

    # Scan-all-malformed inspection mode (no modifications, no close file written)
    if args.scan_all_malformed:
        # --suggest-action implies --classify behavior
        want_suggest = bool(args.scan_all_malformed_suggest_action)
        want_classify = bool(args.scan_all_malformed_classify) or want_suggest

        summary = scan_all_malformed_jsonl_indexes(
            ledger_path,
            sample_k=int(args.scan_all_malformed_with_sample or 0),
            keep_full=want_classify,
        )

        malformed = summary["malformed_indexes"]
        max_n = max(0, int(args.scan_all_malformed_max))
        samples = summary.get("malformed_samples") or []
        k = summary.get("sample_k") or 0

        print("Ledger malformed scan (JSONL)")
        print(f"Ledger: {ledger_path}")
        print(
            f"Non-blank lines: {summary['nonblank_lines']} | "
            f"Parseable: {summary['parseable_lines']} | "
            f"Malformed: {summary['malformed_count']}"
        )

        if malformed:
            if k > 0 or want_classify:
                if k > 0:
                    print(f"Malformed lines (0-based), showing up to {max_n} with first {k} chars:")
                else:
                    print(f"Malformed lines (0-based), showing up to {max_n}:")
                # samples already correspond to all malformed lines in order
                shown = samples[:max_n]
                for item in shown:
                    tag = ""
                    suggest = ""
                    if want_classify:
                        full = item.get("full_line") or ""
                        tag_val = classify_malformed_jsonl_line(full)
                        tag = f"[{tag_val}] "
                        if want_suggest:
                            suggest = suggest_action_for_tag(tag_val)
                    sample_txt = item.get("sample")
                    if sample_txt is None:
                        # If user forgot sample flag, still show a short prefix for readability
                        full = item.get("full_line") or ""
                        sample_txt = full[:120] + ("…" if len(full) > 120 else "")
                    print(f"  - {item['idx']}: {tag}{sample_txt}")
                    if suggest:
                        print(f"      ↳ {suggest}")
                if len(malformed) > max_n:
                    print(f"  ... (+{len(malformed) - max_n} more)")
            else:
                print(f"Malformed line indexes (0-based), showing up to {max_n}:")
                for idx in malformed[:max_n]:
                    print(f"  - {idx}")
                if len(malformed) > max_n:
                    print(f"  ... (+{len(malformed) - max_n} more)")
            # Exit code 2 indicates corruption exists (useful in scripts/CI)
            return 2

        print("No malformed JSONL lines detected.")
        return 0

    # Dry-run preview (no modifications, early exit)
    if args.repair_dry_run:
        preview = get_last_malformed_line_preview(ledger_path, context_n=max(0, args.show_bad_line_context))

        print("Ledger repair dry-run preview")
        print(f"Ledger: {ledger_path}")
        print(f"Result: {preview.get('reason')}")
        if "last_bad_idx" in preview:
            print(f"last_bad_idx: {preview.get('last_bad_idx')}  last_nonblank_idx: {preview.get('last_nonblank_idx')}")

        # Print context lines if requested
        ctx = preview.get("context_prev") or []
        if ctx:
            print(f"---- context: {len(ctx)} preceding non-blank line(s) ----")
            for item in ctx:
                print(f"[{item['idx']}] {item['line']}")
            print("---- end context ----")

        if preview.get("bad_line") is not None:
            # Show the exact line that would be truncated / is malformed
            print("---- last malformed line (verbatim) ----")
            print(preview["bad_line"])
            print("---- end ----")

        # Exit code:
        # 0 = nothing to repair OR repair is possible (informational)
        # 2 = malformed exists but not safely truncatable (signals deeper corruption)
        if preview.get("reason") == "malformed_not_last_line":
            return 2
        return 0

    calibration_path = session_dir / args.calibration
    close_path = session_dir / args.close_out

    # Scan ledger (and optionally repair)
    repair_info: Optional[Dict[str, Any]] = None
    _, ledger_lines, ledger_parseable, last_bad_idx = scan_jsonl_lines(ledger_path)

    # Auto-repair (explicit) takes precedence over manual repair flag
    if args.auto_repair_if and not args.repair_dry_run:
        repair_info = auto_repair_ledger_if_tag(
            ledger_path,
            required_tag=args.auto_repair_if,
            backup_suffix=args.repair_backup_suffix,
            max_drop=args.auto_repair_max_drop,
            require_no_blank_lines=bool(args.auto_repair_if_only),
        )
        # Re-scan after potential repair
        _, ledger_lines, ledger_parseable, last_bad_idx = scan_jsonl_lines(ledger_path)
    elif args.repair_ledger and not args.repair_dry_run:
        repair_info = repair_ledger_truncate_last_bad_line(ledger_path, backup_suffix=args.repair_backup_suffix)
        # Re-scan after potential repair
        _, ledger_lines, ledger_parseable, last_bad_idx = scan_jsonl_lines(ledger_path)

    # Hash after potential repair
    ledger_sha = sha256_file(ledger_path)

    # Enforce ledger integrity threshold if requested
    if args.require_ledger_parseable is not None:
        required_pct = parse_percent(args.require_ledger_parseable)

        # If there are zero non-blank lines, treat as 0% parseable (explicit)
        actual_pct = (ledger_parseable / ledger_lines * 100.0) if ledger_lines > 0 else 0.0

        if actual_pct + 1e-9 < required_pct:
            raise SystemExit(
                f"ERROR: ledger parseability check failed: "
                f"{ledger_parseable}/{ledger_lines} parseable lines = {actual_pct:.3f}% "
                f"(required >= {required_pct:.3f}%). "
                f"Ledger: {ledger_path}"
            )

    calibration_sha = sha256_file(calibration_path) if calibration_path.exists() else None

    close_obj: Dict[str, Any] = {
        "schema": {
            "name": "session_close",
            "version": "1.0",
            "created_at_utc": utc_now_iso(),
        },
        "session": {
            "session_id": session_id,
            "session_dir_name": session_dir.name,
        },
        "signing": {
            "operator": operator,
            "signer": signer,
        },
        "artifacts": {
            "ledger": {
                "relpath": ledger_path.relative_to(session_dir).as_posix(),
                "sha256": ledger_sha,
                "lines": ledger_lines,
                "parseable_lines": ledger_parseable,
            },
            "calibration": {
                "present": calibration_path.exists(),
                "relpath": calibration_path.relative_to(session_dir).as_posix() if calibration_path.exists() else None,
                "sha256": calibration_sha,
            },
        },
        "ledger_repair": repair_info,
        "zip": None,
    }

    # Write session_close.json (atomic-ish)
    tmp = close_path.with_suffix(".tmp")
    write_json(tmp, strip_nulls(close_obj))
    tmp.replace(close_path)

    # Optional zip archive
    if args.zip:
        if args.zip_out:
            zip_path = Path(args.zip_out).expanduser().resolve()
        else:
            zip_path = session_dir.parent / f"session_{session_id}.zip"

        # Default excludes
        excludes = list(args.zip_exclude or [])
        # Always exclude common junk unless user wants them
        for p in [".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".DS_Store"]:
            if p not in excludes:
                excludes.append(p)

        zip_dir(session_dir, zip_path, exclude_patterns=excludes)

        zip_sha = sha256_file(zip_path)
        # Update close file with zip info
        close_obj["zip"] = {
            "created": True,
            "relpath": zip_path.resolve().as_posix(),
            "sha256": zip_sha,
            "bytes": zip_path.stat().st_size,
            "excluded_patterns": excludes,
        }
        tmp2 = close_path.with_suffix(".tmp")
        write_json(tmp2, strip_nulls(close_obj))
        tmp2.replace(close_path)

        print(f"Wrote: {close_path}")
        print(f"Zip:   {zip_path} ({zip_path.stat().st_size} bytes)")
        return 0

    print(f"Wrote: {close_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
