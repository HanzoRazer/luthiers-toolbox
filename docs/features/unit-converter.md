# Unit Converter

Convert between all units common in lutherie, woodworking, and CNC machining.

---

## Categories

### Length

| Unit | Abbreviation | Notes |
|------|--------------|-------|
| Millimeters | mm | Metric standard |
| Centimeters | cm | 10 mm |
| Meters | m | 1000 mm |
| Inches | in, " | Imperial standard |
| Feet | ft, ' | 12 inches |
| Thousandths | thou, mil | 0.001 inch |

**Common Conversions:**

- 1 inch = 25.4 mm
- 1 mm = 0.03937 inches
- 1 thou = 0.0254 mm

---

### Mass

| Unit | Abbreviation | Notes |
|------|--------------|-------|
| Grams | g | Metric standard |
| Kilograms | kg | 1000 g |
| Ounces | oz | Imperial |
| Pounds | lb | 16 oz |

**Common Conversions:**

- 1 lb = 453.592 g
- 1 oz = 28.3495 g
- 1 kg = 2.205 lb

---

### Temperature

| Unit | Symbol | Notes |
|------|--------|-------|
| Celsius | °C | Water freezes at 0° |
| Fahrenheit | °F | Water freezes at 32° |
| Kelvin | K | Absolute zero = 0K |

**Formulas:**

- °C to °F: (°C × 9/5) + 32
- °F to °C: (°F - 32) × 5/9
- °C to K: °C + 273.15

---

### Volume

| Unit | Abbreviation | Notes |
|------|--------------|-------|
| Milliliters | mL | Metric |
| Liters | L | 1000 mL |
| Fluid ounces | fl oz | US measure |
| Cups | cup | 8 fl oz |
| Gallons | gal | 128 fl oz |

---

### Board Feet

Board feet is a specialty unit for lumber volume.

**Formula:**

```
Board Feet = (Thickness" × Width" × Length") ÷ 144
```

**Examples:**

| Dimensions | Board Feet |
|------------|------------|
| 1" × 12" × 12" | 1 bf |
| 2" × 6" × 96" | 8 bf |
| 4/4 × 8" × 48" | 2.67 bf |

!!! note "Nominal vs Actual"
    Lumber is sold by nominal thickness (4/4, 5/4, 6/4, etc.).
    - 4/4 = 1" nominal = ~13/16" actual (surfaced)
    - 5/4 = 1.25" nominal = ~1-1/16" actual

---

### Data

| Unit | Size |
|------|------|
| Bytes | B |
| Kilobytes | KB (1024 B) |
| Megabytes | MB (1024 KB) |
| Gigabytes | GB (1024 MB) |
| Terabytes | TB (1024 GB) |

---

## Using the Converter

### In the UI

1. Navigate to **Tools > Scientific Calculator**
2. Select the **Converter** tab
3. Choose a category
4. Enter a value
5. Select source and target units

### Via API

```python
import requests

# Convert 25.4 mm to inches
response = requests.post(
    "http://localhost:8000/api/calculators/convert",
    json={
        "value": 25.4,
        "from_unit": "mm",
        "to_unit": "inches",
        "category": "length"
    }
)

print(response.json())
# {"result": 1.0, "from": "25.4 mm", "to": "1.0 inches"}
```

---

## Precision Notes

- Length conversions maintain 6 decimal places
- Temperature conversions round to 2 decimal places
- Board feet calculations round to 2 decimal places
- All calculations use IEEE 754 double precision

---

## Related

- [Woodwork Calculator](woodwork-calculator.md) - Board feet with species weights
- [Scale Length Designer](scale-length.md) - Uses length conversions
