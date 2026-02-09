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

## Core Features

### RMOS (Run Manufacturing Operations System)
- Feasibility analysis before G-code generation
- Risk-based decision gating (GREEN/YELLOW/RED)
- Audit trail for all manufacturing runs
- `@safety_critical` decorator for fail-closed behavior

### CAM Workflows
- DXF import and validation
- Adaptive pocketing with island handling
- Multi-post support (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)

### Art Studio
- Rosette pattern generation
- Relief mapping from images
- SVG-to-toolpath conversion

### Saw Lab
- Batch sawing operations
- Advisory signals and override controls
- G-code validation and linting

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
