#!/usr/bin/env python3
"""Summarize a vectorizer-regression run (VECTORIZER-CI-BOUNDARY-001).

Reads the pytest JUnit XML and the optional Melody Maker metrics file written by
tests/test_text_masking_regression.py, writes one compact metrics JSON, and prints
a Markdown summary for $GITHUB_STEP_SUMMARY.

A skipped test is reported as NOT COVERED, never as passing coverage: the Cuatro
cases skip structurally because their PDF is not committed.
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def read_junit(path: Path) -> list[dict]:
    if not path.exists():
        return []
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        status, detail = "passed", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                status = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                detail = node.get("message", "")
                break
        cases.append({
            # A module skipped at import (e.g. a missing optional dependency) is
            # reported by pytest as a testcase with an empty classname. It is not
            # a test this lane selected, so it is kept apart from coverage.
            "collection_skip": not case.get("classname"),
            "test": f"{case.get('classname')}::{case.get('name')}",
            "status": status,
            "time_s": round(float(case.get("time") or 0.0), 1),
            "detail": detail,
        })
    return cases


def build(junit: Path, metrics: Path) -> dict:
    cases = read_junit(junit)
    melody = json.loads(metrics.read_text(encoding="utf-8")) if metrics.exists() else None
    selected = [c for c in cases if not c["collection_skip"]]
    return {
        "schema": "vectorizer_regression_metrics_v1",
        "tests": selected,
        "not_covered": [c["test"] for c in selected if c["status"] == "skipped"],
        "collection_skips_outside_lane": [c["test"].lstrip(":") for c in cases if c["collection_skip"]],
        "melody_maker": melody,
    }


def render(summary: dict) -> str:
    lines = ["## Vectorizer regression", "", "| Test | Status | Time (s) |", "|---|---|---:|"]
    for c in summary["tests"]:
        status = "NOT COVERED (skipped)" if c["status"] == "skipped" else c["status"]
        lines.append(f"| `{c['test']}` | {status} | {c['time_s']} |")
    if not summary["tests"]:
        lines.append("| (no JUnit report) | error | |")
    if summary["not_covered"]:
        lines += ["", "**Not covered by this run** (skipped; this is not regression coverage):", ""]
        lines += [f"- `{t}`" for t in summary["not_covered"]]
    if summary["collection_skips_outside_lane"]:
        lines += ["", "Modules skipped at collection, outside this lane: "
                  + ", ".join(f"`{m}`" for m in summary["collection_skips_outside_lane"])]
    mm = summary["melody_maker"]
    if mm:
        peak = "not reported" if mm["peak_rss_mb"] is None else f"{mm['peak_rss_mb']} MB"
        lines += ["", f"Fixture `{mm['fixture']}` sha256 `{mm['fixture_sha256']}`, peak RSS {peak}", "",
                  "| mask_text | DXF entities | ok | stage | Time (s) |", "|---|---:|---|---|---:|"]
        for conv in mm["conversions"]:
            lines.append(f"| {conv['mask_text']} | {conv['dxf_entity_count']:,} | {conv['ok']} | "
                         f"{conv['stage']} | {conv['elapsed_s']} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = build(args.junit, args.metrics)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
