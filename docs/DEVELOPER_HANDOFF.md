# Developer Handoff: Luthiers-ToolBox Repository

**Version:** 1.0.0
**Date:** 2026-01-13
**Purpose:** Guide a developer into assuming work on the ToolBox repository

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Architecture Summary](#2-architecture-summary)
3. [Governance & Contracts](#3-governance--contracts)
4. [Cost Attribution System](#4-cost-attribution-system)
5. [Calculator Suite](#5-calculator-suite)
6. [CI/CD Pipeline](#6-cicd-pipeline)
7. [Key File Reference](#7-key-file-reference)
8. [Quick Start Commands](#8-quick-start-commands)
9. [Gaps & Future Work](#9-gaps--future-work)

---

## 1. Repository Overview

**Luthiers-ToolBox** is a monorepo containing:
- **API Service** (`services/api/`) - FastAPI backend for CAM operations, calculators, telemetry
- **Client** (`client/` and `packages/client/`) - Vue.js 3D visualization frontend
- **Contracts** (`contracts/`) - JSON schemas for cross-repo governance
- **Scripts** (`scripts/`) - CI gates, validation, and automation

### Related Repositories

| Repository | Purpose | Relationship |
|------------|---------|--------------|
| `luthiers-toolbox` | Manufacturing operations | Primary (this repo) |
| `sg-spec` | Smart Guitar consumer spec | Receives safe exports, sends telemetry |

---

## 2. Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        LUTHIERS-TOOLBOX                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Vue.js)                                              │
│  ├── 3D Viewer (Three.js)                                       │
│  ├── Calculator UI                                              │
│  └── CAM Operation Interface                                    │
├─────────────────────────────────────────────────────────────────┤
│  API (FastAPI)                                                  │
│  ├── /api/calculators/* - Math & business calculators           │
│  ├── /api/telemetry/*   - Smart Guitar telemetry ingestion      │
│  ├── /api/cost/*        - Cost attribution summaries            │
│  ├── /api/cam/*         - CAM operations & toolpaths            │
│  └── /api/geometry/*    - Geometry parity checking              │
├─────────────────────────────────────────────────────────────────┤
│  Contracts (JSON Schema)                                        │
│  ├── Telemetry contract (SG → ToolBox)                          │
│  ├── Safe export contract (ToolBox → SG)                        │
│  └── Internal policies (cost attribution, viewer pack)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Governance & Contracts

### Overview

Cross-repository governance ensures:
- **Manufacturing secrets** stay in luthiers-toolbox
- **Consumer-safe content** flows to sg-spec
- **Telemetry** flows from sg-spec without player/pedagogy data

### Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Governance Summary | `docs/GOVERNANCE_EXECUTIVE_SUMMARY.md` | Master governance doc (v1.4.0) |
| Telemetry Audit | `docs/TELEMETRY_SYSTEM_AUDIT.md` | SG → ToolBox data flow |
| Safe Export Audit | `docs/SAFE_EXPORT_SYSTEM_AUDIT.md` | ToolBox → SG data flow |

### Contracts Structure

```
contracts/
├── smart_guitar_toolbox_telemetry_v1.schema.json    # Telemetry ingest
├── smart_guitar_toolbox_telemetry_v1.schema.sha256
├── toolbox_smart_guitar_safe_export_v1.schema.json  # Safe export
├── toolbox_smart_guitar_safe_export_v1.schema.sha256
├── telemetry_cost_mapping_policy_v1.json            # Cost attribution
├── viewer_pack_v1.schema.json                       # Viewer pack format
├── viewer_pack_v1.schema.sha256
├── CONTRACTS_VERSION.json                           # Immutability sentinel
└── CHANGELOG.md                                     # Required for changes
```

### Telemetry Contract - Forbidden Fields (22)

These fields are **blocked** from flowing SG → ToolBox:

| Category | Forbidden Fields |
|----------|------------------|
| Player Data | player_id, player_profile, player_preferences |
| Lesson Data | lesson_id, lesson_progress, lesson_score |
| Practice Data | practice_session_id, practice_duration, practice_notes |
| Performance Data | accuracy_percent, timing_deviation_ms, chord_accuracy |
| Recording Data | audio_recording, midi_recording, recording_metadata |
| Coach Data | coach_feedback, coach_prompt, coach_response |
| Pedagogical Data | skill_level, learning_path, achievement_badges |

### Safe Export Contract - Forbidden Content

| Type | Forbidden Values |
|------|------------------|
| Extensions (17) | .nc, .gcode, .tap, .ngc, .cnc, .iso, .mpf, .dnc, .eia, etc. |
| Kinds (7) | cam_toolpath, machine_config, post_processor, etc. |

### Governance CI Gate

The **Scenario B Gate** enforces changelog documentation for contract changes:

```bash
# CI runs this on every PR
python scripts/ci/check_contracts_governance.py --base-ref origin/main
```

Key behaviors:
- Scans only **added lines** in CHANGELOG.md (not deleted)
- Uses **regex word boundaries** to prevent partial matches
- Requires explicit documentation of any schema changes

---

## 4. Cost Attribution System

### Purpose

Maps validated telemetry to manufacturing cost dimensions for internal analysis.

### Data Flow

```
Telemetry Ingest → Cost Mapper → Cost Store → Summary API
       │                │              │            │
       │                │              │            └── GET /api/cost/summary
       │                │              └── JSONL by date
       │                └── telemetry_cost_mapping_policy_v1.json
       └── POST /api/telemetry/ingest
```

### Cost Dimensions

| Dimension | Source Metric | Unit |
|-----------|---------------|------|
| compute_cost_hours | hardware_performance.cpu_hours | hours |
| energy_amp_hours | hardware_performance.amp_draw_avg | amp-hours |
| thermal_stress_c | hardware_performance.temp_c_max | celsius |
| wear_cycles | lifecycle.power_cycles | count |

### Module Structure

```
services/api/app/cost_attribution/
├── __init__.py     # Public exports
├── models.py       # CostFact dataclass, CostDimension literal
├── policy.py       # Load/cache mapping policy
├── mapper.py       # telemetry_to_cost_facts()
├── store.py        # JSONL storage, summarize functions
└── api.py          # FastAPI router (/api/cost/*)
```

### Key Integration Point

Cost attribution hooks into telemetry ingestion at `services/api/app/smart_guitar_telemetry/api.py`:

```python
# Lines 191-211 - Non-fatal cost attribution hook
try:
    cost_facts, cost_warnings = telemetry_to_cost_facts(_repo_root(), payload_dict)
    if cost_facts:
        append_cost_facts(_repo_root(), cost_facts)
except Exception as e:
    _log.warning("Cost attribution failed (non-fatal): %s", e)
```

---

## 5. Calculator Suite

### Categories

| Category | Modules | Status |
|----------|---------|--------|
| **General Purpose** | basic, scientific, fraction, financial | Production |
| **Woodworking** | board feet, wedge, miter, dovetail | Production |
| **Instrument Construction** | fret, radius, bracing, rosette, inlay | Production |
| **CAM/Machining** | chipload, heat, deflection, saw adapters | Production |
| **Business** | ROI, amortization, throughput | Backend Only |
| **Electronics** | wiring | Development |

**Overall Readiness: 85% Production-Ready**

### File Structure

```
services/api/app/calculators/
├── service.py                    # Main CalculatorService facade (590 lines)
├── bracing_calc.py               # Guitar brace physics
├── rosette_calc.py               # Sound hole patterns
├── inlay_calc.py                 # Fretboard inlay patterns
├── alternative_temperaments.py   # Non-equal tuning systems
├── fret_slots_cam.py             # Fret slot toolpaths (31KB)
├── suite/
│   ├── basic_calculator.py
│   ├── scientific_calculator.py
│   ├── fraction_calculator.py
│   ├── financial_calculator.py
│   └── luthier_calculator.py
├── business/                     # NOT exposed via REST API
│   ├── roi.py
│   ├── amortization.py
│   └── machine_throughput.py
└── saw/                          # Saw blade physics adapters
```

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/calculators/evaluate` | Math expression evaluation |
| `POST /api/calculators/tvm` | Time Value of Money solver |
| `POST /api/calculators/fret-positions` | Fret slot positions |
| `POST /api/calculators/board-feet` | Lumber volume calculation |
| `POST /api/calculators/string-tension` | String physics |
| `POST /calculators/evaluate` | CAM cut operation evaluation |

### Gap: Business Calculators

The business calculators (`roi.py`, `amortization.py`, `machine_throughput.py`) are:
- Fully implemented with business logic
- Have unit tests
- **NOT exposed via REST API**

This is a potential enhancement opportunity.

---

## 6. CI/CD Pipeline

### Primary Workflow: `.github/workflows/core_ci.yml`

```yaml
jobs:
  api-tests:
    - Art Studio Scope Gate
    - Viewer Pack Schema Parity Gate
    - CONTRACTS_GOVERNANCE_SCENARIO_B_GATE    # Key governance gate
    - Governance Unit Tests (stem_mentioned)  # 25 tests
    - Cost Attribution Unit Tests             # 10 tests
    - Boot API + pytest

  geometry-parity:
    - Geometry parity check (G-code vs paths)

  containers-smoke:
    - Docker build (API, Client, Nginx)
    - Stack health check via proxy
```

### Key CI Scripts

| Script | Purpose |
|--------|---------|
| `scripts/ci/check_contracts_governance.py` | Scenario B gate |
| `scripts/ci/test_check_contracts_governance.py` | 25 stem tests |
| `scripts/ci/check_art_studio_scope.py` | Art studio boundary |
| `scripts/validate/check_viewer_pack_schema_parity.py` | Schema parity |

### Running Tests Locally

```bash
# Governance unit tests (25 tests)
python -m pytest scripts/ci/test_check_contracts_governance.py -v

# Cost attribution tests (10 tests)
cd services/api
python -m pytest tests/test_cost_attribution_mapper_unit.py -v

# Full API test suite
cd services/api
python -m pytest -q

# Business calculator tests
python -m pytest services/api/app/tests/calculators/test_business.py -v
```

---

## 7. Key File Reference

### Governance & Contracts

| File | Purpose |
|------|---------|
| `docs/GOVERNANCE_EXECUTIVE_SUMMARY.md` | Master governance doc |
| `docs/TELEMETRY_SYSTEM_AUDIT.md` | Telemetry deep dive |
| `docs/SAFE_EXPORT_SYSTEM_AUDIT.md` | Safe export deep dive |
| `contracts/CONTRACTS_VERSION.json` | Schema immutability sentinel |
| `contracts/CHANGELOG.md` | Required for schema changes |

### Cost Attribution

| File | Purpose |
|------|---------|
| `contracts/telemetry_cost_mapping_policy_v1.json` | Mapping policy |
| `services/api/app/cost_attribution/models.py` | CostFact dataclass |
| `services/api/app/cost_attribution/mapper.py` | Mapping logic |
| `services/api/app/cost_attribution/api.py` | REST endpoints |
| `services/api/tests/test_cost_attribution_mapper_unit.py` | 10 unit tests |

### CI/CD

| File | Purpose |
|------|---------|
| `.github/workflows/core_ci.yml` | Main CI workflow |
| `scripts/ci/check_contracts_governance.py` | Scenario B gate |
| `scripts/ci/test_check_contracts_governance.py` | Stem tests |

### Calculator Suite

| File | Purpose |
|------|---------|
| `services/api/app/calculators/service.py` | Main facade |
| `services/api/app/routers/ltb_calculator_router.py` | REST routes |
| `services/api/app/calculators/business/` | Business calcs (no API) |

---

## 8. Quick Start Commands

### Environment Setup

```bash
# Clone repository
git clone https://github.com/HanzoRazer/luthiers-toolbox
cd luthiers-toolbox

# Python environment
python -m venv .venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r services/api/requirements.txt

# Start API
cd services/api
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Docker Stack

```bash
# Create .env file
cat > .env <<EOF
SERVER_PORT=8000
CLIENT_PORT=8080
FRONT_PORT=8088
CORS_ORIGINS=http://localhost:8088
COMPOSE_PROJECT_NAME=toolbox
EOF

# Build and start
docker compose --profile proxy up -d

# Health check
curl http://127.0.0.1:8088/api/health
```

### SHA256 Verification

```bash
# PowerShell
Get-ChildItem contracts/*.schema.json | ForEach-Object {
  $hash = (Get-FileHash $_ -Algorithm SHA256).Hash.ToLower()
  $expected = Get-Content ($_.FullName -replace '\.json$','.sha256')
  if ($hash -eq $expected) { "OK: $($_.Name)" } else { "FAIL: $($_.Name)" }
}

# Bash
for f in contracts/*.schema.json; do
  sha=$(sha256sum "$f" | cut -d' ' -f1)
  expected=$(cat "${f%.json}.sha256")
  [ "$sha" = "$expected" ] && echo "OK: $f" || echo "FAIL: $f"
done
```

---

## 9. Gaps & Future Work

### Identified Gaps

| Gap | Severity | Effort |
|-----|----------|--------|
| Business calculators not exposed via REST | Medium | 2-3 hours |
| Electronics/wiring calculator incomplete | Low | TBD |
| No dedicated calculator suite documentation | Low | 1-2 hours |

### Potential Enhancements

1. **Expose Business Calculators via REST API**
   - Create `services/api/app/routers/business_calculator_router.py`
   - Add endpoints for ROI, amortization, throughput
   - Register router in `main.py`

2. **Complete Electronics Calculator**
   - Finish wiring resistance calculations
   - Add pickup configuration analysis

3. **Calculator Suite Documentation**
   - Create `docs/CALCULATOR_SUITE_AUDIT.md`
   - Document all calculator APIs
   - Add usage examples

---

## Recent Commits Reference

| Commit | Description |
|--------|-------------|
| `3ef0c3d` | Stem check tightening (added lines only, word boundaries) |
| `81967dd` | 25 unit tests for stem_mentioned regex |
| `fe48e9c` | Cost attribution bundle (695 lines) |
| `72da081` | Cost attribution tests added to CI |
| `c276e2c` | Cost attribution docs in governance summary |

---

## Contact & Resources

- **GitHub Issues**: https://github.com/HanzoRazer/luthiers-toolbox/issues
- **sg-spec Repository**: https://github.com/HanzoRazer/sg-spec
- **CI Status**: Check `.github/workflows/core_ci.yml` runs

---

*This handoff document was generated to facilitate developer onboarding. For detailed technical specifications, refer to the linked documentation files.*
