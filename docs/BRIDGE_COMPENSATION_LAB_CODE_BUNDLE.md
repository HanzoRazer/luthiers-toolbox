# Interactive Bridge Compensation Lab - Code Bundle

> **Status**: Sandbox in progress - document will be periodically appended
> **Last Updated**: 2026-03-18
> **Version**: 0.3.0-draft

---

## README

### Overview

The **Interactive Bridge Compensation Lab** is a design and setup tool for calculating acoustic guitar saddle compensation. It provides two operational modes:

1. **Setup Mode** - Bench workflow using measured cents error to compute saddle adjustments
2. **Design Mode** - Predictive workflow using string specs (gauge, tension, wound/plain) to estimate compensation

### Key Features

- Live recalculation of per-string compensation targets
- Weighted least-squares saddle line fitting
- SVG visualization with residual whiskers
- CSV import/export for bench workflow
- Project-aware prefill and session save/restore
- Warning system for anomalous values

### File Structure

```
packages/client/src/design-utilities/lutherie/bridge-compensation/
  useBridgeCompensation.ts    # Core composable with all calculation logic
  BridgeCompensationPanel.vue # Interactive UI component
```

### Integration Points

- Calculator Hub
- Bridge Lab
- DESIGN context tools
- Instrument Project state

---

## Implementation Plan

### Phase 1: Core Math Engine (Complete)

- [x] Cents-to-length conversion: `ΔL = L × (2^(e/1200) - 1)`
- [x] Weighted linear regression for saddle line fit
- [x] Residual computation (target - fitted)
- [x] Saddle angle calculation: `θ = arctan(slope)`
- [x] Treble/bass setback from fitted line

### Phase 2: Setup Mode UI (Complete)

- [x] Editable per-string table
- [x] Live recompute on input change
- [x] Fit summary display (angle, treble/bass setback, RMS residual)
- [x] Warning system for large deltas, steep angles
- [x] Fit quality label (Excellent/Good/Fair/Poor/Very Poor)

### Phase 3: Visualization (Complete)

- [x] SVG plot with coordinate system
- [x] Target compensation points
- [x] Fitted saddle line
- [x] Residual whiskers (green/amber/red by magnitude)
- [x] Axis labels and scale

### Phase 4: CSV Workflow (Complete)

- [x] CSV parsing with header detection
- [x] Export input CSV (current state)
- [x] Export results CSV (with computed values)
- [x] Example input CSV generation
- [x] File upload and paste support

### Phase 5: Project Integration (Complete)

- [x] `BridgeCompProjectSeed` interface for prefill
- [x] `BridgeCompSavedSession` interface for persistence
- [x] Auto-save with watcher
- [x] Reset to project defaults
- [x] Host integration pattern (Calculator Hub example)

### Phase 6: Design Mode (Complete)

- [x] Mode toggle (Setup / Design)
- [x] Per-string spec inputs (gauge, tension, wound)
- [x] Action interpolation (treble to bass)
- [x] Semi-empirical compensation estimator
- [x] Mode-aware warnings

### Phase 7: Pending Work

- [ ] Mode-aware CSV support (spec CSV for Design Mode)
- [ ] Break angle integration (Carruth ~6 threshold)
- [ ] Neck angle upstream coupling
- [ ] Calibration against real instruments
- [ ] Integration with existing repo compensation fields

---

## Changelog

### v0.3.0-draft (Current)

**Added**
- Dual-mode support: Setup Mode vs Design Mode
- Per-string spec inputs: `gaugeIn`, `tensionLb`, `isWound`
- Design inputs: `action12TrebleMm`, `action12BassMm`
- Semi-empirical compensation estimator function
- Mode toggle UI with explanatory footnotes
- Mode-aware warnings for Design Mode ranges
- `sourceMode` field on row results

**Changed**
- `BridgeCompStringInput` extended with spec fields
- Default strings now include gauge/tension/wound data
- Auto-save watches mode and designInputs

### v0.2.0-draft

**Added**
- Project-aware prefill from `BridgeCompProjectSeed`
- Session save/restore via `BridgeCompSavedSession`
- `autoSave` option with deep watcher
- Project Context section in UI
- Reset to Project Defaults button
- Last saved timestamp display
- Host integration example (CalculatorHubView)

**Changed**
- `useBridgeCompensation()` now accepts options object
- `resetDefaults()` respects project seed

### v0.1.0-draft

