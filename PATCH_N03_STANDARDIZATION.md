# Patch N.03: Post-Processor Standardization & Validation

**Status:** 🚧 Specification  
**Date:** November 5, 2025  
**Dependencies:** N.0 (Smart Post Configurator), N.01 (Roughing Integration)

---

## 🎯 Overview

Patch N.03 establishes **standardized post-processor integration patterns** across all CAM operations, ensuring consistency, validation, and maintainability.

### **Goals**
- ✅ Unified post-processor interface for all CAM operations
- ✅ Validation framework for post configurations
- ✅ Testing infrastructure for post-processor outputs
- ✅ Documentation standards for post integration
- ✅ Migration path for existing endpoints

---

## 📦 Core Components

### **1. Standardized Post Interface**

All CAM export endpoints should follow this pattern:

```python
from typing import Optional
from pydantic import BaseModel, Field
from ..util.post_wrapper import wrap_with_post

class CAMOperationIn(BaseModel):
    """Standard CAM operation input with post support"""
    # Operation-specific parameters
    tool_d: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    # ... other operation params
    
    # Standard post-processor fields
    post_id: Optional[str] = Field(None, description="Post-processor ID")
    units: str = Field(default="mm", pattern="^(mm|inch)$")
    material: Optional[str] = Field(None, description="Material name for token expansion")
    machine_id: Optional[str] = Field(None, description="Machine profile ID")
    
@router.post("/operation_gcode")
def export_operation_gcode(body: CAMOperationIn):
    """Export G-code with optional post-processor wrapping"""
    # 1. Generate raw G-code body
    gcode_body = generate_operation_moves(body)
    
    # 2. Apply post-processor if specified
    if body.post_id:
        context = build_token_context(body)
        gcode = wrap_with_post(gcode_body, body.post_id, context)
    else:
        gcode = gcode_body
    
    # 3. Return with appropriate filename
    filename = f"{operation_name}_{body.post_id or 'raw'}.nc"
    return Response(
        content=gcode,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

---

### **2. Unified Post Wrapper Utility**

**File:** `services/api/app/util/post_wrapper.py`

```python
"""
Unified post-processor wrapper for all CAM operations.
Provides consistent token expansion and header/footer injection.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime

def wrap_with_post(
    gcode_body: str,
    post_id: str,
    context: Dict[str, Any],
    validate: bool = True
) -> str:
    """
    Wrap G-code body with post-processor headers and footers.
    
    Args:
        gcode_body: Raw G-code moves (no headers/footers)
        post_id: Post-processor identifier
        context: Token expansion context
        validate: Validate post configuration before use
    
    Returns:
        Complete G-code with headers/footers
    
    Raises:
        HTTPException: If post not found or validation fails
    """
    from ..routers.post_router import find_post
    from .post_tokens import expand_tokens, validate_token_context
    
    # Load post configuration
    post = find_post(post_id)
    if not post:
        raise HTTPException(404, f"Post-processor '{post_id}' not found")
    
    # Validate context if requested
    if validate:
        validation = validate_token_context(context, post)
        if validation['errors']:
            raise HTTPException(400, f"Token validation failed: {validation['errors']}")
    
    # Add standard tokens
    context.setdefault('POST_ID', post_id)
    context.setdefault('DATE', datetime.utcnow().isoformat() + 'Z')
    
    # Expand header and footer
    header = expand_tokens(post.header, context)
    footer = expand_tokens(post.footer, context)
    
    # Assemble final G-code
    return '\n'.join([
        *header,
        '',  # blank line after header
        gcode_body.strip(),
        '',  # blank line before footer
        *footer
    ])


def build_token_context(operation_params: Any) -> Dict[str, Any]:
    """
    Build standard token context from operation parameters.
    
    Args:
        operation_params: Pydantic model with operation parameters
    
    Returns:
        Dictionary of token values
    """
    context = {}
    
    # Standard mappings
    if hasattr(operation_params, 'units'):
        context['UNITS'] = operation_params.units
    
    if hasattr(operation_params, 'tool_d'):
        context['TOOL_DIAMETER'] = operation_params.tool_d
    
    if hasattr(operation_params, 'feed_xy'):
        context['FEED_XY'] = operation_params.feed_xy
    
    if hasattr(operation_params, 'feed_z'):
        context['FEED_Z'] = operation_params.feed_z
    
    if hasattr(operation_params, 'material'):
        context['MATERIAL'] = operation_params.material or 'Unknown'
    
    if hasattr(operation_params, 'machine_id'):
        context['MACHINE_ID'] = operation_params.machine_id or 'Generic'
    
    # Optional spindle speed
    if hasattr(operation_params, 'spindle_rpm'):
        context['SPINDLE_RPM'] = operation_params.spindle_rpm
    
    return context


def validate_post_for_operation(
    post_id: str,
    operation_type: str,
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate post-processor compatibility with operation.
    
    Args:
        post_id: Post-processor identifier
        operation_type: Operation type (roughing, finishing, pocket, etc.)
        requirements: Operation-specific requirements (e.g., arcs needed)
    
    Returns:
        Validation result with warnings/errors
    """
    from ..routers.post_router import find_post
    
    result = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    post = find_post(post_id)
    if not post:
        result['valid'] = False
        result['errors'].append(f"Post '{post_id}' not found")
        return result
    
    # Check arc support if required
    if requirements.get('requires_arcs'):
        if post.metadata and not post.metadata.supports_arcs:
            result['warnings'].append(
                f"Post '{post_id}' may not support arcs (G2/G3)"
            )
    
    # Check tool changer if required
    if requirements.get('requires_tool_changer'):
        if post.metadata and not post.metadata.has_tool_changer:
            result['warnings'].append(
                f"Post '{post_id}' does not support tool changes"
            )
    
    # Check line length for complex operations
    if requirements.get('max_line_length'):
        req_length = requirements['max_line_length']
        if post.metadata and post.metadata.max_line_length < req_length:
            result['warnings'].append(
                f"Post '{post_id}' max line length ({post.metadata.max_line_length}) "
                f"< operation requirement ({req_length})"
            )
    
    return result
