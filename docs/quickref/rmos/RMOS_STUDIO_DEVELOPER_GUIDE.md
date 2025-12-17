# RMOS Studio – Developer Integration & Implementation Guide

**Version:** 1.0  
**Status:** Engineering Document  
**Date:** December 9, 2025

---

## 1. Purpose

This guide provides developers with a clear, rigorous, and implementation-focused handbook for extending, maintaining, and integrating RMOS Studio.

It covers:
- Environment setup
- Project structure
- Coding standards
- Architectural expectations
- Module interaction rules
- Testing strategy
- Performance requirements
- Debugging workflow
- Release lifecycle

This document complements the System Architecture, Algorithms, Data Structures, and API specifications.

---

## 2. Developer Environment

### 2.1 Required Tools

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Primary backend language |
| Node.js + Vue 3 | Frontend implementation |
| JSON Schema Validators | Data structure validation |
| PDF Engine | Operator checklist generation |
| Git | Version control |
| VS Code or JetBrains IDE | Development environment |
| pytest | Automated tests |
| flake8 / black / ruff | Style enforcement |

### 2.2 Recommended Architecture Layout

```
rmos_studio/
│
├── core/                   # Logic & Controllers
│   ├── column_manager.py
│   ├── pattern_engine.py
│   ├── ring_manager.py
│   ├── validator.py
│   └── state.py
│
├── geometry/               # Computational modules
│   ├── segmentation.py
│   ├── slices.py
│   ├── kerf.py
│   ├── angles.py
│   └── geometry_utils.py
│
├── planner/                # Manufacturing layer
│   ├── material_usage.py
│   ├── scrap_model.py
│   ├── volume_calc.py
│   ├── operator_checklist.py
│   └── planner_api.py
│
├── joblog/                 # Logs, revisions, notes
│   ├── planning_log.py
│   ├── execution_log.py
│   ├── revision_history.py
│   ├── operator_notes.py
│   └── joblog_api.py
│
├── export/                 # Serialization & export logic
│   ├── json_export.py
│   ├── pdf_export.py
│   ├── batch_export.py
│   └── export_utils.py
│
├── ui/                     # Optional Vue or other UI layer
│   ├── components/
│   ├── views/
│   └── services/
│
├── docs/                   # Documentation suite
│
├── tests/                  # Automated test suite
│
└── main.py                 # Project entry point
```

---

## 3. Coding Standards

### 3.1 Language Guidelines

**Python backend must adhere to PEP8:**
- Function names: `snake_case`
- Class names: `CamelCase`
- Constants: `UPPER_SNAKE_CASE`
- JSON keys: `lowerCamelCase`

### 3.2 Deterministic Output

All operations must be fully deterministic:
- Same input → same output
- Same seed → same pattern
- No nondeterministic operations unless explicitly part of a seeded pattern generator.

### 3.3 No Shared Mutable State

- Geometry objects (e.g., `Slice`) must be immutable.
- Configuration objects (e.g., `Ring`) mutable only within controlled APIs.

---

## 4. Module Integration Rules

This section describes how modules must interact to maintain system integrity.

### 4.1 UI Layer Rules

- UI never performs geometry computations.
- UI passes validated parameters to API interfaces.
- UI listens for change events and triggers re-rendering.

### 4.2 Application Logic Layer Rules

- Manages state transitions.
- Orchestrates module interactions.
- Performs high-level validation before dispatching geometry requests.
- Converts UI units to mm for geometry.

### 4.3 Geometry Layer Rules

- Only receives mm units.
- Outputs are immutable.
- No side effects.
- Must pass numeric boundary checks.

### 4.4 Planner Layer Rules

- Accepts geometry + strip families.
- Produces material usage & planning summaries.
- Must not modify ring or pattern definitions.

### 4.5 JobLog Layer Rules

- All logs append-only.
- Planning logs generated before slicing.
- Execution logs generated during/after slicing.

### 4.6 Export Layer Rules

- Must serialize only validated data.
- Must generate checksums.
- PDF exports must remain stable across runs.

---

## 5. Validation Requirements

Key developer rules:
- Validate user inputs before work begins.
- Validate geometry before slicing.
- Validate saw batches before export.
- Validate manufacturing plans before generating operator checklists.

All validation returns a `ValidationReport` object:

