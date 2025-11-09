# Patch N.01: Roughing Post-Processor Integration (Minimal)

**Status:** 🚧 Minimal Implementation  
**Date:** November 5, 2025  
**Dependencies:** Patch N.0 (Smart Post Configurator)

---

## 🎯 Overview

Patch N.01 adds **post-processor awareness to roughing operations**, allowing roughing G-code to be generated with proper headers/footers and token expansion for any configured post-processor.

### **Scope (Minimal)**
- ✅ Wire existing roughing endpoints to post system
- ✅ Token expansion in roughing G-code export
- ✅ Post selection in roughing UI
- ❌ Advanced features (deferred to N.02+)

---

## 📦 What's Being Modified

### **1. Backend: Roughing Router Enhancement**

**File:** `services/api/app/routers/cam_rough_router.py`

**Changes:**
1. Add `post_id` parameter to roughing export endpoints
2. Import token expansion utility
3. Wrap G-code with post headers/footers
4. Expand tokens with roughing context

**Before:**
```python
@router.post("/roughing_gcode")
def export_roughing_gcode(body: RoughingIn):
    # ... generate G-code
    return Response(content=gcode, media_type="text/plain")
```

**After:**
```python
from ..routers.post_router import find_post
from ..util.post_tokens import expand_tokens

@router.post("/roughing_gcode")
def export_roughing_gcode(body: RoughingIn):
    # Generate G-code body
    gcode_body = generate_roughing_moves(...)
    
    # Apply post-processor if specified
    if body.post_id:
        post = find_post(body.post_id)
        if not post:
            raise HTTPException(404, f"Post '{body.post_id}' not found")
        
        # Token context for roughing
        context = {
            'POST_ID': body.post_id,
            'UNITS': body.units or 'mm',
            'TOOL_DIAMETER': body.tool_d,
            'FEED_XY': body.feed_xy,
            'FEED_Z': body.feed_z,
            'MATERIAL': body.material or 'Unknown',
        }
        
        # Expand header/footer
        header = expand_tokens(post.header, context)
        footer = expand_tokens(post.footer, context)
        
        # Assemble final G-code
        gcode = '\n'.join(header) + '\n' + gcode_body + '\n' + '\n'.join(footer)
    else:
        gcode = gcode_body
    
    return Response(content=gcode, media_type="text/plain")
```

---

### **2. Frontend: Add Post Selection to Roughing UI**

**File:** `packages/client/src/components/RoughingPanel.vue` (or similar)

**Changes:**
1. Add post selector dropdown
2. Wire to roughing export API with `post_id`

**Template Addition:**
```vue
<div class="roughing-controls">
  <!-- Existing controls (tool, feeds, etc.) -->
  
  <!-- NEW: Post Processor Selection -->
  <div class="control-group">
    <label>Post Processor:</label>
    <select v-model="selectedPost">
      <option value="">None (raw G-code)</option>
      <option v-for="post in posts" :key="post.id" :value="post.id">
        {{ post.name }} {{ post.builtin ? '(builtin)' : '' }}
      </option>
    </select>
  </div>
  
  <button @click="exportRoughing">Export Roughing G-code</button>
</div>
```

**Script Addition:**
```typescript
import { ref, onMounted } from 'vue';
import { listPosts, type PostListItem } from '@/api/post';

const posts = ref<PostListItem[]>([]);
const selectedPost = ref<string>('GRBL'); // Default to GRBL

async function loadPosts() {
  posts.value = await listPosts();
}

async function exportRoughing() {
  const response = await fetch('/api/cam/roughing_gcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      // ... existing roughing params
      post_id: selectedPost.value || undefined, // Include post ID
    })
  });
  
  const gcode = await response.text();
  downloadFile(gcode, `roughing_${selectedPost.value || 'raw'}.nc`);
}

onMounted(loadPosts);
```

---

## 🧪 Testing

### **Manual Test**