```

---

### **3. Enhanced Token Validation**

**File:** `services/api/app/util/post_tokens.py` (additions)

```python
def validate_token_context(context: Dict[str, Any], post: PostConfig) -> Dict[str, Any]:
    """
    Validate token context against post configuration.
    
    Args:
        context: Token values to validate
        post: Post configuration
    
    Returns:
        Validation result with warnings/errors
    """
    result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'missing_tokens': []
    }
    
    import re
    
    # Find all tokens in header/footer
    pattern = r'\{\{([A-Z_]+)\}\}'
    required_tokens = set()
    
    for line in post.header + post.footer:
        matches = re.findall(pattern, line)
        required_tokens.update(matches)
    
    # Check which required tokens are missing from context
    for token_name in required_tokens:
        if token_name not in context and token_name not in DEFAULT_TOKENS:
            result['missing_tokens'].append(token_name)
            result['warnings'].append(
                f"Token '{token_name}' required by post but not in context, "
                f"will use default or leave unexpanded"
            )
    
    # Check for invalid token values
    if 'UNITS' in context:
        if context['UNITS'] not in ['mm', 'inch']:
            result['errors'].append(f"Invalid UNITS value: {context['UNITS']}")
            result['valid'] = False
    
    if 'TOOL_DIAMETER' in context:
        try:
            td = float(context['TOOL_DIAMETER'])
            if td <= 0:
                result['errors'].append("TOOL_DIAMETER must be positive")
                result['valid'] = False
        except (ValueError, TypeError):
            result['errors'].append(f"Invalid TOOL_DIAMETER: {context['TOOL_DIAMETER']}")
            result['valid'] = False
    
    return result


def get_token_usage_report(post_id: str) -> Dict[str, Any]:
    """
    Generate report of token usage in a post configuration.
    
    Args:
        post_id: Post-processor identifier
    
    Returns:
        Report with token usage details
    """
    from ..routers.post_router import find_post
    import re
    
    post = find_post(post_id)
    if not post:
        return {'error': f"Post '{post_id}' not found"}
    
    pattern = r'\{\{([A-Z_]+)\}\}'
    header_tokens = []
    footer_tokens = []
    
    for line in post.header:
        header_tokens.extend(re.findall(pattern, line))
    
    for line in post.footer:
        footer_tokens.extend(re.findall(pattern, line))
    
    all_tokens = set(header_tokens + footer_tokens)
    
    return {
        'post_id': post_id,
        'post_name': post.name,
        'total_tokens': len(all_tokens),
        'header_tokens': list(set(header_tokens)),
        'footer_tokens': list(set(footer_tokens)),
        'all_tokens': sorted(all_tokens),
        'standard_tokens': [t for t in all_tokens if t in TOKEN_REGISTRY],
        'custom_tokens': [t for t in all_tokens if t not in TOKEN_REGISTRY]
    }
