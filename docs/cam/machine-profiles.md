# Machine Profiles

Configure your CNC machine parameters for accurate toolpath generation.

---

## Creating a Profile

### Via UI

1. Navigate to **Settings > Machine Profiles**
2. Click **Add Profile**
3. Fill in machine parameters
4. Click **Save**

### Via API

```python
import requests

response = requests.post(
    "http://localhost:8000/api/machines/profiles",
    json={
        "name": "Shapeoko 4 XXL",
        "work_area": {
            "x": 838,
            "y": 838,
            "z": 95
        },
        "limits": {
            "max_feed_xy": 10000,
            "max_feed_z": 5000,
            "max_rpm": 30000
        },
        "controller": "grbl"
    }
)
```

---

## Profile Parameters

### Work Area

| Parameter | Description | Unit |
|-----------|-------------|------|
| X | Maximum X travel | mm |
| Y | Maximum Y travel | mm |
| Z | Maximum Z travel | mm |

!!! note "Effective vs Total Travel"
    Enter the *usable* work area, not total axis travel.
    Account for homing switches, soft limits, and fixture clearance.

---

### Feed Limits

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| Max Feed XY | Maximum XY feed rate | 5000-15000 mm/min |
| Max Feed Z | Maximum Z feed rate | 2000-5000 mm/min |
| Max Rapid XY | Maximum rapid rate | 10000-20000 mm/min |
| Max Rapid Z | Maximum Z rapid rate | 5000-10000 mm/min |

---

### Spindle

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| Min RPM | Minimum spindle speed | 5000-8000 |
| Max RPM | Maximum spindle speed | 24000-30000 |
| Type | Manual / PWM / VFD | - |
| Ramp Time | Spindle spin-up time | 2-5 seconds |

---

### Controller

| Option | Controller Type |
|--------|-----------------|
| `grbl` | Grbl 1.1+ |
| `grbl_hal` | grblHAL |
| `mach` | Mach3/4 |
| `linuxcnc` | LinuxCNC |
| `centroid` | Centroid |
| `generic` | Generic G-code |

---

## Common Machine Profiles

### Shapeoko 4 / Pro

```yaml
name: Shapeoko 4 Pro XL
work_area:
  x: 838
  y: 425
  z: 95
limits:
  max_feed_xy: 10000
  max_feed_z: 5000
  max_rpm: 30000
controller: grbl
post_processor: carbide
```

### X-Carve

```yaml
name: X-Carve 1000mm
work_area:
  x: 750
  y: 750
  z: 65
limits:
  max_feed_xy: 8000
  max_feed_z: 1000
  max_rpm: 30000
controller: grbl
post_processor: grbl
```

### Onefinity

```yaml
name: Onefinity Woodworker
work_area:
  x: 816
  y: 816
  z: 133
limits:
  max_feed_xy: 12000
  max_feed_z: 3000
  max_rpm: 30000
controller: grbl
post_processor: grbl
```

### LongMill

```yaml
name: LongMill MK2 30x30
work_area:
  x: 792
  y: 845
  z: 114
limits:
  max_feed_xy: 4000
  max_feed_z: 3000
  max_rpm: 30000
controller: grbl
post_processor: grbl
```

---

## Advanced Settings

### Homing

| Parameter | Description |
|-----------|-------------|
| Homing Enabled | Whether machine homes on startup |
| Home Direction | +/- for each axis |
| Home Order | Which axis homes first |
| Soft Limits | Enable software travel limits |

### Tool Change

| Parameter | Description |
|-----------|-------------|
| Tool Change Position | X, Y, Z for tool changes |
| Tool Change Method | Manual / ATC / Pause |
| Tool Length Probe | Enable probe for tool length |

### Parking

| Parameter | Description |
|-----------|-------------|
| Park Position | X, Y, Z for end-of-job |
| Spindle Off Delay | Wait after spindle stop |
| Coolant Off Delay | Wait after coolant stop |

---

## Validation

The system validates toolpaths against machine limits:

### Warnings

- Feed rate approaches maximum
- Work area utilization > 90%
- Rapid moves near limits

### Errors (Blocked)

- Toolpath exceeds work area
- Feed rate exceeds maximum
- Spindle speed out of range

---

## Importing/Exporting Profiles

### Export

```bash
# Via API
curl http://localhost:8000/api/machines/profiles/export \
  -o machine_profiles.json
```

### Import

```bash
# Via API
curl -X POST http://localhost:8000/api/machines/profiles/import \
  -F "file=@machine_profiles.json"
```

---

## Troubleshooting

### "Toolpath exceeds work area"

- Check that stock dimensions fit within machine limits
- Verify work origin placement
- Consider repositioning geometry

### "Feed rate too high"

- Reduce feed rate in operation settings
- Update machine profile with correct limits
- Check material/tool recommendations

### "Unknown controller"

- Select a supported controller type
- Use `generic` for unsupported controllers
- Custom post processors may be needed

---

## Related

- [Post Processors](post-processors.md) - G-code output customization
- [Toolpath Generation](../features/toolpaths.md) - Creating toolpaths
- [Safety & RMOS](safety-rmos.md) - Manufacturing safety