**Added**
- Core composable `useBridgeCompensation()`
- `BridgeCompensationPanel.vue` component
- Cents-to-mm conversion
- Weighted least-squares saddle line fit
- SVG plot with targets, fitted line, residuals
- CSV import/export (input and results)
- Warning system
- Fit quality classification

---

## Code Artifacts

### 1. Python v1 - Design Calculator (Prototype)

```python
"""Bridge compensation design calculator - prototype v1."""
from dataclasses import dataclass
from math import atan, degrees
from typing import List

@dataclass
class StringSpec:
    name: str
    gauge_in: float
    tension_lb: float
    is_wound: bool
    x_mm: float

def estimate_compensation_mm(
    scale_length_mm: float,
    action_12th_mm: float,
    strings: List[StringSpec],
    plain_k: float = 0.018,
    wound_k: float = 0.024,
    gauge_exp: float = 1.15,
    action_exp: float = 1.70,
) -> List[float]:
    """
    Semi-empirical compensation estimate per string.

    Returns list of compensation values in mm.
    """
    compensations = []
    for s in strings:
        k = wound_k if s.is_wound else plain_k
        gauge_term = (s.gauge_in ** gauge_exp)
        action_term = (action_12th_mm ** action_exp)
        tension_factor = 25.0 / max(s.tension_lb, 1.0)
        scale_factor = scale_length_mm / 647.7

        c = k * gauge_term * action_term * tension_factor * scale_factor * 1000
        compensations.append(c)

    return compensations

def fit_straight_saddle(x_mm: List[float], c_mm: List[float]):
    """
    Least-squares line fit for straight saddle approximation.

    Returns: (intercept_a, slope_b, angle_deg, treble_setback, bass_setback)
    """
    n = len(x_mm)
    if n < 2:
        return (0.0, 0.0, 0.0, 0.0, 0.0)

    x_bar = sum(x_mm) / n
    c_bar = sum(c_mm) / n

    num = sum((x_mm[i] - x_bar) * (c_mm[i] - c_bar) for i in range(n))
    den = sum((x_mm[i] - x_bar) ** 2 for i in range(n))

    if abs(den) < 1e-12:
        return (c_bar, 0.0, 0.0, c_bar, c_bar)

    b = num / den
    a = c_bar - b * x_bar
    angle_deg = degrees(atan(b))

    treble_setback = a + b * min(x_mm)
    bass_setback = a + b * max(x_mm)

    return (a, b, angle_deg, treble_setback, bass_setback)
```

### 2. Python v2 - Setup Calculator (Full)

