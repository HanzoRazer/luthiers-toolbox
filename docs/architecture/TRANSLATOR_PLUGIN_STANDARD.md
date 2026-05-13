# Translator Plugin Standard

**CAM Dev Order 7A — Plugin Interface Contracts**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the future interface standard for translator and postprocessor plugins. It specifies how plugins will declare capabilities, validate inputs, and produce artifacts without violating governance boundaries.

**This is architecture planning, not implementation.**

---

## Plugin Categories

### Translators

Convert Export Objects to format-specific artifacts.

| Category | Input | Output | Examples |
|----------|-------|--------|----------|
| Geometry Translator | Export Object | Geometry artifact | DXF, SVG, STEP |
| Toolpath Translator | Export Object | Neutral toolpath | JSON toolpath, G-code neutral |

### Postprocessors

Convert neutral toolpaths to controller-specific machine output.

| Category | Input | Output | Examples |
|----------|-------|--------|----------|
| Controller Postprocessor | Neutral toolpath | Machine G-code | GRBL, FANUC, Mach3 |
| Format Postprocessor | Neutral toolpath | Vendor format | ShopBot, Carbide3D |

---

## Translator Plugin Interface

### Future Interface Definition

```python
from typing import Protocol, List, Dict, Any, Optional
from enum import Enum

class TranslatorStatus(Enum):
    READY = "ready"
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_BLOCKED = "execution_blocked"
    ERROR = "error"

class TranslatorCompatibilityReport:
    """Result of translator compatibility validation."""
    compatible: bool
    gate: str  # "green", "yellow", "red"
    blocking_issues: List[str]
    warnings: List[str]
    supported_features: Dict[str, bool]
    unsupported_features: List[str]

class TranslationArtifact:
    """Output of translator execution."""
    artifact_id: str
    artifact_type: str  # "dxf", "svg", "neutral_toolpath", etc.
    content_hash: str  # SHA256 of artifact content
    content_bytes: int
    provenance: Dict[str, Any]  # Links to Export Object, approval chain
    
class TranslatorPlugin(Protocol):
    """
    Standard interface for translator plugins.
    
    IMPORTANT: This is a FUTURE interface definition.
    No translator plugins should be implemented until
    the execution architecture is approved.
    """
    
    # --- Plugin Identity ---
    
    @property
    def translator_id(self) -> str:
        """Unique translator identifier."""
        ...
    
    @property
    def translator_name(self) -> str:
        """Human-readable translator name."""
        ...
    
    @property
    def translator_version(self) -> str:
        """Semantic version string."""
        ...
    
    # --- Capability Declarations ---
    
    @property
    def supported_operations(self) -> List[str]:
        """CAM operations this translator can handle."""
        ...
    
    @property
    def supported_geometry_types(self) -> List[str]:
        """Geometry types this translator can serialize."""
        ...
    
    @property
    def supported_units(self) -> List[str]:
        """Unit systems supported (mm, inch)."""
        ...
    
    @property
    def output_format(self) -> str:
        """Output format identifier (dxf, svg, etc.)."""
        ...
    
    @property
    def output_format_version(self) -> Optional[str]:
        """Output format version (e.g., R2000 for DXF)."""
        ...
    
    # --- Validation Methods ---
    
    def validate_export_object(
        self,
        export_object: Any,
    ) -> TranslatorCompatibilityReport:
        """
        Validate Export Object compatibility with this translator.
        
        This is the validation gate. It runs BEFORE any approval
        boundary and BEFORE any execution.
        
        Must NOT:
        - Modify any state
        - Generate artifacts
        - Access external resources
        - Bypass governance validation
        
        Must:
        - Return deterministic result for same input
        - Report all compatibility issues
        - Be side-effect free
        """
        ...
    
    # --- Execution Methods (Future Only) ---
    
    def generate_translation_artifact(
        self,
        export_object: Any,
        execution_context: Any,  # Authorization, provenance
    ) -> TranslationArtifact:
        """
        Generate translation artifact from Export Object.
        
        FUTURE ONLY — Not to be implemented until execution
        architecture is approved.
        
        Preconditions:
        - Export Object validated (green gate)
        - Translator compatibility validated
        - Human approval granted
        - Execution authorization present
        
        Must NOT:
        - Modify governance state
        - Bypass validation
        - Self-authorize
        - Access resources outside sandbox
        
        Must:
        - Produce deterministic output for same input
        - Include full provenance metadata
        - Record to execution audit
        """
        ...
```

---

## Postprocessor Plugin Interface

### Future Interface Definition

```python
class PostprocessorCompatibilityReport:
    """Result of postprocessor compatibility validation."""
    compatible: bool
    gate: str
    controller_dialect: str
    blocking_issues: List[str]
    warnings: List[str]
    machine_requirements: Dict[str, Any]

class MachineOutputArtifact:
    """Output of postprocessor execution."""
    artifact_id: str
    controller_type: str  # "grbl", "fanuc", "shopbot", etc.
    content_hash: str
    content_bytes: int
    provenance: Dict[str, Any]
    machine_requirements: Dict[str, Any]

class PostprocessorPlugin(Protocol):
    """
    Standard interface for postprocessor plugins.
    
    IMPORTANT: This is a FUTURE interface definition.
    """
    
    # --- Plugin Identity ---
    
    @property
    def postprocessor_id(self) -> str:
        ...
    
    @property
    def postprocessor_name(self) -> str:
        ...
    
    @property
    def postprocessor_version(self) -> str:
        ...
    
    # --- Capability Declarations ---
    
    @property
    def controller_type(self) -> str:
        """Target controller type."""
        ...
    
    @property
    def supported_toolpath_types(self) -> List[str]:
        """Toolpath types this postprocessor can handle."""
        ...
    
    @property
    def supported_operations(self) -> List[str]:
        """CAM operations supported."""
        ...
    
    @property
    def output_dialect(self) -> str:
        """G-code dialect or format identifier."""
        ...
    
    # --- Validation Methods ---
    
    def validate_toolpath(
        self,
        toolpath: Any,
        machine_profile: Any,
    ) -> PostprocessorCompatibilityReport:
        """
        Validate toolpath compatibility with this postprocessor.
        """
        ...
    
    # --- Execution Methods (Future Only) ---
    
    def generate_machine_output(
        self,
        toolpath: Any,
        machine_profile: Any,
        execution_context: Any,
    ) -> MachineOutputArtifact:
        """
        Generate machine-specific output from toolpath.
        
        FUTURE ONLY — Not to be implemented until execution
        architecture is approved.
        """
        ...
```

