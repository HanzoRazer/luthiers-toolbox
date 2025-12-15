# Bridge Compensation Notes

Theory and practice of intonation compensation for guitar bridges.

## Why Compensation is Needed

When a string is fretted, three things happen that affect pitch:

1. **Increased tension** - Pressing the string down stretches it slightly, raising the pitch
2. **String stiffness** - The string doesn't vibrate as a perfect flexible wire, especially at the endpoints
3. **Action height** - Higher action means more stretch when fretting

To compensate, we move the saddle **back** (away from the nut), making the vibrating length slightly longer than the theoretical scale length.

## The Physics

### Fretted Note Frequency

The frequency of a fretted note should be:

$$f_n = f_0 \cdot 2^{n/12}$$

Where:
- $f_0$ = open string frequency
- $n$ = fret number

### Actual Frequency (with compensation)

$$f_{actual} = \frac{1}{2L_{eff}} \sqrt{\frac{T_{eff}}{\mu}}$$

Where:
- $L_{eff}$ = effective vibrating length (affected by saddle position)
- $T_{eff}$ = effective tension (increased by fretting)
- $\mu$ = linear mass density of string

### Compensation Amount

The saddle setback (compensation) is approximately:

$$\Delta L \approx \frac{a^2}{2L} + k \cdot d$$

Where:
- $a$ = action height at 12th fret
- $L$ = scale length
- $k$ = string stiffness coefficient
- $d$ = string diameter

## Typical Compensation Values

### 6-String Guitar (Standard Tuning)

| String | Note | Gauge (inches) | Wound? | Compensation (mm) |
|--------|------|----------------|--------|-------------------|
| 6 (Low E) | E2 | 0.046 | Yes | 2.0 - 3.0 |
| 5 | A2 | 0.036 | Yes | 1.5 - 2.5 |
| 4 | D3 | 0.026 | Yes | 1.5 - 2.0 |
| 3 | G3 | 0.017 | Often | 1.0 - 2.0 |
| 2 | B3 | 0.013 | No | 1.0 - 1.5 |
| 1 (High E) | E4 | 0.010 | No | 1.5 - 2.0 |

### Why Plain Strings Need More Than Expected

Plain strings have higher stiffness-to-mass ratio than wound strings of similar pitch. The high E often needs more compensation than expected.

### 4-String Bass

| String | Note | Typical Compensation (mm) |
|--------|------|---------------------------|
| 4 (Low E) | E1 | 2.5 - 3.5 |
| 3 | A1 | 2.0 - 3.0 |
| 2 | D2 | 1.5 - 2.5 |
| 1 | G2 | 1.0 - 2.0 |

## Saddle Types and Compensation

### Electric Guitar (Adjustable Saddles)

Each string has an individually adjustable saddle. Set by ear using a tuner:
1. Tune open string
2. Play 12th fret (not harmonic)
3. If sharp: move saddle back (away from nut)
4. If flat: move saddle forward (toward nut)
5. Repeat until octave is in tune

### Acoustic Guitar (Fixed Saddle)

Compensation is built into the saddle shape:
- **Straight saddle**: Minimal compensation, less accurate
- **Compensated saddle**: Stepped or angled to provide different setback per string

### Classical Guitar (Nylon Strings)

Nylon strings are more flexible, requiring less compensation. Many classical guitars have straight saddles.

## Nut Compensation

Some builders also compensate at the nut, moving it slightly forward to improve open string intonation. This addresses the "2nd fret problem" where fretted notes are sharp.

Typical nut compensation: 0.2 - 0.5 mm

## Action Height Effects

Higher action requires more compensation because the string stretches more when fretted.

**Rule of thumb**: 
- Add ~0.1mm compensation per 0.25mm increase in action at 12th fret

## Temperature and Humidity

String tension and neck relief change with temperature and humidity, affecting intonation:
- Higher temperature → lower tension → slightly flat
- Higher humidity → neck relief increases → action increases → slightly sharp

## Implementation

- `services/api/app/instrument_geometry/bridge_geometry.py`
  - `compute_saddle_positions_mm(scale_length_mm, compensations_mm)`
  - `compute_compensation_estimate(string_gauge_mm, is_wound, action_mm)`
  - `STANDARD_6_STRING_COMPENSATION` dict

## References

1. Stewart-MacDonald. "Intonation: What it is and how to set it." https://www.stewmac.com/
2. Helmholtz, H. (1954). *On the Sensations of Tone*. Dover Publications.
3. Fletcher, N. & Rossing, T. (1998). *The Physics of Musical Instruments*. Springer.
4. Liutaio Mottola. "Notes on Guitar Bridge and Saddle Intonation." https://www.liutaiomottola.com/
