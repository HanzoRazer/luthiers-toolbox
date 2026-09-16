"""
Schema validation for dxf_catalog_registry.json (DXF-CATALOG-GATE-001).

The registry is the policy source of truth for both DXF catalog gates, so a
malformed registry must fail loudly at load time with a message that names the
problem, not deep inside a clause check as a KeyError.

Schema dxf_catalog_registry_v3. History: v1 -> v2 split observed_evidence into
machine-checked `gate` lines and free-text `review` notes, pinned every record
to its asset's sha256, and made class globs match per path segment. v2 -> v3
adds the `manufacturing_authority` section: positive authorization of a named
asset and its exact bytes, which is the only thing that permits manufacturing
use at runtime. A quarantine record still never grants authority, and an asset
may not be both quarantined and authorized. A registry declaring any other
schema is rejected; bump the schema name whenever the structure changes.

Dependencies: stdlib only (the asset gate job installs only ezdxf). The
authorization section is defined and validated by the runtime-safe substrate
app/instrument_geometry/dxf_authority.py, which both this schema and the
runtime generators read, so CI and runtime cannot disagree about authority.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

from ..instrument_geometry.dxf_authority import validate_authorization_section

SCHEMA = "dxf_catalog_registry_v3"
KNOWN_CLAUSES = (
    "readable", "nonempty", "geometry_present", "version_allowed",
    "closed_outline", "preflight_valid", "topology_valid",
)
BASE_CLAUSES = ("readable", "nonempty", "geometry_present", "version_allowed")
DISPOSITIONS = frozenset({"QUARANTINED", "QUARANTINE_CANDIDATE", "UNADJUDICATED", "NONCONFORMING_VERSION"})
OWNER_STREAM = "DXF Catalog Integrity"
RECORD_FIELDS = (
    "asset", "asset_class", "asset_sha256", "failed_contract", "observed_evidence", "disposition",
    "reason", "owner_stream", "manufacturing_authority", "exit_condition",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DXF_VERSION = re.compile(r"^AC\d{4}$")
_EVIDENCE = re.compile(r"^\[([a-z_]+)\] ")


class RegistryError(ValueError):
    """The DXF catalog registry is malformed or inconsistent."""


def validate_registry(registry: Dict[str, Any], classify: Callable[[str, Dict[str, Any]], Optional[str]]) -> None:
    """Raise RegistryError listing the problems found; return None if valid.

    Stages run in order (top level, then classes and rules, then records) and a
    later stage runs only if the earlier ones are clean: record checks depend
    on valid classes and rules, so running them on a broken base would bury the
    real problem under consequential ones. Within a stage every problem is listed.
    """
    problems = _top_level(registry)
    if not problems:
        problems += _classes(registry) + _rules(registry)
    if not problems:
        problems += _records(registry, classify) + validate_authorization_section(registry, classify)
    if problems:
        raise RegistryError("dxf_catalog_registry.json is invalid:\n  - " + "\n  - ".join(problems))


def _top_level(registry: Dict[str, Any]) -> List[str]:
    problems = []
    if registry.get("schema") != SCHEMA:
        problems.append(f"schema is {registry.get('schema')!r}, expected {SCHEMA!r}")
    for key, kind in (("catalog_root", str), ("version_policy", dict), ("clauses", dict),
                      ("asset_classes", dict), ("class_rules", list), ("quarantine", list),
                      ("manufacturing_authority", dict)):
        if not isinstance(registry.get(key), kind):
            problems.append(f"top-level {key!r} missing or not a {kind.__name__}")
    if problems:
        return problems
    approved = registry["version_policy"].get("approved")
    if not approved or not all(isinstance(v, str) and _DXF_VERSION.match(v) for v in approved):
        problems.append("version_policy.approved must be a non-empty list of AC#### version codes")
    if sorted(registry["clauses"]) != sorted(KNOWN_CLAUSES):
        problems.append(f"clauses must be exactly the implemented set {list(KNOWN_CLAUSES)}, "
                        f"got {sorted(registry['clauses'])}")
    return problems


def _classes(registry: Dict[str, Any]) -> List[str]:
    problems = []
    for name, spec in registry["asset_classes"].items():
        contract = spec.get("contract") if isinstance(spec, dict) else None
        if not isinstance(contract, list) or not set(BASE_CLAUSES) <= set(contract) <= set(KNOWN_CLAUSES):
            problems.append(f"class {name!r}: contract must include {list(BASE_CLAUSES)} "
                            f"and only known clauses")
            continue
        if "closed_outline" in contract:
            problems += _outline_spec(name, spec)
    return problems


def _outline_spec(name: str, spec: Dict[str, Any]) -> List[str]:
    problems = []
    outline = spec.get("outline_layers")
    reference = spec.get("reference_layers", [])
    coverage = spec.get("outline_coverage_min")
    if not isinstance(outline, list) or not outline or not all(isinstance(x, str) for x in outline):
        problems.append(f"class {name!r}: closed_outline needs a non-empty outline_layers list")
    if not isinstance(reference, list) or set(reference) & set(outline or []):
        problems.append(f"class {name!r}: reference_layers must be a list disjoint from outline_layers")
    if not isinstance(coverage, (int, float)) or not 0 < coverage <= 1:
        problems.append(f"class {name!r}: outline_coverage_min must be a number in (0, 1]")
    return problems


def _rules(registry: Dict[str, Any]) -> List[str]:
    problems = []
    for i, rule in enumerate(registry["class_rules"]):
        if not isinstance(rule, dict) or not isinstance(rule.get("glob"), str):
            problems.append(f"class_rules[{i}] needs a string glob")
        elif rule.get("class") not in registry["asset_classes"]:
            problems.append(f"class_rules[{i}] ({rule['glob']}) names unknown class {rule.get('class')!r}")
    return problems


def _records(registry: Dict[str, Any], classify: Callable) -> List[str]:
    problems, seen = [], set()
    for record in registry["quarantine"]:
        asset = record.get("asset") if isinstance(record, dict) else None
        label = f"quarantine[{asset!r}]"
        if not isinstance(record, dict) or not all(record.get(f) for f in RECORD_FIELDS):
            missing = [f for f in RECORD_FIELDS if not isinstance(record, dict) or not record.get(f)]
            problems.append(f"{label}: missing or empty fields {missing}")
            continue
        if asset in seen:
            problems.append(f"{label}: duplicate record")
        seen.add(asset)
        problems += [f"{label}: {p}" for p in _record_problems(record, registry, classify)]
    return problems


def _record_problems(record: Dict[str, Any], registry: Dict[str, Any], classify: Callable) -> List[str]:
    problems = []
    klass = record["asset_class"]
    if klass not in registry["asset_classes"]:
        return [f"unknown asset_class {klass!r}"]
    classified = classify(record["asset"], registry)
    if classified != klass:
        problems.append(f"asset_class {klass!r} but class_rules classify the asset as {classified!r}")
    contract = registry["asset_classes"][klass]["contract"]
    if not set(record["failed_contract"]) <= set(contract):
        problems.append(f"failed_contract {record['failed_contract']} is not within the {klass} contract")
    if record["disposition"] not in DISPOSITIONS:
        problems.append(f"disposition {record['disposition']!r} not in {sorted(DISPOSITIONS)}")
    if record["manufacturing_authority"] != "BLOCKED":
        problems.append("manufacturing_authority must be BLOCKED")
    if record["owner_stream"] != OWNER_STREAM:
        problems.append(f"owner_stream must be {OWNER_STREAM!r}")
    if not _SHA256.match(str(record["asset_sha256"])):
        problems.append("asset_sha256 must be 64 lowercase hex characters")
    return problems + _evidence_problems(record)


def _evidence_problems(record: Dict[str, Any]) -> List[str]:
    """gate lines are '[clause] message' and must cover exactly the failed clauses."""
    evidence = record["observed_evidence"]
    if not isinstance(evidence, dict) or not isinstance(evidence.get("gate"), list) \
            or not isinstance(evidence.get("review", []), list):
        return ["observed_evidence must be {'gate': [...], 'review': [...]}"]
    cited = set()
    for line in evidence["gate"]:
        match = _EVIDENCE.match(line) if isinstance(line, str) else None
        if not match:
            return [f"gate evidence line is not '[clause] message': {line!r}"]
        cited.add(match.group(1))
    if cited != set(record["failed_contract"]):
        return [f"gate evidence cites clauses {sorted(cited)} but failed_contract is "
                f"{sorted(record['failed_contract'])}"]
    return []