```

---

### **4. Testing Framework**

**File:** `tests/test_post_integration.py`

```python
"""
Integration tests for post-processor system across all CAM operations.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test data
STANDARD_POSTS = ['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO']

ROUGHING_PAYLOAD = {
    'paths': [{'type': 'line', 'x1': 0, 'y1': 0, 'x2': 100, 'y2': 0}],
    'tool_d': 6.0,
    'stepdown': 1.5,
    'feed_xy': 1200,
    'feed_z': 400,
    'units': 'mm'
}


@pytest.mark.parametrize('post_id', STANDARD_POSTS)
def test_roughing_with_all_posts(post_id):
    """Test roughing export with each builtin post"""
    payload = {**ROUGHING_PAYLOAD, 'post_id': post_id}
    
    response = client.post('/api/cam/roughing_gcode', json=payload)
    assert response.status_code == 200
    
    gcode = response.text
    
    # Verify post-specific markers
    assert f'POST={post_id}' in gcode or post_id in gcode
    
    # Verify units command
    if payload['units'] == 'mm':
        assert 'G21' in gcode
    else:
        assert 'G20' in gcode
    
    # Verify program end
    assert 'M30' in gcode or 'M02' in gcode


def test_roughing_without_post():
    """Test roughing export with no post (raw G-code)"""
    payload = {**ROUGHING_PAYLOAD, 'post_id': None}
    
    response = client.post('/api/cam/roughing_gcode', json=payload)
    assert response.status_code == 200
    
    gcode = response.text
    
    # Should NOT have post headers
    assert 'POST=' not in gcode
    assert gcode.startswith('G0') or gcode.startswith('G1')


def test_invalid_post_returns_404():
    """Test that invalid post ID returns 404"""
    payload = {**ROUGHING_PAYLOAD, 'post_id': 'INVALID_POST'}
    
    response = client.post('/api/cam/roughing_gcode', json=payload)
    assert response.status_code == 404
    assert 'not found' in response.json()['detail'].lower()


def test_token_expansion_in_output():
    """Test that tokens are properly expanded"""
    payload = {
        **ROUGHING_PAYLOAD,
        'post_id': 'GRBL',
        'tool_d': 6.5,
        'material': 'Hardwood_Maple'
    }
    
    response = client.post('/api/cam/roughing_gcode', json=payload)
    assert response.status_code == 200
    
    gcode = response.text
    
    # Check for expanded tokens (not literal {{TOKEN}})
    assert '{{' not in gcode
    assert '}}' not in gcode
    
    # Check for actual values
    if 'Tool:' in gcode or 'TOOL' in gcode:
        assert '6.5' in gcode
    
    if 'Material:' in gcode or 'MATERIAL' in gcode:
        assert 'Hardwood_Maple' in gcode


def test_post_validation_endpoint():
    """Test post validation before export"""
    # Valid post
    response = client.post('/api/posts/validate', json={
        'id': 'TEST_VALID',
        'name': 'Test',
        'header': ['G90', 'G21'],
        'footer': ['M30']
    })
    assert response.status_code == 200
    result = response.json()
    assert result['valid'] == True
    
    # Invalid post (empty header)
    response = client.post('/api/posts/validate', json={
        'id': 'TEST_INVALID',
        'name': 'Test',
        'header': [],
        'footer': ['M30']
    })
    assert response.status_code == 200
    result = response.json()
    assert result['valid'] == False
    assert len(result['errors']) > 0


@pytest.mark.parametrize('operation,endpoint', [
    ('roughing', '/api/cam/roughing_gcode'),
    ('finishing', '/api/cam/finishing_gcode'),
    ('pocket', '/api/cam/pocket/adaptive/gcode'),
    ('vcarve', '/api/cam_vcarve/export_gcode'),
])
def test_post_integration_all_operations(operation, endpoint):
    """Test that all CAM operations support post integration"""
    # This will be implemented as operations are migrated
    # For now, just verify endpoint exists
    pass
```

---

### **5. Documentation Standard**

**Template for CAM Operation Documentation:**

```markdown
## Post-Processor Integration

### Supported Posts
All 5 builtin post-processors are supported:
- GRBL 1.1
- Mach4
- LinuxCNC (EMC2)
- PathPilot (Tormach)
- MASSO G3

Custom posts can be created via the Post Manager.

### Token Context
This operation provides the following tokens:

| Token | Source | Example |
|-------|--------|---------|
| `POST_ID` | Auto | `GRBL` |
| `UNITS` | `units` param | `mm` |
| `DATE` | Auto (UTC) | `2025-11-05T10:30:00Z` |
| `TOOL_DIAMETER` | `tool_d` param | `6.0` |
| `FEED_XY` | `feed_xy` param | `1200` |
| `FEED_Z` | `feed_z` param | `400` |
| `MATERIAL` | `material` param | `Hardwood_Maple` |
| `MACHINE_ID` | `machine_id` param | `CNC3018_PRO` |

### Requirements
- **Arcs:** [Yes/No] - Operation uses G2/G3 arc commands
- **Tool Changes:** [Yes/No] - Operation requires tool changer
- **Max Line Length:** [Number] - Longest G-code line generated

### Usage Example
```python
response = await fetch('/api/cam/operation_gcode', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    // Operation params...
    post_id: 'GRBL',
    units: 'mm',
    material: 'Hardwood_Maple'
  })
})
```

### Output Format
```gcode
G21
G90
G17
(POST=GRBL;UNITS=mm;DATE=2025-11-05T...)
(Tool: 6.0mm)
G0 Z5.0000
...
M30
```
```

---

## 📋 Migration Checklist

### **CAM Operations to Migrate**

- [x] **Roughing** (N.01 - Complete)
- [ ] **Finishing**
- [ ] **Contouring**
- [ ] **Adaptive Pocketing** (Stages L.0-L.3)
- [ ] **V-Carve** (Art Studio)
- [ ] **Drilling**
- [ ] **Bi-Arc/Curve Export**

### **For Each Operation:**

1. **Schema Update**
   - [ ] Add `post_id: Optional[str]` field
   - [ ] Add `material: Optional[str]` field
   - [ ] Add `machine_id: Optional[str]` field
   - [ ] Ensure `units` field exists

2. **Router Update**
   - [ ] Import `wrap_with_post` utility
   - [ ] Import `build_token_context` utility
   - [ ] Add post wrapping logic to export endpoint
   - [ ] Update filename generation

3. **Testing**
   - [ ] Add pytest test with all 5 builtin posts
   - [ ] Add test for raw G-code (no post)
   - [ ] Add test for invalid post (404)
   - [ ] Add test for token expansion
   - [ ] Add smoke test script

4. **Documentation**
   - [ ] Add "Post-Processor Integration" section
   - [ ] Document token context
   - [ ] Document operation requirements
   - [ ] Add usage example

5. **Frontend**
   - [ ] Add post selector to UI
   - [ ] Wire to export endpoint with `post_id`
   - [ ] Update filename display
   - [ ] Add post preview (optional)

---

## 🧪 Testing Strategy

### **Unit Tests** (`tests/test_post_wrapper.py`)
```python
def test_wrap_with_post_basic():
    """Test basic post wrapping"""
    gcode_body = "G0 Z5\nG1 X10 Y10 F1200\nM30"
    context = {'UNITS': 'mm', 'TOOL_DIAMETER': 6.0}
    
    result = wrap_with_post(gcode_body, 'GRBL', context)
    
    assert 'G21' in result  # mm units
    assert 'G90' in result  # absolute mode
    assert 'POST=GRBL' in result
    assert gcode_body in result

def test_wrap_with_invalid_post():
    """Test wrapping with invalid post raises 404"""
    with pytest.raises(HTTPException) as exc:
        wrap_with_post("G0 Z5", 'INVALID', {})
    
    assert exc.value.status_code == 404

def test_token_context_builder():
    """Test token context building from params"""
    class Params:
        tool_d = 6.0
        feed_xy = 1200
        feed_z = 400
        units = 'mm'
        material = 'Pine'
    
    context = build_token_context(Params())
    
    assert context['TOOL_DIAMETER'] == 6.0
    assert context['FEED_XY'] == 1200
    assert context['UNITS'] == 'mm'
    assert context['MATERIAL'] == 'Pine'
```

### **Integration Tests** (`tests/test_post_integration.py`)
- Test each CAM operation with all 5 builtin posts
- Test raw G-code output (no post)
- Test invalid post returns 404
- Test token expansion in output
- Test post validation before export

### **Smoke Tests** (`scripts/smoke_posts_all_ops.py`)
```python
"""Smoke test for post integration across all operations"""

OPERATIONS = [
    ('roughing', '/api/cam/roughing_gcode', ROUGHING_PAYLOAD),
    ('finishing', '/api/cam/finishing_gcode', FINISHING_PAYLOAD),
    ('pocket', '/api/cam/pocket/adaptive/gcode', POCKET_PAYLOAD),
]

for op_name, endpoint, payload in OPERATIONS:
    for post_id in ['GRBL', 'Mach4', 'LinuxCNC']:
        print(f"Testing {op_name} with {post_id}...")
        response = requests.post(
            f"http://localhost:8000{endpoint}",
            json={**payload, 'post_id': post_id}
        )
        assert response.status_code == 200
        assert f'POST={post_id}' in response.text
        print(f"  ✓ {op_name} + {post_id}")
```

---

## 🔧 Configuration Examples

### **Example 1: Custom Post for Roughing**

```json
{
  "id": "ROUGHING_HEAVY",
  "name": "Heavy Roughing Post",
  "description": "Optimized for aggressive material removal",
  "header": [
    "G21 G90 G17",
    "(Heavy Roughing - {{MATERIAL}})",
    "(Tool: {{TOOL_DIAMETER}}mm)",
    "(Feed: {{FEED_XY}}mm/min)",
    "G0 Z15.0",
    "M3 S18000"
  ],
  "footer": [
    "G0 Z15.0",
    "M5",
    "M30",
    "(Roughing time estimate: {{TIME_ESTIMATE}})"
  ],
  "metadata": {
    "controller_family": "grbl",
    "supports_arcs": true,
    "optimized_for": "roughing"
  }
}
```

### **Example 2: Validation Before Export**

```typescript
async function exportWithValidation(operation: string, params: any) {
  // 1. Validate post compatibility
  const validation = await validatePostForOperation(
    params.post_id,
    operation,
    { requires_arcs: true }
  );
  
  if (validation.errors.length > 0) {
    alert(`Post validation failed: ${validation.errors.join(', ')}`);
    return;
  }
  
  if (validation.warnings.length > 0) {
    const proceed = confirm(
      `Warnings:\n${validation.warnings.join('\n')}\n\nProceed anyway?`
    );
    if (!proceed) return;
  }
  
  // 2. Export with post
  const response = await fetch(`/api/cam/${operation}_gcode`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(params)
  });
  
  const gcode = await response.text();
  downloadFile(gcode, `${operation}_${params.post_id}.nc`);
}
```

---

## 🚀 Rollout Plan

### **Phase 1: Core Infrastructure** (Complete)
- [x] N.0: Smart Post Configurator
- [x] N.01: Roughing Integration
- [x] N.03: Standardization (this patch)

### **Phase 2: Operation Migration** (2-3 weeks)
- [ ] Week 1: Finishing + Contouring
- [ ] Week 2: Adaptive Pocketing (L.0-L.3)
- [ ] Week 3: V-Carve + Drilling + Bi-Arc

### **Phase 3: Advanced Features** (1-2 weeks)
- [ ] Post validation UI
- [ ] Token usage reports
- [ ] Post testing framework
- [ ] Performance profiling

### **Phase 4: Documentation & Training** (1 week)
- [ ] Complete API documentation
- [ ] User guide for custom posts
- [ ] Video tutorials
- [ ] Migration guide for existing workflows

---

## 📊 Success Metrics

### **Code Quality**
- ✅ 100% of CAM operations support post integration
- ✅ All operations use standardized interface
- ✅ >90% test coverage for post system
- ✅ Zero duplicate post-wrapping logic

### **User Experience**
- ✅ Single post selector component (reusable)
- ✅ Consistent filename patterns
- ✅ Clear validation error messages
- ✅ <100ms overhead for post wrapping

### **Maintainability**
- ✅ Single source of truth (`post_wrapper.py`)
- ✅ Documented token expansion rules
- ✅ Automated testing for all posts
- ✅ Migration checklist for new operations

---

## 📚 Related Documentation

- [Patch N.0: Smart Post Configurator](./PATCH_N0_SMART_POST_SCAFFOLD.md)
- [Patch N.0: Implementation Guide](./PATCH_N0_IMPLEMENTATION_GUIDE.md)
- [Patch N.01: Roughing Integration](./PATCH_N01_ROUGHING_POST_MIN.md)
- [Multi-Post Export System (Stage K)](./PATCH_K_EXPORT_COMPLETE.md)
- [CAM/CAD Developer Handoff](./CAM_CAD_DEVELOPER_HANDOFF.md)

---

## 🎯 Next Steps

1. **Implement `post_wrapper.py`** (core utility)
2. **Migrate Finishing operation** (apply standard pattern)
3. **Migrate Contouring operation** (apply standard pattern)
4. **Create integration test suite** (all operations × all posts)
5. **Update documentation** (API reference + usage examples)

---

**Status:** 🚧 Specification Complete — Ready for Implementation  
**Estimated Effort:** 3-4 weeks (all operations + testing + docs)  
**Priority:** High (enables consistent post support across entire CAM system)  
**Next Action:** Implement `post_wrapper.py` utility module
