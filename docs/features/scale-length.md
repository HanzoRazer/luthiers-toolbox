# Scale Length Designer

Calculate string tension and compare different instrument configurations.

---

## What is Scale Length?

Scale length is the vibrating length of the string—the distance from the nut to the saddle. It directly affects:

- **String tension** - Longer scale = higher tension at same pitch
- **Fret spacing** - Longer scale = wider fret spacing
- **Tone** - Longer scale = brighter, tighter bass response

---

## Using the Designer

### 1. Select a Preset

Choose from common scale lengths:

| Instrument | Scale Length |
|------------|--------------|
| Fender Stratocaster | 25.5" (648mm) |
| Gibson Les Paul | 24.75" (628.7mm) |
| PRS Standard | 25" (635mm) |
| Fender Bass | 34" (864mm) |
| Classical Guitar | 650mm |

### 2. Configure Strings

For each string, set:

- **Gauge** - String diameter in inches (e.g., 0.010)
- **Tuning** - Target pitch (e.g., E4, A4)
- **Material** - Plain steel, wound, nylon

### 3. View Results

The calculator displays:

- Tension in pounds (lbs) and Newtons (N)
- Total tension across all strings
- Tension balance visualization

---

## Mersenne's Law

String tension is calculated using Mersenne's Law:

```
T = μ × (2 × L × f)²
```

Where:

- **T** = Tension
- **μ** = Linear mass density (mass per unit length)
- **L** = Scale length (vibrating length)
- **f** = Frequency (pitch)

---

## Multi-Scale (Fanned Frets)

For fanned fret instruments:

1. Set **Bass Scale** (e.g., 27")
2. Set **Treble Scale** (e.g., 25.5")
3. Set **Perpendicular Fret** (typically 7th-9th fret)

The calculator will show tension for each string at its actual scale length.

---

## Tips for Balanced Tension

| Goal | Approach |
|------|----------|
| Even feel | Target 15-18 lbs per string |
| Easy bending | Lower tension on trebles |
| Tight bass | Higher gauge on bass strings |
| Drop tuning | Heavier gauge to maintain tension |

---

## API Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/api/calculators/string-tension",
    json={
        "scale_length_mm": 648,
        "strings": [
            {"gauge": 0.010, "pitch": "E4", "material": "plain_steel"},
            {"gauge": 0.013, "pitch": "B3", "material": "plain_steel"},
            {"gauge": 0.017, "pitch": "G3", "material": "plain_steel"},
            {"gauge": 0.026, "pitch": "D3", "material": "wound"},
            {"gauge": 0.036, "pitch": "A2", "material": "wound"},
            {"gauge": 0.046, "pitch": "E2", "material": "wound"}
        ]
    }
)

print(response.json())
```

---

## Related

- [Fret Calculator](fret-calculator.md) - Calculate fret positions
- [Unit Converter](unit-converter.md) - Convert between mm and inches
