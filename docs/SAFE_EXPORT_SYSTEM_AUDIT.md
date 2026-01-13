# Safe Export System Audit: luthiers-toolbox

> **Version**: 1.0.0
> **Created**: 2026-01-12
> **Scope**: ToolBox → Smart Guitar Safe Export v1
> **Status**: Active

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Module Structure](#3-module-structure)
4. [Schema Definition](#4-schema-definition)
5. [Content Policy Enforcement](#5-content-policy-enforcement)
6. [Validation Engine](#6-validation-engine)
7. [Export Builder](#7-export-builder)
8. [Test Coverage](#8-test-coverage)
9. [Sample Bundle](#9-sample-bundle)

---

## 1. Executive Summary

### Purpose

The safe export system creates **teaching/learning content bundles** that are explicitly "Smart Guitar-safe":

- **Read-only / Non-authoritative**: No decisions, no governance state
- **Non-manufacturing**: No G-code, no toolpaths, no CNC settings
- **Content-addressed**: SHA256 hashes for integrity verification
- **Composable**: Can add scanned-book content or other educational material

### Key Statistics

| Metric | Value |
|--------|-------|
| Pydantic Models | 14 |
| Forbidden Extensions | 17 |
| Forbidden Kinds | 7 |
| Allowed File Kinds | 15 |
| Content Policy Flags | 4 (all `const: true`) |
| Test Cases | 15+ |

### Data Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           luthiers-toolbox                               │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    PROTECTED CONTENT (blocked)                    │  │
│  │  • G-code (.nc, .gcode)      • Toolpaths (.sbp, .crv)            │  │
│  │  • DXF/DWG drawings          • RMOS decisions/artifacts          │  │
│  │  • CAM outputs               • Secrets (.pem, .key, .env)        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    ExportBuilder                                   │  │
│  │  • add_topic()               • add_lesson()                       │  │
│  │  • add_drill()               • add_file()                         │  │
│  │                    ↓                                               │  │
│  │              Validator (Gate Check)                               │  │
│  │  • Forbidden extensions ❌   • Content policy ✓                  │  │
│  │  • SHA256 verification ✓    • File integrity ✓                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│                                 ↓                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │               SAFE EXPORT BUNDLE                                  │  │
│  │  smart_guitar_export_v1_{export_id}/                              │  │
│  │  ├── manifest.json          (content policy: all true)           │  │
│  │  ├── index/                                                       │  │
│  │  │   ├── topics.json                                              │  │
│  │  │   ├── lessons.json                                             │  │
│  │  │   └── drills.json                                              │  │
│  │  ├── assets/                                                      │  │
│  │  │   └── {sha256}.md        (lesson content)                      │  │
│  │  └── provenance/                                                  │  │
│  │      └── build.json         (git commit, timestamp)               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
         ═════════════════════════════════════════ GOVERNANCE BOUNDARY
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           Smart Guitar                                   │
│  • smart_guitar_app            • smart_guitar_coach                     │
│  • smart_guitar_firmware_tools                                          │
│                                                                          │
│  RECEIVES:                     CANNOT RECEIVE:                          │
│  ✓ Lesson markdown             ❌ G-code files                          │
│  ✓ Audio samples               ❌ DXF toolpaths                         │
│  ✓ Topic/drill indexes         ❌ Manufacturing parameters              │
│  ✓ Reference content           ❌ RMOS decisions                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
services/api/app/smart_guitar_export/
├── __init__.py          # Public API exports (18 items)
├── schemas.py           # Pydantic models (14 classes)
├── validator.py         # Gate enforcement logic
└── exporter.py          # Bundle builder

contracts/
├── toolbox_smart_guitar_safe_export_v1.schema.json    # JSON Schema
├── toolbox_smart_guitar_safe_export_v1.schema.sha256  # Checksum

services/api/tests/
└── test_smart_guitar_export_gate.py    # Boundary enforcement tests

services/api/data/smart_guitar_exports/
└── smart_guitar_export_v1_sample_001/   # Sample bundle
    ├── manifest.json
    ├── index/
    ├── assets/
    └── provenance/
```

---

## 3. Module Structure

### 3.1 Public Exports (`__init__.py`)

```python
# Schemas
SmartGuitarExportManifest   # Root manifest model
ExportProducer              # Producer metadata
ExportScope                 # Domain and consumers
ContentPolicy               # Safety flags (all const: true)
ExportFileEntry             # File manifest entry
TopicEntry                  # Topic in index
LessonEntry                 # Lesson in index
DrillEntry                  # Drill in index
TopicsIndex                 # Topics index file
LessonsIndex                # Lessons index file
DrillsIndex                 # Drills index file

# Validator
validate_manifest()         # Dict → ValidationResult
validate_bundle()           # Path → ValidationResult (full check)
ValidationResult            # Dataclass with valid, errors, warnings
FORBIDDEN_EXTENSIONS        # frozenset of 17 blocked extensions
FORBIDDEN_KINDS             # frozenset of 7 blocked kinds

# Exporter
create_export_bundle()      # Convenience function
ExportBuilder               # Builder class for creating bundles
```

---

## 4. Schema Definition

### 4.1 Top-Level Required Fields (9)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `schema_id` | string | `const: "toolbox_smart_guitar_safe_export"` | Fixed identifier |
| `schema_version` | string | `const: "v1"` | Fixed version |
| `created_at_utc` | string | ISO 8601 | Creation timestamp |
| `export_id` | string | - | Stable export identifier |
| `producer` | object | see below | Origin system info |
| `scope` | object | see below | Domain and consumers |
| `content_policy` | object | see below | **Safety assertions** |
| `files` | array | see below | File manifest |
| `bundle_sha256` | string | 64 hex chars | SHA256 of pre-hash manifest |

### 4.2 Producer Object

```python
class ExportProducer(BaseModel):
    system: Literal["luthiers-toolbox"] = "luthiers-toolbox"  # Fixed
    repo: str           # Repository URL
    commit: str         # Git commit SHA
    build_id: Optional[str]  # CI build ID
```

### 4.3 Scope Object

```python
class ExportScope(BaseModel):
    domain: ExportDomain        # education, practice, coaching, reference
    safe_for: Literal["smart_guitar"] = "smart_guitar"  # Fixed
    intended_consumers: List[IntendedConsumer]  # Optional list
```

**Export Domains (4)**:
| Domain | Purpose |
|--------|---------|
| `education` | Instructional content |
| `practice` | Practice routines |
| `coaching` | Coaching guidance |
| `reference` | Reference materials |

**Intended Consumers (3)**:
| Consumer | Description |
|----------|-------------|
| `smart_guitar_app` | Mobile/desktop app |
| `smart_guitar_coach` | Coaching system |
| `smart_guitar_firmware_tools` | Device firmware tools |

### 4.4 Content Policy Object - **THE GOVERNANCE BOUNDARY**

```python
class ContentPolicy(BaseModel):
    no_manufacturing: Literal[True] = True   # MUST be true
    no_toolpaths: Literal[True] = True       # MUST be true
    no_rmos_authority: Literal[True] = True  # MUST be true
    no_secrets: Literal[True] = True         # MUST be true
    notes: Optional[str]                     # Optional explanation
```

> **Key Insight**: All four flags use `Literal[True]`, meaning Pydantic will REJECT any manifest where these are `false` or missing. This is enforced at the schema level.

### 4.5 File Entry Structure

```python
class ExportFileEntry(BaseModel):
    relpath: str      # Relative path in bundle
    sha256: str       # Content hash
    bytes: int        # File size
    mime: str         # MIME type
    kind: FileKind    # Classification
```

### 4.6 Allowed File Kinds (15)

| Kind | Description |
|------|-------------|
| `manifest` | The manifest.json file |
| `topic_index` | topics.json index |
| `lesson_index` | lessons.json index |
| `drill_index` | drills.json index |
| `lesson_md` | Lesson markdown content |
| `lesson_json` | Lesson JSON content |
| `reference_md` | Reference markdown |
| `reference_json` | Reference JSON |
| `audio_wav` | WAV audio files |
| `audio_flac` | FLAC audio files |
| `image_png` | PNG images |
| `image_jpg` | JPEG images |
| `chart_csv` | Chart data (CSV) |
| `provenance` | Build provenance info |
| `unknown` | Unclassified (allowed) |

---

## 5. Content Policy Enforcement

### 5.1 Forbidden Extensions (17)

**Location**: `validator.py:28-51`

```python
FORBIDDEN_EXTENSIONS = frozenset({
    # G-code / CNC
    ".nc",          # Standard G-code
    ".gcode",       # 3D printer G-code
    ".ngc",         # NGC format
    ".tap",         # TAP format
    ".cnc",         # Generic CNC

    # CAM / DXF
    ".dxf",         # AutoCAD DXF
    ".dwg",         # AutoCAD DWG

    # Toolpaths
    ".toolpath",    # Generic toolpath
    ".sbp",         # ShopBot
    ".crv",         # Vectric Aspire/VCarve

    # Executables
    ".exe",         # Windows executable
    ".dll",         # Windows library
    ".so",          # Linux shared object
    ".dylib",       # macOS dynamic library

    # Secrets
    ".pem",         # SSL certificates
    ".key",         # Private keys
    ".env",         # Environment files
})
```

### 5.2 Forbidden Kinds (7)

```python
FORBIDDEN_KINDS = frozenset({
    "gcode",
    "toolpath",
    "dxf",
    "cam_output",
    "rmos_artifact",
    "run_decision",
    "manufacturing",
})
```

### 5.3 Forbidden Path Patterns (5)

```python
FORBIDDEN_PATH_PATTERNS = [
    "/api/cam/",
    "/api/rmos/",
    "toolpaths/",
    "gcode/",
    ".nc",
]
```

---

## 6. Validation Engine

### 6.1 Validation Steps

**Location**: `validator.py`

#### `validate_manifest(manifest_dict)` - Schema-only validation

```python
def validate_manifest(manifest_dict: Dict[str, Any]) -> ValidationResult:
    # 1) Parse with Pydantic (validates schema + Literal constraints)
    manifest = SmartGuitarExportManifest.model_validate(manifest_dict)

    # 2) Double-check content policy flags
    if not policy.no_manufacturing:
        result.add_error("content_policy.no_manufacturing must be true")
    # ... (same for no_toolpaths, no_rmos_authority, no_secrets)

    # 3) Check for forbidden file extensions
    for f in manifest.files:
        ext = Path(f.relpath).suffix.lower()
        if ext in FORBIDDEN_EXTENSIONS:
            result.add_error(f"Forbidden extension '{ext}' in file: {f.relpath}")

    # 4) Check for forbidden file kinds
    # 5) Check for forbidden path patterns
```

#### `validate_bundle(bundle_path)` - Full bundle validation

```python
def validate_bundle(bundle_path: Path) -> ValidationResult:
    # 1) Check bundle directory exists
    # 2) Check manifest.json exists
    # 3) Load and validate manifest (calls validate_manifest)
    # 4) For each file in manifest:
    #    - Check file exists
    #    - Check byte size matches
    #    - Check SHA256 matches
    # 5) Warn about extra files not in manifest
```

### 6.2 ValidationResult

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    manifest: Optional[SmartGuitarExportManifest] = None
```

---

## 7. Export Builder

### 7.1 ExportBuilder Class

**Location**: `exporter.py:157-395`

```python
class ExportBuilder:
    """Builder for creating Smart Guitar safe export bundles."""

    def __init__(
        self,
        domain: ExportDomain = ExportDomain.EDUCATION,
        export_id: Optional[str] = None,
        build_id: Optional[str] = None,
    ):
        ...

    def add_topic(self, topic_id, title, tags=None) -> "ExportBuilder"
    def add_lesson(self, lesson_id, title, level, content_md, topic_ids=None) -> "ExportBuilder"
    def add_drill(self, drill_id, title, tempo_min=60, tempo_max=120, tempo_step=5, metrics=None) -> "ExportBuilder"
    def add_file(self, relpath, content, mime=None, kind=None) -> "ExportBuilder"
    def add_file_from_path(self, src_path, relpath=None) -> "ExportBuilder"
    def build(self, output_dir) -> Path
```

### 7.2 Bundle Directory Structure

```
smart_guitar_export_v1_{export_id}/
├── manifest.json              # Root manifest
├── index/
│   ├── topics.json            # Topic index
│   ├── lessons.json           # Lesson index
│   └── drills.json            # Drill index
├── assets/
│   └── {sha256}.md            # Content-addressed lesson files
└── provenance/
    └── build.json             # Git commit, timestamp
```

### 7.3 Content-Addressed Storage

Lesson content is stored by SHA256 hash:

```python
def add_lesson(self, lesson_id, title, level, content_md, topic_ids=None):
    sha = _sha256_of_bytes(content_md.encode("utf-8"))
    relpath = f"assets/{sha}.md"  # Content-addressed
    ...
```

### 7.4 Bundle SHA256 Calculation

```python
# Build manifest WITHOUT bundle_sha256
manifest_dict["bundle_sha256"] = ""
manifest_pre_bytes = json.dumps(manifest_dict, indent=2, sort_keys=True).encode("utf-8")
bundle_sha256 = _sha256_of_bytes(manifest_pre_bytes)

# Then add the real sha256
manifest_dict["bundle_sha256"] = bundle_sha256
```

### 7.5 Convenience Function

```python
def create_export_bundle(
    output_dir: Path,
    domain: ExportDomain = ExportDomain.EDUCATION,
    topics: List[Dict] = None,
    lessons: List[Dict] = None,
    drills: List[Dict] = None,
    files: List[Dict] = None,
    export_id: str = None,
    validate: bool = True,  # Auto-validates by default
) -> Path:
    ...
```

---

## 8. Test Coverage

### 8.1 Test File: `test_smart_guitar_export_gate.py`

**Location**: `services/api/tests/test_smart_guitar_export_gate.py`

| Test Category | Count | Purpose |
|---------------|-------|---------|
| Schema Validation | 2 | Required fields, valid manifest |
| Content Policy | 2 | Reject false flags |
| Forbidden Extensions | 3+ | Block .nc, .dxf, etc. |
| Builder Tests | 3 | Create valid bundles |
| Bundle Validation | 3 | Missing files, SHA256 mismatch |
| Integration | 1 | Full workflow test |

### 8.2 Key Test Cases

```python
# Content policy enforcement
def test_manifest_rejects_manufacturing_flag_false():
    """content_policy.no_manufacturing must be true."""
    manifest["content_policy"]["no_manufacturing"] = False  # BAD
    result = validate_manifest(manifest)
    assert not result.valid

# Forbidden extensions
@pytest.mark.parametrize("ext", list(FORBIDDEN_EXTENSIONS)[:5])
def test_forbidden_extensions_rejected(ext):
    """All forbidden extensions should be rejected."""
    manifest["files"] = [{"relpath": f"assets/file{ext}", ...}]
    result = validate_manifest(manifest)
    assert not result.valid

# Builder rejects forbidden files
def test_builder_rejects_forbidden_file():
    """ExportBuilder rejects forbidden file extensions."""
    builder = ExportBuilder(domain="education")
    with pytest.raises(ValueError, match="Forbidden extension"):
        builder.add_file("toolpath.nc", b"G0 X0 Y0")

# SHA256 integrity check
def test_validate_bundle_detects_sha256_mismatch():
    """validate_bundle detects SHA256 mismatches."""
    manifest["files"][0]["sha256"] = "wrong_hash"
    result = validate_bundle(bundle_path)
    assert not result.valid
    assert any("sha256 mismatch" in e.lower() for e in result.errors)
```

### 8.3 Running Tests

```bash
cd services/api
pytest tests/test_smart_guitar_export_gate.py -v
```

---

## 9. Sample Bundle

### 9.1 Sample Manifest

**Location**: `services/api/data/smart_guitar_exports/smart_guitar_export_v1_sample_001/manifest.json`

```json
{
  "schema_id": "toolbox_smart_guitar_safe_export",
  "schema_version": "v1",
  "created_at_utc": "2026-01-11T07:08:57.146622+00:00",
  "export_id": "sample_001",
  "producer": {
    "system": "luthiers-toolbox",
    "repo": "https://github.com/HanzoRazer/luthiers-toolbox.git",
    "commit": "d74a70a8a3676ca9e14742a1936e60a65e95a73b",
    "build_id": null
  },
  "scope": {
    "domain": "education",
    "safe_for": "smart_guitar",
    "intended_consumers": []
  },
  "content_policy": {
    "no_manufacturing": true,
    "no_toolpaths": true,
    "no_rmos_authority": true,
    "no_secrets": true,
    "notes": null
  },
  "index": {
    "topics_relpath": "index/topics.json",
    "lessons_relpath": "index/lessons.json",
    "drills_relpath": "index/drills.json"
  },
  "files": [
    {"relpath": "index/topics.json", "sha256": "1009c90f...", "bytes": 486, "mime": "application/json", "kind": "topic_index"},
    {"relpath": "index/lessons.json", "sha256": "31922230...", "bytes": 1090, "mime": "application/json", "kind": "lesson_index"},
    {"relpath": "index/drills.json", "sha256": "08dae427...", "bytes": 1222, "mime": "application/json", "kind": "drill_index"},
    {"relpath": "assets/78eb926d....md", "sha256": "78eb926d...", "bytes": 769, "mime": "text/markdown", "kind": "lesson_md"},
    {"relpath": "provenance/build.json", "sha256": "31f4888c...", "bytes": 215, "mime": "application/json", "kind": "provenance"}
  ],
  "bundle_sha256": "ff5be945a0c814ff7ba421e2397ce0572bb085aa86383269bfb7ffdc4c6e2d82"
}
```

### 9.2 Sample File Count

| File Type | Count |
|-----------|-------|
| Index files | 3 |
| Lesson markdown | 4 |
| Provenance | 1 |
| **Total** | **8** |

---

## Appendix A: Quick Reference

### Valid Export Template

```python
from app.smart_guitar_export import ExportBuilder, create_export_bundle

# Using ExportBuilder
builder = ExportBuilder(domain="education")
builder.add_topic("setup", "Setup Guide", tags=["beginner"])
builder.add_lesson("lesson_001", "Clean Fretting", "beginner", "# Content...")
builder.add_drill("drill_001", "Alternate Picking", tempo_min=60, tempo_max=120)
bundle_path = builder.build("/output/path")

# Using convenience function
bundle_path = create_export_bundle(
    "/output/path",
    domain="education",
    topics=[{"id": "setup", "title": "Setup Guide", "tags": ["beginner"]}],
    lessons=[{"id": "lesson_001", "title": "Clean Fretting", "level": "beginner", "content_md": "# Content..."}],
)
```

### Forbidden Extensions Quick List

```
.nc, .gcode, .ngc, .tap, .cnc,
.dxf, .dwg,
.toolpath, .sbp, .crv,
.exe, .dll, .so, .dylib,
.pem, .key, .env
```

### Content Policy Requirements

```json
{
  "content_policy": {
    "no_manufacturing": true,    // REQUIRED: true
    "no_toolpaths": true,        // REQUIRED: true
    "no_rmos_authority": true,   // REQUIRED: true
    "no_secrets": true           // REQUIRED: true
  }
}
```

### Allowed File Kinds

```
manifest, topic_index, lesson_index, drill_index,
lesson_md, lesson_json, reference_md, reference_json,
audio_wav, audio_flac, image_png, image_jpg,
chart_csv, provenance, unknown
```

---

## Document History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-12 | 1.0.0 | Development Team | Initial creation |

---

*This document should be updated whenever the safe export system is modified.*
