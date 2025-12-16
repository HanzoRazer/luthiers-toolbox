# SAW LAB 2.0 — Executive Handoff Document

**Version:** 2.0  
**Date:** December 15, 2025  
**Status:** Production Ready  
**Classification:** Technical Architecture & Safety Systems

---

## 🎯 Executive Summary

**Saw Lab 2.0** is a specialized subsystem within the Luthier's Tool Box platform that enables **safe, physics-informed table saw operations** for guitar lutherie workflows. It integrates with the broader **RMOS (Rosette Manufacturing Operating System)** to provide bidirectional design-to-manufacturing workflows.

### Core Value Proposition

| Capability | Business Impact |
|------------|-----------------|
| **Safety-First Design** | Prevents dangerous operations via real-time physics validation |
| **Bidirectional Workflow** | Seamless transition between Art Studio design and CNC execution |
| **Physics-Based Scoring** | Manufacturing feasibility based on actual blade mechanics |
| **Multi-Calculator Pipeline** | 5 specialized safety calculators working in concert |

### Key Differentiator
Unlike generic CAM software, Saw Lab 2.0 **prevents dangerous saw configurations before they reach the shop floor** through real-time kickback risk assessment, rim speed validation, and blade deflection analysis.

---

## 🔄 Bidirectional Workflow Architecture

### Design → Manufacturing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BIDIRECTIONAL WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐     ┌─────────────────┐     ┌────────────────────────┐   │
│  │  Art Studio   │────▶│  RMOS Gateway   │────▶│  Calculator Service    │   │
│  │  (Design UI)  │     │  (Mode Router)  │     │  (Router/Saw Branch)   │   │
│  └───────────────┘     └─────────────────┘     └────────────────────────┘   │
│         │                      │                         │                   │
│         │                      ▼                         ▼                   │
│         │              ┌─────────────────┐     ┌────────────────────────┐   │
│         │              │   Tool ID Check │     │   Saw Calculator Set   │   │
│         │              │  saw:* prefix?  │────▶│  • Heat                │   │
│         │              └─────────────────┘     │  • Deflection          │   │
│         │                      │ No            │  • Rim Speed           │   │
│         │                      ▼               │  • Bite Load           │   │
│         │              ┌─────────────────┐     │  • Kickback ⚠️         │   │
│         │              │ Router Calcs    │     └────────────────────────┘   │
│         │              │ (chipload, etc) │               │                   │
│         │              └─────────────────┘               ▼                   │
│         │                                      ┌────────────────────────┐   │
│         │                                      │  Feasibility Result    │   │
│         │◀─────────────────────────────────────│  Score + Risk Bucket   │   │
│         │         Feedback Loop                │  Warnings + Guidance   │   │
│                                                └────────────────────────┘   │
│                                                          │                   │
│                                                          ▼                   │
│                                                ┌────────────────────────┐   │
│                                                │  Saw Ops Pipeline      │   │
│                                                │  • Slice Preview       │   │
│                                                │  • Toolpath Generation │   │
│                                                │  • G-code Export       │   │
│                                                └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mode Detection Logic

The system automatically detects saw operations via tool ID prefix:

```python
def _is_saw_tool(tool_id: Optional[str]) -> bool:
    """Check if tool_id indicates a saw blade operation."""
    if not tool_id:
        return False
    return tool_id.lower().startswith("saw:")
```

**Tool ID Format:** `saw:<diameter_inches>_<tooth_count>_<kerf_mm>`

| Example | Interpretation |
|---------|----------------|
| `saw:10_24_3.0` | 10" blade, 24 teeth, 3.0mm kerf |
| `saw:12_60_3.5` | 12" blade, 60 teeth, 3.5mm kerf |
| `saw:8_40_2.5` | 8" blade, 40 teeth, 2.5mm kerf |

---

## ⚠️ Safety & Physics Direction

### Philosophy

Saw Lab 2.0 is built on the principle that **safety is not optional**. Every operation passes through a multi-stage physics validation pipeline before reaching the shop floor.

### The Five Safety Calculators

#### 1. Kickback Risk Calculator (`kickback_adapter.py`)
**Most Critical Safety Feature**

Kickback is the leading cause of table saw injuries. This calculator assesses:

| Risk Factor | Assessment |
|-------------|------------|
| Blade height above work | Should be 3-6mm for safety |
| Riving knife presence | Major risk reduction |
| Anti-kickback pawls | Additional protection |
| Bite per tooth | Aggressive = higher risk |
| Cut type | Rip cuts higher risk than crosscuts |