```python
"""Bridge compensation setup calculator v2 - bench workflow."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional
import math
import csv
import argparse
from io import StringIO

@dataclass
class StringMeasurementInput:
    """Per-string bench measurement input."""
    name: str
    x_mm: float
    current_comp_mm: float
    cents_error: float
    weight: float = 1.0

@dataclass
class StringSetupResult:
    """Per-string setup calculation result."""
    name: str
    x_mm: float
    current_comp_mm: float
    cents_error: float
    weight: float
    delta_mm: float
    target_comp_mm: float
    fitted_comp_mm: float
    residual_mm: float

@dataclass
class SaddleFitResult:
    """Saddle line fitting result."""
    intercept_a: float
    slope_b: float
    angle_deg: float
    treble_setback_mm: float
    bass_setback_mm: float
    rms_residual_mm: float
    max_residual_mm: float
    fit_quality: str

@dataclass
class SetupCalculatorResult:
    """Complete setup calculation output."""
    scale_length_mm: float
    strings: List[StringSetupResult]
    saddle_fit: SaddleFitResult

def cents_to_length_delta_mm(scale_length_mm: float, cents_error: float) -> float:
    """
    Convert cents error to saddle position change.

    Formula: ΔL = L × (2^(e/1200) - 1)

    Positive cents (sharp) -> positive delta (move saddle back)
    Negative cents (flat) -> negative delta (move saddle forward)
    """
    return scale_length_mm * (2 ** (cents_error / 1200) - 1)

def weighted_line_fit(
    x: List[float],
    y: List[float],
    weights: List[float],
) -> tuple[float, float]:
    """
    Weighted least-squares line fit.

    Returns (intercept, slope).
    """
    n = len(x)
    if n < 2:
        return (sum(y) / max(n, 1), 0.0)

    w_sum = sum(weights)
    if w_sum < 1e-12:
        w_sum = 1.0
        weights = [1.0] * n

    x_bar = sum(w * xi for w, xi in zip(weights, x)) / w_sum
    y_bar = sum(w * yi for w, yi in zip(weights, y)) / w_sum

    num = sum(w * (xi - x_bar) * (yi - y_bar) for w, xi, yi in zip(weights, x, y))
    den = sum(w * (xi - x_bar) ** 2 for w, xi in zip(weights, x))

    if abs(den) < 1e-12:
        return (y_bar, 0.0)

    slope = num / den
    intercept = y_bar - slope * x_bar

    return (intercept, slope)

def classify_fit_quality(rms: float) -> str:
    """Classify fit quality by RMS residual."""
    if rms < 0.05:
        return "Excellent"
    elif rms < 0.10:
        return "Good"
    elif rms < 0.20:
        return "Fair"
    elif rms < 0.35:
        return "Poor"
    else:
        return "Very Poor"

def build_setup_result(
    scale_length_mm: float,
    inputs: List[StringMeasurementInput],
) -> SetupCalculatorResult:
    """
    Main orchestration: compute setup corrections and saddle fit.
    """
    # Sort by x position
    sorted_inputs = sorted(inputs, key=lambda s: s.x_mm)

    # Compute deltas and targets
    deltas = [cents_to_length_delta_mm(scale_length_mm, s.cents_error) for s in sorted_inputs]
    targets = [s.current_comp_mm + d for s, d in zip(sorted_inputs, deltas)]

    # Weighted line fit
    x_vals = [s.x_mm for s in sorted_inputs]
    weights = [s.weight for s in sorted_inputs]
    intercept, slope = weighted_line_fit(x_vals, targets, weights)

    # Fitted values and residuals
    fitted = [intercept + slope * xi for xi in x_vals]
    residuals = [t - f for t, f in zip(targets, fitted)]

    # Build string results
    string_results = []
    for i, s in enumerate(sorted_inputs):
        string_results.append(StringSetupResult(
            name=s.name,
            x_mm=s.x_mm,
            current_comp_mm=s.current_comp_mm,
            cents_error=s.cents_error,
            weight=s.weight,
            delta_mm=deltas[i],
            target_comp_mm=targets[i],
            fitted_comp_mm=fitted[i],
            residual_mm=residuals[i],
        ))

    # Compute fit statistics
    rms = math.sqrt(sum(r ** 2 for r in residuals) / len(residuals)) if residuals else 0.0
    max_res = max(abs(r) for r in residuals) if residuals else 0.0
    angle_deg = math.degrees(math.atan(slope))
    treble_setback = intercept + slope * min(x_vals)
    bass_setback = intercept + slope * max(x_vals)

    saddle_fit = SaddleFitResult(
        intercept_a=intercept,
        slope_b=slope,
        angle_deg=angle_deg,
        treble_setback_mm=treble_setback,
        bass_setback_mm=bass_setback,
        rms_residual_mm=rms,
        max_residual_mm=max_res,
        fit_quality=classify_fit_quality(rms),
    )

    return SetupCalculatorResult(
        scale_length_mm=scale_length_mm,
        strings=string_results,
        saddle_fit=saddle_fit,
    )

def format_text_report(result: SetupCalculatorResult) -> str:
    """Format result as human-readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("BRIDGE COMPENSATION SETUP REPORT")
    lines.append("=" * 60)
    lines.append(f"Scale Length: {result.scale_length_mm:.2f} mm")
    lines.append("")

    lines.append("PER-STRING ANALYSIS")
    lines.append("-" * 60)
    lines.append(f"{'String':<8} {'X(mm)':<8} {'Curr':<8} {'Cents':<8} {'Delta':<8} {'Target':<8} {'Fitted':<8} {'Resid':<8}")
    lines.append("-" * 60)

    for s in result.strings:
        lines.append(
            f"{s.name:<8} {s.x_mm:<8.2f} {s.current_comp_mm:<8.2f} "
            f"{s.cents_error:<8.1f} {s.delta_mm:<8.3f} {s.target_comp_mm:<8.3f} "
            f"{s.fitted_comp_mm:<8.3f} {s.residual_mm:<8.3f}"
        )

    lines.append("")
    lines.append("SADDLE FIT SUMMARY")
    lines.append("-" * 60)
    fit = result.saddle_fit
    lines.append(f"Saddle Angle:      {fit.angle_deg:+.2f} deg")
    lines.append(f"Treble Setback:    {fit.treble_setback_mm:.3f} mm")
    lines.append(f"Bass Setback:      {fit.bass_setback_mm:.3f} mm")
    lines.append(f"RMS Residual:      {fit.rms_residual_mm:.3f} mm")
    lines.append(f"Max Residual:      {fit.max_residual_mm:.3f} mm")
    lines.append(f"Fit Quality:       {fit.fit_quality}")
    lines.append("=" * 60)

    return "\n".join(lines)

# CSV I/O functions
def read_string_inputs_from_csv(csv_text: str) -> List[StringMeasurementInput]:
    """Parse CSV text into string measurement inputs."""
    reader = csv.DictReader(StringIO(csv_text))
    inputs = []
    for row in reader:
        inputs.append(StringMeasurementInput(
            name=row.get('name', row.get('string', '')),
            x_mm=float(row.get('x_mm', row.get('x', 0))),
            current_comp_mm=float(row.get('current_comp_mm', row.get('current', 0))),
            cents_error=float(row.get('cents_error', row.get('cents', 0))),
            weight=float(row.get('weight', 1.0)),
        ))
    return inputs

def write_results_to_csv(result: SetupCalculatorResult) -> str:
    """Export results as CSV text."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'name', 'x_mm', 'current_comp_mm', 'cents_error', 'weight',
        'delta_mm', 'target_comp_mm', 'fitted_comp_mm', 'residual_mm'
    ])
    for s in result.strings:
        writer.writerow([
            s.name, f"{s.x_mm:.2f}", f"{s.current_comp_mm:.2f}",
            f"{s.cents_error:.1f}", f"{s.weight:.2f}",
            f"{s.delta_mm:.4f}", f"{s.target_comp_mm:.4f}",
            f"{s.fitted_comp_mm:.4f}", f"{s.residual_mm:.4f}"
        ])
    return output.getvalue()

def write_example_input_csv() -> str:
    """Generate example input CSV template."""
    return """name,x_mm,current_comp_mm,cents_error,weight
e,0.0,1.60,2.5,1.0
B,10.8,1.95,4.0,1.0
G,21.6,2.40,3.0,1.0
D,32.4,2.95,1.0,1.0
A,43.2,3.35,-0.5,1.0
E,54.0,3.70,2.0,1.0
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bridge Compensation Setup Calculator")
    parser.add_argument("--scale-length", type=float, default=628.65, help="Scale length in mm")
    parser.add_argument("--input-csv", type=str, help="Input CSV file path")
    parser.add_argument("--output-csv", type=str, help="Output CSV file path")
    parser.add_argument("--write-example-csv", type=str, help="Write example input CSV to path")
    args = parser.parse_args()

    if args.write_example_csv:
        with open(args.write_example_csv, 'w', newline='') as f:
            f.write(write_example_input_csv())
        print(f"Wrote example input CSV to {args.write_example_csv}")
    elif args.input_csv:
        with open(args.input_csv, 'r') as f:
            inputs = read_string_inputs_from_csv(f.read())
        result = build_setup_result(args.scale_length, inputs)
        print(format_text_report(result))
        if args.output_csv:
            with open(args.output_csv, 'w', newline='') as f:
                f.write(write_results_to_csv(result))
            print(f"\nWrote results CSV to {args.output_csv}")
    else:
        # Demo with default data
        demo_inputs = [
            StringMeasurementInput("e", 0.0, 1.60, 2.5),
            StringMeasurementInput("B", 10.8, 1.95, 4.0),
            StringMeasurementInput("G", 21.6, 2.40, 3.0),
            StringMeasurementInput("D", 32.4, 2.95, 1.0),
            StringMeasurementInput("A", 43.2, 3.35, -0.5),
            StringMeasurementInput("E", 54.0, 3.70, 2.0),
        ]
        result = build_setup_result(args.scale_length, demo_inputs)
        print(format_text_report(result))
```

