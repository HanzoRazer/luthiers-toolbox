# Fret Calculator

Calculate precise fret positions for any scale length and temperament.

---

## Equal Temperament (12-TET)

The standard Western tuning system divides the octave into 12 equal semitones.

### Formula

```
Fret Position = Scale Length - (Scale Length ÷ 2^(n/12))
```

Where `n` is the fret number (1-24).

### Example: 25.5" Scale

| Fret | Distance from Nut | Distance from Previous |
|------|-------------------|------------------------|
| 1 | 1.432" | 1.432" |
| 2 | 2.782" | 1.350" |
| 3 | 4.055" | 1.273" |
| 5 | 6.376" | 1.133" |
| 7 | 8.409" | 1.009" |
| 12 | 12.75" | 0.716" |
| 24 | 19.125" | 0.338" |

---

## Using the Calculator

### 1. Set Scale Length

Enter your scale length in mm or inches.

### 2. Set Fret Count

Choose number of frets (typically 21-24 for guitar, 20-24 for bass).

### 3. Choose Intonation Model

| Model | Description |
|-------|-------------|
| `equal_temperament_12` | Standard 12-TET (default) |
| `custom_ratios` | User-provided frequency ratios |

### 4. Export Results

Download as:

- **CSV** - For spreadsheet calculations
- **DXF** - For CNC fret slot cutting
- **JSON** - For API integration

---

## Custom Temperaments

For historical or experimental temperaments, use `custom_ratios` mode.

!!! warning "Advanced Feature"
    Custom ratios create key-specific fret positions. The resulting fretboard
    will not play equally in tune in all keys. This is intentional for
    historical accuracy or specific musical applications.

### Providing Ratios

Each fret requires a frequency ratio relative to the open string:

```json
{
  "intonation_model": "custom_ratios",
  "scale_length_mm": 648,
  "fret_count": 22,
  "ratios": [
    1.05946,  // Fret 1
    1.12246,  // Fret 2
    1.18921,  // Fret 3
    // ... one ratio per fret
  ]
}
```

### Named Ratio Sets

Common historical temperaments are available as presets:

| Ratio Set | Description |
|-----------|-------------|
| `JUST_MAJOR` | Just intonation (major key) |
| `PYTHAGOREAN` | Pure fifths tuning |
| `MEANTONE` | Quarter-comma meantone |

!!! note "Ratio Set Limitation"
    Named ratio sets are expanded to explicit per-fret ratios at request time.
    The API requires explicit ratios for CAM export to prevent accidental
    key-locked fretboards.

---

## Compensation

Fret position calculations assume ideal conditions. Real-world compensation accounts for:

### Nut Compensation

The nut position may be moved slightly toward the first fret to compensate for string stiffness.

```
Nut Compensation ≈ 0.5mm - 1.0mm (typical)
```

### Saddle Compensation

The saddle is moved back from the theoretical position:

| String Type | Typical Compensation |
|-------------|---------------------|
| Plain steel | 1.5mm - 2.0mm |
| Wound | 2.5mm - 3.5mm |
| Bass | 3.0mm - 5.0mm |

### Factors Affecting Compensation

- String gauge (heavier = more compensation)
- Action height (higher = more compensation)
- Scale length (longer = less compensation needed)
- String material and core type

---

## API Usage

### Equal Temperament (Default)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/calculators/fret-positions",
    json={
        "scale_length_mm": 648,
        "fret_count": 22
    }
)

positions = response.json()["positions"]
for i, pos in enumerate(positions, 1):
    print(f"Fret {i}: {pos:.3f} mm")
```

### Custom Ratios

```python
# 22-fret 12-TET ratios (for example)
ratios = [2**(n/12) for n in range(1, 23)]

response = requests.post(
    "http://localhost:8000/api/calculators/fret-positions",
    json={
        "scale_length_mm": 648,
        "fret_count": 22,
        "intonation_model": "custom_ratios",
        "ratios": ratios
    }
)
```

---

## Multi-Scale Frets

For fanned fret instruments, calculate positions for each string separately:

```python
bass_scale = 686  # 27"
treble_scale = 648  # 25.5"
perpendicular_fret = 7

# Calculate for each string, interpolating scale length
for string_idx in range(6):
    t = string_idx / 5  # 0 to 1
    scale = bass_scale + (treble_scale - bass_scale) * t
    # Calculate fret positions for this scale length
```

---

## Manufacturability

The calculator validates positions for CNC machining:

- Minimum fret spacing (typically > 3mm)
- Slot width compatibility with fret tang
- Material thickness at fret locations

---

## Related

- [Scale Length Designer](scale-length.md) - Tension calculations
- [DXF Import](dxf-import.md) - Import existing fret layouts
- [Toolpath Generation](toolpaths.md) - Cut fret slots