```powershell
# 1. Start backend
cd services/api
uvicorn app.main:app --reload --port 8000

# 2. Test roughing with GRBL post
$body = @{
  paths = @(
    @{type="line"; x1=0; y1=0; x2=100; y2=0}
  )
  tool_d = 6.0
  stepdown = 1.5
  feed_xy = 1200
  feed_z = 400
  post_id = "GRBL"  # NEW: Post processor
  units = "mm"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:8000/api/cam/roughing_gcode" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body `
  -OutFile "roughing_grbl.nc"

# 3. Verify output
Get-Content roughing_grbl.nc | Select-Object -First 10
# Should show:
# G21
# G90
# G17
# (POST=GRBL;UNITS=mm;DATE=...)
# G0 Z5.0000
# ...
```

### **Expected Output Structure**

```gcode
G21
G90
G17
(POST=GRBL;UNITS=mm;DATE=2025-11-05T10:30:00Z)
(Tool: 6.0mm)
(Feed XY: 1200mm/min)
G0 Z5.0000
G0 X0.0000 Y0.0000
G1 Z-1.5000 F400.0
G1 X100.0000 Y0.0000 F1200.0
G0 Z5.0000
M30
(End of program)
```

---

## 📋 Implementation Checklist

### **Backend** (30 min)
- [ ] Modify `cam_rough_router.py` to accept `post_id` parameter
- [ ] Add token expansion import
- [ ] Implement post header/footer wrapping
- [ ] Define roughing token context (TOOL_DIAMETER, FEED_XY, FEED_Z)
- [ ] Test with curl/PowerShell

### **Frontend** (30 min)
- [ ] Add post selector dropdown to roughing UI
- [ ] Import post API client
- [ ] Load posts on component mount
- [ ] Pass `post_id` to roughing export endpoint
- [ ] Update filename with post ID (e.g., `roughing_GRBL.nc`)

### **Testing** (15 min)
- [ ] Test with GRBL post (verify header/footer)
- [ ] Test with Mach4 post (verify different headers)
- [ ] Test without post (verify raw G-code)
- [ ] Test token expansion (check TOOL_DIAMETER in comments)

### **Documentation** (15 min)
- [ ] Update roughing API docs with `post_id` parameter
- [ ] Add usage example to GETTING_STARTED.md
- [ ] Update CAM_CAD_DEVELOPER_HANDOFF.md

---

## 🔧 Code Snippets

### **Backend: RoughingIn Schema Update**

```python
# In services/api/app/routers/cam_rough_router.py

class RoughingIn(BaseModel):
    """Roughing operation input"""
    paths: List[Dict[str, Any]]
    tool_d: float = Field(..., gt=0)
    stepdown: float = Field(..., gt=0)
    feed_xy: float = Field(..., gt=0)
    feed_z: float = Field(..., gt=0)
    safe_z: float = Field(default=5.0)
    units: str = Field(default="mm")
    post_id: Optional[str] = None  # NEW: Post processor ID
    material: Optional[str] = None  # NEW: Material name for tokens
```

### **Backend: Post Wrapping Function**

```python
def wrap_with_post(gcode_body: str, post_id: str, context: Dict[str, Any]) -> str:
    """Wrap G-code with post-processor headers/footers"""
    from ..routers.post_router import find_post
    from ..util.post_tokens import expand_tokens
    
    post = find_post(post_id)
    if not post:
        raise HTTPException(404, f"Post '{post_id}' not found")
    
    # Expand tokens
    header = expand_tokens(post.header, context)
    footer = expand_tokens(post.footer, context)
    
    # Assemble
    return '\n'.join(header) + '\n' + gcode_body + '\n' + '\n'.join(footer)
