"""G2-MANUFACTURING-SPINE-001 — read-only validator for the current-state registry.

This checks *claims*. It does not discover truth, grant execution authority, or
decide governance:

    validator != authority
    registry  != execution permission
    maturity  != governance disposition

What it enforces is that every claim carries what the order requires before it
is believed: the maturity ladder is monotonic and matches the proven levels;
YES and NO each need current evidence of an admissible kind; CONSUMED needs an
exact product-consumer chain that is not synthetic; absence of evidence is
UNKNOWN, never NO.

Stdlib only. No git, no network, no writes. Exit 0 = valid, 1 = invalid,
2 = usage / unreadable input.

    python -m tools.manufacturing_spine.validate_current_state REGISTRY.json \
        [--identity-registry services/api/app/rmos/manufacturing_authority_registry.json] \
        [--summary]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

ORDER_ID = "G2-MANUFACTURING-SPINE-001"
SCHEMA_VERSION = "manufacturing_spine_current_state.v1"

LEVELS = ("declared", "wired", "exercised", "effective", "consumed")
VALUES = frozenset({"YES", "NO", "UNKNOWN", "NOT_OBTAINED_SAFELY"})
MATURITY = ("NONE", "DECLARED", "WIRED", "EXERCISED", "EFFECTIVE", "CONSUMED")
SURFACE_KINDS = frozenset({"manufacturing_capability", "artifact_transformation",
                           "artifact_retrieval", "advisory"})
MANUFACTURING = "manufacturing_capability"
BUCKETS = frozenset({"G2-READY", "G2-DEFICIT", "POST-MVS / NOT-REQUIRED-YET", "NOT-MANUFACTURING"})
MVS_RELEVANCE = frozenset({"UNKNOWN", "MVS", "POST-MVS"})
TEMPORAL = frozenset({"current", "historical"})
BASIS = frozenset({"CURRENT", "HISTORICAL"})
CHANGE = frozenset({"UNCHANGED", "CHANGED", "REMOVED", "ADDED", "UNKNOWN"})

EVIDENCE_KINDS = frozenset({
    "registry",          # the identity-source registry entry
    "source",            # a file:symbol in the repository
    "route_table",       # the mounted route walk (census)
    "runtime",           # an in-process request against the current app
    "test",              # a current test and what it asserts
    "client_reference",  # a client file that mentions a route (never a consumer by itself)
    "consumer_chain",    # mounted entry -> invocation -> route -> result used
    "document",          # a document, e.g. the frozen historical authority map
})

# Which evidence kinds can carry a YES at each level. A NO (a proven negative)
# may rest on any kind, but it must rest on something.
YES_KINDS = {
    "declared": frozenset({"registry", "source"}),
    "wired": frozenset({"route_table", "source"}),
    "exercised": frozenset({"runtime", "test"}),
    "effective": frozenset({"runtime", "test"}),
    "consumed": frozenset({"consumer_chain"}),
}
CONSUMER_KEYS = ("entry", "invocation", "route", "result_use")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def proven_maturity(row: Dict[str, Any]) -> str:
    """Highest level L such that every level up to and including L is YES."""
    reached = "NONE"
    for level in LEVELS:
        if row.get(level) == "YES":
            reached = level.upper()
        else:
            break
    return reached


def _nonempty(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _load_identity(path: Optional[str]) -> Optional[set]:
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {c.get("capability_id") for c in data.get("capabilities", [])}


def _validate_evidence(cid: str, refs: Any, errs: List[str]) -> List[Dict[str, Any]]:
    good = []
    if not isinstance(refs, list):
        errs.append(f"{cid}: evidence_refs must be a list")
        return good
    for i, e in enumerate(refs):
        where = f"{cid}: evidence_refs[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{where} must be an object")
            continue
        if e.get("level") not in LEVELS:
            errs.append(f"{where}: level must be one of {list(LEVELS)}")
            continue
        if e.get("kind") not in EVIDENCE_KINDS:
            errs.append(f"{where}: unknown evidence kind {e.get('kind')!r}")
            continue
        if not _nonempty(e.get("ref")):
            errs.append(f"{where}: ref must be a non-empty string")
            continue
        if e.get("temporal") not in TEMPORAL:
            errs.append(f"{where}: temporal must be 'current' or 'historical'")
            continue
        if not isinstance(e.get("synthetic_probe"), bool):
            errs.append(f"{where}: synthetic_probe must be true or false")
            continue
        good.append(e)
    return good


def _validate_row(row: Dict[str, Any], errs: List[str]) -> None:
    cid = row.get("capability_id") or "<missing id>"

    if row.get("surface_kind") not in SURFACE_KINDS:
        errs.append(f"{cid}: surface_kind must be one of {sorted(SURFACE_KINDS)}")

    for level in LEVELS:
        if row.get(level) not in VALUES:
            errs.append(f"{cid}: {level} must be one of {sorted(VALUES)}")

    # The ladder is monotonic: a level can only be YES if the one below it is.
    for lower, upper in zip(LEVELS, LEVELS[1:]):
        if row.get(upper) == "YES" and row.get(lower) != "YES":
            errs.append(f"{cid}: {upper}=YES requires {lower}=YES")

    maturity = row.get("maturity")
    if maturity not in MATURITY:
        errs.append(f"{cid}: maturity must be one of {list(MATURITY)}, got {maturity!r}")
    else:
        proven = proven_maturity(row)
        if maturity != proven:
            errs.append(f"{cid}: maturity {maturity} does not match the proven ladder ({proven})")

    basis = row.get("classification_basis", "CURRENT")
    if basis not in BASIS:
        errs.append(f"{cid}: classification_basis must be one of {sorted(BASIS)}")
    allowed_temporal = {"current", "historical"} if basis == "HISTORICAL" else {"current"}

    refs = _validate_evidence(cid, row.get("evidence_refs"), errs)

    for level in LEVELS:
        value = row.get(level)
        if value not in ("YES", "NO"):
            continue
        at_level = [e for e in refs if e["level"] == level and e["temporal"] in allowed_temporal]
        if level == "consumed" and value == "YES":
            chains = [e for e in at_level if e["kind"] == "consumer_chain"]
            if not chains:
                errs.append(f"{cid}: consumed=YES requires consumer_chain evidence "
                            "(a client reference, test or runtime call is not a consumer)")
            elif all(e["synthetic_probe"] for e in chains):
                errs.append(f"{cid}: consumed=YES cannot rest on SYNTHETIC_PROBE evidence (D5a)")
            continue
        if value == "YES":
            if not any(e["kind"] in YES_KINDS[level] for e in at_level):
                errs.append(f"{cid}: {level}=YES has no current evidence of kind "
                            f"{sorted(YES_KINDS[level])}")
        elif not at_level:  # NO is a proven negative, not an absence
            errs.append(f"{cid}: {level}=NO has no current evidence (absence of evidence is UNKNOWN)")

    if any(row.get(level) == "NOT_OBTAINED_SAFELY" for level in LEVELS):
        lims = row.get("limitations")
        if not (isinstance(lims, list) and any(_nonempty(x) for x in lims)):
            errs.append(f"{cid}: NOT_OBTAINED_SAFELY requires a limitation stating why")

    if row.get("consumed") == "YES":
        consumer = row.get("consumer")
        if not isinstance(consumer, dict):
            errs.append(f"{cid}: consumed=YES requires a consumer {{{', '.join(CONSUMER_KEYS)}}}")
        else:
            for key in CONSUMER_KEYS:
                if not _nonempty(consumer.get(key)):
                    errs.append(f"{cid}: consumer.{key} is empty")

    bucket = row.get("g2_bucket")
    if bucket not in BUCKETS:
        errs.append(f"{cid}: g2_bucket must be one of {sorted(BUCKETS)}")
    elif row.get("surface_kind") in SURFACE_KINDS:
        if row["surface_kind"] != MANUFACTURING and bucket != "NOT-MANUFACTURING":
            errs.append(f"{cid}: a non-manufacturing surface cannot count toward G2 manufacturing "
                        "coverage (g2_bucket must be NOT-MANUFACTURING)")
        if row["surface_kind"] == MANUFACTURING and bucket == "NOT-MANUFACTURING":
            errs.append(f"{cid}: a manufacturing capability cannot be NOT-MANUFACTURING")

    if row.get("mvs_relevance", "UNKNOWN") not in MVS_RELEVANCE:
        errs.append(f"{cid}: mvs_relevance must be one of {sorted(MVS_RELEVANCE)}")
    if "change_since_frozen" in row and row["change_since_frozen"] not in CHANGE:
        errs.append(f"{cid}: change_since_frozen must be one of {sorted(CHANGE)}")


def validate(doc: Dict[str, Any], identity_registry: Optional[str] = None) -> List[str]:
    """Return every error found. An empty list means the registry is valid.

    Never mutates ``doc``.
    """
    errs: List[str] = []
    if not isinstance(doc, dict):
        return ["registry must be a JSON object"]
    if doc.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if doc.get("order_id") != ORDER_ID:
        errs.append(f"order_id must be exactly {ORDER_ID!r}, got {doc.get('order_id')!r}")
    if not (isinstance(doc.get("baseline_sha"), str) and _SHA.match(doc["baseline_sha"])):
        errs.append("baseline_sha must be a full 40-character lowercase SHA")

    rows = doc.get("capabilities")
    if not isinstance(rows, list) or not rows:
        errs.append("capabilities must be a non-empty list")
        return errs

    identity = _load_identity(identity_registry)
    seen = Counter()
    for row in rows:
        if not isinstance(row, dict) or not _nonempty(row.get("capability_id")):
            errs.append("every capability needs a non-empty capability_id")
            continue
        seen[row["capability_id"]] += 1
        if identity is not None and row["capability_id"] not in identity:
            errs.append(f"{row['capability_id']}: capability_id is not in the identity registry "
                        "(do not mint a second naming system)")
        _validate_row(row, errs)
    for cid, n in sorted(seen.items()):
        if n > 1:
            errs.append(f"duplicate capability_id: {cid} appears {n} times")
    return errs


def summarise(doc: Dict[str, Any]) -> Dict[str, Any]:
    rows = [r for r in doc.get("capabilities", []) if isinstance(r, dict)]
    return {
        "capabilities": len(rows),
        "yes_by_level": {lvl: sum(r.get(lvl) == "YES" for r in rows) for lvl in LEVELS},
        "maturity": dict(Counter(r.get("maturity") for r in rows)),
        "g2_bucket": dict(Counter(r.get("g2_bucket") for r in rows)),
        "change_since_frozen": dict(Counter(r.get("change_since_frozen") for r in rows)),
        "not_obtained_safely_rows": sum(
            any(r.get(lvl) == "NOT_OBTAINED_SAFELY" for lvl in LEVELS) for r in rows),
        "mvs_relevance_unknown": sum(r.get("mvs_relevance", "UNKNOWN") == "UNKNOWN" for r in rows),
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("registry")
    ap.add_argument("--identity-registry", default=None)
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)
    try:
        with open(args.registry, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"cannot read registry: {exc}", file=sys.stderr)
        return 2
    try:
        errs = validate(doc, identity_registry=args.identity_registry)
    except (OSError, ValueError) as exc:
        print(f"cannot read identity registry: {exc}", file=sys.stderr)
        return 2
    for e in errs:
        print(f"ERROR {e}")
    if args.summary:
        print(json.dumps(summarise(doc), indent=2))
    print("OK" if not errs else f"INVALID: {len(errs)} error(s)")
    return 0 if not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
