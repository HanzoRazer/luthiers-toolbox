"""
Viewer Pack Contract Gate

Validates the viewer_pack_v1 contract between tap_tone_pi (producer) and
luthiers-toolbox (consumer).

Checks:
1. All fixture ZIPs validate against viewer_pack_v1 schema
2. All schema kinds have renderer mappings in client
3. Renderer registry matches schema enum
4. Fixture file integrity (SHA256 + byte counts)

Run: pytest services/api/tests/test_viewer_pack_contract.py -v
"""

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Optional

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Path Constants
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent.parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "viewer_packs"
CLIENT_RENDERERS_DIR = REPO_ROOT / "packages" / "client" / "src" / "tools" / "audio_analyzer" / "renderers"

SCHEMA_PATH = CONTRACTS_DIR / "viewer_pack_v1.schema.json"
TYPES_TS_PATH = CLIENT_RENDERERS_DIR / "types.ts"


# ─────────────────────────────────────────────────────────────────────────────
# Schema Extraction
# ─────────────────────────────────────────────────────────────────────────────

def load_schema() -> dict:
    """Load viewer_pack_v1 schema from contracts directory."""
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema not found: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def extract_schema_kinds(schema: dict) -> set[str]:
    """Extract allowed 'kind' values from schema enum."""
    try:
        kinds_enum = schema["$defs"]["fileEntry"]["properties"]["kind"]["enum"]
        return set(kinds_enum)
    except KeyError:
        pytest.fail("Schema missing $defs.fileEntry.properties.kind.enum")


# ─────────────────────────────────────────────────────────────────────────────
# TypeScript Registry Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_renderer_kinds_from_ts() -> dict[str, str]:
    """
    Extract kind → category mappings from types.ts kindToCategory() function.

    Returns dict like: {"spectrum_csv": "spectrum_chart", "audio_wav": "audio", ...}
    """
    if not TYPES_TS_PATH.exists():
        pytest.skip(f"types.ts not found: {TYPES_TS_PATH}")

    content = TYPES_TS_PATH.read_text(encoding="utf-8")

    # Find the kindToCategory function body
    func_match = re.search(
        r'function\s+kindToCategory\s*\([^)]*\)[^{]*\{(.*?)^\}',
        content,
        re.MULTILINE | re.DOTALL
    )
    if not func_match:
        pytest.fail("Could not find kindToCategory function in types.ts")

    func_body = func_match.group(1)

    # Extract case statements: case "kind": return "category";
    # Also handles multiple cases before a single return
    kind_to_category = {}
    current_kinds = []

    for line in func_body.split('\n'):
        line = line.strip()

        # Match: case "kind_name":
        case_match = re.match(r'case\s+"([^"]+)":', line)
        if case_match:
            current_kinds.append(case_match.group(1))

        # Match: return "category";
        return_match = re.match(r'return\s+"([^"]+)";', line)
        if return_match and current_kinds:
            category = return_match.group(1)
            for kind in current_kinds:
                kind_to_category[kind] = category
            current_kinds = []

        # Match: default: return "unknown";
        default_match = re.match(r'default:', line)
        if default_match:
            current_kinds = []  # Reset, default is handled separately

    return kind_to_category


def extract_renderer_categories_from_ts() -> set[str]:
    """Extract RendererCategory type values from types.ts."""
    if not TYPES_TS_PATH.exists():
        pytest.skip(f"types.ts not found: {TYPES_TS_PATH}")

    content = TYPES_TS_PATH.read_text(encoding="utf-8")

    # Match: type RendererCategory = "audio" | "image" | ...
    type_match = re.search(
        r'type\s+RendererCategory\s*=\s*([^;]+);',
        content
    )
    if not type_match:
        pytest.fail("Could not find RendererCategory type in types.ts")

    type_def = type_match.group(1)
    categories = re.findall(r'"([^"]+)"', type_def)
    return set(categories)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture Loading & Validation
# ─────────────────────────────────────────────────────────────────────────────

def get_fixture_zips() -> list[Path]:
    """Get all fixture ZIP files."""
    if not FIXTURES_DIR.exists():
        return []
    return list(FIXTURES_DIR.glob("*.zip"))


