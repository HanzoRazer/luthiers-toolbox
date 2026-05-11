# CAM Machine Profile Standard

**Date:** 2026-05-10  
**Status:** ARCHITECTURAL DEFINITION  
**Dev Order:** 6A  
**Scope:** Machine abstraction model for postprocessors

---

## Purpose

This document defines the **Machine Profile** — the abstraction layer that separates postprocessor logic from machine-specific configuration.

---

## Design Principles

1. **Machine-agnostic postprocessors** — Postprocessor code should not contain machine-specific constants
2. **Profile-driven behavior** — All machine-specific behavior comes from the profile
3. **Declarative specification** — Profiles declare capabilities, not procedures
4. **Validation-friendly** — Profile structure supports pre-translation validation
5. **User-manageable** — Profiles are JSON files users can edit

---

## Machine Profile Schema

### Top-Level Structure

```json
{
  "schema_version": "1.0.0",
  "profile_id": "user_cnc_router",
  "profile_name": "User's CNC Router",
  
  "controller": { ... },
  "work_envelope": { ... },
  "spindle": { ... },
  "feed_rates": { ... },
  "tool_change": { ... },
  "capabilities": { ... },
  "safety": { ... },
  "metadata": { ... }
}
```

---

### Controller Block

```json
{
  "controller": {
    "type": "grbl",
    "version": "1.1h",
    "dialect": "grbl_1.1",
    "firmware_notes": "Standard GRBL on Arduino Uno"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | Controller family (grbl, linuxcnc, fanuc, etc.) |
| version | string | No | Specific firmware version |
| dialect | string | Yes | G-code dialect identifier |
| firmware_notes | string | No | User notes |

**Supported Controller Types:**

| Type | Dialect | Description |
|------|---------|-------------|
| grbl | grbl_1.1 | GRBL 1.1 on Arduino/ESP32 |
| grbl | grbl_0.9 | Legacy GRBL |
| linuxcnc | linuxcnc | LinuxCNC/Mach3 compatible |
| fanuc | fanuc | FANUC-style industrial |
| haas | haas | Haas controllers |
| tinyg | tinyg | TinyG/g2core |

---

### Work Envelope Block

```json
{
  "work_envelope": {
    "x_mm": 300.0,
    "y_mm": 400.0,
    "z_mm": 80.0,
    "a_deg": null,
    "coordinate_system": "right_handed",
    "home_position": {
      "x": 0.0,
      "y": 0.0,
      "z": 0.0
    },
    "soft_limits_enabled": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| x_mm | number | Yes | X axis travel |
| y_mm | number | Yes | Y axis travel |
| z_mm | number | Yes | Z axis travel (positive = above work) |
| a_deg | number | No | A axis rotation (if present) |
| coordinate_system | string | Yes | "right_handed" or "left_handed" |
| home_position | object | No | Machine home in work coordinates |
| soft_limits_enabled | boolean | No | Whether controller enforces limits |

---

### Spindle Block

```json
{
  "spindle": {
    "type": "router",
    "control": "pwm",
    "min_rpm": 8000,
    "max_rpm": 24000,
    "speed_control": true,
    "direction_control": false,
    "default_rpm": 18000,
    "collet_sizes_mm": [3.175, 6.0, 6.35]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | "router", "spindle_motor", "vfd_spindle" |
| control | string | Yes | "manual", "pwm", "rs485", "analog" |
| min_rpm | number | Yes | Minimum usable RPM |
| max_rpm | number | Yes | Maximum RPM |
| speed_control | boolean | Yes | Can G-code control speed? |
| direction_control | boolean | Yes | Can G-code reverse direction? |
| default_rpm | number | No | Default if not specified |
| collet_sizes_mm | array | No | Available collet sizes |

---

### Feed Rates Block

```json
{
  "feed_rates": {
    "max_xy_mm_min": 3000,
    "max_z_mm_min": 1000,
    "max_rapid_mm_min": 5000,
    "default_xy_mm_min": 1000,
    "default_z_mm_min": 300,
    "default_plunge_mm_min": 100
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| max_xy_mm_min | number | Yes | Maximum XY feed rate |
| max_z_mm_min | number | Yes | Maximum Z feed rate |
| max_rapid_mm_min | number | No | Maximum rapid traverse |
| default_xy_mm_min | number | No | Default cutting feed |
| default_z_mm_min | number | No | Default Z feed |
| default_plunge_mm_min | number | No | Default plunge feed |

---

### Tool Change Block

```json
{
  "tool_change": {
    "type": "manual",
    "supports_m6": false,
    "tool_length_probe": false,
    "tool_change_position": {
      "x": 0.0,
      "y": 0.0,
      "z": 50.0
    },
    "pause_for_tool_change": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | Yes | "manual", "atc", "carousel" |
| supports_m6 | boolean | Yes | Does controller handle M6? |
| tool_length_probe | boolean | No | Has tool length probe? |
| tool_change_position | object | No | Position for tool change |
| pause_for_tool_change | boolean | No | Pause program for manual change? |

---

### Capabilities Block

```json
{
  "capabilities": {
    "arcs": true,
    "arc_planes": ["XY"],
    "helical_arcs": false,
    "canned_cycles": false,
    "probing": false,
    "work_offsets": ["G54"],
    "tool_compensation": false,
    "coolant_control": false,
    "spindle_orientation": false
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| arcs | boolean | Yes | G2/G3 support |
| arc_planes | array | No | Supported arc planes (XY, XZ, YZ) |
| helical_arcs | boolean | No | Helical interpolation |
| canned_cycles | boolean | No | G81, G83, etc. |
| probing | boolean | No | G38.x probing cycles |
| work_offsets | array | No | Supported work offsets |
| tool_compensation | boolean | No | G41/G42 compensation |
| coolant_control | boolean | No | M7/M8/M9 support |

---

### Safety Block

```json
{
  "safety": {
    "safe_z_mm": 10.0,
    "retract_z_mm": 5.0,
    "max_plunge_depth_mm": 5.0,
    "require_spindle_on_before_move": true,
    "require_homing_before_run": true,
    "emergency_stop_behavior": "power_off"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| safe_z_mm | number | Yes | Safe Z for rapid moves |
| retract_z_mm | number | Yes | Z clearance above work |
| max_plunge_depth_mm | number | No | Maximum single plunge |
| require_spindle_on_before_move | boolean | No | Safety check |
| require_homing_before_run | boolean | No | Safety check |

---

### Metadata Block

```json
{
  "metadata": {
    "created_at": "2026-05-10T12:00:00Z",
    "created_by": "user@example.com",
    "machine_make": "Generic",
    "machine_model": "3018 Pro",
    "notes": "Entry-level CNC router for small parts"
  }
}
```

---

## Example: Complete GRBL Profile

```json
{
  "schema_version": "1.0.0",
  "profile_id": "cnc_3018_grbl",
  "profile_name": "CNC 3018 Pro with GRBL",
  
  "controller": {
    "type": "grbl",
    "version": "1.1h",
    "dialect": "grbl_1.1"
  },
  
  "work_envelope": {
    "x_mm": 300.0,
    "y_mm": 180.0,
    "z_mm": 45.0,
    "coordinate_system": "right_handed",
    "soft_limits_enabled": true
  },
  
  "spindle": {
    "type": "router",
    "control": "pwm",
    "min_rpm": 1000,
    "max_rpm": 10000,
    "speed_control": true,
    "direction_control": false,
    "collet_sizes_mm": [3.175]
  },
  
  "feed_rates": {
    "max_xy_mm_min": 2000,
    "max_z_mm_min": 500,
    "default_xy_mm_min": 500,
    "default_plunge_mm_min": 50
  },
  
  "tool_change": {
    "type": "manual",
    "supports_m6": false,
    "pause_for_tool_change": true
  },
  
  "capabilities": {
    "arcs": true,
    "arc_planes": ["XY"],
    "helical_arcs": false,
    "canned_cycles": false,
    "probing": false,
    "work_offsets": ["G54"]
  },
  
  "safety": {
    "safe_z_mm": 10.0,
    "retract_z_mm": 3.0,
    "max_plunge_depth_mm": 3.0
  },
  
  "metadata": {
    "created_at": "2026-05-10T12:00:00Z",
    "machine_make": "Generic",
    "machine_model": "3018 Pro"
  }
}
```

---

## Example: LinuxCNC Profile

```json
{
  "schema_version": "1.0.0",
  "profile_id": "linuxcnc_router",
  "profile_name": "Shop Router with LinuxCNC",
  
  "controller": {
    "type": "linuxcnc",
    "version": "2.8",
    "dialect": "linuxcnc"
  },
  
  "work_envelope": {
    "x_mm": 1200.0,
    "y_mm": 600.0,
    "z_mm": 150.0,
    "coordinate_system": "right_handed"
  },
  
  "spindle": {
    "type": "vfd_spindle",
    "control": "rs485",
    "min_rpm": 6000,
    "max_rpm": 24000,
    "speed_control": true,
    "direction_control": true,
    "collet_sizes_mm": [6.0, 6.35, 8.0, 12.0, 12.7]
  },
  
  "feed_rates": {
    "max_xy_mm_min": 6000,
    "max_z_mm_min": 2000,
    "max_rapid_mm_min": 10000
  },
  
  "tool_change": {
    "type": "manual",
    "supports_m6": true,
    "tool_length_probe": true,
    "pause_for_tool_change": true
  },
  
  "capabilities": {
    "arcs": true,
    "arc_planes": ["XY", "XZ", "YZ"],
    "helical_arcs": true,
    "canned_cycles": true,
    "probing": true,
    "work_offsets": ["G54", "G55", "G56", "G57", "G58", "G59"],
    "tool_compensation": true
  },
  
  "safety": {
    "safe_z_mm": 25.0,
    "retract_z_mm": 10.0
  }
}
```

---

## Profile Validation

### Required Fields

Every profile must have:
- schema_version
- profile_id
- controller.type
- controller.dialect
- work_envelope.x_mm, y_mm, z_mm
- spindle.type, min_rpm, max_rpm
- feed_rates.max_xy_mm_min, max_z_mm_min
- safety.safe_z_mm, retract_z_mm

### Validation Rules

| Rule | Condition |
|------|-----------|
| Envelope positive | All dimensions > 0 |
| Spindle range valid | min_rpm < max_rpm |
| Feed rates positive | All rates > 0 |
| Safe Z above retract | safe_z_mm >= retract_z_mm |
| Dialect known | dialect in supported list |

---

## Profile Registry

Profiles are stored in `data/machine_profiles/` with naming convention:

```
{profile_id}.json
```

Example:
```
data/machine_profiles/
  cnc_3018_grbl.json
  linuxcnc_router.json
  shapeoko_3.json
```

---

## Cross-Reference

| Document | Purpose |
|----------|---------|
| `CAM_GOVERNED_EXPORT_ARCHITECTURE.md` | Architectural context |
| `CAM_POSTPROCESSOR_INTERFACE_STANDARD.md` | Consumer interface |
| `CAM_TOOL_LIBRARY_STANDARD.md` | Tooling abstraction |

---

*Standard defined: 2026-05-10*