```python
{
  "valid": true/false,
  "errors": [],      # Block pipeline
  "warnings": []     # Do not block
}
```

**Errors block the pipeline; warnings do not.**

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Minimum coverage:**
- Geometry calculations
- Slice generation
- Kerf compensation
- Angle validation
- Material usage
- Strip family logic

**Run with:**
```powershell
pytest tests/unit/ -v
```

### 6.2 Integration Tests

**Scope:**
- UI → API → Geometry → Planner pipeline
- Export workflows (JSON, PDF, DXF)
- JobLog creation and retrieval

**Run with:**
```powershell
pytest tests/integration/ -v
```

### 6.3 Regression Tests

**Purpose:** Ensure changes don't break existing functionality.

**Golden data:** Store validated outputs in `tests/golden/`

**Run with:**
```powershell
pytest tests/regression/ --compare-golden
```

### 6.4 Performance Tests

**Benchmarks:**
- Ring slicing: < 100ms for 100 slices
- Pattern generation: < 200ms for complex patterns
- Export: < 500ms for PDF generation

**Run with:**
```powershell
pytest tests/performance/ --benchmark
```

---

## 7. API Endpoint Structure

### 7.1 Rosette Manufacturing Endpoints

**Base:** `/api/rmos/`

```
POST   /rmos/rings/create          # Create new ring definition
GET    /rmos/rings/{ring_id}       # Get ring details
PUT    /rmos/rings/{ring_id}       # Update ring
DELETE /rmos/rings/{ring_id}       # Delete ring

POST   /rmos/patterns/generate     # Generate slice pattern
GET    /rmos/patterns/{pattern_id} # Get pattern details

POST   /rmos/plan/material_usage   # Calculate material requirements
POST   /rmos/plan/operator_checklist # Generate PDF checklist

POST   /rmos/export/json           # Export ring + pattern as JSON
POST   /rmos/export/pdf            # Export operator checklist PDF
POST   /rmos/export/dxf            # Export DXF for CAM
```

### 7.2 Request/Response Patterns

**Standard success response:**
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "timestamp": "2025-12-09T10:30:00Z",
    "version": "1.0.0"
  }
}
```

**Standard error response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ring radius must be positive",
    "details": { ... }
  }
}
```

---

## 8. State Management

### 8.1 Ring State

**Ring Lifecycle:**
1. `DRAFT` - Being edited
2. `VALIDATED` - Passed validation
3. `GENERATED` - Pattern generated
4. `PLANNED` - Material usage calculated
5. `EXPORTED` - Ready for manufacturing

### 8.2 Pattern State

**Pattern Lifecycle:**
1. `PENDING` - Awaiting generation
2. `GENERATING` - In progress
3. `COMPLETE` - Generation successful
4. `FAILED` - Generation error

### 8.3 JobLog State

**JobLog Types:**
- `PLANNING` - Pre-manufacturing calculations
- `EXECUTION` - During manufacturing
- `REVISION` - Design changes
- `NOTES` - Operator annotations

---

## 9. Performance Requirements

### 9.1 Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Ring validation | 50ms | 200ms |
| Pattern generation | 100ms | 500ms |
| Material planning | 150ms | 1000ms |
| PDF export | 300ms | 2000ms |
| DXF export | 200ms | 1000ms |

### 9.2 Memory Constraints

- Single ring: < 10 MB
- Pattern with 200 slices: < 50 MB
- PDF export: < 20 MB

### 9.3 Concurrency

- Support 10 concurrent users
- Queue long-running operations (PDF generation)
- Use background tasks for exports

---

## 10. Error Handling Patterns

### 10.1 Validation Errors

```python
from fastapi import HTTPException

if ring_radius <= 0:
    raise HTTPException(
        status_code=400,
        detail="Ring radius must be positive"
    )
```

### 10.2 Geometry Errors

```python
try:
    slices = generate_slices(ring)
except GeometryError as e:
    raise HTTPException(
        status_code=422,
        detail=f"Geometry computation failed: {e}"
    )
```

### 10.3 Export Errors

```python
try:
    pdf_bytes = export_to_pdf(checklist)
except ExportError as e:
    raise HTTPException(
        status_code=500,
        detail=f"PDF export failed: {e}"
    )
```

---

## 11. Debugging Workflow

### 11.1 Development Server

```powershell
cd services/api
uvicorn app.main:app --reload --port 8000
```

