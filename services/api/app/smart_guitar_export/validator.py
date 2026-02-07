"""
Validator for ToolBox -> Smart Guitar Safe Export v1

Gate enforcement:
1. Validates manifest.json against schema
2. Checks all files exist with correct sha256 + byte size
3. Rejects forbidden file extensions (.nc, .gcode, etc.)
4. Rejects forbidden file kinds
5. Rejects if content_policy flags are not all true
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .schemas import SmartGuitarExportManifest, ContentPolicy


# =============================================================================
# Forbidden Content (Manufacturing / Authority Boundary)
# =============================================================================


FORBIDDEN_EXTENSIONS = frozenset({
    # G-code / CNC
    ".nc",
    ".gcode",
    ".ngc",
    ".tap",
    ".cnc",
    # CAM / DXF
    ".dxf",
    ".dwg",
    # Toolpaths
    ".toolpath",
    ".sbp",  # ShopBot
    ".crv",  # Vectric
    # Executables
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    # Secrets
    ".pem",
    ".key",
    ".env",
})

FORBIDDEN_KINDS = frozenset({
    "gcode",
    "toolpath",
    "dxf",
    "cam_output",
    "rmos_artifact",
    "run_decision",
    "manufacturing",
})

FORBIDDEN_PATH_PATTERNS = [
    "/api/cam/",
    "/api/rmos/",
    "toolpaths/",
    "gcode/",
    ".nc",
]


# =============================================================================
# Validation Result
# =============================================================================


@dataclass
class ValidationResult:
    """Result of validating an export bundle."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    manifest: Optional[SmartGuitarExportManifest] = None

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# =============================================================================
# Validation Functions
# =============================================================================


def _sha256_of_bytes(data: bytes) -> str:
    """Compute SHA256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def _sha256_of_file(path: Path) -> str:
    """Compute SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(manifest_dict: Dict[str, Any]) -> ValidationResult:
    """
    Validate a manifest dictionary against the schema.

    Does NOT check file existence - use validate_bundle for that.
    """
    result = ValidationResult(valid=True)

    # 1) Parse with Pydantic (validates schema)
    try:
        manifest = SmartGuitarExportManifest.model_validate(manifest_dict)
        result.manifest = manifest
    except (ValueError, TypeError) as e:  # WP-1: narrowed from except Exception
        result.add_error(f"Schema validation failed: {e}")
        return result

    # 2) Check content policy flags (should be enforced by Literal types, but double-check)
    policy = manifest.content_policy
    if not policy.no_manufacturing:
        result.add_error("content_policy.no_manufacturing must be true")
    if not policy.no_toolpaths:
        result.add_error("content_policy.no_toolpaths must be true")
    if not policy.no_rmos_authority:
        result.add_error("content_policy.no_rmos_authority must be true")
    if not policy.no_secrets:
        result.add_error("content_policy.no_secrets must be true")

    # 3) Check for forbidden file extensions
    for f in manifest.files:
        ext = Path(f.relpath).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS:
            result.add_error(f"Forbidden extension '{ext}' in file: {f.relpath}")

    # 4) Check for forbidden file kinds
    for f in manifest.files:
        kind_lower = f.kind.value.lower()
        if kind_lower in FORBIDDEN_KINDS:
            result.add_error(f"Forbidden kind '{f.kind}' in file: {f.relpath}")

    # 5) Check for forbidden path patterns
    for f in manifest.files:
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if pattern in f.relpath.lower():
                result.add_error(f"Forbidden path pattern '{pattern}' in: {f.relpath}")

    return result


def validate_bundle(bundle_path: Union[str, Path]) -> ValidationResult:
    """
    Validate a complete export bundle on disk.

    Checks:
    1. manifest.json exists and validates
    2. All files in manifest exist
    3. SHA256 and byte sizes match
    4. No forbidden content
    """
    bundle_path = Path(bundle_path)
    result = ValidationResult(valid=True)

    # 1) Check bundle exists
    if not bundle_path.exists():
        result.add_error(f"Bundle path does not exist: {bundle_path}")
        return result

    if not bundle_path.is_dir():
        result.add_error(f"Bundle path is not a directory: {bundle_path}")
        return result

    # 2) Check manifest exists
    manifest_path = bundle_path / "manifest.json"
    if not manifest_path.exists():
        result.add_error("manifest.json not found in bundle")
        return result

    # 3) Load and validate manifest
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_dict = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in manifest.json: {e}")
        return result

    manifest_result = validate_manifest(manifest_dict)
    result.errors.extend(manifest_result.errors)
    result.warnings.extend(manifest_result.warnings)
    result.valid = result.valid and manifest_result.valid
    result.manifest = manifest_result.manifest

    if not manifest_result.valid or not manifest_result.manifest:
        return result

    manifest = manifest_result.manifest

    # 4) Verify each file in manifest
    for file_entry in manifest.files:
        file_path = bundle_path / file_entry.relpath

        # Check existence
        if not file_path.exists():
            result.add_error(f"File not found: {file_entry.relpath}")
            continue

        # Check byte size
        actual_size = file_path.stat().st_size
        if actual_size != file_entry.bytes:
            result.add_error(
                f"Size mismatch for {file_entry.relpath}: "
                f"expected {file_entry.bytes}, got {actual_size}"
            )

        # Check SHA256
        actual_sha = _sha256_of_file(file_path)
        if actual_sha != file_entry.sha256:
            result.add_error(
                f"SHA256 mismatch for {file_entry.relpath}: "
                f"expected {file_entry.sha256}, got {actual_sha}"
            )

    # 5) Check for extra files not in manifest (warning only)
    manifest_relpaths = {f.relpath for f in manifest.files}
    for file_path in bundle_path.rglob("*"):
        if file_path.is_file():
            relpath = str(file_path.relative_to(bundle_path)).replace("\\", "/")
            if relpath not in manifest_relpaths:
                result.add_warning(f"Extra file not in manifest: {relpath}")

    return result


def validate_manifest_json(manifest_json: str) -> ValidationResult:
    """Validate manifest from JSON string."""
    try:
        manifest_dict = json.loads(manifest_json)
    except json.JSONDecodeError as e:
        result = ValidationResult(valid=False)
        result.add_error(f"Invalid JSON: {e}")
        return result
    return validate_manifest(manifest_dict)
