# CAM & CNC Overview

Computer-Aided Manufacturing tools for CNC routing, milling, and cutting.

---

## What is CAM?

CAM (Computer-Aided Manufacturing) is the process of converting CAD designs into machine instructions (G-code) that CNC machines can execute.

```
CAD Design → CAM Processing → G-code → CNC Machine → Finished Part
```

---

## Workflow

### 1. Import Geometry

- Upload DXF files
- Validate geometry
- Fix issues (open contours, intersections)

### 2. Configure Stock

- Set material dimensions
- Define work origin
- Specify material type

### 3. Select Operations

| Operation | Purpose |
|-----------|---------|
| Pocket | Clear enclosed areas |
| Contour | Cut along outlines |
| Drill | Point holes |
| V-Carve | Engrave with V-bits |

### 4. Configure Tools

- Select from tool library
- Set feeds and speeds
- Configure depth parameters

### 5. Generate Toolpath

- Preview path visualization
- Verify clearances
- Check estimated time

### 6. Export G-code

- Select post processor
- Configure output options
- Download or send to machine

---

## Safety System

Luthier's ToolBox includes RMOS (Run Management & Operations System) for manufacturing safety:

### Feasibility Analysis

Every toolpath is evaluated before export:

| Level | Meaning | Action |
|-------|---------|--------|
| GREEN | Safe to run | Proceed |
| YELLOW | Review warnings | Operator decision |
| RED | Blocked | Cannot export without override |

### Safety Rules

Common checks include:

- Tool diameter vs pocket width
- Stepdown vs material hardness
- Feed rate vs tool/material limits
- Spindle speed sanity checks
- Collision detection

[Learn more about RMOS →](safety-rmos.md)

---

## Supported Machines

Luthier's ToolBox generates G-code for various CNC controllers:

### Hobby/Prosumer

| Machine | Controller | Post Processor |
|---------|------------|----------------|
| Shapeoko | Grbl | `grbl` |
| X-Carve | Grbl | `grbl` |
| Onefinity | buildbotics | `grbl` |
| MPCNC | Marlin | `marlin` |
| LongMill | Grbl | `grbl` |

### Professional

| Machine | Controller | Post Processor |
|---------|------------|----------------|
| Shopbot | Shopbot | `shopbot` |
| Laguna | Fanuc | `fanuc` |
| Thermwood | Custom | `thermwood` |

### Universal

| Controller | Post Processor |
|------------|----------------|
| Mach3/4 | `mach` |
| LinuxCNC | `linuxcnc` |
| Generic | `generic` |

[Configure your machine →](machine-profiles.md)

---

## Key Concepts

### Work Coordinate System (WCS)

The coordinate system used during machining:

- **G54-G59**: Standard work offsets
- **Origin**: Where X=0, Y=0, Z=0
- **Safe Z**: Height for rapid moves

### Feeds and Speeds

Critical parameters for successful cutting:

- **Feed Rate**: How fast the tool moves (mm/min)
- **Spindle Speed**: Tool rotation (RPM)
- **Chip Load**: Material removed per tooth per revolution

### Tool Compensation

Adjustments for tool geometry:

- **Cutter Compensation (G41/G42)**: Offset for tool radius
- **Tool Length Offset (G43)**: Offset for tool length
- **Wear Compensation**: Adjust for tool wear

### Depth Parameters

How deep to cut:

- **Stepdown**: Depth per pass
- **Final Depth**: Total depth
- **Stock to Leave**: Material for finishing pass

---

## Best Practices

### Before Cutting

1. Verify all dimensions in preview
2. Check tool compatibility with material
3. Confirm work origin location
4. Secure workpiece properly
5. Test spindle direction

### During Cutting

1. Monitor first cuts closely
2. Listen for unusual sounds
3. Watch for chip evacuation
4. Be ready to emergency stop
5. Don't leave machine unattended

### After Cutting

1. Verify dimensions with calipers
2. Inspect surface quality
3. Log successful parameters
4. Clean chips and dust
5. Maintain tools

---

## Quick Links

- [Machine Profiles](machine-profiles.md) - Configure your CNC
- [Post Processors](post-processors.md) - G-code customization
- [G-code Preview](gcode-preview.md) - Visualize toolpaths
- [Safety & RMOS](safety-rmos.md) - Manufacturing safety system