**Output Categories:**
- `LOW` — Safe to proceed
- `MEDIUM` — Proceed with caution
- `HIGH` — Review setup before proceeding
- `CRITICAL` — Do not proceed, adjust parameters

```python
@dataclass
class KickbackRiskResult:
    risk_score: float      # 0-1 scale
    category: RiskCategory # LOW/MEDIUM/HIGH/CRITICAL
    risk_factors: List[str]
    message: str
```

#### 2. Heat Risk Calculator (`heat_adapter.py`)
Estimates thermal risk during cutting:

| Factor | Effect |
|--------|--------|
| High rim speed | Increased friction heat |
| Low bite per tooth | Rubbing instead of cutting |
| Dense materials | Ebony, rosewood = higher heat |
| Resinous materials | Pitch buildup, burning |

**Material Heat Sensitivity:**
```python
MATERIAL_HEAT_FACTORS = {
    "ebony": 1.4,      # Most sensitive
    "rosewood": 1.3,
    "maple": 1.0,      # Baseline
    "spruce": 0.7,
    "cedar": 0.65,     # Least sensitive
}
```

#### 3. Blade Deflection Calculator (`deflection_adapter.py`)
Estimates blade wobble under load:

| Factor | Effect |
|--------|--------|
| Blade diameter | Larger = more deflection |
| Plate thickness | Thinner = more flex |
| Kerf width | Thin-kerf = less stiff |
| Feed force | Higher = more deflection |

**Risk Assessment:**
- `GREEN` — Deflection within 0.5mm tolerance
- `YELLOW` — Approaching limits
- `RED` — Excessive deflection risk

#### 4. Rim Speed Calculator (`rim_speed_adapter.py`)
Validates peripheral blade velocity:

**Formula:**
```
rim_speed_m_s = π × diameter_m × rpm / 60
```

**Safe Operating Ranges:**
| Material | Rim Speed (m/s) |
|----------|-----------------|
| Wood (carbide) | 40-70 |
| Wood (HSS) | 30-50 |
| Maximum carbide | 60 |

#### 5. Bite Per Tooth Calculator (`bite_per_tooth_adapter.py`)
Ensures proper chip formation:

**Formula:**
```
bite_mm = feed_mm_min / (rpm × tooth_count)
```

| Range | Condition |
|-------|-----------|
| < 0.05mm | Too low — rubbing, burning |
| 0.05-0.50mm | Optimal range |
| > 0.50mm | Too high — overload risk |

---

## 📊 Risk Evaluation Pipeline

### Overall Risk Assessment

```python
class SawRiskEvaluator:
    """Evaluates safety risks for saw operations."""
    
    def evaluate(self, design: SawDesign, ctx: SawContext) -> SawRiskLevel:
        risks = []
        risks.append(self._check_kickback_risk(design, ctx))
        risks.append(self._check_blade_exposure(design, ctx))
        risks.append(self._check_rpm_safety(ctx))
        risks.append(self._check_feed_safety(design, ctx))
        
        # Return worst case
        if SawRiskLevel.RED in risks:
            return SawRiskLevel.RED
        elif SawRiskLevel.YELLOW in risks:
            return SawRiskLevel.YELLOW
        return SawRiskLevel.GREEN
```

### Risk Levels

| Level | Meaning | UI Treatment |
|-------|---------|--------------|
| `GREEN` | Safe to proceed | Green indicators, no warnings |
| `YELLOW` | Proceed with caution | Yellow warnings, review recommended |
| `RED` | Do not proceed | Red stop, mandatory review |

---

## 🗂️ Namespace & Module Structure

### Primary Namespace: `app.saw_lab`