### 3. Vue Composable - useBridgeCompensation.ts

```typescript
import { computed, ref, watch } from 'vue'

export interface BridgeCompStringInput {
  id: string
  name: string
  xMm: number
  currentCompMm: number
  centsError: number
  weight: number
  gaugeIn: number
  tensionLb: number
  isWound: boolean
}

export interface BridgeCompRowResult extends BridgeCompStringInput {
  deltaMm: number
  targetCompMm: number
  fittedCompMm: number
  residualMm: number
  sourceMode: 'setup' | 'design'
}

export interface BridgeCompFitResult {
  interceptA: number
  slopeB: number
  angleDeg: number
  trebleSetbackMm: number
  bassSetbackMm: number
  rmsResidualMm: number
  maxResidualMm: number
}

export interface BridgeCompPlotResult {
  points: Array<{ x: number; y: number; name: string }>
  lineStart: { x: number; y: number }
  lineEnd: { x: number; y: number }
  residuals: Array<{ x: number; y1: number; y2: number; name: string }>
  xMin: number
  xMax: number
  yMin: number
  yMax: number
}

export interface BridgeCompProjectSeed {
  scaleLengthMm?: number
  strings?: Array<{
    name?: string
    xMm?: number
    currentCompMm?: number
    centsError?: number
    gaugeIn?: number
    tensionLb?: number
    isWound?: boolean
    weight?: number
  }>
}

export interface BridgeCompSavedSession {
  version: number
  scaleLengthMm: number
  strings: BridgeCompStringInput[]
  savedAt: string
}

export interface BridgeCompensationOptions {
  projectSeed?: BridgeCompProjectSeed | null
  savedSession?: BridgeCompSavedSession | null
  onSaveSession?: (session: BridgeCompSavedSession) => Promise<void>
  autoSave?: boolean
}

export type BridgeCompMode = 'setup' | 'design'

export interface BridgeCompDesignInputs {
  action12TrebleMm: number
  action12BassMm: number
}

const BRIDGE_COMP_SESSION_VERSION = 1

function centsToLengthDeltaMm(scaleLengthMm: number, centsError: number): number {
  return scaleLengthMm * (2 ** (centsError / 1200) - 1)
}

function safeNumber(value: unknown, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function weightedLineFit(
  x: number[],
  y: number[],
  weights: number[],
): { a: number; b: number } {
  const n = x.length
  if (n < 2) {
    const yBar = y.reduce((s, v) => s + v, 0) / Math.max(n, 1)
    return { a: yBar, b: 0 }
  }

  let wSum = weights.reduce((s, w) => s + w, 0)
  if (wSum < 1e-12) {
    wSum = n
    weights = Array(n).fill(1)
  }

  const xBar = weights.reduce((s, w, i) => s + w * x[i], 0) / wSum
  const yBar = weights.reduce((s, w, i) => s + w * y[i], 0) / wSum

  let num = 0
  let den = 0
  for (let i = 0; i < n; i++) {
    num += weights[i] * (x[i] - xBar) * (y[i] - yBar)
    den += weights[i] * (x[i] - xBar) ** 2
  }

  if (Math.abs(den) < 1e-12) return { a: yBar, b: 0 }

  const b = num / den
  const a = yBar - b * xBar
  return { a, b }
}

function defaultStrings(): BridgeCompStringInput[] {
  return [
    { id: 'e', name: 'e', xMm: 0.0,  currentCompMm: 1.60, centsError:  2.5, weight: 1.0, gaugeIn: 0.012, tensionLb: 23.3, isWound: false },
    { id: 'B', name: 'B', xMm: 10.8, currentCompMm: 1.95, centsError:  4.0, weight: 1.0, gaugeIn: 0.016, tensionLb: 23.1, isWound: false },
    { id: 'G', name: 'G', xMm: 21.6, currentCompMm: 2.40, centsError:  3.0, weight: 1.0, gaugeIn: 0.024, tensionLb: 31.7, isWound: true  },
    { id: 'D', name: 'D', xMm: 32.4, currentCompMm: 2.95, centsError:  1.0, weight: 1.0, gaugeIn: 0.032, tensionLb: 29.4, isWound: true  },
    { id: 'A', name: 'A', xMm: 43.2, currentCompMm: 3.35, centsError: -0.5, weight: 1.0, gaugeIn: 0.042, tensionLb: 29.2, isWound: true  },
    { id: 'E', name: 'E', xMm: 54.0, currentCompMm: 3.70, centsError:  2.0, weight: 1.0, gaugeIn: 0.053, tensionLb: 24.8, isWound: true  },
  ]
}

function defaultDesignInputs(): BridgeCompDesignInputs {
  return {
    action12TrebleMm: 1.9,
    action12BassMm: 2.4,
  }
}

function inchesToMm(valueIn: number): number {
  return valueIn * 25.4
}

function interpolateActionForString(
  xMm: number,
  xMinMm: number,
  xMaxMm: number,
  actionTrebleMm: number,
  actionBassMm: number,
): number {
  if (Math.abs(xMaxMm - xMinMm) < 1e-9) return actionTrebleMm
  const t = (xMm - xMinMm) / (xMaxMm - xMinMm)
  return actionTrebleMm + t * (actionBassMm - actionTrebleMm)
}

function estimateStringCompensationMm(
  scaleLengthMm: number,
  stringInput: BridgeCompStringInput,
  localActionMm: number,
): number {
  const gaugeMm = inchesToMm(stringInput.gaugeIn)
  const base = 0.45
  const gaugeTerm = 0.55 * gaugeMm
  const actionTerm = 0.18 * (localActionMm ** 1.7)
  const scaleTerm = 0.25 * (scaleLengthMm / 647.7)
  const tensionTerm = 7.5 / Math.max(stringInput.tensionLb, 1.0)
  const woundTerm = stringInput.isWound ? 0.55 : 0.0

  return base + gaugeTerm + actionTerm + scaleTerm + tensionTerm + woundTerm
}

export function useBridgeCompensation(options: BridgeCompensationOptions = {}) {
  const mode = ref<BridgeCompMode>('setup')
  const designInputs = ref<BridgeCompDesignInputs>(defaultDesignInputs())
  const scaleLengthMm = ref(safeNumber(options.projectSeed?.scaleLengthMm, 628.65))
  const strings = ref<BridgeCompStringInput[]>(defaultStrings())
  const csvText = ref('')
  const csvMessage = ref('')
  const csvError = ref('')
  const lastSavedAt = ref(options.savedSession?.savedAt || '')

  const sortedStrings = computed(() =>
    [...strings.value].sort((a, b) => safeNumber(a.xMm) - safeNumber(b.xMm))
  )

  const rows = computed<BridgeCompRowResult[]>(() => {
    const src = sortedStrings.value.map((s) => ({
      ...s,
      xMm: safeNumber(s.xMm),
      currentCompMm: safeNumber(s.currentCompMm),
      centsError: safeNumber(s.centsError),
      weight: Math.max(0.0001, safeNumber(s.weight, 1)),
      gaugeIn: Math.max(0.001, safeNumber(s.gaugeIn, 0.012)),
      tensionLb: Math.max(0.1, safeNumber(s.tensionLb, 20)),
      isWound: Boolean(s.isWound),
    }))

    const x = src.map((s) => s.xMm)
    const weights = src.map((s) => s.weight)
    const xMin = Math.min(...x)
    const xMax = Math.max(...x)

    const deltas = src.map((s) =>
      mode.value === 'setup'
        ? centsToLengthDeltaMm(scaleLengthMm.value, s.centsError)
        : 0
    )

    const targets = src.map((s, i) => {
      if (mode.value === 'setup') {
        return s.currentCompMm + deltas[i]
      }

      const localActionMm = interpolateActionForString(
        s.xMm,
        xMin,
        xMax,
        designInputs.value.action12TrebleMm,
        designInputs.value.action12BassMm,
      )

      return estimateStringCompensationMm(
        scaleLengthMm.value,
        s,
        localActionMm,
      )
    })

    const { a, b } = weightedLineFit(x, targets, weights)
    const fitted = x.map((xi) => a + b * xi)

    return src.map((s, i) => ({
      ...s,
      deltaMm: deltas[i],
      targetCompMm: targets[i],
      fittedCompMm: fitted[i],
      residualMm: targets[i] - fitted[i],
      sourceMode: mode.value,
    }))
  })

  const fit = computed<BridgeCompFitResult>(() => {
    const x = rows.value.map((r) => r.xMm)
    const targets = rows.value.map((r) => r.targetCompMm)
    const weights = rows.value.map((r) => r.weight)

    const { a, b } = weightedLineFit(x, targets, weights)
    const residuals = rows.value.map((r) => r.residualMm)

    const rms = Math.sqrt(residuals.reduce((s, r) => s + r * r, 0) / Math.max(residuals.length, 1))
    const maxRes = Math.max(...residuals.map(Math.abs))

    return {
      interceptA: a,
      slopeB: b,
      angleDeg: Math.atan(b) * (180 / Math.PI),
      trebleSetbackMm: a + b * Math.min(...x),
      bassSetbackMm: a + b * Math.max(...x),
      rmsResidualMm: rms,
      maxResidualMm: maxRes,
    }
  })

  const fitQualityLabel = computed(() => {
    const rms = fit.value.rmsResidualMm
    if (rms < 0.05) return 'Excellent'
    if (rms < 0.10) return 'Good'
    if (rms < 0.20) return 'Fair'
    if (rms < 0.35) return 'Poor'
    return 'Very Poor'
  })

  const warnings = computed<string[]>(() => {
    const out: string[] = []
    if (fit.value.rmsResidualMm > 0.20) {
      out.push('Residuals are large. A straight saddle may be a weak approximation.')
    }
    if (mode.value === 'setup' && rows.value.some((r) => Math.abs(r.deltaMm) > 2.0)) {
      out.push('One or more setup corrections exceed 2.0 mm. Check nut height, witness points, strings, and relief.')
    }
    if (mode.value === 'design' && rows.value.some((r) => r.targetCompMm < 0.5 || r.targetCompMm > 5.5)) {
      out.push('One or more predicted compensation values are outside the expected range. Verify gauge, tension, and action inputs.')
    }
    if (Math.abs(fit.value.angleDeg) > 6) {
      out.push('Computed saddle slant is unusually steep. Verify spacing, cents readings, and current compensation inputs.')
    }
    return out
  })

  function updateString(id: string, patch: Partial<BridgeCompStringInput>): void {
    const idx = strings.value.findIndex((s) => s.id === id)
    if (idx >= 0) {
      strings.value[idx] = { ...strings.value[idx], ...patch }
    }
  }

  function setMode(nextMode: BridgeCompMode): void {
    mode.value = nextMode
  }

  function updateDesignInputs(patch: Partial<BridgeCompDesignInputs>): void {
    designInputs.value = { ...designInputs.value, ...patch }
  }

  function resetDefaults(): void {
    scaleLengthMm.value = safeNumber(options.projectSeed?.scaleLengthMm, 628.65)
    strings.value = defaultStrings()
  }

  return {
    mode,
    designInputs,
    scaleLengthMm,
    strings,
    rows,
    fit,
    fitQualityLabel,
    warnings,
    csvText,
    csvMessage,
    csvError,
    lastSavedAt,
    setMode,
    updateString,
    updateDesignInputs,
    resetDefaults,
  }
}
```

