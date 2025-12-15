# Extension Validation Feature - Quick Reference

**Status:** ✅ Complete  
**Component:** CompareLabView  
**Date:** November 28, 2025

---

## 🎯 Overview

The **Extension Validation** feature automatically detects when a filename template's extension doesn't match the selected export format and provides one-click fixes to resolve the mismatch.

**Problem Solved:**
- User sets template to `comparison_{date}.svg` but selects PNG format
- Export fails or produces unexpected results
- User confusion about which takes precedence (template vs format)

**Solution:**
- Real-time mismatch detection via computed property
- Clear warning banner with visual feedback
- Two auto-fix buttons to resolve conflict instantly
- Template and format changes persist to localStorage

---

## 🔍 Mismatch Detection Logic

### **When Warnings Appear**

```typescript
// Template: comparison_{date}.svg
// Format: PNG
// Result: ⚠️ Warning (template has .svg, format is png)

// Template: output_{timestamp}.png
// Format: CSV  
// Result: ⚠️ Warning (template has .png, format is csv)

// Template: metrics.csv
// Format: SVG
// Result: ⚠️ Warning (template has .csv, format is svg)
```

### **When Warnings DO NOT Appear**

```typescript
// Template: comparison_{date}.svg
// Format: SVG
// Result: ✅ No warning (match)

// Template: output_{timestamp}  (no extension)
// Format: PNG
// Result: ✅ No warning (no extension = OK)

// Template: {preset}__{date}  (no extension)
// Format: CSV
// Result: ✅ No warning (exportFilename adds correct extension)
```

### **Extension Extraction Rules**

1. **Tokens ignored**: `{preset.svg}` does NOT count as .svg extension
2. **Last extension wins**: `my.file.name.svg` → detects `.svg`
3. **Case insensitive**: `.SVG`, `.svg`, `.Svg` all treated as `svg`
4. **Valid extensions**: `svg`, `png`, `csv`, `dxf`, `nc`, `gcode`
5. **Invalid extensions**: `txt`, `jpg`, `json` → trigger warning

---

## 🛠️ Auto-Fix Actions

### **Fix 1: Change Template Extension**

**Button:** "Fix Template → .[format]"

**Action:**
```typescript
// Before: comparison_{date}.svg  (Format: PNG)
// After:  comparison_{date}.png  (Format: PNG)
// Result: Warning disappears
```

**Implementation:**
```typescript
function fixTemplateExtension() {
  const regex = new RegExp(`\\.${templateExt}$`, 'i')
  filenameTemplate.value = filenameTemplate.value.replace(regex, `.${expectedExt}`)
}
```

### **Fix 2: Change Export Format**

**Button:** "Fix Format → [template_ext]"

**Action:**
```typescript
// Before: output.svg  (Format: PNG)
// After:  output.svg  (Format: SVG)
// Result: Warning disappears
```

**Implementation:**
```typescript
function fixExportFormat() {
  const validFormat = extensionMismatch.value.templateExt as 'svg' | 'png' | 'csv'
  if (['svg', 'png', 'csv'].includes(validFormat)) {
    exportFormat.value = validFormat
  }
}
```

---

## 💾 localStorage Integration

Extension validation integrates with existing state persistence:

```typescript
// Keys stored
STORAGE_KEYS = {
  TEMPLATE: 'comparelab.filenameTemplate',  // e.g., "output_{date}.svg"
  FORMAT: 'comparelab.exportFormat'         // e.g., "png"
}

// On page load
loadExportState()  // Restores template and format
// If mismatch: Warning appears automatically

// On template/format change
watch([filenameTemplate, exportFormat], saveExportState)
// Warning updates reactively via computed property
```

---

## 🎨 UI Components

### **Warning Banner**

