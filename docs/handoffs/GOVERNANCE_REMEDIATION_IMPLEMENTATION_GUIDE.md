# Governance Remediation Implementation Guide

**Status:** ACTIVE IMPLEMENTATION REFERENCE  
**Date:** 2026-05-12  
**Purpose:** Concrete implementation guide with scripts, functions, and code examples  
**Audience:** Development teams implementing governance remediation

---

# Table of Contents

1. [Governance Enforcement Infrastructure](#1-governance-enforcement-infrastructure)
2. [Adding Protected Systems](#2-adding-protected-systems)
3. [Capability Registry Implementation](#3-capability-registry-implementation)
4. [Policy Engine Integration](#4-policy-engine-integration)
5. [Semantic Authority Boundaries](#5-semantic-authority-boundaries)
6. [Manifest Management](#6-manifest-management)
7. [Pre-Commit Hook Configuration](#7-pre-commit-hook-configuration)
8. [Testing Governance Compliance](#8-testing-governance-compliance)
9. [Common Implementation Patterns](#9-common-implementation-patterns)
10. [Anti-Pattern Detection Scripts](#10-anti-pattern-detection-scripts)

---

# 1. Governance Enforcement Infrastructure

## 1.1 Protected Path Check Script

**Location:** `scripts/check_protected_paths.py`

**Purpose:** Block commits to protected systems without explicit approval.

### Core Function: `check_protected_paths()`

```python
def check_protected_paths() -> int:
    """
    Main check function.
    
    Flow:
    1. Check GOVERNANCE_APPROVED_CHANGE environment variable
    2. Load governance manifest from docs/governance/governance_manifest.json
    3. Get staged files via git diff --cached
    4. Match staged files against protected paths
    5. If violations found and not approved, return 1 (fail)
    
    Returns:
        0 if no violations or approved
        1 if violations found without approval
    """
    approved = os.environ.get("GOVERNANCE_APPROVED_CHANGE") == "1"
    manifest = load_manifest()
    staged_files = get_staged_files()
    
    violations = []
    for staged_file in staged_files:
        for system in manifest.get("protected_systems", []):
            if file_matches_protected_path(staged_file, system.get("paths", [])):
                violations.append({
                    "file": staged_file,
                    "system": system.get("id"),
                    "protection_level": system.get("protection_level")
                })
    
    if violations and not approved:
        print("[FAIL] Protected system modified without approval")
        return 1
    return 0
```

### Path Matching Logic

```python
def file_matches_protected_path(file_path: str, protected_paths: list[str]) -> bool:
    """
    Check if a file matches any protected path pattern.
    
    Matching rules:
    1. Directory match: path ends with "/" → match all files under directory
    2. Exact file match: path matches exactly
    3. Subdirectory match: file starts with protected + "/"
    
    Examples:
        protected: "services/api/app/routers/blueprint/"
        matches: "services/api/app/routers/blueprint/vectorize_router.py"
        
        protected: "services/api/app/util/dxf_compat.py"
        matches: "services/api/app/util/dxf_compat.py" (exact only)
    """
    file_path = file_path.replace("\\", "/")
    
    for protected in protected_paths:
        protected = protected.replace("\\", "/")
        
        # Directory match
        if protected.endswith("/"):
            if file_path.startswith(protected):
                return True
        # Exact file match
        elif file_path == protected:
            return True
        # File under protected directory
        elif file_path.startswith(protected + "/"):
            return True
    
    return False
```

### Usage Examples

```bash
# Normal commit (will fail if touching protected paths)
git add services/api/app/services/blueprint_orchestrator.py
git commit -m "Fix bug"
# Output: [FAIL] Protected system modified without approval

# Approved commit (bypass with environment variable)
# PowerShell:
$env:GOVERNANCE_APPROVED_CHANGE = "1"
git commit -m "Approved governance change"

# Bash:
GOVERNANCE_APPROVED_CHANGE=1 git commit -m "Approved governance change"

# Verify enforcement is working
python scripts/check_protected_paths.py
echo $?  # Should be 0 if clean, 1 if violations
```

---

## 1.2 Sprint Namespace Check Script

**Location:** `scripts/check_sprint_namespace.py`

**Purpose:** Warn on unnamespaced dev order references (warn-only mode).

### Valid Namespace Prefixes

```python
VALID_NAMESPACES = {
    "VECTOR",  # Blueprint Reader vectorizer
    "IBG",     # Image Body Generator
    "BOE",     # Body Outline Editor
    "DXF",     # DXF compliance and export
    "CAM",     # CAM pipeline and toolpaths
    "RMOS",    # Router Machine OS
    "SPIRAL",  # Spiral soundhole system
    "MRP",     # Morphology Reconstruction Platform
}
```

### Pattern Detection

```python
# Correct format: PREFIX-NUMBER[SUFFIX]
NAMESPACED_PATTERN = re.compile(
    r'\b(' + '|'.join(VALID_NAMESPACES) + r')-\d+[A-Z]?\b'
)
# Examples: VECTOR-1A, MRP-1A, CAM-6B, IBG-1

# Incorrect format detection
UNNAMESPACED_PATTERNS = [
    re.compile(r'\bDev Order \d+\b', re.IGNORECASE),  # "Dev Order 24"
    re.compile(r'\bOrder \d+[A-Z]?\b'),                # "Order 5G"
    re.compile(r'\bSprint \d+[A-Z]?\b(?!\s*\()'),      # "Sprint 5G" but not "Sprint 9 (date)"
]
```

### Adding New Namespace Prefix

```python
# In scripts/check_sprint_namespace.py, add to VALID_NAMESPACES:
VALID_NAMESPACES = {
    "VECTOR",
    "IBG",
    "BOE",
    "DXF",
    "CAM",
    "RMOS",
    "SPIRAL",
    "MRP",
    "ACOUSTIC",  # NEW: Acoustic modeling system
}

# Also update docs/governance/SPRINT_NAMESPACE_STANDARD.md:
# | ACOUSTIC | Acoustic modeling system | Production |
```

---

# 2. Adding Protected Systems

## 2.1 Governance Manifest Schema

**Location:** `docs/governance/governance_manifest.json`

### Full Schema Definition

```json
{
  "manifest_version": "1.0.0",
  "effective_date": "2026-05-11",
  "governance_framework": "docs/governance/MORPHOLOGY_RECONSTRUCTION_PLATFORM.md",
  
  "protected_systems": [
    {
      "id": "SYSTEM_IDENTIFIER",
      "protection_level": "LOCKED | STABILIZED",
      "paths": [
        "path/to/protected/directory/",
        "path/to/protected/file.py"
      ],
      "governance_doc": "docs/governance/SYSTEM_PROTECTION_RULES.md",
      "requires_explicit_approval": true,
      "forbidden_actions": [
        "action_that_is_not_allowed",
        "another_forbidden_action"
      ],
      "allowed_actions": [
        "read",
        "audit",
        "document"
      ],
      "regression_required": true,
      "notes": "Optional notes about this system"
    }
  ],
  
  "approval_mechanism": {
    "environment_variable": "GOVERNANCE_APPROVED_CHANGE",
    "required_value": "1"
  },
  
  "enforcement_scripts": {
    "protected_paths": "scripts/check_protected_paths.py",
    "sprint_namespace": "scripts/check_sprint_namespace.py"
  }
}
```

### Adding a New Protected System

```python
# Step 1: Add entry to governance_manifest.json
new_system = {
    "id": "ACOUSTIC_SOLVER_CORE",
    "protection_level": "LOCKED",
    "paths": [
        "services/api/app/calculators/acoustic/",
        "services/api/app/calculators/helmholtz_solver.py"
    ],
    "governance_doc": "docs/governance/ACOUSTIC_SOLVER_PROTECTION_RULES.md",
    "requires_explicit_approval": True,
    "forbidden_actions": [
        "alter_physics_constants",
        "remove_validation_gates",
        "bypass_calibration"
    ],
    "allowed_actions": [
        "read",
        "audit",
        "document",
        "add_instrument_presets"
    ],
    "regression_required": True,
    "notes": "Helmholtz resonator and acoustic solver math verified against published research"
}

# Step 2: Add governance header to protected files
"""
# GOVERNANCE:
# SYSTEM: ACOUSTIC_SOLVER_CORE
# STATUS: PROTECTED_PRODUCTION_BASELINE
# DOC: docs/governance/ACOUSTIC_SOLVER_PROTECTION_RULES.md
# RULE: Do not alter production behavior without GOVERNANCE_APPROVED_CHANGE.
"""

# Step 3: Create governance doc (docs/governance/ACOUSTIC_SOLVER_PROTECTION_RULES.md)
```

### Protection Level Semantics

```python
PROTECTION_LEVELS = {
    "LOCKED": {
        "description": "Production-critical system, no changes without explicit approval",
        "requires_approval": True,
        "regression_required": True,
        "ci_blocking": True
    },
    "STABILIZED": {
        "description": "Governance documentation, additions allowed, deletions blocked",
        "requires_approval": True,
        "regression_required": False,
        "ci_blocking": True
    },
    "MONITORED": {
        "description": "Changes allowed but logged for audit",
        "requires_approval": False,
        "regression_required": False,
        "ci_blocking": False
    }
}
```

---

# 3. Capability Registry Implementation

## 3.1 Adding New CAM Operation

**Location:** `services/api/app/cam/cam_operation_registry.py`

### Full Capability Declaration

```python
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# Type definitions
ExportabilityClass = Literal[
    "preview_only",       # Preview generation only, no export
    "governed_export",    # Full export pipeline
    "translator_ready",   # Export + translator validation
    "machine_candidate",  # Export + translator + machine validation (future)
]

MaturityLevel = Literal[
    "experimental",  # Under development, YELLOW gate
    "candidate",     # Feature complete, needs validation, YELLOW gate
    "governed",      # Validated, GREEN gate
    "canonical",     # Production stable, GREEN gate
]

# Adding a new operation
CAM_OPERATION_REGISTRY["fret_slot"] = CAMOperationCapability(
    # Identity
    operation="fret_slot",
    
    # Lifecycle Support Flags
    lifecycle_supported=True,
    export_object_supported=True,
    machine_validation_supported=True,
    translator_validation_supported=True,
    rmos_persistence_supported=True,
    
    # Routes
    preview_route="/api/cam/fret-slots/preview",
    lifecycle_route="/api/cam/export/lifecycle/validate",
    
    # Classification
    exportability_class="governed_export",
    maturity="canonical",
    
    # Machine Requirements (semantic descriptors)
    required_machine_capabilities=[
        "3_axis_motion",
        "linear_interpolation",
        "precise_positioning",
        "slot_cutting",
    ],
    
    # Translator Requirements
    required_translator_features=[
        "polyline_support",
        "line_support",
    ],
    
    # Geometry Types
    supported_geometry_types=[
        "line",
        "polyline",
    ],
    
    # Safety Assertions (MUST remain false until machine output implemented)
    machine_ready=False,
    machine_output_supported=False,
    
    # Documentation
    notes="Fret slot cutting for fretted instruments. Governed preview since 5D.",
)
```

### Registry Query Functions

```python
def get_operation_capability(operation: str) -> Optional[CAMOperationCapability]:
    """Get capability for specific operation."""
    return CAM_OPERATION_REGISTRY.get(operation)

def list_lifecycle_supported_operations() -> List[str]:
    """Operations that support lifecycle orchestration."""
    return [op for op, cap in CAM_OPERATION_REGISTRY.items() if cap.lifecycle_supported]

def list_governed_operations() -> List[str]:
    """Operations with governed or canonical maturity."""
    return [op for op, cap in CAM_OPERATION_REGISTRY.items() 
            if cap.maturity in ("governed", "canonical")]

def list_exportable_operations() -> List[str]:
    """Operations that support export object generation."""
    return [op for op, cap in CAM_OPERATION_REGISTRY.items() if cap.export_object_supported]

# Usage example
>>> from app.cam.cam_operation_registry import get_operation_capability
>>> cap = get_operation_capability("nut_slot")
>>> cap.maturity
'canonical'
>>> cap.exportability_class
'governed_export'
>>> cap.required_machine_capabilities
['3_axis_motion', 'controlled_plunge', 'linear_interpolation']
```

---

# 4. Policy Engine Integration

## 4.1 Lifecycle Policy Evaluation

**Location:** `services/api/app/cam/cam_lifecycle_policy_engine.py`

### Policy Evaluation Model

```python
from pydantic import BaseModel
from typing import List, Optional

class LifecyclePolicyEvaluation(BaseModel):
    """Result of policy evaluation for an operation."""
    
    # Operation identity
    operation: str
    
    # Overall decision
    allowed: bool
    lifecycle_gate: str  # "green", "yellow", "red"
    
    # Classification (from capability)
    exportability_class: str
    maturity: str
    
    # Policy check results
    policy_checks: List[str]  # ["operation_registered: PASS", ...]
    blocking_issues: List[str]
    warnings: List[str]
    
    # Stage permissions (determined by policy)
    preview_allowed: bool
    export_object_allowed: bool
    machine_validation_allowed: bool
    translator_validation_allowed: bool
    rmos_persistence_allowed: bool
    
    # Hard prohibitions (always false until implemented)
    machine_output_allowed: bool = False
    translator_execution_allowed: bool = False
```

### Policy Evaluation Function

```python
def evaluate_lifecycle_policy(
    operation: str,
    persist_to_rmos: bool = False
) -> LifecyclePolicyEvaluation:
    """
    Evaluate lifecycle policy for an operation.
    
    This runs BEFORE any lifecycle stages execute.
    If policy returns RED, no stages run.
    
    Flow:
    1. Check if operation is registered
    2. Check exportability class permissions
    3. Check maturity level gates
    4. Check RMOS eligibility if requested
    5. Aggregate gate status
    """
    capability = get_operation_capability(operation)
    
    policy_checks = []
    blocking_issues = []
    warnings = []
    
    # Check 1: Operation registered
    if capability is None:
        policy_checks.append("operation_registered: FAIL")
        blocking_issues.append(f"Operation '{operation}' not registered in capability registry")
        return LifecyclePolicyEvaluation(
            operation=operation,
            allowed=False,
            lifecycle_gate="red",
            exportability_class="unknown",
            maturity="unknown",
            policy_checks=policy_checks,
            blocking_issues=blocking_issues,
            warnings=warnings,
            preview_allowed=False,
            export_object_allowed=False,
            machine_validation_allowed=False,
            translator_validation_allowed=False,
            rmos_persistence_allowed=False,
        )
    
    policy_checks.append("operation_registered: PASS")
    
    # Check 2: Exportability class permissions
    stage_permissions = get_stage_permissions(capability.exportability_class)
    
    # Check 3: Maturity level
    gate = "green"
    if capability.maturity in ("experimental", "candidate"):
        gate = "yellow"
        warnings.append(f"Operation maturity is {capability.maturity}")
    
    # Check 4: RMOS eligibility
    if persist_to_rmos and not capability.rmos_persistence_supported:
        blocking_issues.append("Operation does not permit RMOS persistence")
        gate = "red"
    
    return LifecyclePolicyEvaluation(
        operation=operation,
        allowed=(gate != "red"),
        lifecycle_gate=gate,
        exportability_class=capability.exportability_class,
        maturity=capability.maturity,
        policy_checks=policy_checks,
        blocking_issues=blocking_issues,
        warnings=warnings,
        preview_allowed=stage_permissions["preview"],
        export_object_allowed=stage_permissions["export_object"],
        machine_validation_allowed=stage_permissions["machine_validation"],
        translator_validation_allowed=stage_permissions["translator_validation"],
        rmos_persistence_allowed=stage_permissions["rmos_persistence"],
    )


def get_stage_permissions(exportability_class: str) -> dict:
    """
    Get stage permissions based on exportability class.
    
    | Class             | preview | export | machine | translator | rmos |
    |-------------------|---------|--------|---------|------------|------|
    | preview_only      | ✓       | ✗      | ✗       | ✗          | ✗    |
    | governed_export   | ✓       | ✓      | ✓       | ✓          | ✓    |
    | translator_ready  | ✓       | ✓      | ✓       | ✓          | ✓    |
    | machine_candidate | ✓       | ✓      | ✓       | ✓          | ✓    |
    """
    permissions = {
        "preview_only": {
            "preview": True,
            "export_object": False,
            "machine_validation": False,
            "translator_validation": False,
            "rmos_persistence": False,
        },
        "governed_export": {
            "preview": True,
            "export_object": True,
            "machine_validation": True,
            "translator_validation": True,
            "rmos_persistence": True,
        },
        "translator_ready": {
            "preview": True,
            "export_object": True,
            "machine_validation": True,
            "translator_validation": True,
            "rmos_persistence": True,
        },
        "machine_candidate": {
            "preview": True,
            "export_object": True,
            "machine_validation": True,
            "translator_validation": True,
            "rmos_persistence": True,
        },
    }
    return permissions.get(exportability_class, permissions["preview_only"])
```

### Orchestrator Integration

```python
def orchestrate_lifecycle_validation(request: LifecycleRequest) -> LifecycleResponse:
    """
    Main lifecycle orchestrator with policy engine integration.
    
    Flow:
    0. Evaluate policy FIRST
    1. If policy RED → return early with policy report
    2. Generate preview (if preview_allowed)
    3. Build export object (if export_object_allowed and preview GREEN)
    4. Run machine validation (if machine_validation_allowed)
    5. Run translator validation (if translator_validation_allowed)
    6. Aggregate lifecycle report
    """
    # Step 0: Policy evaluation (BEFORE any stages run)
    policy = evaluate_lifecycle_policy(
        operation=request.operation,
        persist_to_rmos=request.persist_to_rmos
    )
    
    if not policy.allowed:
        return LifecycleResponse(
            lifecycle_gate="red",
            export_ready=False,
            policy_evaluation=policy,
            blocking_issues=policy.blocking_issues,
            # ... early return with policy report
        )
    
    # Step 1-5: Run allowed stages...
    preview_result = None
    if policy.preview_allowed:
        preview_result = dispatch_preview(request.operation, request.payload)
    
    export_object = None
    if policy.export_object_allowed and preview_result.gate != "red":
        export_object = dispatch_export_object(request.operation, preview_result)
    
    # ... continue with other stages
```

---

# 5. Semantic Authority Boundaries

## 5.1 Authority Boundary Enforcement

### DO: Proper Layer Separation

```python
# CORRECT: Export Object is DXF-agnostic
# services/api/app/cam/export_object_builder.py

class ExportObject(BaseModel):
    """
    Portable manufacturing representation.
    
    AUTHORITY: Manufacturing semantics
    NOT AUTHORITY: Serialization format
    """
    geometry: GeometryBlock      # Abstract geometry, not DXF entities
    toolpaths: ToolpathBlock     # Neutral toolpath moves
    tooling: ToolingBlock        # Tool specification
    intent: IntentBlock          # Manufacturing intent
    
    # NO DXF-specific fields here:
    # - No "dxf_entities"
    # - No "layer_names"
    # - No "lwpolyline_flags"

# CORRECT: DXF is translator concern only
# services/api/app/cam/translators/dxf_translator.py

def translate_to_dxf(export_object: ExportObject) -> bytes:
    """
    Translate ExportObject to DXF format.
    
    AUTHORITY: DXF serialization
    NOT AUTHORITY: Manufacturing semantics
    
    This is a one-way translation from manufacturing meaning to serialization.
    """
    doc = dxf_compat.create_document(version='R2000')
    
    for entity in export_object.geometry.entities:
        # Translator decides HOW to serialize
        # ExportObject decides WHAT to serialize
        if entity.type == "line":
            dxf_compat.add_line(doc, entity.start, entity.end)
        elif entity.type == "arc":
            dxf_compat.add_arc(doc, entity.center, entity.radius, entity.angles)
    
    return doc.to_bytes()
```

### DON'T: Semantic Leakage

```python
# WRONG: Export Object has DXF semantics
class BadExportObject(BaseModel):
    dxf_layers: List[str]        # DXF leakage
    lwpolyline_flags: int        # DXF leakage
    acad_version: str            # DXF leakage

# WRONG: Geometry system has CAM semantics
class BadGeometry(BaseModel):
    feed_rate: float             # CAM leakage into geometry
    spindle_rpm: int             # CAM leakage into geometry
    toolpath_type: str           # CAM leakage into geometry

# WRONG: IBG has translator assumptions
class BadIBGOutput:
    def to_dxf_entities(self):   # Translator leakage into morphology
        return [DXFEntity(...)]  # IBG should return geometry, not DXF
```

## 5.2 Cross-Domain Integration Pattern

```python
# CORRECT: Use services/ layer for cross-domain orchestration
# services/api/app/services/cam_export_service.py

class CAMExportService:
    """
    Cross-domain orchestration service.
    
    Per ARCHITECTURE_INVARIANTS.md:
    - Cross-domain glue goes in services/
    - Domain modules remain self-contained
    """
    
    def __init__(
        self,
        geometry_engine: GeometryEngine,      # Domain module
        cam_generator: CAMGenerator,          # Domain module
        export_builder: ExportObjectBuilder,  # Domain module
        rmos_persistence: RMOSPersistence,    # Domain module
    ):
        self.geometry_engine = geometry_engine
        self.cam_generator = cam_generator
        self.export_builder = export_builder
        self.rmos_persistence = rmos_persistence
    
    def generate_export(self, request: ExportRequest) -> ExportResult:
        """Orchestrate across domains without domain contamination."""
        # Each domain does its job
        geometry = self.geometry_engine.compute(request.params)
        toolpath = self.cam_generator.generate(geometry, request.cam_params)
        export_object = self.export_builder.build(geometry, toolpath)
        
        # RMOS handles persistence
        run_id = self.rmos_persistence.persist(export_object)
        
        return ExportResult(export_object=export_object, run_id=run_id)
```

---

# 6. Manifest Management

## 6.1 Manifest Index

**Create:** `docs/governance/MANIFEST_INDEX.md`

```markdown
# Manifest Index

Central registry of all governance manifests in the repository.

| Manifest | Location | Domain | Purpose | Version |
|----------|----------|--------|---------|---------|
| governance_manifest.json | docs/governance/ | MRP | Protected systems | 1.0.0 |
| governed_export_manifest.json | docs/architecture/ | CAM | Export architecture | 1.0.0 |
| cam_preview_standard_manifest.json | docs/architecture/ | CAM | Preview standards | 1.0.0 |
| cam_machine_output_manifest.json | docs/architecture/ | CAM | Machine output | 1.0.0 |
| rosette_cam_route_manifest.json | docs/architecture/ | CAM | Rosette routes | 1.0.0 |
| regression_corpus/manifest.json | tests/ | MRP | Regression artifacts | 1.0.0 |

## Adding New Manifest

1. Create manifest file with standard schema header
2. Add entry to this index
3. Update check scripts if enforcement needed
```

## 6.2 Manifest Schema Template

```json
{
  "$schema": "manifest-schema-v1",
  "manifest_version": "1.0.0",
  "manifest_type": "governance | capability | routing | regression",
  "effective_date": "2026-05-12",
  "owner_system": "MRP | CAM | RMOS | VECTOR",
  "governance_tier": 1 | 2 | 3,
  
  "entries": [
    {
      "id": "unique_identifier",
      "status": "active | deprecated | planned",
      "...domain_specific_fields": "..."
    }
  ],
  
  "cross_references": [
    {
      "manifest": "path/to/related/manifest.json",
      "relationship": "depends_on | extends | replaces"
    }
  ]
}
```

---

# 7. Pre-Commit Hook Configuration

## 7.1 Pre-Commit Config

**Location:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      # Governance protected path check
      - id: governance-protected-paths
        name: Check governance protected paths
        entry: python scripts/check_protected_paths.py
        language: python
        pass_filenames: false
        always_run: true
        stages: [commit]
      
      # Sprint namespace check (warn-only)
      - id: sprint-namespace-check
        name: Check sprint namespace conventions
        entry: python scripts/check_sprint_namespace.py
        language: python
        pass_filenames: false
        always_run: true
        stages: [commit]
        verbose: true
      
      # Future: Capability registry validation
      - id: capability-registry-check
        name: Validate capability registry
        entry: python scripts/check_capability_registry.py
        language: python
        pass_filenames: false
        files: 'cam_operation_registry\.py$'
        stages: [commit]
```

## 7.2 Installing Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks in repository
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run governance-protected-paths

# Skip hooks (use sparingly, with approval)
# PowerShell:
$env:GOVERNANCE_APPROVED_CHANGE = "1"
git commit -m "Approved change" --no-verify  # Also skips other hooks

# Better: approve governance only, keep other hooks
$env:GOVERNANCE_APPROVED_CHANGE = "1"
git commit -m "Approved change"  # Governance passes, other hooks run
```

---

# 8. Testing Governance Compliance

## 8.1 Governance Test Suite

**Location:** `tests/test_governance.py`

```python
"""
Governance compliance test suite.

Tests verify:
1. Protected path enforcement
2. Capability registry integrity
3. Policy engine correctness
4. Manifest schema compliance
"""

import json
import pytest
from pathlib import Path


class TestProtectedPaths:
    """Test protected path enforcement."""
    
    def test_governance_manifest_exists(self):
        """Governance manifest must exist."""
        manifest_path = Path("docs/governance/governance_manifest.json")
        assert manifest_path.exists(), "Governance manifest missing"
    
    def test_governance_manifest_schema(self):
        """Governance manifest must have required fields."""
        with open("docs/governance/governance_manifest.json") as f:
            manifest = json.load(f)
        
        assert "manifest_version" in manifest
        assert "protected_systems" in manifest
        assert isinstance(manifest["protected_systems"], list)
        
        for system in manifest["protected_systems"]:
            assert "id" in system
            assert "protection_level" in system
            assert "paths" in system
            assert system["protection_level"] in ("LOCKED", "STABILIZED", "MONITORED")
    
    def test_protected_files_have_headers(self):
        """All protected files should have governance headers."""
        with open("docs/governance/governance_manifest.json") as f:
            manifest = json.load(f)
        
        for system in manifest["protected_systems"]:
            for path in system["paths"]:
                if path.endswith(".py") and Path(path).exists():
                    content = Path(path).read_text()
                    assert "# GOVERNANCE:" in content, \
                        f"Protected file {path} missing governance header"


class TestCapabilityRegistry:
    """Test capability registry integrity."""
    
    def test_all_operations_have_required_fields(self):
        """All registered operations must have required fields."""
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
        
        required_fields = [
            "operation",
            "lifecycle_supported",
            "exportability_class",
            "maturity",
        ]
        
        for op_name, capability in CAM_OPERATION_REGISTRY.items():
            for field in required_fields:
                assert hasattr(capability, field), \
                    f"Operation {op_name} missing required field {field}"
    
    def test_machine_ready_always_false(self):
        """Safety assertion: machine_ready must be false."""
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
        
        for op_name, capability in CAM_OPERATION_REGISTRY.items():
            assert capability.machine_ready is False, \
                f"Operation {op_name} has machine_ready=True (safety violation)"
            assert capability.machine_output_supported is False, \
                f"Operation {op_name} has machine_output_supported=True (safety violation)"
    
    def test_canonical_operations_have_routes(self):
        """Canonical operations must have preview routes."""
        from app.cam.cam_operation_registry import CAM_OPERATION_REGISTRY
        
        for op_name, capability in CAM_OPERATION_REGISTRY.items():
            if capability.maturity == "canonical":
                assert capability.preview_route is not None, \
                    f"Canonical operation {op_name} missing preview_route"


class TestPolicyEngine:
    """Test policy engine correctness."""
    
    def test_unknown_operation_returns_red(self):
        """Unknown operations should return RED gate."""
        from app.cam.cam_lifecycle_policy_engine import evaluate_lifecycle_policy
        
        result = evaluate_lifecycle_policy("nonexistent_operation")
        
        assert result.allowed is False
        assert result.lifecycle_gate == "red"
        assert len(result.blocking_issues) > 0
    
    def test_canonical_operation_returns_green(self):
        """Canonical operations should return GREEN gate."""
        from app.cam.cam_lifecycle_policy_engine import evaluate_lifecycle_policy
        
        result = evaluate_lifecycle_policy("nut_slot")
        
        assert result.allowed is True
        assert result.lifecycle_gate == "green"
    
    def test_preview_only_blocks_export(self):
        """preview_only operations should block export stages."""
        from app.cam.cam_lifecycle_policy_engine import get_stage_permissions
        
        permissions = get_stage_permissions("preview_only")
        
        assert permissions["preview"] is True
        assert permissions["export_object"] is False
        assert permissions["machine_validation"] is False
```

## 8.2 Running Governance Tests

```bash
# Run all governance tests
pytest tests/test_governance.py -v

# Run with coverage
pytest tests/test_governance.py --cov=scripts --cov=app.cam -v

# Run specific test class
pytest tests/test_governance.py::TestCapabilityRegistry -v

# Expected output for passing tests
# tests/test_governance.py::TestProtectedPaths::test_governance_manifest_exists PASSED
# tests/test_governance.py::TestCapabilityRegistry::test_machine_ready_always_false PASSED
# tests/test_governance.py::TestPolicyEngine::test_canonical_operation_returns_green PASSED
```

---

# 9. Common Implementation Patterns

## 9.1 Adding Governance Header to File

```python
"""
Module description here.
"""
# GOVERNANCE:
# SYSTEM: SYSTEM_ID_FROM_MANIFEST
# STATUS: PROTECTED_PRODUCTION_BASELINE
# DOC: docs/governance/SYSTEM_PROTECTION_RULES.md
# RULE: Do not alter production behavior without GOVERNANCE_APPROVED_CHANGE.

# Rest of the file...
```

## 9.2 Creating New Governed Operation

```python
# Step 1: Add to capability registry
# services/api/app/cam/cam_operation_registry.py

CAM_OPERATION_REGISTRY["new_operation"] = CAMOperationCapability(
    operation="new_operation",
    lifecycle_supported=True,
    export_object_supported=True,
    machine_validation_supported=True,
    translator_validation_supported=True,
    rmos_persistence_supported=True,
    preview_route="/api/cam/new-operation/preview",
    lifecycle_route="/api/cam/export/lifecycle/validate",
    exportability_class="governed_export",
    maturity="candidate",  # Start as candidate, promote to canonical after validation
    machine_ready=False,
    machine_output_supported=False,
)

# Step 2: Add preview dispatcher branch
# services/api/app/cam/export_lifecycle_orchestrator.py

def dispatch_preview(operation: str, payload: Dict) -> Tuple:
    if operation == "new_operation":
        request = NewOperationPreviewRequest(**payload)
        preview = generate_new_operation_preview(request)
        return preview, preview.gate.value, list(preview.errors), list(preview.warnings)
    # ... existing operations

# Step 3: Add export object dispatcher branch
def dispatch_export_object(operation: str, preview: Any) -> Optional[ExportObject]:
    if operation == "new_operation":
        return build_new_operation_export_object(preview)
    # ... existing operations

# Step 4: Create preview endpoint
# services/api/app/routers/cam/new_operation_router.py

@router.post("/preview", response_model=NewOperationPreviewResponse)
async def preview_new_operation(request: NewOperationPreviewRequest):
    # Implementation...
```

## 9.3 Promoting Operation Maturity

```python
# When operation is validated and stable:

# Step 1: Update maturity in registry
CAM_OPERATION_REGISTRY["new_operation"].maturity = "canonical"

# Step 2: Update notes
CAM_OPERATION_REGISTRY["new_operation"].notes = "Governed preview since CAM-7A. Promoted to canonical 2026-05-15."

# Step 3: Update governed_export_manifest.json
{
    "governed_preview_operations": [
        {
            "operation": "new_operation_preview",
            "status": "COMPLETE",
            "dev_order": "CAM-7A",
            "endpoint": "/api/cam/new-operation/preview"
        }
    ]
}

# Step 4: Run tests to verify
pytest tests/cam/test_new_operation*.py -v
```

---

# 10. Anti-Pattern Detection Scripts

## 10.1 Semantic Leakage Detector

**Create:** `scripts/check_semantic_leakage.py`

```python
#!/usr/bin/env python3
"""
Semantic Leakage Detection Script

Detects patterns that indicate improper coupling between architectural layers.

Anti-patterns detected:
1. DXF semantics in Export Object
2. CAM semantics in Geometry systems
3. Machine semantics in Morphology systems
4. Translator assumptions in upstream systems
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Define leakage patterns by layer
LEAKAGE_PATTERNS = {
    "export_object": {
        "forbidden_imports": [
            r"from.*ezdxf",
            r"import ezdxf",
            r"from.*dxf_compat",
        ],
        "forbidden_fields": [
            r"dxf_\w+",
            r"lwpolyline",
            r"acad_version",
            r"dxf_layer",
        ],
        "paths": ["app/cam/export_object*.py"],
    },
    "geometry": {
        "forbidden_imports": [
            r"from.*cam.*import",
            r"from.*toolpath.*import",
        ],
        "forbidden_fields": [
            r"feed_rate",
            r"spindle_rpm",
            r"toolpath_type",
            r"g_code",
        ],
        "paths": ["app/geometry/*.py", "app/instrument_geometry/*.py"],
    },
    "morphology": {
        "forbidden_imports": [
            r"from.*translator.*import",
            r"from.*postprocessor.*import",
        ],
        "forbidden_fields": [
            r"to_dxf",
            r"to_gcode",
            r"serialize_to_",
        ],
        "paths": ["app/instrument_geometry/body/ibg/*.py"],
    },
}


def check_file_for_leakage(file_path: Path, layer: str) -> List[Tuple[int, str, str]]:
    """Check a file for semantic leakage patterns."""
    violations = []
    patterns = LEAKAGE_PATTERNS.get(layer, {})
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return violations
    
    for line_num, line in enumerate(content.split("\n"), start=1):
        # Check forbidden imports
        for pattern in patterns.get("forbidden_imports", []):
            if re.search(pattern, line):
                violations.append((line_num, line.strip(), f"Forbidden import: {pattern}"))
        
        # Check forbidden fields
        for pattern in patterns.get("forbidden_fields", []):
            if re.search(pattern, line):
                violations.append((line_num, line.strip(), f"Forbidden field pattern: {pattern}"))
    
    return violations


def main() -> int:
    """Run leakage detection."""
    repo_root = Path(__file__).parent.parent
    all_violations = []
    
    for layer, config in LEAKAGE_PATTERNS.items():
        for glob_pattern in config.get("paths", []):
            for file_path in repo_root.glob(f"services/api/{glob_pattern}"):
                violations = check_file_for_leakage(file_path, layer)
                if violations:
                    all_violations.append((file_path, layer, violations))
    
    if all_violations:
        print("[WARN] Potential semantic leakage detected:")
        print()
        for file_path, layer, violations in all_violations:
            print(f"  File: {file_path}")
            print(f"  Layer: {layer}")
            for line_num, line_text, reason in violations:
                print(f"    Line {line_num}: {reason}")
                print(f"      {line_text[:80]}")
            print()
        return 1
    
    print("[OK] No semantic leakage detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## 10.2 False Canonization Detector

**Create:** `scripts/check_false_canonization.py`

```python
#!/usr/bin/env python3
"""
False Canonization Detection Script

Detects commits/PRs that claim canonization without proper verification.

Red flags:
1. Baseline approval without regression tests
2. "Definition of done" without behavioral verification
3. Metric match claims without semantic comparison
"""

import re
import subprocess
import sys
from pathlib import Path


# Patterns that suggest false canonization claims
FALSE_CANONIZATION_PATTERNS = [
    # Approval without verification
    r"approved.*baseline.*without.*test",
    r"canonical.*status.*claimed",
    r"promoted.*canonical.*no.*regression",
    
    # Metric-only claims
    r"dimensions.*match.*therefore.*correct",
    r"metrics.*identical.*approved",
    r"output.*same.*size",
    
    # Skipped verification
    r"skip.*verification",
    r"bypass.*regression",
    r"no.*time.*for.*test",
]


def check_commit_message(message: str) -> list:
    """Check commit message for false canonization patterns."""
    issues = []
    for pattern in FALSE_CANONIZATION_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            issues.append(f"Potential false canonization: matches '{pattern}'")
    return issues


def check_recent_commits(n: int = 10) -> int:
    """Check recent commit messages."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--format=%s%n%b"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        return 0
    
    issues_found = False
    for message in result.stdout.split("\n\n"):
        issues = check_commit_message(message)
        if issues:
            print(f"[WARN] Commit message may indicate false canonization:")
            print(f"  Message: {message[:100]}...")
            for issue in issues:
                print(f"    - {issue}")
            issues_found = True
    
    return 1 if issues_found else 0


if __name__ == "__main__":
    sys.exit(check_recent_commits())
```

---

# Quick Reference: Implementation Checklist

## Adding Protected System

- [ ] Add entry to `docs/governance/governance_manifest.json`
- [ ] Create governance doc `docs/governance/SYSTEM_PROTECTION_RULES.md`
- [ ] Add governance header to all protected files
- [ ] Add entry to `MANIFEST_INDEX.md`
- [ ] Run `pytest tests/test_governance.py -v`

## Adding CAM Operation

- [ ] Add to `cam_operation_registry.py` with maturity="candidate"
- [ ] Add preview dispatcher branch
- [ ] Add export object dispatcher branch
- [ ] Create preview endpoint
- [ ] Add tests
- [ ] Add to `governed_export_manifest.json`

## Promoting to Canonical

- [ ] Verify all tests pass
- [ ] Verify browser functionality
- [ ] Update maturity to "canonical"
- [ ] Update notes with promotion date
- [ ] Update manifest
- [ ] Document in handoff

## Creating Governance PR

- [ ] Run `pre-commit run --all-files`
- [ ] Verify `GOVERNANCE_APPROVED_CHANGE=1` if touching protected paths
- [ ] Include parity checklist if migration
- [ ] Reference sprint namespace (e.g., CAM-7A)
- [ ] Update relevant manifests

---

*Implementation Guide — 2026-05-12*