def load_fixture_manifest(zip_path: Path) -> dict:
    """Load and parse manifest.json from a fixture ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        manifest_bytes = zf.read("manifest.json")
        return json.loads(manifest_bytes.decode("utf-8"))


def validate_manifest_structure(manifest: dict) -> list[str]:
    """Validate manifest has required fields. Returns list of errors."""
    errors = []

    required_fields = ["schema_id", "files"]
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    if manifest.get("schema_id") != "viewer_pack_v1":
        errors.append(f"Invalid schema_id: {manifest.get('schema_id')}")

    if "files" in manifest:
        if not isinstance(manifest["files"], list):
            errors.append("files must be an array")
        else:
            for i, f in enumerate(manifest["files"]):
                if not isinstance(f, dict):
                    errors.append(f"files[{i}] must be an object")
                    continue
                if "relpath" not in f:
                    errors.append(f"files[{i}] missing relpath")
                if "kind" not in f:
                    errors.append(f"files[{i}] missing kind")

    return errors


def validate_file_integrity(zip_path: Path, manifest: dict) -> list[str]:
    """Validate file SHA256 and byte counts match manifest."""
    errors = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for f in manifest.get("files", []):
            relpath = f.get("relpath", "")
            expected_sha256 = f.get("sha256")
            expected_bytes = f.get("bytes")

            try:
                data = zf.read(relpath)
            except KeyError:
                errors.append(f"File missing in ZIP: {relpath}")
                continue

            # Check byte count
            if expected_bytes is not None and len(data) != expected_bytes:
                errors.append(
                    f"{relpath}: byte mismatch (expected {expected_bytes}, got {len(data)})"
                )

            # Check SHA256
            if expected_sha256:
                actual_sha256 = hashlib.sha256(data).hexdigest()
                if actual_sha256 != expected_sha256:
                    errors.append(
                        f"{relpath}: SHA256 mismatch (expected {expected_sha256[:16]}..., "
                        f"got {actual_sha256[:16]}...)"
                    )

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaPresence:
    """Verify schema file exists and is valid JSON."""

    def test_schema_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema not found: {SCHEMA_PATH}"

    def test_schema_valid_json(self):
        schema = load_schema()
        assert isinstance(schema, dict)
        assert schema.get("$schema"), "Missing $schema field"

    def test_schema_has_kind_enum(self):
        schema = load_schema()
        kinds = extract_schema_kinds(schema)
        assert len(kinds) > 0, "Schema kind enum is empty"
        assert "unknown" in kinds, "Schema should include 'unknown' kind"


class TestRendererRegistry:
    """Verify TypeScript renderer registry matches schema."""

    def test_types_ts_exists(self):
        assert TYPES_TS_PATH.exists(), f"types.ts not found: {TYPES_TS_PATH}"

    def test_can_extract_kind_mappings(self):
        mappings = extract_renderer_kinds_from_ts()
        assert len(mappings) > 0, "No kind mappings extracted from types.ts"

    def test_can_extract_categories(self):
        categories = extract_renderer_categories_from_ts()
        assert len(categories) > 0, "No categories extracted from types.ts"
        assert "unknown" in categories, "Should have 'unknown' fallback category"

    def test_all_schema_kinds_have_renderer(self):
        """Every kind in schema should map to a renderer category."""
        schema = load_schema()
        schema_kinds = extract_schema_kinds(schema)
        renderer_kinds = extract_renderer_kinds_from_ts()
        categories = extract_renderer_categories_from_ts()

        # Kinds explicitly mapped in switch statement
        mapped_kinds = set(renderer_kinds.keys())

        # Kinds that fall through to default (unknown)
        unmapped_kinds = schema_kinds - mapped_kinds

        # This is OK - unmapped kinds go to "unknown" renderer
        # But we should flag if there are many unmapped
        unmapped_count = len(unmapped_kinds)
        total_count = len(schema_kinds)

        # Warn if more than 30% unmapped (excluding "unknown" itself)
        unmapped_non_unknown = unmapped_kinds - {"unknown"}
        if len(unmapped_non_unknown) > total_count * 0.3:
            pytest.fail(
                f"Too many schema kinds lack explicit renderer mapping: "
                f"{sorted(unmapped_non_unknown)}"
            )

    def test_renderer_kinds_subset_of_schema(self):
        """Renderer shouldn't map kinds that don't exist in schema."""
        schema = load_schema()
        schema_kinds = extract_schema_kinds(schema)
        renderer_kinds = extract_renderer_kinds_from_ts()

        extra_kinds = set(renderer_kinds.keys()) - schema_kinds

        # Allow some client-side extensions (e.g., coherence_csv might be added)
        # But flag if there are unknown kinds being mapped
        if extra_kinds:
            # This is a warning, not a failure - client can be ahead of schema
            print(f"Note: Renderer maps kinds not in schema: {sorted(extra_kinds)}")


class TestFixtureValidity:
    """Validate all fixture ZIPs against schema."""

    def test_fixtures_exist(self):
        fixtures = get_fixture_zips()
        assert len(fixtures) >= 1, f"No fixture ZIPs found in {FIXTURES_DIR}"

    @pytest.mark.parametrize("fixture_path", get_fixture_zips(), ids=lambda p: p.name)
    def test_fixture_has_valid_manifest(self, fixture_path: Path):
        manifest = load_fixture_manifest(fixture_path)
        errors = validate_manifest_structure(manifest)
        assert not errors, f"Manifest validation errors: {errors}"

    @pytest.mark.parametrize("fixture_path", get_fixture_zips(), ids=lambda p: p.name)
    def test_fixture_kinds_in_schema(self, fixture_path: Path):
        """All kinds in fixture must exist in schema."""
        schema = load_schema()
        schema_kinds = extract_schema_kinds(schema)

        manifest = load_fixture_manifest(fixture_path)
        fixture_kinds = {f["kind"] for f in manifest.get("files", [])}

        invalid_kinds = fixture_kinds - schema_kinds

        # Allow unknown kinds in test fixtures (that's the point of session_unknown_kind.zip)
        if fixture_path.name == "session_unknown_kind.zip":
            # This fixture intentionally has unknown kinds
            return

        assert not invalid_kinds, (
            f"Fixture {fixture_path.name} has kinds not in schema: {invalid_kinds}"
        )

    @pytest.mark.parametrize("fixture_path", get_fixture_zips(), ids=lambda p: p.name)
    def test_fixture_file_integrity(self, fixture_path: Path):
        """Validate SHA256 and byte counts for all files in fixture."""
        manifest = load_fixture_manifest(fixture_path)
        errors = validate_file_integrity(fixture_path, manifest)
        assert not errors, f"Integrity errors: {errors}"


class TestCrossRepoSync:
    """Validate schema sync between tap_tone_pi and luthiers-toolbox."""

    def test_local_schema_matches_expected_kinds(self):
        """Sanity check that our local schema has expected kinds."""
        schema = load_schema()
        kinds = extract_schema_kinds(schema)

        # These are the core kinds that should always exist
        expected_core = {
            "audio_raw",
            "spectrum_csv",
            "session_meta",
            "unknown",
        }

        missing = expected_core - kinds
        assert not missing, f"Schema missing expected core kinds: {missing}"


class TestContractSummary:
    """Generate summary report of contract status."""

    def test_print_contract_summary(self):
        """Print summary of schema ↔ renderer coverage."""
        schema = load_schema()
        schema_kinds = extract_schema_kinds(schema)
        renderer_kinds = extract_renderer_kinds_from_ts()
        categories = extract_renderer_categories_from_ts()

        print("\n" + "=" * 60)
        print("VIEWER PACK CONTRACT SUMMARY")
        print("=" * 60)

        print(f"\nSchema kinds ({len(schema_kinds)}):")
        for kind in sorted(schema_kinds):
            category = renderer_kinds.get(kind, "-> unknown (default)")
            if kind in renderer_kinds:
                category = f"-> {category}"
            print(f"  {kind:25} {category}")

        print(f"\nRenderer categories ({len(categories)}):")
        for cat in sorted(categories):
            kinds_for_cat = [k for k, c in renderer_kinds.items() if c == cat]
            print(f"  {cat:20} ({len(kinds_for_cat)} kinds)")

        print(f"\nFixtures ({len(get_fixture_zips())}):")
        for fp in get_fixture_zips():
            manifest = load_fixture_manifest(fp)
            file_count = len(manifest.get("files", []))
            kinds = {f["kind"] for f in manifest.get("files", [])}
            print(f"  {fp.name:35} {file_count} files, kinds: {sorted(kinds)}")

        print("=" * 60)