```vue
<div v-if="extensionMismatch" class="extension-warning">
  <div class="warning-banner">
    <span class="warning-icon">⚠️</span>
    <div class="warning-content">
      <strong>Extension Mismatch Detected</strong>
      <p>
        Template has <code>.{{ extensionMismatch.templateExt }}</code> extension 
        but export format is <strong>{{ extensionMismatch.expectedExt.toUpperCase() }}</strong>
      </p>
    </div>
  </div>
  <div class="warning-actions">
    <button @click="fixTemplateExtension">
      Fix Template → .{{ extensionMismatch.expectedExt }}
    </button>
    <button @click="fixExportFormat" class="secondary">
      Fix Format → {{ extensionMismatch.templateExt.toUpperCase() }}
    </button>
  </div>
</div>
```

### **Visual Design**

- **Background:** Amber (`#fef3c7`) with orange border (`#f59e0b`)
- **Icon:** ⚠️ warning emoji
- **Typography:** Strong heading + descriptive text
- **Buttons:** Primary (Fix Template) + Secondary (Fix Format)
- **Hover:** Subtle lift effect on buttons

---

## 🧪 Testing Scenarios

### **Scenario 1: SVG Template, PNG Format**

```typescript
// Setup
filenameTemplate.value = '{preset}__{date}.svg'
exportFormat.value = 'png'

// Expected
extensionMismatch.value = {
  templateExt: 'svg',
  expectedExt: 'png',
  hasConflict: true
}

// Action: Click "Fix Template → .png"
// Result: Template becomes '{preset}__{date}.png'
// Result: Warning disappears
```

### **Scenario 2: PNG Template, SVG Format**

```typescript
// Setup
filenameTemplate.value = 'comparison_{timestamp}.png'
exportFormat.value = 'svg'

// Expected
extensionMismatch.value = {
  templateExt: 'png',
  expectedExt: 'svg',
  hasConflict: true
}

// Action: Click "Fix Format → PNG"
// Result: exportFormat becomes 'png'
// Result: Warning disappears
```

### **Scenario 3: CSV Template, SVG Format**

```typescript
// Setup
filenameTemplate.value = 'metrics_{date}.csv'
exportFormat.value = 'svg'

// Expected
extensionMismatch.value = {
  templateExt: 'csv',
  expectedExt: 'svg',
  hasConflict: true
}

// Both fix buttons should work
```

### **Scenario 4: No Extension (Valid)**

```typescript
// Setup
filenameTemplate.value = '{preset}_comparison'
exportFormat.value = 'png'

// Expected
extensionMismatch.value = null  // No warning

// Filename preview: 'preset_comparison.png' (extension added by exportFilename)
```

### **Scenario 5: Matching Extension (Valid)**

```typescript
// Setup
filenameTemplate.value = 'output.svg'
exportFormat.value = 'svg'

// Expected
extensionMismatch.value = null  // No warning
```

### **Scenario 6: Unsupported Extension**

```typescript
// Setup
filenameTemplate.value = 'file.dxf'
exportFormat.value = 'svg'

// Expected
extensionMismatch.value = {
  templateExt: 'dxf',
  expectedExt: 'svg',
  hasConflict: true
}

// Warning appears even though .dxf is valid (not in export format list)
```

---

## 🔬 Edge Cases

### **Edge Case 1: Multiple Dots**

```typescript
filenameTemplate.value = 'my.file.name.svg'
// Extracts: .svg (last extension wins)
```

### **Edge Case 2: Extension in Token**

```typescript
filenameTemplate.value = '{preset.svg}__{date}'
// After token removal: '__'
// Extracts: null (no extension outside tokens)
```

### **Edge Case 3: Case Insensitivity**

```typescript
filenameTemplate.value = 'output.SVG'
exportFormat.value = 'svg'
// Match: 'svg' === 'svg' (normalized to lowercase)
// Result: No warning
```

### **Edge Case 4: Invalid Format from localStorage**

```typescript
// localStorage has: comparelab.exportFormat = "invalid"
loadExportState() {
  if (['svg', 'png', 'csv'].includes(savedFormat)) {
    exportFormat.value = savedFormat  // Validated
  }
  // Otherwise: Keep default 'svg'
}
```

---

## 📊 State Flow Diagram

