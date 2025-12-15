# Fret Scale Theory

Mathematical foundations for fret position calculations in equal temperament.

## Core Concept: Equal Temperament

Modern Western music uses **equal temperament**, where the octave is divided into 12 equal semitones. Each semitone has a frequency ratio of:

$$r = \sqrt[12]{2} = 2^{1/12} \approx 1.05946309435929$$

This means each fret raises the pitch by exactly one semitone.

## The Fundamental Formula

### Distance from Nut to Fret n

The distance from the nut to the nth fret is:

$$d_n = L - \frac{L}{2^{n/12}}$$

Or equivalently:

$$d_n = L \cdot \left(1 - 2^{-n/12}\right)$$

Where:
- $L$ = scale length (nut to bridge)
- $n$ = fret number (1, 2, 3, ...)
- $d_n$ = distance from nut to fret n

### Why This Formula Works

1. The 12th fret should be at exactly half the scale length (one octave)
2. Setting n=12: $d_{12} = L - L/2 = L/2$ ✓
3. Each fret divides the remaining string length by the semitone ratio

### Fret-to-Fret Distance

The distance between consecutive frets:

$$\Delta_n = d_n - d_{n-1} = \frac{L}{2^{(n-1)/12}} - \frac{L}{2^{n/12}}$$

This decreases as you go higher up the neck.

## Worked Example: 25.5" (648mm) Scale

| Fret | Distance from Nut (mm) | Spacing (mm) |
|------|----------------------|--------------|
| 1    | 36.40                | 36.40        |
| 2    | 70.75                | 34.35        |
| 3    | 103.17               | 32.43        |
| 4    | 133.77               | 30.60        |
| 5    | 162.65               | 28.88        |
| 6    | 189.92               | 27.26        |
| 7    | 215.65               | 25.73        |
| 8    | 239.96               | 24.31        |
| 9    | 262.90               | 22.94        |
| 10   | 284.56               | 21.65        |
| 11   | 305.00               | 20.44        |
| 12   | 324.00               | 19.00        |
| ...  | ...                  | ...          |
| 22   | 439.11               | 10.07        |

Note: The 12th fret is at exactly 324mm = 648mm / 2

## Common Scale Lengths

| Name | Inches | Millimeters | Usage |
|------|--------|-------------|-------|
| Fender Standard | 25.5" | 648.0 mm | Strat, Tele, most electrics |
| Gibson Standard | 24.75" | 628.65 mm | Les Paul, SG, ES-335 |
| PRS Standard | 25" | 635.0 mm | PRS guitars |
| Classical | 25.6" | 650.0 mm | Classical/nylon |
| Parlor | 24" | 609.6 mm | Small-body acoustics |
| Baritone | 27" | 685.8 mm | Baritone guitars |
| Bass (Long) | 34" | 863.6 mm | Standard bass |
| Bass (Short) | 30" | 762.0 mm | Short-scale bass |

## Multiscale (Fanned Frets)

For multiscale instruments, each string has a different scale length. The formula is applied independently for bass and treble sides, with intermediate strings interpolated.

$$d_n^{(s)} = L^{(s)} \cdot \left(1 - 2^{-n/12}\right)$$

Where $L^{(s)}$ is the scale length for string $s$.

## Assumptions & Limitations

1. **Equal temperament only** - This formula assumes 12-TET. Historical temperaments (meantone, etc.) require different calculations.

2. **Zero nut compensation** - Real instruments may have nut compensation (typically 0.2-0.5mm) for improved intonation.

3. **Zero saddle compensation** - Bridge saddles are typically set back 1-3mm beyond the theoretical scale length for intonation.

4. **Perpendicular frets** - Formula assumes frets are perpendicular to the string. Multiscale instruments require additional geometry.

5. **Ideal string behavior** - Real strings have stiffness that affects vibration, especially on wound strings.

## Implementation

- `services/api/app/instrument_geometry/scale_length.py`
  - `compute_fret_positions_mm(scale_length_mm, fret_count)`
  - `compute_fret_spacing_mm(scale_length_mm, fret_count)`
  - `compute_compensated_scale_length_mm(scale_length_mm, saddle_comp_mm, nut_comp_mm)`

## References

1. Liutaio Mottola. "Fret Spacing Calculator." https://www.liutaiomottola.com/formulae/fret.htm
2. Stewart-MacDonald. "Fret Scale Template Calculator." https://www.stewmac.com/
3. Cumpiano, W. & Natelson, J. (1993). *Guitar Making: Tradition and Technology*. Chronicle Books.
4. Gore, T. & Gilet, G. (2011). *Contemporary Acoustic Guitar Design and Build*. Trevor Gore.
5. French, M. (2008). *Engineering the Guitar: Theory and Practice*. Springer.
