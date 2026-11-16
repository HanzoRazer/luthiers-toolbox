"""Structural check for the blackwoods / Acacia-family documentation split.

TONEWOOD-BLACKWOODS-RECONCILIATION-003. The check is about roles, links,
headings, dispositions, and untouched FPL examples. It does not revalidate
a measurement.

Nothing in ``scripts/ci`` is collected unless a workflow names the file.
``.github/workflows/core_ci.yml`` names this one.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLACK_REL = "docs/tonewood/tonewood_comparison_blackwoods_african_vs_malaysian.md"
ACACIA_REL = "docs/tonewood/tonewood_comparison_acacia_family_blackwoods_koa.md"
LOG_REL = "docs/tonewood/VERIFICATION_LOG.md"
RECORD_REL = "docs/investigations/tonewood-verification-003/BLACKWOODS_RECONCILIATION.md"

BLACK = ROOT / BLACK_REL
ACACIA = ROOT / ACACIA_REL
LOG = ROOT / LOG_REL
RECORD = ROOT / RECORD_REL

ORIGINAL_SHA256 = {
    "blackwoods": "3059c59a319073918a48d7948e3d18d2c9ecb13895f7aa464bb9fc1515147f58",
    "acacia": "e8998f6876a86d4ce2f4b5f1b2d2ff0a5f3ac511b4953f38635f4c8e54bdb7dd",
}

TITLE = "# Tonewood Comparison: African Blackwood vs Malaysian Blackwood"

REQUIRED_BLACK_HEADINGS = (
    "## Purpose and limits",
    "## Species and trade-name identity",
    "## African versus Malaysian properties",
    "## Instrument-use implications",
    "## Availability, sourcing, and regulatory distinctions",
    "## Known evidence gaps",
    "## Shared reference",
    "## Sources for this comparison",
)

# Family-survey headings. They belong in the Acacia document. Their return
# in the focused comparison is the duplication this order removed.
PROHIBITED_BLACK_HEADINGS = (
    "## Nomenclature Clarification",
    "## Koa vs Blackwood: Are They Interchangeable?",
    "## Mangium: The Plantation Alternative",
    "## Part II: The Albizia Cousins — Monkeypod, Mugavu, and African Relatives",
    '## The "Malaysian Blackwood" Question',
    "## Summary: The Acacia Tonewood Family",
    "## Combined Family Summary",
)

PROHIBITED_PASSAGES = (
    "Malaysian Blackwood is simply *Acacia melanoxylon* grown in Malaysia",
    "Tasmanian, Malaysian, and Australian Blackwood are all *Acacia melanoxylon*",
)

# Figures printed in the comparison before this order. Presence, not a new
# calculation. A planted edit that drops one must fail.
PRESERVED_NUMBERS = (
    "1,270",
    "1,960",
    "640",
    "1,160",
    "1.27",
    "0.58",
    "8,719",
    "5,160",
    "17.95",
    "11.82",
    "213.6",
    "96.5",
    "4.38",
    "8.38",
    "14.1",
    "18.5",
    "~3,760",
    "~4,300",
    "~4.78",
    "~2.75",
    "0.48",
    "0.17",
    "1,238",
    "1,650",
    "0.98",
    "0.45",
    "0.56",
    "0.70",
    "0.28",
    "0.20",
    "0.16",
    "0.10",
    "3,200",
    "4,000",
    "14,480",
    "12,000",
)

ORIGINAL_SECTIONS = (
    "Source and generated lines",
    "Estimated Janka banner",
    "Identity caution",
    "Intro paragraph",
    "At a Glance",
    "Physical Properties",
    "Derived Acoustic Properties",
    'What Creates the "Glassy" vs "Warm" Tone Difference?',
    "The Builder's Observation",
    "The Physics Behind It",
    "Acoustic Mechanism Comparison",
    "Think of the Back/Sides as a Filter",
    "Thermal Properties",
    "CNC Machining",
    "Lutherie Profile",
    "Why This Matters for Modal Research",
    "Resonance Peaks",
    "Q Factor (Quality Factor)",
    "Decay Time",
    "Impedance Mismatch at Boundaries",
    "Working Hypothesis",
    "Analysis",
    "Not Actually Similar Woods",
    "Application Implications",
    "The Neck Effect",
    "Data Gaps to Address",
    "References",
)

DISPOSITIONS = {
    "KEEP_COMPARISON",
    "MOVE_TO_SHARED_REFERENCE",
    "REPLACE_WITH_LINK",
    "KEEP_WITH_CAVEAT",
    "PRESERVE_HISTORICAL_ONLY",
    "REQUIRES_SEPARATE_VERIFICATION",
}

ACACIA_BACKGROUND = (
    "## Nomenclature Clarification",
    "## Focused comparisons",
    "## Part II: The Albizia Cousins — Monkeypod, Mugavu, and African Relatives",
    "a Dalbergia, not an Acacia",
    "No source in this repo establishes that \"Malaysian Blackwood\" is *Acacia melanoxylon*",
    "*Acacia koa*",
    "*Acacia melanoxylon*",
    "Albizia is the sister genus to Acacia",
)

FPL_AND_DATA_PATHS = (
    "CLAUDE.md",
    "docs/process/wood_species_update_template.md",
    "docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv",
)

RECONCILIATION_MARKERS = {BLACK_REL, RECORD_REL}

SHA256_RE = re.compile(r"[0-9a-f]{64}")
NOT_REVALIDATED = (
    "No measurement in either document was independently revalidated by this reconciliation."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def markdown_link(text: str, filename: str) -> bool:
    return f"]({filename})" in text


def missing_headings(text: str, headings: tuple[str, ...]) -> list[str]:
    lines = {line.strip() for line in text.splitlines()}
    return [h for h in headings if h not in lines]


def prohibited_heading_hits(text: str) -> list[str]:
    lines = {line.strip() for line in text.splitlines()}
    return [h for h in PROHIBITED_BLACK_HEADINGS if h in lines]


def prohibited_passage_hits(text: str) -> list[str]:
    return [p for p in PROHIBITED_PASSAGES if p in text]


def missing_numbers(text: str) -> list[str]:
    return [n for n in PRESERVED_NUMBERS if n not in text]


def section_body(text: str, heading: str) -> str:
    """Body under one heading, up to the next heading of the same or higher level."""
    lines = text.splitlines()
    start = None
    level = heading.split(" ", 1)[0].count("#")
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            this = len(stripped) - len(stripped.lstrip("#"))
            if this <= level:
                break
        body.append(line)
    return "\n".join(body)


def disposition_rows(record: str) -> list[tuple[str, str]]:
    body = section_body(record, "## Blackwoods section dispositions")
    rows = []
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in {"Original section", "---"} or set(cells[0]) <= {"-"}:
            continue
        if re.fullmatch(r"-+", cells[0].replace(" ", "")):
            continue
        rows.append((cells[0], cells[1]))
    return rows


def invalid_dispositions(rows: list[tuple[str, str]]) -> list[str]:
    return [f"{name}: {disp}" for name, disp in rows if disp not in DISPOSITIONS]


def missing_sections(rows: list[tuple[str, str]]) -> list[str]:
    found = [name for name, _ in rows]
    missing = [name for name in ORIGINAL_SECTIONS if name not in found]
    dupes = [name for name in ORIGINAL_SECTIONS if found.count(name) > 1]
    return missing + [f"duplicate row: {name}" for name in dupes]


def o05_line(log: str) -> str:
    for line in log.splitlines():
        if "**O-05**" in line:
            return line
    return ""


def claims_o05_resolved(log: str) -> bool:
    line = o05_line(log)
    return "resolved as duplication only" in line and "Still open" not in line


def structural_problems(black: str, acacia: str) -> list[str]:
    problems: list[str] = []
    if not black.startswith(TITLE):
        problems.append("blackwoods title changed")
    if missing_headings(black, REQUIRED_BLACK_HEADINGS):
        problems.append("missing headings: " + ", ".join(missing_headings(black, REQUIRED_BLACK_HEADINGS)))
    hits = prohibited_heading_hits(black)
    if hits:
        problems.append("prohibited headings returned: " + "; ".join(hits))
    passages = prohibited_passage_hits(black) + prohibited_passage_hits(acacia)
    if passages:
        problems.append("prohibited passage returned")
    if not markdown_link(black, "tonewood_comparison_acacia_family_blackwoods_koa.md"):
        problems.append("blackwoods doc does not link to the Acacia reference")
    if not markdown_link(acacia, "tonewood_comparison_blackwoods_african_vs_malaysian.md"):
        problems.append("Acacia reference does not link to the focused comparison")
    if "## Focused comparisons" not in {line.strip() for line in acacia.splitlines()}:
        problems.append("Acacia reference has no Focused comparisons heading")
    for needle in ACACIA_BACKGROUND:
        if needle not in acacia:
            problems.append(f"Acacia background missing: {needle}")
    shared = section_body(black, "## Shared reference")
    if "|" in shared:
        problems.append("shared-reference section contains a table")
    if "not a purchasing, regulatory, engineering, or manufacturing authority" not in black:
        problems.append("research-authority caveat missing")
    if "No source in this repo establishes that \"Malaysian Blackwood\" is *Acacia melanoxylon*" not in black:
        problems.append("identity caution missing from the comparison")
    gone = missing_numbers(black)
    if gone:
        problems.append("preserved number missing: " + ", ".join(gone))
    return problems


def o05_problems(log: str, black: str, acacia: str) -> list[str]:
    structure = structural_problems(black, acacia)
    if claims_o05_resolved(log) and structure:
        return ["O-05 marked resolved while structural conditions fail"] + structure
    if not claims_o05_resolved(log):
        return ["O-05 is not marked resolved as duplication only"]
    return []


def changed_paths() -> set[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=ROOT,
        text=True,
    )
    return {line.strip() for line in out.splitlines() if line.strip()}


def fpl_collision(changed: set[str]) -> list[str]:
    """Fail only when this reconciliation diff also edits FPL examples or species data."""
    if not (changed & RECONCILIATION_MARKERS):
        return []
    bad = []
    for path in changed:
        if path in FPL_AND_DATA_PATHS or path.endswith("wood_species.json"):
            bad.append(path)
        elif path.startswith(("packages/client/", "services/api/app/")):
            bad.append(path)
    return bad


def test_both_documents_exist() -> None:
    assert BLACK.is_file()
    assert ACACIA.is_file()
    assert RECORD.is_file()


def test_reciprocal_links_and_required_headings() -> None:
    black = BLACK.read_text(encoding="utf-8")
    acacia = ACACIA.read_text(encoding="utf-8")
    assert structural_problems(black, acacia) == []


def test_o05_resolved_only_when_structure_holds() -> None:
    assert o05_problems(LOG.read_text(encoding="utf-8"), BLACK.read_text(encoding="utf-8"), ACACIA.read_text(encoding="utf-8")) == []


def test_dispositions_cover_every_original_section() -> None:
    rows = disposition_rows(RECORD.read_text(encoding="utf-8"))
    assert invalid_dispositions(rows) == []
    assert missing_sections(rows) == []
    assert NOT_REVALIDATED in RECORD.read_text(encoding="utf-8")


def test_record_sha256_matches_files() -> None:
    record = RECORD.read_text(encoding="utf-8")
    final_black = sha256(BLACK)
    final_acacia = sha256(ACACIA)
    assert is_sha256(final_black) and is_sha256(final_acacia)
    assert is_sha256(ORIGINAL_SHA256["blackwoods"])
    for label, digest in (
        ("original_sha256_blackwoods", ORIGINAL_SHA256["blackwoods"]),
        ("original_sha256_acacia", ORIGINAL_SHA256["acacia"]),
        ("final_sha256_blackwoods", final_black),
        ("final_sha256_acacia", final_acacia),
    ):
        assert re.search(rf"{label}:\s*{digest}", record), label
    assert NOT_REVALIDATED in record


def test_reconciliation_does_not_modify_fpl_examples_or_runtime() -> None:
    assert fpl_collision(changed_paths()) == []


def test_planted_duplicate_passage_fails() -> None:
    planted = BLACK.read_text(encoding="utf-8") + "\n" + PROHIBITED_PASSAGES[0] + "\n"
    assert prohibited_passage_hits(planted) == [PROHIBITED_PASSAGES[0]]
    assert structural_problems(planted, ACACIA.read_text(encoding="utf-8"))


def test_planted_numeric_change_fails() -> None:
    planted = BLACK.read_text(encoding="utf-8").replace("17.95", "17.96", 1)
    assert "17.95" in missing_numbers(planted)
    assert structural_problems(planted, ACACIA.read_text(encoding="utf-8"))


def test_planted_resolution_without_structure_fails() -> None:
    fake_log = "| **O-05** | resolved as duplication only |\n"
    assert o05_problems(fake_log, "# Renamed\n", ACACIA.read_text(encoding="utf-8"))


def test_planted_fpl_edit_collides() -> None:
    bad = {BLACK_REL, "docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv"}
    assert fpl_collision(bad) == ["docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv"]
    assert fpl_collision({"docs/reference/fpl-gtr282/fpl_gtr282_species_tables.csv"}) == []


def test_sha256_form_rejects_non_hash() -> None:
    assert not is_sha256(ORIGINAL_SHA256["blackwoods"][:63])
    assert not is_sha256(ORIGINAL_SHA256["blackwoods"].upper())
    assert is_sha256("a" * 64)


def test_invalid_disposition_token_is_rejected() -> None:
    rows = [("At a Glance", "MADE_UP")]
    assert invalid_dispositions(rows) == ["At a Glance: MADE_UP"]


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))


MANIFEST_REL = ".cbsp21/patches/tonewood-blackwoods-reconciliation-003.json"
O05_CONTRADICTIONS = re.compile(r"\b(closed|deferred|still open|separate reconciliation order)\b", re.I)


def o05_status_problems(log: str, record: str, manifest: str) -> list[str]:
    """Every record that states O-05's status must say: resolved as duplication only.

    C-09 resolved only the extreme-density part, so its heading may not claim all of
    O-05. No record may call O-05 closed, deferred, or still open.
    """
    bad: list[str] = []
    status = next((l for l in log.splitlines() if l.startswith("> **Status:**")), "")
    if "O-05" not in status or "documentation structure only" not in status:
        bad.append("log status line does not record O-05 as documentation-structure-only")
    for line in log.splitlines():
        if line.startswith("### ") and "O-05" in line and "resolves O-05)" in line:
            bad.append(f"heading claims all of O-05: {line.strip()}")
    if "resolved as duplication only" not in o05_line(log):
        bad.append("O-05 table row does not say resolved as duplication only")
    if "O-05 in `docs/tonewood/VERIFICATION_LOG.md` is resolved as duplication only" not in record:
        bad.append("reconciliation record does not say O-05 is resolved as duplication only")
    if "O-05 resolved as duplication only" not in manifest:
        bad.append("CBSP21 manifest does not say O-05 resolved as duplication only")
    for name, text in (("log", log), ("record", record), ("manifest", manifest)):
        for line in text.splitlines():
            if "O-05" in line and O05_CONTRADICTIONS.search(line):
                bad.append(f"{name}: {line.strip()[:160]}")
    return bad


def test_o05_status_agrees_across_records() -> None:
    log = LOG.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    manifest = (ROOT / MANIFEST_REL).read_text(encoding="utf-8")
    assert o05_status_problems(log, record, manifest) == []


def test_planted_o05_status_contradictions_fail() -> None:
    """Negative control: the wordings this PR replaced must each be caught."""
    log = LOG.read_text(encoding="utf-8")
    record = RECORD.read_text(encoding="utf-8")
    manifest = (ROOT / MANIFEST_REL).read_text(encoding="utf-8")
    old_heading = log.replace("(resolves the extreme-density part of O-05)", "(resolves O-05)")
    assert any("heading claims all of O-05" in p for p in o05_status_problems(old_heading, record, manifest))
    closed = record + "\nO-05 is closed in `VERIFICATION_LOG.md`.\n"
    assert any(p.startswith("record:") for p in o05_status_problems(log, closed, manifest))
    deferred = log + "\n| **O-05** note | Still open; separate reconciliation order |\n"
    assert any(p.startswith("log:") for p in o05_status_problems(deferred, record, manifest))