```
services/api/app/
├── saw_lab/                          # SAW LAB 2.0 CORE
│   ├── __init__.py                   # Package exports
│   ├── models.py                     # Pydantic schemas
│   ├── risk_evaluator.py             # Safety risk pipeline
│   ├── geometry.py                   # Cut geometry calculations
│   ├── path_planner.py               # Saw toolpath generation
│   ├── toolpath_builder.py           # G-code construction
│   ├── debug_router.py               # Physics debug endpoints
│   ├── debug_schemas.py              # Debug API schemas
│   └── calculators/                  # Physics calculators
│       ├── __init__.py
│       ├── saw_heat.py               # Heat risk core
│       ├── saw_deflection.py         # Deflection core
│       ├── saw_rimspeed.py           # Rim speed core
│       ├── saw_bite_load.py          # Bite load core
│       └── saw_kickback.py           # Kickback risk core
│
├── calculators/
│   ├── saw/                          # CALCULATOR ADAPTERS
│   │   ├── __init__.py
│   │   ├── heat_adapter.py           # RMOS ↔ Saw Lab bridge
│   │   ├── deflection_adapter.py     # RMOS ↔ Saw Lab bridge
│   │   ├── rim_speed_adapter.py      # RMOS ↔ Saw Lab bridge
│   │   ├── bite_per_tooth_adapter.py # RMOS ↔ Saw Lab bridge
│   │   └── kickback_adapter.py       # RMOS ↔ Saw Lab bridge
│   └── service.py                    # Unified calculator facade
│
├── cam_core/
│   └── saw_lab/                      # CAM CORE INTEGRATION
│       ├── __init__.py
│       ├── models.py                 # CAM-specific models
│       ├── operations.py             # Cut operations
│       ├── queue.py                  # Job queuing
│       ├── learning.py               # ML feed optimization
│       ├── saw_blade_registry.py     # Blade database
│       ├── saw_blade_validator.py    # Blade spec validation
│       └── importers/                # PDF/CSV blade import
│
├── toolpath/
│   ├── saw_engine.py                 # RMOS saw toolpath engine
│   └── service.py                    # Toolpath service (mode routing)
│
├── routers/
│   ├── rmos_saw_ops_router.py        # Saw ops API endpoints
│   ├── saw_blade_router.py           # Blade CRUD API
│   ├── saw_validate_router.py        # Validation API
│   └── dashboard_router.py           # Saw Lab dashboard
│
└── data/
    └── cam_core/
        └── saw_blades/               # Blade JSON fixtures
            └── saw_blades.json
```

---

## 📋 Schema Reference

### Core Data Models

#### SawContext
```python
class SawContext(BaseModel):
    """Saw blade and machine context."""
    blade_diameter_mm: float = Field(ge=100.0, le=600.0)
    blade_kerf_mm: float = Field(ge=1.0, le=10.0)
    tooth_count: int = Field(ge=10, le=120)
    max_rpm: int = Field(ge=1000, le=10000)
    arbor_size_mm: float = Field(ge=10.0, le=50.0)
    material_id: Optional[str]
    stock_thickness_mm: float = Field(ge=1.0, le=150.0)
    feed_rate_mm_per_min: float = Field(ge=100.0, le=20000.0)
    use_dust_collection: bool = True
```

#### SawDesign
```python
class SawDesign(BaseModel):
    """Saw cut design parameters."""
    cut_length_mm: float = Field(ge=10.0, le=3000.0)
    cut_type: str  # rip, crosscut, miter, bevel, dado
    miter_angle_deg: float = Field(ge=-60.0, le=60.0)
    bevel_angle_deg: float = Field(ge=-45.0, le=45.0)
    dado_width_mm: float = Field(ge=0.0, le=50.0)
    dado_depth_mm: float = Field(ge=0.0, le=75.0)
    repeat_count: int = Field(ge=1, le=100)
    offset_mm: float = Field(ge=0.0, le=1000.0)
```

#### SawBladeSpec
```python
class SawBladeSpec(BaseModel):
    """Normalized saw blade specification."""
    id: str                          # Unique blade ID
    vendor: str                      # Tenryu, Kanefusa, Freud, etc.
    model_code: str                  # Manufacturer part number
    diameter_mm: float               # Blade outer diameter
    kerf_mm: float                   # Cutting width
    plate_thickness_mm: float        # Blade body thickness
    bore_mm: float                   # Arbor hole diameter
    teeth: int                       # Number of teeth
    hook_angle_deg: Optional[float]  # Tooth hook angle
    application: Optional[str]       # Rip, crosscut, combo
    material_family: Optional[str]   # Hardwood, softwood, plywood
```

#### SawRiskLevel
```python
class SawRiskLevel(str, Enum):
    GREEN = "GREEN"    # Safe to proceed
    YELLOW = "YELLOW"  # Proceed with caution
    RED = "RED"        # Do not proceed
```

---

## 🔌 API Endpoints