### 4. Vue Component - BridgeCompensationPanel.vue (Template Structure)

```vue
<template>
  <div class="bcp">
    <!-- Project Context Section -->
    <section v-if="projectMetaLabel || lastSavedAt" class="bcp-card">
      <div class="bcp-card-header"><h3>Project Context</h3></div>
      <div class="bcp-project-meta">
        <div v-if="projectMetaLabel" class="bcp-note bcp-note--neutral">
          Prefilled from {{ projectMetaLabel }}.
        </div>
        <div class="bcp-project-actions">
          <button class="bcp-btn" @click="resetDefaults">Reset to Project Defaults</button>
          <button class="bcp-btn bcp-btn--primary" @click="handleSaveSession">Save to Project</button>
        </div>
        <p v-if="lastSavedAt" class="bcp-footnote">Last saved: {{ formatTimestamp(lastSavedAt) }}</p>
      </div>
    </section>

    <!-- Mode Toggle Section -->
    <section class="bcp-card">
      <div class="bcp-card-header"><h3>Mode</h3></div>
      <div class="bcp-mode-toggle">
        <button class="bcp-btn" :class="{ 'bcp-btn--primary': mode === 'setup' }" @click="setMode('setup')">
          Setup Mode
        </button>
        <button class="bcp-btn" :class="{ 'bcp-btn--primary': mode === 'design' }" @click="setMode('design')">
          Design Mode
        </button>
      </div>
      <p class="bcp-footnote">
        <template v-if="mode === 'setup'">
          Bench solver: measured cents error per string is converted into saddle movement targets.
        </template>
        <template v-else>
          Predictive solver: gauge, tension, wound/plain state, action, and scale length estimate per-string compensation.
        </template>
      </p>
      <div v-if="mode === 'design'" class="bcp-design-controls">
        <label class="bcp-label">
          Action @ 12th (Treble)
          <input v-model.number="designInputs.action12TrebleMm" type="number" step="0.01" class="bcp-input bcp-input--narrow">
        </label>
        <label class="bcp-label">
          Action @ 12th (Bass)
          <input v-model.number="designInputs.action12BassMm" type="number" step="0.01" class="bcp-input bcp-input--narrow">
        </label>
      </div>
    </section>

    <!-- Per-String Table -->
    <section class="bcp-card">
      <table class="bcp-table">
        <thead>
          <tr>
            <th>String</th>
            <th>X (mm)</th>
            <th>Current Comp</th>
            <th v-if="mode === 'design'">Gauge (in)</th>
            <th v-if="mode === 'design'">Tension (lb)</th>
            <th v-if="mode === 'design'">Wound</th>
            <th>Cents</th>
            <th>Weight</th>
            <th>Delta (mm)</th>
            <th>Target</th>
            <th>Fitted</th>
            <th>Residual</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <!-- Editable cells for each field -->
          </tr>
        </tbody>
      </table>
    </section>

    <!-- SVG Plot -->
    <section class="bcp-card">
      <svg :viewBox="`0 0 ${PLOT.right + 24} ${PLOT.bottom + 48}`">
        <!-- Axis lines, labels, target points, fitted line, residual whiskers -->
      </svg>
    </section>

    <!-- Fit Summary -->
    <section class="bcp-card">
      <h3>Fit Summary</h3>
      <dl class="bcp-summary">
        <dt>Saddle Angle</dt><dd>{{ fit.angleDeg.toFixed(2) }} deg</dd>
        <dt>Treble Setback</dt><dd>{{ fit.trebleSetbackMm.toFixed(3) }} mm</dd>
        <dt>Bass Setback</dt><dd>{{ fit.bassSetbackMm.toFixed(3) }} mm</dd>
        <dt>RMS Residual</dt><dd>{{ fit.rmsResidualMm.toFixed(3) }} mm</dd>
        <dt>Fit Quality</dt><dd>{{ fitQualityLabel }}</dd>
      </dl>
    </section>

    <!-- Warnings -->
    <section v-if="warnings.length" class="bcp-card bcp-card--warn">
      <ul>
        <li v-for="w in warnings" :key="w">{{ w }}</li>
      </ul>
    </section>
  </div>
</template>
```

