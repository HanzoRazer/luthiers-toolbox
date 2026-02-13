# Post Processors

Customize G-code output for your specific CNC controller.

---

## What is a Post Processor?

A post processor translates generic toolpath data into the specific G-code dialect your machine controller expects. Different controllers have different:

- G-code syntax variations
- Modal group handling
- Canned cycle support
- Safety header/footer requirements
- Comment formatting

---

## Built-in Post Processors

### Grbl (`grbl`)

Standard post for Grbl 1.1+ controllers.

**Features:**

- No canned cycles (expanded to explicit moves)
- Decimal format configurable
- No tool change support
- Metric or imperial output

**Example Output:**

```gcode
G21 ; mm mode
G90 ; absolute
G17 ; XY plane
M3 S18000
G0 Z10.000
G0 X0.000 Y0.000
G1 Z-2.000 F500
G1 X50.000 F2000
...
M5
M30
```

---

### Mach3/4 (`mach`)

Post for Mach3 and Mach4 controllers.

**Features:**

- Canned drilling cycles (G81, G83)
- Tool change with M6
- Subprogram support
- Decimal precision options

**Example Output:**

```gcode
(Luthier's ToolBox)
G20 ; inches
G90 G40 G49 G80
T1 M6
M3 S18000
G43 H1
G0 Z1.000
G0 X0.000 Y0.000
G1 Z-0.100 F20
...
M5
M30
```

---

### LinuxCNC (`linuxcnc`)

Post for LinuxCNC (EMC2) controllers.

**Features:**

- Full canned cycle support
- Tool table integration
- Named parameters
- O-word subroutines

---

### Carbide Motion (`carbide`)

Post for Carbide 3D's Carbide Motion software.

**Features:**

- BitSetter support
- Carbide-specific safety headers
- No M6 tool changes (manual)

---

### Generic (`generic`)

Minimal, widely compatible post.

**Features:**

- Only essential G-codes
- No assumptions about controller
- Manual editing may be needed

---

## Post Processor Settings

### Units

| Setting | Options |
|---------|---------|
| Output Units | Metric (G21) / Imperial (G20) |
| Decimal Places | 2-6 |

### Safety

| Setting | Description |
|---------|-------------|
| Safe Z Height | Height for rapids |
| Clearance Plane | Height above stock |
| Program Start | G-codes at program start |
| Program End | G-codes at program end |

### Spindle

| Setting | Description |
|---------|-------------|
| Spindle On Code | M3 (CW) / M4 (CCW) |
| Spindle Warmup | Dwell after spindle start |
| Spindle Off Code | M5 |

### Comments

| Setting | Options |
|---------|---------|
| Comment Style | Parentheses / Semicolon / Both |
| Include Tool Info | Yes / No |
| Include Time Estimate | Yes / No |

---

## Customizing Output

### Header Template

Add custom G-codes at program start:

```gcode
; Custom header
G90 G94 G17 G21
G28 G91 Z0
G90
```

### Footer Template

Add custom G-codes at program end:

```gcode
; Custom footer
M5
G28 G91 Z0
G28 X0 Y0
M30
```

### Line Numbers

| Option | Description |
|--------|-------------|
| Disabled | No line numbers |
| Every Line | N10, N20, N30... |
| Blocks Only | Only on key blocks |
| Increment | Step between numbers (10) |

---

## Creating Custom Posts

For unsupported controllers, create a custom post processor:

### 1. Copy Base Post

```bash
cp services/api/app/cam/posts/grbl.py services/api/app/cam/posts/mycontroller.py
```

### 2. Modify Output Methods

```python
class MyControllerPost(BasePost):
    def format_line(self, command, params):
        # Custom formatting
        return f"N{self.line_num} {command} {params}"

    def start_spindle(self, rpm, direction="cw"):
        # Custom spindle start
        return f"M3 S{rpm}\nG4 P2 ; warmup"
```

### 3. Register Post

```python
# In posts/__init__.py
from .mycontroller import MyControllerPost

POSTS = {
    ...
    "mycontroller": MyControllerPost,
}
```

---

## G-code Reference

### Motion Commands

| Code | Description |
|------|-------------|
| G0 | Rapid move |
| G1 | Linear feed move |
| G2 | Clockwise arc |
| G3 | Counter-clockwise arc |

### Plane Selection

| Code | Plane |
|------|-------|
| G17 | XY plane |
| G18 | XZ plane |
| G19 | YZ plane |

### Distance Mode

| Code | Mode |
|------|------|
| G90 | Absolute positioning |
| G91 | Incremental positioning |

### Canned Cycles

| Code | Operation |
|------|-----------|
| G80 | Cancel canned cycle |
| G81 | Simple drilling |
| G82 | Drill with dwell |
| G83 | Peck drilling |
| G84 | Tapping |

### Tool Compensation

| Code | Description |
|------|-------------|
| G40 | Cancel cutter compensation |
| G41 | Cutter compensation left |
| G42 | Cutter compensation right |
| G43 | Tool length offset |
| G49 | Cancel tool length offset |

---

## Troubleshooting

### "Unknown G-code" errors

- Your controller may not support all G-codes
- Use a simpler post processor
- Check controller documentation

### Arc errors

- Some controllers don't support arcs
- Enable "Linearize Arcs" option
- Reduce arc tolerance for smoother output

### Tool change issues

- Verify M6 compatibility
- Check tool table setup
- Use manual tool change mode

---

## Related

- [Machine Profiles](machine-profiles.md) - Configure machine parameters
- [G-code Preview](gcode-preview.md) - Visualize G-code
- [Toolpath Generation](../features/toolpaths.md) - Creating toolpaths
