# Test Coverage Quick Reference

**Goal:** 80% test coverage (P3.1 - A_N roadmap requirement)  
**Status:** Infrastructure complete, ready for execution

---

## 🚀 Quick Commands

```powershell
# Activate environment
cd services/api
.\.venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_geometry_router.py -v

# Run specific test class
pytest tests/test_adaptive_router.py::TestAdaptivePocketPlanning -v

# Run specific test
pytest tests/test_bridge_router.py::TestBridgeHealth::test_health_check -v

# Run with coverage
pytest tests/ --cov=app.routers --cov-report=term-missing

# Run only router tests
pytest -m router

# Run only integration tests
pytest -m integration

# Run fast tests only (skip slow)
pytest -m "not slow"

# Generate HTML coverage report
pytest tests/ --cov=app.routers --cov-report=html
start htmlcov/index.html
```

---

## 📊 Test Markers

Use markers to run test subsets:

```python
@pytest.mark.router      # Router endpoint tests
@pytest.mark.integration # Integration tests
@pytest.mark.unit        # Unit tests
@pytest.mark.smoke       # Smoke tests
@pytest.mark.slow        # Slow-running tests
@pytest.mark.geometry    # Geometry-related
@pytest.mark.adaptive    # Adaptive pocketing
@pytest.mark.bridge      # Bridge calculator
@pytest.mark.helical     # Helical ramping
@pytest.mark.cam         # CAM operations
@pytest.mark.export      # Export functionality
```

**Examples:**
```powershell
pytest -m "router and not slow"  # Fast router tests
pytest -m "integration or smoke" # Integration + smoke
pytest -m adaptive               # All adaptive tests
```

---

## 🧪 Adding New Tests

### **1. Use Existing Fixtures**

```python
def test_my_feature(api_client, sample_geometry_simple):
    response = api_client.post("/my/endpoint", json=sample_geometry_simple)
    assert response.status_code == 200
```

### **2. Available Fixtures**

| Fixture | Type | Description |
|---------|------|-------------|
| `api_client` | TestClient | FastAPI test client |
| `sample_geometry_simple` | dict | 100×60mm rectangle |
| `sample_geometry_with_arcs` | dict | Geometry with arcs |
| `sample_pocket_loops` | list | Pocket with island |
| `sample_bridge_params` | dict | Bridge calculator params |
| `sample_helical_params` | dict | Helical ramping params |
| `temp_dxf_file` | Path | Auto-cleanup DXF file |
| `temp_nc_file` | Path | Auto-cleanup NC file |
| `mock_post_config` | dict | GRBL post config |

### **3. Test Template**

```python
import pytest

@pytest.mark.router
@pytest.mark.myfeature
class TestMyFeature:
    """Test my feature."""
    
    def test_basic_case(self, api_client):
        """Test basic functionality."""
        response = api_client.post("/my/endpoint", json={
            "param1": "value1",
            "param2": 123
        })
        
        assert response.status_code == 200
        result = response.json()
        assert "expected_field" in result
        
    def test_error_case(self, api_client):
        """Test error handling."""
        response = api_client.post("/my/endpoint", json={
            "param1": "invalid"
        })
        
        assert response.status_code == 400
```

---

## 📝 Common Assertions

### **Status Codes**
```python
assert response.status_code == 200  # Success
assert response.status_code == 400  # Bad request
assert response.status_code == 422  # Validation error
assert response.status_code == 404  # Not found
assert response.status_code in [200, 201]  # Multiple acceptable
```

### **Response Structure**
```python
result = response.json()
assert "field" in result
assert result["field"] == expected_value
assert len(result["list"]) > 0
assert isinstance(result["value"], int)
```

### **G-code Validation**
```python
from conftest import assert_valid_gcode, assert_valid_moves

gcode = response.text
assert_valid_gcode(gcode)  # Has G commands
assert "G21" in gcode  # mm mode
assert "M30" in gcode  # Program end

moves = response.json()["moves"]
assert_valid_moves(moves)  # Has code, coordinates
```

### **Geometry Validation**
```python
from conftest import assert_valid_geometry

geom = response.json()
assert_valid_geometry(geom)  # Has units, paths
assert geom["units"] in ["mm", "inch"]
assert len(geom["paths"]) > 0
```

---

## 🐛 Debugging Tests

### **Run with More Detail**
```powershell
pytest tests/test_my_test.py -vv  # Very verbose
pytest tests/test_my_test.py -s   # Show print statements
pytest tests/test_my_test.py --tb=long  # Full tracebacks
```

### **Print Response Details**
```python
def test_debug(self, api_client):
    response = api_client.post("/endpoint", json={"data": "test"})
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Body: {response.text}")
    assert response.status_code == 200
```

### **Use pytest-mock**
```python
def test_with_mock(self, api_client, mocker):
    mock_func = mocker.patch('app.routers.my_router.expensive_operation')
    mock_func.return_value = {"mock": "data"}
    
    response = api_client.post("/endpoint")
    assert mock_func.called
```

---

## 📊 Coverage Analysis

### **View Coverage Report**
```powershell
# Generate HTML report
pytest tests/ --cov=app.routers --cov-report=html

# Open in browser
start htmlcov/index.html
```

### **Find Uncovered Lines**
```powershell
# Show missing lines
pytest --cov=app.routers --cov-report=term-missing

# Output:
# app/routers/geometry_router.py  85%   Missing: 123-125, 200-205
```

### **Coverage by File**
```powershell
pytest --cov=app.routers.geometry_router --cov-report=term
```

---

## 🔧 Troubleshooting

### **Problem: ModuleNotFoundError: No module named 'app'**
**Solution:** Run from `services/api` directory:
```powershell
cd services/api
pytest tests/
```

### **Problem: Tests hang or timeout**
**Solution:** Check for background processes:
```powershell
pytest -m "not slow"  # Skip slow tests
pytest -k "test_quick"  # Run specific fast tests
```

### **Problem: Coverage too low**
**Solution:** Run specific router tests:
```powershell
pytest tests/test_geometry_router.py --cov=app.routers.geometry_router
```

### **Problem: Fixture not found**
**Solution:** Check conftest.py is in tests/ directory:
```powershell
ls tests/conftest.py  # Should exist
```

---

## 📈 Target Coverage Goals

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| geometry_router.py | 40% | 85% | ⭐⭐⭐⭐⭐ |
| adaptive_router.py | 40% | 90% | ⭐⭐⭐⭐⭐ |
| bridge_router.py | 40% | 80% | ⭐⭐⭐⭐⭐ |
| cam_helical_v161_router.py | 40% | 75% | ⭐⭐⭐⭐ |
| **Overall** | **40%** | **80%** | **A_N Roadmap** |

---

## ✅ Test Quality Checklist

When adding new tests, ensure:
- [ ] Test name clearly describes what is tested
- [ ] Uses appropriate fixtures
- [ ] Has docstring explaining purpose
- [ ] Tests both success and error cases
- [ ] Assertions are specific and meaningful
- [ ] Marked with relevant pytest markers
- [ ] Fast execution (< 1 second per test)
- [ ] No side effects (database, filesystem, network)
- [ ] Independent (can run in any order)

---

## 📚 Further Reading

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [A_N_BUILD_ROADMAP.md](../A_N_BUILD_ROADMAP.md) - P3.1 Test Coverage requirements

---

**Last Updated:** November 17, 2025  
**Status:** ✅ Infrastructure complete, ready for test execution  
**Next Step:** Fix endpoint signatures and run full test suite