### RMOS Integration Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rmos/feasibility` | POST | Unified feasibility (auto-routes to saw) |
| `/api/rmos/toolpaths` | POST | Generate toolpaths (saw or router) |
| `/api/rmos/bom` | POST | Bill of materials |

### Saw-Specific Operations

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rmos/saw-ops/slice/preview` | POST | Slice operation preview |
| `/api/rmos/saw-ops/pipeline/handoff` | POST | Design → manufacturing handoff |

### Debug & Diagnostics

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/saw/debug/.../physics-debug` | GET | Physics engine debug |
| `/api/saw/debug/.../health` | GET | Health check |

### Blade Management (Planned)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/saw/blades` | GET | List all blades |
| `/api/saw/blades/{id}` | GET | Get blade by ID |
| `/api/saw/blades` | POST | Create blade |
| `/api/saw/blades/{id}` | PUT | Update blade |
| `/api/saw/blades/{id}` | DELETE | Remove blade |

---

## 🧪 Validation & Testing

### Blade Library Validation

```bash
python scripts/validate_saw_blade_library.py path/to/saw_blades.json
python scripts/validate_saw_blade_library.py path/to/saw_blades.json --strict
```

**Validation Rules:**
- Required fields: `blade_id`, `manufacturer`, `model`, `diameter_mm`, `kerf_mm`, `plate_thickness_mm`, `max_rpm`, `tooth_count`
- Type checks: Numeric fields must be numbers
- Range checks: `kerf_mm` must be 0.2-10.0mm
- Physical plausibility: `kerf > plate_thickness`
- Rim speed sanity: Must be within safe bounds

### Integration Tests

```powershell
# Full Saw Lab 2.0 test suite
.\scripts\test_saw_lab_2_0.ps1

# Expected output:
# ✓ Router mode confirmed (chipload calculator present)
# ✓ Saw mode detected (saw calculators present)
# ✓ Saw toolpaths generated
# ✓ BOM generated
```

---

## 🚀 Future Roadmap

### Phase 1: Current (v2.0) ✅
- [x] Saw mode detection via tool_id prefix
- [x] Five safety calculators operational
- [x] RMOS integration complete
- [x] Slice preview endpoint
- [x] Risk evaluation pipeline

### Phase 2: Enhanced Safety (v2.1)
- [ ] Real-time blade wear tracking
- [ ] ML-based kickback prediction
- [ ] Dust collection integration
- [ ] Blade temperature monitoring

### Phase 3: Advanced CAM (v2.2)
- [ ] Multi-pass dado operations
- [ ] Finger joint automation
- [ ] Box joint patterns
- [ ] Compound miter optimization

### Phase 4: Shop Integration (v3.0)
- [ ] SawStop integration
- [ ] Festool CMS compatibility
- [ ] Shaper Origin support
- [ ] IoT dust collection triggers

---

## 📞 Technical Contacts

| Role | Responsibility |
|------|----------------|
| **CAM Lead** | Saw Lab physics models, toolpath algorithms |
| **Safety Lead** | Kickback prevention, risk evaluation |
| **RMOS Lead** | Bidirectional workflow, calculator service |
| **Frontend Lead** | Art Studio → Saw Lab UI integration |

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| `SAW_LAB_TEST_REPORT_DEC15.md` | Test results and validation |
| `WORKSPACE_HEALTH_REPORT.md` | Repository health status |
| `ADAPTIVE_POCKETING_MODULE_L.md` | Router CAM module (counterpart) |
| `ART_STUDIO_QUICKREF.md` | Design UI integration |
| `copilot-instructions.md` | AI agent guidance |

---

## ✅ Handoff Checklist

**For Receiving Team:**

- [ ] Review bidirectional workflow architecture
- [ ] Understand saw mode detection (`saw:` prefix)
- [ ] Familiarize with 5 safety calculators
- [ ] Test `/api/rmos/feasibility` with saw tool_id
- [ ] Validate blade JSON fixtures
- [ ] Run `test_saw_lab_2_0.ps1` integration tests
- [ ] Review risk evaluation pipeline
- [ ] Understand namespace structure

**Acceptance Criteria:**
1. All saw calculators return valid scores
2. Kickback risk properly assessed
3. Mode switching works correctly
4. Slice preview generates valid statistics
5. No blocking errors in health check

---

**Document Status:** COMPLETE  
**Last Updated:** December 15, 2025  
**Next Review:** January 2026
