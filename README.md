# Luthier's Tool Box

A CNC guitar lutherie platform with parametric design tools, CAM workflows, and manufacturing safety controls.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/HanzoRazer/luthiers-toolbox/actions/workflows/api_tests.yml/badge.svg)](https://github.com/HanzoRazer/luthiers-toolbox/actions)

## Quick Start

```bash
# Clone
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox

# Backend (FastAPI)
cd services/api
python -m venv .venv
.venv/Scripts/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (Vue 3) - separate terminal
cd packages/client
npm install
npm run dev
```

- **API**: http://localhost:8000 (Swagger: http://localhost:8000/docs)
- **Frontend**: http://localhost:5173

## Project Structure

```
luthiers-toolbox/
├── packages/
│   └── client/              # Vue 3 + Vite frontend
├── services/
│   └── api/                 # FastAPI backend
│       ├── app/             # Application code (1,200+ Python files)
│       └── tests/           # Test suite (1,069 tests passing)
├── contracts/               # JSON schema contracts
├── docker/                  # Container configurations
├── docs/                    # Documentation (30 files)
└── presets/                 # CAM presets and templates
```

## Current State

| Component | Version | Status |
|-----------|---------|--------|
| RMOS | 2.0 | Stable |
| Adaptive Pocketing | 3.0 (L.3) | Stable |
| Saw Lab | 1.0 | Stable |
| Art Studio | 1.0 | Stable |
| DXF Import | 2.0 | Stable |
| Blueprint AI | 1.0 | Beta |
| Vision Engine | 1.0 | Beta |

**API Endpoints**: `GET /api/features/catalog` for full feature list with use cases.

## What Works Today

### RMOS (Run Manufacturing Operations System) v2.0
- Server-side feasibility analysis with 22 safety rules
- Risk-based decision gating (GREEN/YELLOW/RED)
- Immutable audit trail for all manufacturing runs
- `@safety_critical` decorator for fail-closed behavior
- Startup validation blocks unsafe deployments

### Adaptive Pocketing v3.0
- L.1: Robust polygon offsetting with island handling
- L.2: Continuous spiral toolpaths with adaptive stepover
- L.3: Trochoidal insertion + jerk-aware time estimation
- Multi-post support (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)

### DXF Import v2.0
- Geometry validation and preflight checks
- LWPOLYLINE and LINE extraction
- Scale detection and unit conversion

### Art Studio v1.0
- Rosette pattern generation
- Relief mapping from images
- Design-first workflow with snapshots

### Saw Lab v1.0
- Batch sawing operations with cut plans
- Advisory signals and override controls
- G-code validation and linting

## Quick Start by Use Case

### DXF → G-code
```bash
# 1. Validate DXF geometry
curl -X POST http://localhost:8000/api/dxf/preflight \
  -F "file=@pocket.dxf"

# 2. Generate toolpath
curl -X POST http://localhost:8000/api/cam/pocket/adaptive/plan \
  -H "Content-Type: application/json" \
  -d '{"loops": [...], "tool_d": 6.0, "stepover": 0.45}'

# 3. Export G-code (GRBL)
curl -X POST http://localhost:8000/api/cam/pocket/adaptive/gcode \
  -H "Content-Type: application/json" \
  -d '{"loops": [...], "tool_d": 6.0, "post_id": "GRBL"}'
```

### Fret Calculation
```bash
curl -X POST http://localhost:8000/api/calculators/frets/positions \
  -H "Content-Type: application/json" \
  -d '{"scale_length_mm": 648, "fret_count": 22}'
```

### Rosette Design
```bash
# Browse patterns
curl http://localhost:8000/api/art/patterns

# Generate rosette
curl -X POST http://localhost:8000/api/art/generators/rosette \
  -H "Content-Type: application/json" \
  -d '{"pattern_id": "celtic_knot", "outer_radius_mm": 52}'
```

## Development

### Run Tests
```bash
cd services/api
pytest tests/ -v
# Expected: 1,069 passed
```

### Type Checking
```bash
# Backend
cd services/api && mypy app/

# Frontend
cd packages/client && npm run type-check
```

### Docker
```bash
docker compose up --build
```

## Configuration

Environment variables (`.env`):
```
RMOS_RUNS_DIR=./data/runs
LOG_LEVEL=INFO
```

## Documentation

Key docs in `docs/`:
- `RMOS_FEASIBILITY_RULES_v1.md` - Feasibility rule reference
- `RMOS_V1_VALIDATION_PROTOCOL.md` - 30-run validation protocol
- `BOUNDARY_RULES.md` - Architectural boundary enforcement

## License

MIT License - see [LICENSE](LICENSE) for details.