### 11.2 Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 11.3 Common Issues

**Issue:** Geometry calculation produces NaN  
**Solution:** Check for division by zero in angle calculations

**Issue:** Pattern generation hangs  
**Solution:** Verify ring parameters don't create infinite loops

**Issue:** PDF export corrupted  
**Solution:** Check for special characters in operator notes

---

## 12. Release Checklist

### 12.1 Pre-Release

- [ ] All tests passing (unit + integration + regression)
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] API changelog generated
- [ ] Migration guide written (if breaking changes)

### 12.2 Release Process

1. Update version in `pyproject.toml`
2. Tag release: `git tag v1.2.0`
3. Build Docker image
4. Deploy to staging
5. Run smoke tests
6. Deploy to production
7. Monitor logs for 24 hours

### 12.3 Post-Release

- [ ] Verify production metrics
- [ ] Update status dashboard
- [ ] Notify team of release
- [ ] Archive release artifacts

---

## 13. Integration with Art Studio

RMOS Studio integrates with Art Studio for rosette design:

**Art Studio → RMOS:**
- Design parameters (radii, widths, patterns)
- Material selections
- Aesthetic constraints

**RMOS → Art Studio:**
- Slice positions (for preview)
- Material usage estimates
- Feasibility scores
- Risk warnings

**API Contract:** See `ART_STUDIO_RMOS_INTEGRATION.md`

---

## 14. Integration with CAM Systems

RMOS Studio exports to CAM systems for CNC machining:

**Export Formats:**
- DXF R12 (Fusion 360, VCarve)
- G-code (GRBL, Mach4, LinuxCNC)
- JSON (custom toolpath processors)

**CAM Workflow:**
1. RMOS generates slice geometry
2. Export to DXF with layers (SLICE_1, SLICE_2, ...)
3. CAM imports and generates toolpaths
4. Post-processor adds headers/footers
5. G-code sent to CNC controller

---

## 15. Database Schema

### 15.1 Rings Table

```sql
CREATE TABLE rings (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255),
    outer_radius_mm FLOAT,
    inner_radius_mm FLOAT,
    column_count INT,
    pattern_type VARCHAR(50),
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 15.2 Patterns Table

```sql
CREATE TABLE patterns (
    id UUID PRIMARY KEY,
    ring_id UUID REFERENCES rings(id),
    slice_count INT,
    generation_time_ms INT,
    geometry_json JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP
);
```

### 15.3 JobLogs Table

```sql
CREATE TABLE joblogs (
    id UUID PRIMARY KEY,
    ring_id UUID REFERENCES rings(id),
    log_type VARCHAR(20),
    content TEXT,
    operator VARCHAR(100),
    created_at TIMESTAMP
);
```

---

## 16. Contributor Guidelines

### 16.1 Code Review Checklist

- [ ] Code follows PEP8 style
- [ ] All functions have docstrings
- [ ] Tests included for new features
- [ ] No breaking changes without migration guide
- [ ] Performance impact assessed

### 16.2 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No new warnings introduced
```

---

## 17. Troubleshooting

### 17.1 Common Development Issues

**Issue:** `ModuleNotFoundError: No module named 'pyclipper'`  
**Solution:** `pip install pyclipper==1.3.0.post5`

**Issue:** Tests fail with "Connection refused"  
**Solution:** Start API server: `uvicorn app.main:app --reload`

**Issue:** PDF export fails with encoding error  
**Solution:** Ensure UTF-8 encoding in all text fields

### 17.2 Production Issues

**Issue:** High memory usage  
**Solution:** Check for memory leaks in pattern generation

**Issue:** Slow API responses  
**Solution:** Enable query profiling, optimize database indexes

**Issue:** Export timeouts  
**Solution:** Move exports to background tasks

---

## 18. References

- [RMOS System Architecture](./RMOS_SYSTEM_ARCHITECTURE.md)
- [RMOS API Specification](./RMOS_API_SPECIFICATION.md)
- [RMOS Validation Rules](./RMOS_VALIDATION.md)
- [Art Studio Integration](./ART_STUDIO_RMOS_INTEGRATION.md)
- [CAM Export Guide](./CAM_EXPORT_GUIDE.md)

---

**Document Status:** ✅ Complete  
**Last Updated:** December 9, 2025  
**Maintainer:** Luthier's Tool Box Team