---

## Host Integration Pattern

```typescript
// CalculatorHubView.vue
<script setup lang="ts">
import BridgeCompensationPanel from '@/design-utilities/lutherie/bridge-compensation/BridgeCompensationPanel.vue'
import { computed } from 'vue'
import { useInstrumentProject } from '@/composables/useInstrumentProject'

const { project, updateProjectNotes } = useInstrumentProject()

const bridgeCompProjectSeed = computed(() => {
  const scaleLengthMm = project.value?.scale_length_mm ?? 628.65
  const spacing = project.value?.bridge_string_spacing_mm ?? 54.0
  const step = spacing / 5

  return {
    scaleLengthMm,
    strings: [
      { name: 'e', xMm: 0 * step, currentCompMm: project.value?.compensation_treble_mm ?? 1.6, centsError: 0, weight: 1 },
      { name: 'B', xMm: 1 * step, currentCompMm: 1.9, centsError: 0, weight: 1 },
      { name: 'G', xMm: 2 * step, currentCompMm: 2.4, centsError: 0, weight: 1 },
      { name: 'D', xMm: 3 * step, currentCompMm: 2.9, centsError: 0, weight: 1 },
      { name: 'A', xMm: 4 * step, currentCompMm: 3.3, centsError: 0, weight: 1 },
      { name: 'E', xMm: 5 * step, currentCompMm: project.value?.compensation_bass_mm ?? 3.7, centsError: 0, weight: 1 },
    ],
  }
})

const savedBridgeCompSession = computed(() => {
  return project.value?.notes?.bridgeCompensationSession ?? null
})

function handleSaveBridgeCompSession(session: unknown): void {
  updateProjectNotes({
    bridgeCompensationSession: session,
  })
}
</script>

<template>
  <BridgeCompensationPanel
    :project-seed="bridgeCompProjectSeed"
    :saved-session="savedBridgeCompSession"
    project-meta-label="Instrument Project"
    @save-session="handleSaveBridgeCompSession"
  />
</template>
```

---

## Merge Classification

### Bucket A - Directly Mergeable

- Cents-to-mm correction engine
- Straight-saddle fit algorithm
- Residual computations
- CSV I/O concepts
- Interactive panel behavior

### Bucket B - Mergeable After Adaptation

- Project-aware prefill/save-back
- Integration with Bridge Lab / DESIGN context
- Warning system
- SVG plotting layer

### Bucket C - Keep as Design Reference

- Full design-mode predictive compensation model
- Break-angle adjustment heuristics
- Broader architectural claims about missing upstream geometry

---

*Document will be periodically appended as sandbox development continues.*