---

## Capability Declaration Requirements

### Required Declarations

Every plugin must declare:

| Declaration | Purpose |
|-------------|---------|
| `translator_id` / `postprocessor_id` | Unique identifier |
| `supported_operations` | Which CAM operations can be processed |
| `supported_geometry_types` | Which geometry types can be serialized |
| `supported_units` | Unit systems (mm, inch) |
| `output_format` / `output_dialect` | Output format identifier |

### Optional Declarations

| Declaration | Purpose |
|-------------|---------|
| `output_format_version` | Format version (e.g., DXF R2000) |
| `machine_requirements` | Machine capability requirements |
| `resource_limits` | Memory, time limits |
| `determinism_guarantee` | Whether output is deterministic |

---

## Validation Contract

### Validation Must Be Pure

```python
# Validation is a PURE function
# Same input → same output
# No side effects
# No state modification

def validate_export_object(export_object) -> CompatibilityReport:
    # READ ONLY operations
    # NO external calls
    # NO file I/O
    # NO network access
    # NO governance modification
    pass
```

### Validation vs Execution Separation

```
┌─────────────────────────────────────────────────────────┐
│                  VALIDATION PHASE                        │
│                                                          │
│  validate_export_object() → CompatibilityReport         │
│                                                          │
│  - Pure function                                         │
│  - No side effects                                       │
│  - No artifacts generated                                │
│  - No approval required                                  │
│  - Runs during lifecycle orchestration                   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              [HUMAN APPROVAL GATE]
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  EXECUTION PHASE                         │
│                                                          │
│  generate_translation_artifact() → TranslationArtifact  │
│                                                          │
│  - May have side effects                                 │
│  - Produces artifacts                                    │
│  - Requires approval                                     │
│  - Runs in isolated execution context                    │
│  - Records to execution audit                            │
└─────────────────────────────────────────────────────────┘
```

---

## Plugin Registration Model

### Future Registry Structure

```python
# PLANNING ONLY — Do not implement

TRANSLATOR_PLUGIN_REGISTRY = {
    "dxf_r2000": {
        "plugin_type": "translator",
        "translator_id": "dxf_r2000",
        "output_format": "dxf",
        "output_format_version": "R2000",
        "supported_operations": ["nut_slot", "drilling", "pocket"],
        "supported_geometry_types": ["line", "arc", "circle", "polyline"],
        "supported_units": ["mm", "inch"],
        "execution_allowed": False,  # Until approved
        "validation_only": True,     # Current state
    },
    "grbl_postprocessor": {
        "plugin_type": "postprocessor",
        "postprocessor_id": "grbl_v1",
        "controller_type": "grbl",
        "output_dialect": "grbl_1.1",
        "supported_operations": ["nut_slot", "drilling"],
        "execution_allowed": False,
        "validation_only": True,
    },
}
```

### Registry vs Capability Registry

| Registry | Purpose | Scope |
|----------|---------|-------|
| CAM_OPERATION_REGISTRY | Operation capabilities | Governance |
| TRANSLATOR_PLUGIN_REGISTRY | Translator capabilities | Execution |

These are separate registries with separate authority.

---

## Plugin Isolation Requirements

### Sandboxing

Future plugins must:
- Execute in isolated process/sandbox
- Have no direct filesystem access
- Have no network access
- Have bounded memory usage
- Have bounded execution time
- Have no access to governance state

### Determinism

Plugins should produce deterministic output:
- Same Export Object → same artifact content
- Same toolpath → same machine output
- Randomness explicitly prohibited

---

## Existing Validation Layer Integration

The current validation modules form the validation boundary:

| Current Module | Future Plugin Role |
|----------------|-------------------|
| `DXFTranslatorProfile` | Becomes input to `DXFTranslator.validate_export_object()` |
| `evaluate_dxf_translator_compatibility()` | Calls plugin validation |
| `MachineProfileValidationOnly` | Becomes input to postprocessor validation |
| `evaluate_postprocessor_compatibility()` | Calls plugin validation |

The existing validation infrastructure remains. Plugins extend it, not replace it.

---

## Plugin Lifecycle States

```
REGISTERED
    │
    ▼
VALIDATION_ENABLED (current state for all)
    │
    ▼
EXECUTION_APPROVED (future, requires human approval)
    │
    ▼
ACTIVE
```

No plugin may transition to EXECUTION_APPROVED without explicit human approval.

---

## Related Documents

- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `EXECUTION_CAPABILITY_REGISTRY_MODEL.md` — Capability declarations
- `TRANSLATOR_SECURITY_MODEL.md` — Isolation requirements

---

*Translator Plugin Standard — CAM 7A — 2026-05-13*
