# Sprint P4-B — Production Shop Inverse Engine Wiring

## Files

| Source | Destination | Action |
|--------|-------------|--------|
| app/analyzer/viewer_pack_bridge.py | app/analyzer/viewer_pack_bridge.py | NEW |
| app/calculators/plate_design/brace_prescription.py | app/calculators/plate_design/brace_prescription.py | NEW |
| tests/test_viewer_pack_bridge.py | tests/test_viewer_pack_bridge.py | NEW |

## What these do

**viewer_pack_bridge.py** — the single coupling point between tap_tone_pi measurement
data and the existing inverse solver. Reads a ViewerPackV1 (from viewer_pack_loader.py)
and extracts PlateInputs: E_L_GPa, E_C_GPa, rho, plate dimensions, and modal targets.
Falls back to species defaults when bending data is absent. Works with both
the ViewerPackV1 dataclass and raw dicts.

**brace_prescription.py** — translates InverseSolverResult into physical brace specs.
Scales X-brace height and fan strut height to wood stiffness (softer wood → taller
braces). Enforces manufacturability constraints: 4 mm minimum width (router bit
diameter), 14 mm maximum height. Returns BracePrescription with summary() method.

## How to wire into the existing inverse_solver

```python
from app.analyzer.viewer_pack_loader import load_viewer_pack
from app.analyzer.viewer_pack_bridge import plate_inputs_from_pack
from app.calculators.plate_design.inverse_solver import solve_for_thickness
from app.calculators.plate_design.rayleigh_ritz import OrthotropicPlate
from app.calculators.plate_design.brace_prescription import prescribe_bracing

# Load the measurement bundle
pack = load_viewer_pack("path/to/session.zip")
inputs = plate_inputs_from_pack(pack)

# Construct the plate model for the forward solver
plate = OrthotropicPlate.from_wood(**inputs.to_orthotropic_plate_kwargs())

# Run the inverse solver
target_hz = inputs.target_frequencies[0][1] if inputs.target_frequencies else 200.0
result = solve_for_thickness(
    target_f1_Hz=target_hz,
    E_L=inputs.E_L_GPa * 1e9,
    E_C=inputs.E_C_GPa * 1e9,
    rho=inputs.rho_kg_m3,
    a=inputs.plate_length_mm / 1000,
    b=inputs.plate_width_mm / 1000,
)

# Produce the brace prescription
prescription = prescribe_bracing(inputs, result, style="x_brace")
print(prescription.summary())
```

## Install and verify

```bash
# From services/api directory
cp -r app/analyzer/viewer_pack_bridge.py app/analyzer/
cp -r app/calculators/plate_design/brace_prescription.py app/calculators/plate_design/
cp tests/test_viewer_pack_bridge.py tests/

python -m pytest tests/test_viewer_pack_bridge.py -q
# Expected: 29 passed

git add app/analyzer/viewer_pack_bridge.py \
        app/calculators/plate_design/brace_prescription.py \
        tests/test_viewer_pack_bridge.py
git commit -m "feat: Sprint P4-B — viewer_pack_bridge and brace_prescription"
```
