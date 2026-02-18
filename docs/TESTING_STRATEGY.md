# Testing Strategy

**Last Updated:** February 2026

This document outlines the testing strategy for Luthier's ToolBox.

---

## Current State

- **Test Count:** 753+ tests
- **Coverage:** ~20% line coverage
- **Target:** 50% line coverage by v2.0

---

## Test Categories

### 1. Unit Tests (Backend)

**Location:** `services/api/tests/`

**Focus areas:**
- Feasibility rules (F001-F029)
- CAM parameter validation
- G-code generation
- Content-addressed storage

**Naming convention:** `test_{module}_{function}.py`

### 2. Integration Tests (Backend)

**Location:** `services/api/tests/`

**Focus areas:**
- API endpoint responses
- RMOS run lifecycle
- Operator pack generation

**Markers:** `@pytest.mark.integration`

### 3. E2E Tests (Backend)

**Location:** `services/api/tests/`

**Focus areas:**
- DXF → G-code golden path
- Run artifact persistence
- Override workflows

**Markers:** `@pytest.mark.e2e`

### 4. Component Tests (Frontend)

**Location:** `packages/client/src/__tests__/` (to be created)

**Focus areas:**
- Vue component rendering
- Store mutations
- SDK endpoint calls

**Framework:** Vitest

### 5. Contract Tests

**Location:** `services/api/tests/`

**Focus areas:**
- JSON Schema validation
- API response shapes
- Breaking change detection

**Naming convention:** `test_{domain}_contract.py`

---

## Priority Test Areas

### P0 - Safety Critical

| Area | Status | Coverage Goal |
|------|--------|---------------|
| Feasibility engine | ✅ Tested | 100% |
| Risk level assignment | ✅ Tested | 100% |
| Override validation | ✅ Tested | 100% |
| Export gating | ✅ Tested | 100% |

### P1 - Core Workflows

| Area | Status | Coverage Goal |
|------|--------|---------------|
| DXF parsing | ✅ Tested | 80% |
| G-code generation | ✅ Tested | 80% |
| Post-processing | ⚠️ Partial | 60% |
| Run artifact storage | ✅ Tested | 80% |

### P2 - UI Components

| Area | Status | Coverage Goal |
|------|--------|---------------|
| RiskBadge | 🔜 Planned | 80% |
| WhyPanel | 🔜 Planned | 80% |
| RmosTooltip | 🔜 Planned | 80% |
| CamParametersForm | 🔜 Planned | 60% |

---

## Running Tests

### Backend (pytest)

```bash
# All tests
cd services/api && .venv/Scripts/python -m pytest

# With coverage
.venv/Scripts/python -m pytest --cov=app --cov-report=html

# Specific marker
.venv/Scripts/python -m pytest -m "not slow"

# Single file
.venv/Scripts/python -m pytest tests/test_feasibility_engine.py -v
```

### Frontend (Vitest)

```bash
# All tests (when implemented)
cd packages/client && npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

---

## Writing New Tests

### Backend Test Template

```python
"""Test {module} {functionality}."""
import pytest
from app.{module} import {function}

class TestFunctionName:
    """Tests for {function}."""

    def test_happy_path(self):
        """Should return expected result for valid input."""
        result = function(valid_input)
        assert result.ok is True

    def test_invalid_input(self):
        """Should handle invalid input gracefully."""
        with pytest.raises(ValueError):
            function(invalid_input)

    @pytest.mark.parametrize("input,expected", [
        (case1_input, case1_expected),
        (case2_input, case2_expected),
    ])
    def test_parametrized_cases(self, input, expected):
        """Should handle various input cases."""
        assert function(input) == expected
```

### Frontend Test Template

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ComponentName from './ComponentName.vue'

describe('ComponentName', () => {
  it('renders correctly', () => {
    const wrapper = mount(ComponentName, {
      props: { /* ... */ }
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('emits event on action', async () => {
    const wrapper = mount(ComponentName)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('action')).toBeTruthy()
  })
})
```

---

## CI Integration

Tests run on every PR via GitHub Actions:

- `api_tests.yml` - Backend pytest suite
- `client_tests.yml` - Frontend Vitest suite (when implemented)
- `contract_tests.yml` - Schema validation

**Coverage gates:**
- PRs must not decrease coverage
- Safety-critical paths require 100% coverage

---

## Next Steps

1. [ ] Set up Vitest for frontend testing
2. [ ] Add component tests for extracted Vue components
3. [ ] Add coverage badges to README
4. [ ] Implement coverage gate in CI

---

*This document is part of the Phase 4 documentation effort.*
