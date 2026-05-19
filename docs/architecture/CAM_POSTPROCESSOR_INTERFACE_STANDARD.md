# CAM Postprocessor Interface Standard

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Machine translation boundary contract

---

## Purpose

This document defines the **Postprocessor Interface** — the contract between portable Export Objects and machine-specific output generation.

---

## Design Principles

1. **Export Object is input** — Postprocessors consume Export Objects, not raw toolpaths
2. **Machine Profile is required** — No postprocessor runs without explicit machine specification
3. **Output is machine-specific** — G-code syntax, conventions, and limits come from the machine profile
4. **Validation before translation** — All export and machine compatibility checks run before G-code generation
5. **Audit trail mandatory** — Every postprocessor run is logged with input hash and output hash

---

## Postprocessor Contract

### Interface Definition

```python
class PostprocessorInterface(Protocol):
    """
    Contract for all postprocessors.
    Implementations translate Export Objects to machine-specific output.
    """
    
    def validate_compatibility(
        self,
        export_object: ExportObject,
        machine_profile: MachineProfile
    ) -> ValidationResult:
        """
        Check whether the export object can be processed for this machine.
        Returns validation result with issues/warnings.
        Must pass before translate() is called.
        """
        ...
    
    def translate(
        self,
        export_object: ExportObject,
        machine_profile: MachineProfile,
        options: PostprocessorOptions
    ) -> MachineOutput:
        """
        Translate export object to machine-specific output.
        Requires validate_compatibility() to have passed.
        Returns machine output with G-code and metadata.
        """
        ...
    
    def get_supported_controllers(self) -> list[str]:
        """
        Return list of controller types this postprocessor supports.
        E.g., ["grbl", "grbl_1.1", "linuxcnc"]
        """
        ...
```

---

## Input: Export Object

The postprocessor receives a validated Export Object (see `CAM_EXPORT_OBJECT_MODEL.md`).

### Required Export Object Fields

| Field | Purpose |
|-------|---------|
| export_id | Traceability |
| geometry.coordinate_system | Coordinate interpretation |
| toolpaths.operations | Move sequences to translate |
| tooling | Tool requirements |
| validation.gate_status | Must be GREEN or YELLOW |

### Export Object Invariants

The postprocessor may assume:
- All coordinates are in mm
- Z-zero is top of stock
- All moves are in workpiece-local coordinates
- Tool geometry is specified

---

## Input: Machine Profile

The postprocessor receives a Machine Profile (see `CAM_MACHINE_PROFILE_STANDARD.md`).

### Required Machine Profile Fields

| Field | Purpose |
|-------|---------|
| controller_type | G-code dialect selection |
| work_envelope | Bounds checking |
| spindle | Speed limits |
| feed_rates | Feed limit enforcement |
| capabilities | Feature availability |

---

## Output: Machine Output

### Structure

```python
@dataclass
class MachineOutput:
    """
    Result of postprocessor translation.
    """
    # Identity
    output_id: str              # Unique identifier
    export_id: str              # Source export object
    machine_profile_id: str     # Target machine
    
    # Content
    gcode: str                  # Machine-specific G-code
    gcode_dialect: str          # E.g., "grbl_1.1"
    
    # Metadata
    created_at: datetime
    line_count: int
    estimated_time_s: float
    
    # Validation
    input_hash: str             # SHA256 of export object
    output_hash: str            # SHA256 of gcode
    
    # Audit
    postprocessor_id: str
    postprocessor_version: str
    warnings: list[str]
```

### G-code Requirements

| Requirement | Rationale |
|-------------|-----------|
| Header comment with export_id | Traceability |
| Units declaration (G21) | Explicit mm mode |
| Coordinate mode (G90/G91) | No assumption |
| Feed mode (G94) | Units per minute |
| No controller-specific assumptions | Profile drives syntax |

---

## Validation Phase

### validate_compatibility() Checks

```python
def validate_compatibility(
    self,
    export_object: ExportObject,
    machine_profile: MachineProfile
) -> ValidationResult:
    issues = []
    warnings = []
    
    # 1. Controller compatibility
    if machine_profile.controller_type not in self.get_supported_controllers():
        issues.append(f"Controller {machine_profile.controller_type} not supported")
    
    # 2. Work envelope check
    bounds = export_object.geometry.bounds
    envelope = machine_profile.work_envelope
    if bounds.x_max > envelope.x_mm:
        issues.append(f"X exceeds envelope: {bounds.x_max} > {envelope.x_mm}")
    if bounds.y_max > envelope.y_mm:
        issues.append(f"Y exceeds envelope: {bounds.y_max} > {envelope.y_mm}")
    if abs(bounds.z_min) > envelope.z_mm:
        issues.append(f"Z exceeds envelope: {bounds.z_min} > -{envelope.z_mm}")
    
    # 3. Spindle check
    # (Tool RPM requirements vs machine spindle limits)
    
    # 4. Tool compatibility
    tool = export_object.tooling
    if tool.geometry.shank_diameter_mm not in machine_profile.collet_sizes_mm:
        warnings.append(f"Shank {tool.geometry.shank_diameter_mm}mm may require adapter")
    
    # 5. Feed rate limits
    for op in export_object.toolpaths.operations:
        for move in op.moves:
            if hasattr(move, 'f') and move.f > machine_profile.feed_rates.max_xy_mm_min:
                issues.append(f"Feed {move.f} exceeds max {machine_profile.feed_rates.max_xy_mm_min}")
    
    return ValidationResult(
        passed=len(issues) == 0,
        issues=issues,
        warnings=warnings
    )
```