```
Page Load
    ↓
loadExportState()
    ↓
[Template Loaded] + [Format Loaded]
    ↓
extensionMismatch (computed) evaluates
    ↓
    ├─→ No extension in template → No warning
    ├─→ Extension matches format → No warning
    └─→ Extension != format → ⚠️ Warning displayed
            ↓
    User clicks fix button
            ↓
    ├─→ Fix Template: Update filenameTemplate
    └─→ Fix Format: Update exportFormat
            ↓
    saveExportState() (via watcher)
            ↓
    extensionMismatch re-evaluates
            ↓
    Warning disappears ✅
```

---

## 🎯 Benefits

### **User Experience**
- ✅ Prevents export errors from extension mismatches
- ✅ Clear visual feedback when conflict detected
- ✅ One-click fixes (no manual editing required)
- ✅ Persists corrected state to localStorage

### **Developer Experience**
- ✅ Reactive computed property (automatic updates)
- ✅ Pure functions (easy to test)
- ✅ No backend changes required
- ✅ Integrates with existing state persistence

### **Quality Assurance**
- ✅ Reduces user error rate
- ✅ Improves export success rate
- ✅ Self-documenting UI (warning explains issue)
- ✅ Testable with clear scenarios

---

## 🚀 Usage Example

```vue
<!-- CompareLabView.vue Export Dialog -->
<div class="export-dialog">
  <label>
    Filename Template:
    <input v-model="filenameTemplate" />
  </label>
  
  <!-- Warning appears here if mismatch -->
  <div v-if="extensionMismatch" class="extension-warning">
    <!-- Banner and fix buttons -->
  </div>
  
  <div class="export-options">
    <label>
      <input type="radio" v-model="exportFormat" value="svg" />
      SVG
    </label>
    <!-- PNG and CSV options -->
  </div>
  
  <div class="filename-preview">
    <code>{{ exportFilename }}</code>
    <!-- Always shows correct extension -->
  </div>
</div>
```

---

## 🐛 Known Limitations

1. **Only validates export formats:** Does not validate NC/G-code formats (separate system)
2. **No batch validation:** Only checks current template/format pair
3. **Client-side only:** No server-side validation of extension correctness
4. **No cross-tab sync:** Changes in one tab don't update other tabs (storage event not implemented)

---

## 🔮 Future Enhancements

1. **Auto-fix on format change:**
   - When user changes format, automatically update template extension
   - Configurable via settings toggle

2. **Extension history:**
   - Track recently used template/format combinations
   - Suggest common patterns

3. **Batch validation:**
   - Validate all export presets at once
   - Dashboard showing presets with mismatches

4. **Backend validation:**
   - Server-side check before export
   - Return error if mismatch detected

5. **Smart suggestions:**
   - Analyze filename and suggest best format
   - Example: "template.svg" → suggest SVG format

---

## 📚 Related Documentation

- [STATE_PERSISTENCE_QUICKREF.md](./STATE_PERSISTENCE_QUICKREF.md) - localStorage system
- [B21_MULTI_RUN_COMPARISON_QUICKREF.md](./B21_MULTI_RUN_COMPARISON_QUICKREF.md) - Multi-run comparison
- [UNIFIED_PRESET_INTEGRATION_STATUS.md](./UNIFIED_PRESET_INTEGRATION_STATUS.md) - Overall project status
- [test_extension_validation.ps1](./test_extension_validation.ps1) - Test script

---

## ✅ Implementation Checklist

- [x] Create `extensionMismatch` computed property
- [x] Add extension extraction logic (regex with token handling)
- [x] Implement `fixTemplateExtension()` function
- [x] Implement `fixExportFormat()` function
- [x] Add warning banner UI component
- [x] Add fix action buttons
- [x] Style warning banner (amber background, orange border)
- [x] Integrate with localStorage persistence
- [x] Test all 6 scenarios
- [x] Test 4 edge cases
- [x] Create test script
- [x] Create documentation

---

**Feature Version:** 1.0  
**Last Updated:** November 28, 2025  
**Status:** ✅ Production Ready