```

### **Frontend: Post Selector Component**

```vue
<template>
  <div class="post-selector">
    <label>Post Processor:</label>
    <select v-model="selectedPost" @change="$emit('update:modelValue', selectedPost)">
      <option value="">None (raw G-code)</option>
      <option v-for="post in posts" :key="post.id" :value="post.id">
        {{ post.name }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { listPosts, type PostListItem } from '@/api/post';

defineProps<{
  modelValue?: string;
}>();

defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const posts = ref<PostListItem[]>([]);
const selectedPost = ref<string>('');

onMounted(async () => {
  posts.value = await listPosts();
  selectedPost.value = localStorage.getItem('last_post_id') || 'GRBL';
});
</script>
```

---

## 🚀 Usage Example

### **1. Configure Custom Post (Optional)**

```typescript
// Create custom post with roughing-specific comments
await createPost({
  id: 'ROUGHING_OPTIMIZED',
  name: 'Roughing Optimized',
  description: 'Post optimized for roughing operations',
  header: [
    'G21 G90 G17',
    '(Roughing Operation)',
    '(Tool: {{TOOL_DIAMETER}}mm)',
    '(Feed: {{FEED_XY}}mm/min)',
    '(Material: {{MATERIAL}})',
    'G0 Z10.0',  // Extra safe Z for roughing
  ],
  footer: [
    'G0 Z10.0',  // Retract high
    'M5',        // Spindle off
    'M30'
  ],
  tokens: {},
  metadata: {
    controller_family: 'grbl',
    supports_arcs: true
  }
});
```

### **2. Export Roughing with Post**

```typescript
async function exportRoughingWithPost() {
  const response = await fetch('/api/cam/roughing_gcode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paths: geometryPaths.value,
      tool_d: 6.0,
      stepdown: 2.0,
      feed_xy: 1500,
      feed_z: 500,
      safe_z: 5.0,
      units: 'mm',
      post_id: 'ROUGHING_OPTIMIZED',  // Use custom post
      material: 'Softwood_Pine'
    })
  });
  
  const gcode = await response.text();
  downloadFile(gcode, 'roughing_optimized.nc');
}
```

### **3. Verify Output**

```gcode
G21 G90 G17
(Roughing Operation)
(Tool: 6.0mm)
(Feed: 1500mm/min)
(Material: Softwood_Pine)
G0 Z10.0
G0 X0.0000 Y0.0000
G1 Z-2.0000 F500.0
G1 X100.0000 Y0.0000 F1500.0
...
G0 Z10.0
M5
M30
```

---

## 🔍 Integration Points

### **With Existing Systems**

1. **Adaptive Pocketing (Module L)**
   - Add `post_id` to adaptive endpoints
   - Reuse token expansion logic
   - Consistent header/footer format

2. **Machine Profiles (Module M)**
   - Link post to machine profile
   - Auto-select post based on active machine
   - Token: `{{MACHINE_ID}}` from profile

3. **Multi-Post Export (Stage K)**
   - Reuse bundle generation logic
   - Export roughing with multiple posts
   - Single geometry → N roughing NC files

---

## 📚 Related Documentation

- [Patch N.0: Smart Post Configurator Scaffold](./PATCH_N0_SMART_POST_SCAFFOLD.md)
- [Patch N.0: Implementation Guide](./PATCH_N0_IMPLEMENTATION_GUIDE.md)
- [Multi-Post Export System](./PATCH_K_EXPORT_COMPLETE.md)
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md)
- [Machine Profiles Module M](./MACHINE_PROFILES_MODULE_M.md)

---

## 🎯 Success Criteria

✅ **Functional:**
- [ ] Roughing G-code exports with GRBL headers/footers
- [ ] Roughing G-code exports with Mach4 headers/footers
- [ ] Token expansion works (TOOL_DIAMETER, FEED_XY visible in comments)
- [ ] Raw G-code export still works (no post_id)

✅ **Quality:**
- [ ] No breaking changes to existing roughing API
- [ ] Backward compatible (post_id optional)
- [ ] Frontend post selector loads all posts

✅ **Performance:**
- [ ] Token expansion adds < 5ms to export time
- [ ] Post loading cached in frontend

---

## 🚀 Next Steps: N.02 (Future)

### **N.02: Full CAM Post Integration**
- Apply post system to all CAM operations:
  - Finishing
  - Contouring  
  - Drilling
  - V-carve
  - Adaptive pocketing
- Unified post selection UI component
- Post-specific feed overrides
- Post validation for operation compatibility

---

**Status:** 🚧 Minimal Implementation Ready  
**Estimated Effort:** 90 minutes (backend + frontend + testing)  
**Dependencies:** Patch N.0 (post router + token system)  
**Next Action:** Implement backend changes to `cam_rough_router.py`