---

## Translation Phase

### translate() Process

```python
def translate(
    self,
    export_object: ExportObject,
    machine_profile: MachineProfile,
    options: PostprocessorOptions
) -> MachineOutput:
    
    # 1. Generate header
    lines = self._generate_header(export_object, machine_profile)
    
    # 2. Set machine state
    lines.extend(self._generate_preamble(machine_profile))
    
    # 3. Translate operations
    for op in export_object.toolpaths.operations:
        lines.extend(self._translate_operation(op, machine_profile))
    
    # 4. Generate footer
    lines.extend(self._generate_footer(machine_profile))
    
    # 5. Build output
    gcode = '\n'.join(lines)
    
    return MachineOutput(
        output_id=generate_output_id(),
        export_id=export_object.export_id,
        machine_profile_id=machine_profile.profile_id,
        gcode=gcode,
        gcode_dialect=machine_profile.controller_type,
        created_at=datetime.utcnow(),
        line_count=len(lines),
        estimated_time_s=self._estimate_time(export_object, machine_profile),
        input_hash=hash_export_object(export_object),
        output_hash=hashlib.sha256(gcode.encode()).hexdigest(),
        postprocessor_id=self.postprocessor_id,
        postprocessor_version=self.version,
        warnings=[]
    )
```

---

## Move Type Translation

### Neutral → GRBL Example

| Neutral Move | GRBL Output |
|--------------|-------------|
| `{"type": "rapid", "x": 10, "y": 20, "z": 5}` | `G0 X10.000 Y20.000 Z5.000` |
| `{"type": "plunge", "z": -2, "f": 100}` | `G1 Z-2.000 F100` |
| `{"type": "linear", "x": 10, "y": 25, "z": -2, "f": 500}` | `G1 X10.000 Y25.000 Z-2.000 F500` |
| `{"type": "retract", "z": 5}` | `G0 Z5.000` |
| `{"type": "arc_cw", "x": 15, "y": 20, "i": 5, "j": 0, "f": 400}` | `G2 X15.000 Y20.000 I5.000 J0.000 F400` |

---

## Postprocessor Options

```python
@dataclass
class PostprocessorOptions:
    """
    User-configurable postprocessor options.
    """
    # Formatting
    decimal_places: int = 3
    include_comments: bool = True
    include_line_numbers: bool = False
    line_number_increment: int = 10
    
    # Safety
    include_tool_change_pause: bool = True
    include_spindle_warmup: bool = False
    warmup_time_s: int = 5
    
    # Output
    output_format: str = "file"  # "file" | "stream"
    file_extension: str = ".nc"
```

---

## GRBL Postprocessor Reference

### Preamble

```gcode
; Export: EXP-NUT-20260510-abc123
; Machine: user_cnc_router
; Generated: 2026-05-10T12:00:00Z
;
G21 ; mm mode
G90 ; absolute positioning
G94 ; feed per minute
G17 ; XY plane
```

### Footer

```gcode
M5 ; spindle stop
G0 Z10.000 ; safe retract
G0 X0.000 Y0.000 ; return to origin
M30 ; program end
```

---

## Audit Requirements

Every postprocessor run must record:

| Field | Value |
|-------|-------|
| timestamp | ISO8601 |
| export_id | Source export object ID |
| export_hash | SHA256 of input |
| machine_profile_id | Target machine |
| output_hash | SHA256 of G-code |
| postprocessor_id | Which postprocessor |
| postprocessor_version | Version |
| validation_result | PASSED/FAILED with issues |
| user_id | Who initiated |

---

## Error Handling

### Validation Failures

If `validate_compatibility()` fails:
- Do NOT proceed to translation
- Return ValidationResult with all issues
- Log validation failure

### Translation Failures

If `translate()` fails:
- Do NOT produce partial output
- Raise PostprocessorError with context
- Log translation failure

---

## Implementation Status

| Postprocessor | Status | Controllers |
|---------------|--------|-------------|
| GRBLPostprocessor | Interface defined | grbl, grbl_1.1 |
| LinuxCNCPostprocessor | Interface defined | linuxcnc |
| FANUCPostprocessor | Interface defined | fanuc |

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Architectural context |
| `CAM_EXPORT_OBJECT_MODEL.md` | Input schema |
| `CAM_MACHINE_PROFILE_STANDARD.md` | Machine abstraction |
| `CAM_TOOL_LIBRARY_STANDARD.md` | Tooling abstraction |

---

*Interface defined: 2026-05-10*
