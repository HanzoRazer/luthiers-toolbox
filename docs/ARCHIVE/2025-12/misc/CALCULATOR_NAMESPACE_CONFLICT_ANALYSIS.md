# Calculator Namespace Conflict Analysis

**Date:** December 11, 2025  
**Canonical Source:** `files (41)/calculators_package/` (5 modules + `__init__.py`)  
**Prefix Strategy:** `LTB` (Luthier's ToolBox)  
**Status:** ⚠️ CONFLICTS DETECTED - Renaming Required

---

## 🚨 CRITICAL FINDINGS

### **Existing Calculator Infrastructure in Repo**

**Location:** `services/api/app/calculators/`

**Existing Files:**
1. `service.py` - **CalculatorService** class (RMOS 2.0 unified facade)
2. `bracing_calc.py` - Bracing calculations
3. `fret_slots_cam.py` - Fret slot CAM operations
4. `fret_slots_export.py` - Fret slot export logic
5. `inlay_calc.py` - Inlay calculations
6. `rosette_calc.py` - Rosette pattern calculations
7. `tool_profiles.py` - Tool profile management
8. `saw_bridge.py` - Saw calculator bridge
9. `business/` - Business logic subdirectory
10. `saw/` - Saw-specific calculators
11. `wiring/` - Wiring calculators
12. `__init__.py` - Package initialization

**Existing Router:**
- `services/api/app/routers/calculators_router.py` - Wave 8 router (547 lines)
  - Prefix: `/calculators` (not `/api/calculators`)
  - Purpose: Cut operation evaluation (router bits, saw blades)
  - Endpoints: Chipload, heat, deflection, rim speed, kickback

---

## ⚠️ NAMESPACE CONFLICTS

### **1. Directory Conflict**

**CONFLICT:**
- Existing: `services/api/app/calculators/` (RMOS manufacturing calculators)
- New: Would go to `services/api/app/calculators/` (general-purpose calculators)

**PROBLEM:** Same directory, different purposes!

**Existing Purpose:**
- Manufacturing feasibility (chipload, heat, deflection, rim speed)
- RMOS 2.0 integration
- Saw/router operation validation
- Specialized lutherie CAM calculations

**New Calculator Purpose:**
- General-purpose math (basic, scientific, financial)
- Luthier geometry (radius, frets, string tension)
- Woodworking calculations (board feet, miter angles)
- Pure input→output functions (no CAM)

---

### **2. Router Prefix Conflict**

**CONFLICT:**
- Existing: `/calculators` (Wave 8 router)
- New: `/api/calculators` (from `files (41)/calculator_router.py`)

**PROBLEM:** Potential overlap if new router doesn't use `/api` prefix!

**Resolution:** New router already uses `/api/calculators` prefix ✅

---

### **3. Class Name Conflicts**

**EXISTING CLASSES:**
- `CalculatorService` (`calculators/service.py`)
- `SawHeatCalculator` (`saw_lab/calculators/saw_heat.py`)
- `SawDeflectionCalculator` (`saw_lab/calculators/saw_deflection.py`)
- `SawRimSpeedCalculator` (`saw_lab/calculators/saw_rimspeed.py`)
- `SawBiteLoadCalculator` (`saw_lab/calculators/saw_bite_load.py`)
- `SawKickbackCalculator` (`saw_lab/calculators/saw_kickback.py`)
- `FeasibilityCalculatorBundle` (`saw_lab/calculators/__init__.py`)
- `SawCalculatorResult` (`saw_lab/models.py`)
- `CalculatorBundleResponse` (`routers/calculators_router.py`)

**NEW CLASSES (would conflict if not renamed):**
- `BasicCalculator` ❌ (generic name, could conflict with future additions)
- `FractionCalculator` ❌ (generic name)
- `ScientificCalculator` ❌ (generic name)
- `FinancialCalculator` ❌ (generic name)
- `LuthierCalculator` ❌ (specific but still generic)

**RECOMMENDATION:** Prefix all new classes with `LTB` to avoid conflicts

---

## ✅ RESOLUTION STRATEGY

### **Option 1: Separate Directory (RECOMMENDED)**

**New Location:** `services/api/app/ltb_calculators/`

**Structure:**
```
services/api/app/
├── calculators/                    # Existing RMOS manufacturing calcs
│   ├── service.py                  # CalculatorService (RMOS)
│   ├── bracing_calc.py
│   ├── fret_slots_cam.py
│   └── ...
├── ltb_calculators/                # NEW - General-purpose calculators
│   ├── __init__.py
│   ├── basic_calculator.py         # LTBBasicCalculator
│   ├── fraction_calculator.py      # LTBFractionCalculator
│   ├── scientific_calculator.py    # LTBScientificCalculator
│   ├── financial_calculator.py     # LTBFinancialCalculator
│   └── luthier_calculator.py       # LTBLuthierCalculator
└── routers/
    ├── calculators_router.py       # Existing Wave 8 router
    └── ltb_calculator_router.py    # NEW - General calculator router
```

**Pros:**
- ✅ No directory conflicts
- ✅ Clear separation of concerns (RMOS vs general-purpose)
- ✅ Existing code untouched
- ✅ Easy to understand namespace

**Cons:**
- ⚠️ Different directory name than integration guide
- ⚠️ Need to update all import paths in new calculators

---

### **Option 2: Subdirectory Under Existing**

**New Location:** `services/api/app/calculators/ltb/`

**Structure:**
```
services/api/app/calculators/
├── ltb/                            # NEW - General-purpose calculators
│   ├── __init__.py
│   ├── basic_calculator.py
│   ├── fraction_calculator.py
│   ├── scientific_calculator.py
│   ├── financial_calculator.py
│   └── luthier_calculator.py
├── service.py                      # Existing RMOS service
├── bracing_calc.py
└── ...
```

**Pros:**
- ✅ Keeps all calculators under one parent directory
- ✅ Minimal router changes

**Cons:**
- ⚠️ Longer import paths
- ⚠️ Potential confusion (RMOS vs LTB)

---

### **Option 3: Rename Existing Directory (NOT RECOMMENDED)**

**New Location:** `services/api/app/rmos_calculators/` (existing) + `services/api/app/ltb_calculators/` (new)

**Pros:**
- ✅ Clean separation

**Cons:**
- ❌ Breaks all existing imports (high risk)
- ❌ Requires extensive refactoring
- ❌ Not worth the effort

---

## 📝 CLASS RENAMING PLAN

### **Required Changes (All Files)**

**1. `basic_calculator.py`**
```python
# OLD:
class BasicCalculator:
    ...

# NEW:
class LTBBasicCalculator:
    ...
```

**2. `fraction_calculator.py`**
```python
# OLD:
from basic_calculator import BasicCalculator
class FractionCalculator(BasicCalculator):
    ...

# NEW:
from .basic_calculator import LTBBasicCalculator
class LTBFractionCalculator(LTBBasicCalculator):
    ...
```

**3. `scientific_calculator.py`**
```python
# OLD:
from fraction_calculator import FractionCalculator
class ScientificCalculator(FractionCalculator):
    ...

# NEW:
from .fraction_calculator import LTBFractionCalculator
class LTBScientificCalculator(LTBFractionCalculator):
    ...
```

**4. `financial_calculator.py`**
```python
# OLD:
from scientific_calculator import ScientificCalculator
class FinancialCalculator(ScientificCalculator):
    ...

# NEW:
from .scientific_calculator import LTBScientificCalculator
class LTBFinancialCalculator(LTBScientificCalculator):
    ...
```

**5. `luthier_calculator.py`**
```python
# OLD:
from scientific_calculator import ScientificCalculator
class LuthierCalculator(ScientificCalculator):
    ...

# NEW:
from .scientific_calculator import LTBScientificCalculator
class LTBLuthierCalculator(LTBScientificCalculator):
    ...
```

**6. `__init__.py`**
```python
# OLD:
from .basic_calculator import BasicCalculator
from .fraction_calculator import FractionCalculator
from .scientific_calculator import ScientificCalculator
from .financial_calculator import FinancialCalculator
from .luthier_calculator import LuthierCalculator

__all__ = [
    'BasicCalculator',
    'FractionCalculator',
    'ScientificCalculator',
    'FinancialCalculator',
    'LuthierCalculator',
]

# NEW:
from .basic_calculator import LTBBasicCalculator
from .fraction_calculator import LTBFractionCalculator
from .scientific_calculator import LTBScientificCalculator
from .financial_calculator import LTBFinancialCalculator
from .luthier_calculator import LTBLuthierCalculator

__all__ = [
    'LTBBasicCalculator',
    'LTBFractionCalculator',
    'LTBScientificCalculator',
    'LTBFinancialCalculator',
    'LTBLuthierCalculator',
]
```

---

## 🔧 ROUTER RENAMING PLAN

### **`calculator_router.py` → `ltb_calculator_router.py`**

**Location:** `services/api/app/routers/ltb_calculator_router.py`

**Changes Required:**

```python
# OLD (from files (41)/calculator_router.py):
from ..calculators import (
    BasicCalculator,
    FractionCalculator,
    ScientificCalculator,
    FinancialCalculator,
    LuthierCalculator,
)

# NEW:
from ..ltb_calculators import (
    LTBBasicCalculator,
    LTBFractionCalculator,
    LTBScientificCalculator,
    LTBFinancialCalculator,
    LTBLuthierCalculator,
)

# Update all endpoint implementations:
# OLD: calc = ScientificCalculator()
# NEW: calc = LTBScientificCalculator()
```

**Router Prefix:** Keep as `/api/calculators` (no conflict with existing `/calculators`)

---

## 📊 IMPORT PATH SUMMARY

### **Current (ZIP files):**
```python
# In fraction_calculator.py:
from basic_calculator import BasicCalculator  ❌ Absolute import

# In scientific_calculator.py:
from fraction_calculator import FractionCalculator  ❌ Absolute import

# In financial_calculator.py:
from scientific_calculator import ScientificCalculator  ❌ Absolute import

# In luthier_calculator.py:
from scientific_calculator import ScientificCalculator  ❌ Absolute import
```

### **Required (after integration):**
```python
# In ltb_calculators/fraction_calculator.py:
from .basic_calculator import LTBBasicCalculator  ✅ Relative import

# In ltb_calculators/scientific_calculator.py:
from .fraction_calculator import LTBFractionCalculator  ✅ Relative import

# In ltb_calculators/financial_calculator.py:
from .scientific_calculator import LTBScientificCalculator  ✅ Relative import

# In ltb_calculators/luthier_calculator.py:
from .scientific_calculator import LTBScientificCalculator  ✅ Relative import
```

---

## 🎯 RECOMMENDED INTEGRATION PLAN

### **Phase 1: Preparation (30 min)**
1. ✅ Create `services/api/app/ltb_calculators/` directory
2. ✅ Copy 5 calculator files + `__init__.py` from ZIP
3. ✅ Rename all classes: `Calculator` → `LTBCalculator`
4. ✅ Fix all imports (absolute → relative with `.` prefix)
5. ✅ Update `__init__.py` exports

### **Phase 2: Router Integration (30 min)**
6. ✅ Copy `calculator_router.py` → `routers/ltb_calculator_router.py`
7. ✅ Update imports: `from ..ltb_calculators import LTB*`
8. ✅ Update all calculator instantiations in endpoints
9. ✅ Register router in `main.py`

### **Phase 3: Testing (1-2 hours)**
10. ✅ Create pytest suite
11. ✅ Create API integration tests
12. ✅ Run tests and verify

**Total Estimated Time:** 2-3 hours

---

## 📋 DETAILED CHANGE CHECKLIST

### **File: `basic_calculator.py`**
- [ ] Rename `class BasicCalculator` → `class LTBBasicCalculator`
- [ ] Update docstrings (replace "BasicCalculator" with "LTBBasicCalculator")
- [ ] Update return type hints: `'BasicCalculator'` → `'LTBBasicCalculator'`
- [ ] Update CLI function name: `calculator_repl()` → `ltb_basic_calculator_repl()`
- [ ] **Total Changes:** ~25 occurrences

### **File: `fraction_calculator.py`**
- [ ] Change import: `from basic_calculator import BasicCalculator` → `from .basic_calculator import LTBBasicCalculator`
- [ ] Rename `class FractionCalculator(BasicCalculator)` → `class LTBFractionCalculator(LTBBasicCalculator)`
- [ ] Update `super().__init__()` calls (no change needed)
- [ ] Update return type hints: `'FractionCalculator'` → `'LTBFractionCalculator'`
- [ ] Update docstrings
- [ ] **Total Changes:** ~30 occurrences

### **File: `scientific_calculator.py`**
- [ ] Change imports:
  - `from fraction_calculator import FractionCalculator` → `from .fraction_calculator import LTBFractionCalculator`
  - `from basic_calculator import CalculatorState, Operation` → `from .basic_calculator import CalculatorState, Operation`
- [ ] Rename `class ScientificCalculator(FractionCalculator)` → `class LTBScientificCalculator(LTBFractionCalculator)`
- [ ] Update return type hints: `'ScientificCalculator'` → `'LTBScientificCalculator'`
- [ ] Update docstrings
- [ ] **Total Changes:** ~35 occurrences

### **File: `financial_calculator.py`**
- [ ] Change import: `from scientific_calculator import ScientificCalculator` → `from .scientific_calculator import LTBScientificCalculator`
- [ ] Rename `class FinancialCalculator(ScientificCalculator)` → `class LTBFinancialCalculator(LTBScientificCalculator)`
- [ ] Update return type hints: `'FinancialCalculator'` → `'LTBFinancialCalculator'`
- [ ] Update docstrings
- [ ] **Total Changes:** ~30 occurrences

### **File: `luthier_calculator.py`**
- [ ] Change import: `from scientific_calculator import ScientificCalculator` → `from .scientific_calculator import LTBScientificCalculator`
- [ ] Rename `class LuthierCalculator(ScientificCalculator)` → `class LTBLuthierCalculator(LTBScientificCalculator)`
- [ ] Update return type hints: `'LuthierCalculator'` → `'LTBLuthierCalculator'`
- [ ] Update docstrings
- [ ] **Total Changes:** ~25 occurrences

### **File: `__init__.py`**
- [ ] Update all imports (5 classes)
- [ ] Update `__all__` list (5 entries)
- [ ] **Total Changes:** 10 occurrences

### **File: `ltb_calculator_router.py` (new)**
- [ ] Change import path: `from ..calculators import` → `from ..ltb_calculators import`
- [ ] Update all class names (5 calculators × multiple endpoints)
- [ ] **Total Changes:** ~50 occurrences

---

## 🚀 SUCCESS CRITERIA

### **Phase 1: No Import Errors**
```bash
cd services/api
python -c "from app.ltb_calculators import LTBBasicCalculator; print('✓ Basic')"
python -c "from app.ltb_calculators import LTBLuthierCalculator; print('✓ Luthier')"
python -c "from app.ltb_calculators import LTBFinancialCalculator; print('✓ Financial')"
```

### **Phase 2: Router Registration**
```bash
uvicorn app.main:app --reload
# Check: http://localhost:8000/docs
# Verify: /api/calculators/* endpoints visible
```

### **Phase 3: Endpoint Tests**
```bash
curl -X POST http://localhost:8000/api/calculators/evaluate \
  -H "Content-Type: application/json" \
  -d '{"expression": "e^1"}' | jq .result
# Expected: 2.718281828459045
```

---

## ⚠️ MIGRATION IMPACT

### **Impact on Existing Code: ZERO** ✅

**Why no impact?**
1. New directory: `ltb_calculators/` (not touching `calculators/`)
2. New router: `ltb_calculator_router.py` (separate from `calculators_router.py`)
3. New prefix: `/api/calculators` (different from `/calculators`)
4. New class names: `LTB*` prefix (no overlap with existing classes)

**Existing systems continue to work:**
- ✅ RMOS 2.0 Calculator Service (`calculators/service.py`)
- ✅ Wave 8 Router (`routers/calculators_router.py`)
- ✅ Saw Lab calculators (`saw_lab/calculators/`)
- ✅ All existing imports unchanged

---

## 📝 NEXT STEPS

**Ready to proceed?**

1. **APPROVE** this namespace strategy
2. **RUN** automated renaming script (I can generate this)
3. **TEST** imports and endpoints
4. **DEPLOY** to development environment

**Estimated total effort:** 2-3 hours

---

**Status:** ⚠️ Awaiting approval to proceed with automated renaming and integration
