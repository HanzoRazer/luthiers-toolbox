"""
Manufacturing authority for governed DXF catalog assets (DXF-RUNTIME-AUTHORITY-001).

Answers one question about one file: may a manufacturing path consume it?

    inside the governed catalog, positively authorized for these exact bytes
        -> ALLOWED
    inside the governed catalog, anything else
        -> BLOCKED
    outside the governed catalog
        -> NOT_CATALOG, and the caller's existing non-catalog contract applies
           (uploaded and user-supplied DXFs keep going through the export gate;
           they do not acquire catalog requirements by having no record here)

**Quarantine records describe known failure; they never grant manufacturing
authority. Manufacturing authority is a separate positive assertion over a
specific catalog asset and its exact bytes** (owner ruling 2026-09-16). The
absence of a quarantine record is not authorization either, and replacing a
file does not restore manufacturing on its own: the new digest has to be
authorized before a manufacturing path will read it.

This is the shared substrate: the CI catalog gates and the runtime generators
resolve authority through this one module, so they cannot disagree about a
file. It is deliberately narrow - path normalization, classification, the
authorization lookup and the digest comparison - and carries no HTTP, no
database, no ezdxf and no import of app/ci. Everything else about the catalog
(contract clauses, geometry, quarantine judgement) stays in the CI policy.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

CATALOG_ROOT = Path(__file__).resolve().parent
# Shared registry data. The CI gates own the file; this module only reads it,
# and never imports app/ci (production must not depend on CI modules).
REGISTRY_PATH = CATALOG_ROOT.parent / "ci" / "dxf_catalog_registry.json"

ALLOWED = "ALLOWED"
BLOCKED = "BLOCKED"
NOT_CATALOG = "NOT_CATALOG"
AUTHORITY_VALUES = frozenset({ALLOWED})
AUTHORIZATION_FIELDS = ("asset", "asset_sha256", "authority", "basis")
ERROR_CODE = "DXF_MANUFACTURING_AUTHORITY_BLOCKED"
_SHA256 = re.compile(r"[0-9a-f]{64}")


class ManufacturingAuthorityBlocked(ValueError):
    """A manufacturing path asked for a catalog asset it may not consume.

    Subclasses ValueError so the existing 4xx mapping in the CAM routers
    (ValueError -> 422) already covers callers that do not handle it explicitly.
    """

    def __init__(self, authority: "DXFManufacturingAuthority"):
        self.code = ERROR_CODE
        self.authority = authority
        self.asset = authority.asset
        self.disposition = authority.disposition
        self.manufacturing_authority = BLOCKED
        self.reason = authority.reason
        self.exit_condition = authority.exit_condition
        super().__init__(str(authority))

    def as_detail(self) -> Dict[str, Any]:
        """Client-facing payload: catalog-relative asset only, never a filesystem path."""
        detail = {"code": self.code, "asset": self.asset, "manufacturing_authority": BLOCKED,
                  "reason": self.reason}
        if self.disposition:
            detail["disposition"] = self.disposition
        if self.exit_condition:
            detail["exit_condition"] = self.exit_condition
        return detail


@dataclass(frozen=True)
class DXFManufacturingAuthority:
    """What the registry says about manufacturing use of one file."""
    state: str
    asset: Optional[str] = None
    asset_class: Optional[str] = None
    registered: bool = False
    sha256_matches: Optional[bool] = None
    disposition: Optional[str] = None
    reason: str = ""
    exit_condition: Optional[str] = None

    @property
    def blocked(self) -> bool:
        return self.state == BLOCKED

    @property
    def governed(self) -> bool:
        """True when the asset is inside the governed catalog root."""
        return self.state != NOT_CATALOG

    def __str__(self) -> str:
        return f"{self.asset or 'asset'}: {self.reason}"


# -----------------------------------------------------------------------------
# Paths and classification (shared with the CI gates)
# -----------------------------------------------------------------------------

def glob_match(path: str, pattern: str) -> bool:
    """Match per '/' segment: '*' stays inside one segment, '**' spans any number."""
    return _match_segments(path.split("/"), pattern.split("/"))


def _match_segments(parts: List[str], patterns: List[str]) -> bool:
    if not patterns:
        return not parts
    if patterns[0] == "**":
        return any(_match_segments(parts[i:], patterns[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], patterns[0]) and _match_segments(parts[1:], patterns[1:])


class AmbiguousClassification(ValueError):
    """Rules for two classes match the same asset; classification must not depend on order."""


def classify(asset: Optional[str], registry: Dict[str, Any]) -> Optional[str]:
    """Asset class for a catalog-relative POSIX path, or None if unclassified."""
    if asset is None:
        return None
    classes = {rule["class"] for rule in registry["class_rules"] if glob_match(asset, rule["glob"])}
    if len(classes) > 1:
        raise AmbiguousClassification(f"Ambiguous classification: {asset!r} matches {sorted(classes)}")
    return classes.pop() if classes else None


def catalog_relative_path(path: Path, catalog_root: Optional[Path] = None) -> Optional[str]:
    """POSIX path inside the governed catalog, or None when the file is outside it.

    Resolves first, so traversal ('.../body/../../elsewhere.dxf') cannot present
    an outside file as a catalog asset.
    """
    root = (catalog_root or CATALOG_ROOT).resolve()
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return None


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# -----------------------------------------------------------------------------
# The authorization section of the registry
# -----------------------------------------------------------------------------

def authorizations(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    section = registry.get("manufacturing_authority") or {}
    entries = section.get("authorized") or []
    return entries if isinstance(entries, list) else []


def authorization_for(asset: Optional[str], registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for entry in authorizations(registry):
        if isinstance(entry, dict) and entry.get("asset") == asset:
            return entry
    return None


def quarantine_record(asset: Optional[str], registry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for record in registry.get("quarantine", []):
        if record.get("asset") == asset:
            return record
    return None


def validate_authorization_section(registry: Dict[str, Any],
                                   classify_fn: Callable[[str, Dict[str, Any]], Optional[str]]) -> List[str]:
    """Problems with the manufacturing_authority section (empty list = valid).

    Called by the registry schema so CI rejects a malformed section at load,
    rather than runtime discovering it at the moment someone asks to machine.
    """
    section = registry.get("manufacturing_authority")
    if not isinstance(section, dict) or not isinstance(section.get("authorized"), list):
        return ["manufacturing_authority must be an object with an 'authorized' list "
                "(empty when nothing is authorized)"]
    problems, seen = [], set()
    for index, entry in enumerate(section["authorized"]):
        label = f"manufacturing_authority.authorized[{index}]"
        if not isinstance(entry, dict) or not all(entry.get(f) for f in AUTHORIZATION_FIELDS):
            problems.append(f"{label}: missing or empty fields {list(AUTHORIZATION_FIELDS)}")
            continue
        problems += [f"{label}: {p}" for p in _entry_problems(entry, registry, classify_fn, seen)]
        seen.add(entry["asset"])
    return problems


def _entry_problems(entry: Dict[str, Any], registry: Dict[str, Any],
                    classify_fn: Callable[[str, Dict[str, Any]], Optional[str]], seen: set) -> List[str]:
    problems = []
    asset = entry["asset"]
    if asset in seen:
        problems.append("duplicate authorization")
    if entry["authority"] not in AUTHORITY_VALUES:
        problems.append(f"authority {entry['authority']!r} is not one of {sorted(AUTHORITY_VALUES)}; "
                        f"this section only grants authority, it never records a block")
    if not _SHA256.fullmatch(str(entry["asset_sha256"])):
        problems.append("asset_sha256 must be 64 lowercase hex characters")
    if classify_fn(asset, registry) is None:
        problems.append("asset is not classified by class_rules, so it is not a governed catalog asset")
    if quarantine_record(asset, registry) is not None:
        problems.append("asset also carries a quarantine record: known nonconformance cannot be authorized")
    return problems


# -----------------------------------------------------------------------------
# Resolution
# -----------------------------------------------------------------------------

def _load_registry(registry_path: Path) -> Tuple[Optional[Dict[str, Any]], str]:
    try:
        registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"the catalog registry could not be read ({type(exc).__name__})"
    if not isinstance(registry, dict) or not isinstance(registry.get("class_rules"), list):
        return None, "the catalog registry is malformed (no class_rules)"
    return registry, ""


def resolve_manufacturing_authority(path: Path, registry_path: Optional[Path] = None,
                                    catalog_root: Optional[Path] = None) -> DXFManufacturingAuthority:
    """Whether a manufacturing path may consume `path`. Fail-closed for governed assets."""
    asset = catalog_relative_path(path, catalog_root)
    if asset is None:
        return DXFManufacturingAuthority(NOT_CATALOG, reason="outside the governed DXF catalog")
    registry, problem = _load_registry(registry_path or REGISTRY_PATH)
    if registry is None:
        return DXFManufacturingAuthority(BLOCKED, asset=asset, reason=problem)
    try:
        asset_class = classify(asset, registry)
    except AmbiguousClassification as exc:
        return DXFManufacturingAuthority(BLOCKED, asset=asset, reason=str(exc))
    if asset_class is None:
        return DXFManufacturingAuthority(
            BLOCKED, asset=asset,
            reason="catalog asset is not classified by the registry, so it has no manufacturing authority")
    return _authorize(path, asset, asset_class, registry)


def _authorize(path: Path, asset: str, asset_class: str,
               registry: Dict[str, Any]) -> DXFManufacturingAuthority:
    record = quarantine_record(asset, registry)
    if record is not None:
        return DXFManufacturingAuthority(
            BLOCKED, asset=asset, asset_class=asset_class, registered=True,
            disposition=record.get("disposition"), exit_condition=record.get("exit_condition"),
            reason=f"quarantine record: {record.get('disposition')} "
                   f"({record.get('reason', 'known nonconformance')})")
    entry = authorization_for(asset, registry)
    if entry is None or entry.get("authority") not in AUTHORITY_VALUES:
        return DXFManufacturingAuthority(
            BLOCKED, asset=asset, asset_class=asset_class,
            reason="no positive manufacturing authorization for this asset",
            exit_condition="adjudicate the asset and record an authorization for its digest")
    try:
        digest = file_sha256(path)
    except OSError as exc:
        return DXFManufacturingAuthority(BLOCKED, asset=asset, asset_class=asset_class, registered=True,
                                         reason=f"the asset could not be read ({type(exc).__name__})")
    if digest != entry["asset_sha256"]:
        return DXFManufacturingAuthority(
            BLOCKED, asset=asset, asset_class=asset_class, registered=True, sha256_matches=False,
            reason="the file's bytes are not the authorized bytes (digest mismatch)",
            exit_condition="re-adjudicate the changed asset and authorize its new digest")
    return DXFManufacturingAuthority(ALLOWED, asset=asset, asset_class=asset_class, registered=True,
                                     sha256_matches=True, reason=f"authorized: {entry['basis']}")


def require_manufacturing_authority(path: Path, registry_path: Optional[Path] = None,
                                    catalog_root: Optional[Path] = None) -> DXFManufacturingAuthority:
    """Raise ManufacturingAuthorityBlocked unless `path` may be manufactured from."""
    authority = resolve_manufacturing_authority(path, registry_path, catalog_root)
    if authority.blocked:
        raise ManufacturingAuthorityBlocked(authority)
    return authority
