# Radius Theory: Compound and Single Radius Fretboards

Mathematical theory of fretboard radius profiles.

## What is Fretboard Radius?

The fretboard radius is the radius of the cylindrical surface that forms the fretboard's cross-section. Looking down the neck from the nut, the fretboard surface is an arc of a circle.

$$\text{Smaller radius} \rightarrow \text{More curved} \rightarrow \text{Easier barre chords}$$
$$\text{Larger radius} \rightarrow \text{Flatter} \rightarrow \text{Better for bending}$$

## Single Radius (Cylindrical)

A single-radius fretboard has the same radius throughout its length. It forms a portion of a cylinder.

### Common Single Radius Values

| Radius | Inches | Typical Use |
|--------|--------|-------------|
| 184.15 mm | 7.25" | Vintage Fender |
| 241.30 mm | 9.5" | Modern Fender |
| 254.00 mm | 10" | Some Gibson, PRS |
| 304.80 mm | 12" | Gibson standard |
| 355.60 mm | 14" | Ibanez JEM |
| 406.40 mm | 16" | Martin acoustic |
| 508.00 mm | 20" | Very flat electric |
| ∞ | Flat | Classical guitars |

## Compound Radius (Conical)

A compound radius fretboard transitions from a smaller radius at the nut to a larger radius at the higher frets. This combines:

- **Curved at nut** - comfortable for chord shapes
- **Flatter at high frets** - prevents "fretting out" during bends

### Linear Interpolation Formula

The radius at position $x$ along the fretboard:

$$R(x) = R_{nut} + \frac{x}{L} \cdot (R_{end} - R_{nut})$$

Where:
- $R_{nut}$ = radius at the nut
- $R_{end}$ = radius at the end of the fretboard
- $x$ = distance from nut
- $L$ = total fretboard length

### Common Compound Radius Combinations

| Start | End | Description |
|-------|-----|-------------|
| 9.5" (241mm) | 14" (356mm) | Modern Fender |
| 10" (254mm) | 16" (406mm) | PRS style |
| 12" (305mm) | 16" (406mm) | Gentle compound |
| 7.25" (184mm) | 12" (305mm) | Vintage feel to modern |

## Radius Drop Calculation

The "drop" is how much lower the edge of the fretboard is compared to the center.

For a fretboard of width $W$ and radius $R$:

$$\text{drop} = R - \sqrt{R^2 - (W/2)^2}$$

For small $W/R$ (typical fretboards), this approximates to:

$$\text{drop} \approx \frac{W^2}{8R}$$

### Example: 9.5" Radius, 42mm Wide Fretboard

$$\text{drop} = 241.3 - \sqrt{241.3^2 - 21^2} = 0.92 \text{ mm}$$

## Geometric Construction

### Single Radius Arc

An arc of radius $R$ centered at $(0, -R)$ passing through the origin:

$$x^2 + (y + R)^2 = R^2$$

Solving for $y$:

$$y = \sqrt{R^2 - x^2} - R$$

For CNC machining, generate points:

```python
for x in range(-W/2, W/2, step):
    y = sqrt(R**2 - x**2) - R
```

### Compound Radius Surface

A compound radius surface is a section of a cone (not cylinder). The centerline is straight, but the cross-section changes continuously.

For accurate CNC machining, calculate the radius at each fret position and generate the arc for that specific radius.

## Effect on String Action

On a radiused fretboard with a radiused bridge, the strings follow the curve. The action (string height) should be:

$$h(x) = h_{center} + \text{drop}(x)$$

Where $x$ is the lateral position from center.

### Fretting Out on Bends

A common problem on small-radius fretboards: when bending a string, it can hit a higher fret (called "fretting out" or "choking out").

The string rises above the fretboard level during a bend. On a curved surface, the adjacent frets are lower than the bent string's path.

**Solution**: Larger radius (flatter) fretboards at high frets, or compound radius.

## Manufacturing Considerations

### Radius Sanding Block

For hand-leveling, use a sanding block with the correct radius. The block should be:
- Long enough to span multiple frets
- Curved to match the fretboard radius

### CNC Machining

For compound radius:
1. Calculate radius at each fret position
2. Generate toolpath with appropriate depth per pass
3. Use ball-end mill sized appropriately for the minimum radius

### Fret Pressing/Hammering

Pre-radiused fret wire should match the fretboard radius (or slightly tighter) for clean installation.

## Implementation

- `services/api/app/instrument_geometry/radius_profiles.py`
  - `compute_compound_radius_at_fret(fret_index, total_frets, start_radius_mm, end_radius_mm)`
  - `compute_radius_arc_points(radius_mm, width_mm, num_points)`
  - `compute_radius_drop_mm(radius_mm, offset_mm)`

## References

1. Stewart-MacDonald. "Understanding Fretboard Radius." https://www.stewmac.com/
2. Erlewine, D. (2007). *The Guitar Player Repair Guide*. Backbeat Books.
3. Koch, M. (2001). *Building Electric Guitars*. Koch Verlag.
4. Hiscock, M. (2014). *Make Your Own Electric Guitar*. NBS Publications.
