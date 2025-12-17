# Neck Context Wiring - Export Integration Enhancement

**Status:** ✅ Complete  
**Date:** November 28, 2025  
**Feature:** Export Dialog Neck Profile/Section Token Resolution

---

## 🎯 Overview

This enhancement wires neck profile and section context into the CompareLabView export dialog, enabling proper resolution of `{neck_profile}` and `{neck_section}` tokens in export filename templates.

### **Key Capabilities:**
- ✅ **Multi-source context extraction** from 4 priority levels
- ✅ **URL query parameter support** for external integrations
- ✅ **Geometry metadata parsing** from embedded meta fields
- ✅ **Source string parsing** for NeckLab origin tracking
- ✅ **LocalStorage persistence** for session continuity
- ✅ **Visual feedback** showing detected neck context in UI

---

## 📦 Implementation Details

### **Context Extraction Priority (Waterfall)**

The system attempts to extract neck context from multiple sources in order:

#### **Priority 1: URL Query Parameters**
```typescript
// URL: /compare-lab?neck_profile=Fender_Modern_C&neck_section=Fret_5
const queryProfile = route.query.neck_profile as string
const querySection = route.query.neck_section as string
```

**Use Case:** External links from NeckLab or other tools  
**Example:** User clicks "Compare in CompareLab" button from NeckLab

---

#### **Priority 2: Geometry Metadata**
```typescript
// Embedded in geometry structure
currentGeometry.paths[0].meta.neck_profile = "Fender_Modern_C"
currentGeometry.paths[0].meta.neck_section = "Fret_5"
```

**Use Case:** Geometry exported from NeckLab with embedded metadata  
**Example:** NeckLab exports geometry with profile/section tags

---

#### **Priority 3: Source String Parsing**
```typescript
// Colon-separated source identifier
currentGeometry.source = "NeckLab:Fender_Modern_C:Fret_5"
// Parses to:
//   origin: "NeckLab"
//   neck_profile: "Fender_Modern_C"
//   neck_section: "Fret_5"
```

**Use Case:** Legacy geometry with source provenance  
**Example:** Geometry from Adaptive Lab tagged with NeckLab origin

---

#### **Priority 4: LocalStorage Fallback**
```typescript
// Persisted from previous session
localStorage.getItem('toolbox.compare.neckProfile')
localStorage.getItem('toolbox.compare.neckSection')
```

**Use Case:** Session continuity when context not in geometry  
**Example:** User previously loaded NeckLab geometry, now loading generic geometry

---

## 🎨 User Interface Changes

### **Export Dialog Enhancement**

**Before:**
```
Tokens: {preset}, {compare_mode}, {neck_profile}, {neck_section}, {date}, {timestamp}
```

**After (with neck context):**
```
Tokens: {preset}, {compare_mode}, {neck_profile}, {neck_section}, {date}, {timestamp}
ℹ Neck context: Profile: Fender_Modern_C  Section: Fret_5
```

**After (without neck context):**
```
Tokens: {preset}, {compare_mode}, {neck_profile}, {neck_section}, {date}, {timestamp}
⚠ No neck context detected. Tokens {neck_profile} and {neck_section} will be empty.
```

### **Visual Feedback**
- **Blue info badge** when context detected (with specific values shown)
- **Amber warning badge** when no context available
- **Inline code tags** for profile/section names with light blue background

---

## 🔧 Integration Points

### **1. Geometry Import**
When user imports geometry JSON:
```typescript
handleFile(event) {
  // ... load geometry ...
  currentGeometry.value = normalized
  extractNeckContext()  // ← Extracts from metadata/source
}
```

### **2. Load from Adaptive Lab**
When user loads persisted geometry:
```typescript
loadPersistedGeometry() {
  currentGeometry.value = JSON.parse(localStorage.getItem(STORAGE_KEY))
  extractNeckContext()  // ← Extracts from loaded geometry
}
```

### **3. Export Dialog Open**
When export dialog opens:
```typescript
watch(showExportDialog, (isOpen) => {
  if (isOpen) {
    loadExportPresets()
    extractNeckContext()  // ← Refresh context in case it changed
  }
})
```

### **4. Geometry Change**
When geometry updates:
```typescript
watch(currentGeometry, (value) => {
  if (value) {
    persistGeometry(value)
    extractNeckContext()  // ← Re-extract on geometry change
  }
}, { deep: true })
```

---

## 📋 Usage Examples

### **Example 1: NeckLab → CompareLab Integration**

**Scenario:** User compares two neck profiles in NeckLab, clicks "Compare" button

**Flow:**
1. NeckLab navigates to: `/compare-lab?neck_profile=Fender_Modern_C&neck_section=Fret_5`
2. CompareLabView reads query params
3. `neckProfileContext` = `"Fender_Modern_C"`
4. `neckSectionContext` = `"Fret_5"`
5. Values persisted to localStorage
6. Export dialog shows: **ℹ Neck context: Profile: Fender_Modern_C Section: Fret_5**
7. Template `{preset}__{neck_profile}__{neck_section}__{date}.svg` resolves to:
   - `Compare__Fender_Modern_C__Fret_5__2025-11-28.svg`

---

### **Example 2: Geometry with Embedded Metadata**

**Scenario:** User imports geometry JSON with metadata

**Geometry JSON:**
```json
{
  "units": "mm",
  "paths": [
    {
      "segments": [...],
      "meta": {
        "neck_profile": "Gibson_Vintage_50s",
        "neck_section": "Fret_12"
      }
    }
  ]
}
```

**Flow:**
1. User imports JSON via "Import Geometry JSON" button
2. `extractNeckContext()` reads `paths[0].meta`
3. `neckProfileContext` = `"Gibson_Vintage_50s"`
4. `neckSectionContext` = `"Fret_12"`
5. Values persisted to localStorage
6. Export filename: `Compare__Gibson_Vintage_50s__Fret_12__2025-11-28.svg`

---

### **Example 3: Legacy Source String**

**Scenario:** User loads geometry with source provenance

**Geometry JSON:**
```json
{
  "units": "mm",
  "source": "NeckLab:Ibanez_Wizard:Fret_7",
  "paths": [...]
}
```

**Flow:**
1. Geometry loaded from Adaptive Lab
2. `extractNeckContext()` parses `source` field
3. Splits on `:` → `["NeckLab", "Ibanez_Wizard", "Fret_7"]`
4. `neckProfileContext` = `"Ibanez_Wizard"`
5. `neckSectionContext` = `"Fret_7"`
6. Export filename: `Compare__Ibanez_Wizard__Fret_7__2025-11-28.svg`

---

### **Example 4: No Context Available**

**Scenario:** User imports generic geometry without neck metadata

**Flow:**
1. Geometry has no metadata, no source, no query params
2. localStorage also empty (first session)
3. Export dialog shows: **⚠ No neck context detected. Tokens {neck_profile} and {neck_section} will be empty.**
4. Template `{preset}__{neck_profile}__{neck_section}__{date}.svg` resolves to:
   - `Compare____2025-11-28.svg` (empty tokens collapse to double underscores)
5. User can manually enter prefix to avoid empty filename

---

## 🔍 Technical Details

### **LocalStorage Keys**
```typescript
const NECK_PROFILE_KEY = 'toolbox.compare.neckProfile'
const NECK_SECTION_KEY = 'toolbox.compare.neckSection'
```

### **Context State**
```typescript
const neckProfileContext = ref<string | null>(null)
const neckSectionContext = ref<string | null>(null)
```

### **Token Resolution (in exportFilename computed)**
```typescript
const context: Record<string, string> = {
  preset: exportPrefix.value || diffResult.value.baseline_name || 'compare',
  compare_mode: 'neck_diff',
  date: new Date().toISOString().slice(0, 10),
  timestamp: new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
}

// Add neck context if available
if (neckProfileContext.value) {
  context.neck_profile = neckProfileContext.value
}
if (neckSectionContext.value) {
  context.neck_section = neckSectionContext.value
}

// Resolve template
let resolved = filenameTemplate.value
Object.keys(context).forEach(key => {
  const regex = new RegExp(`\\{${key}\\}`, 'gi')
  resolved = resolved.replace(regex, context[key] || '')
})
```

---

## ✅ Testing Checklist

### **Priority 1: URL Query Parameters**
- [ ] Navigate to `/compare-lab?neck_profile=Test_Profile&neck_section=Fret_1`
- [ ] Verify context shows in export dialog
- [ ] Verify localStorage updated
- [ ] Verify export filename includes profile/section

### **Priority 2: Geometry Metadata**
- [ ] Import geometry with `paths[0].meta.neck_profile` and `paths[0].meta.neck_section`
- [ ] Verify context extracted
- [ ] Verify localStorage updated
- [ ] Verify export filename correct

### **Priority 3: Source String Parsing**
- [ ] Load geometry with `source: "NeckLab:Profile_Name:Section_Name"`
- [ ] Verify parsing works
- [ ] Verify profile = "Profile_Name", section = "Section_Name"
- [ ] Verify export filename correct

### **Priority 4: LocalStorage Fallback**
- [ ] Set localStorage manually
- [ ] Load generic geometry (no metadata)
- [ ] Verify context loads from localStorage
- [ ] Verify export filename uses persisted context

### **UI Feedback**
- [ ] With context: Blue info badge displays
- [ ] Without context: Amber warning displays
- [ ] Profile/section values shown in code tags
- [ ] Warning message accurate

### **Edge Cases**
- [ ] Empty profile but section present
- [ ] Profile present but empty section
- [ ] Both empty → warning shown
- [ ] Special characters in profile/section names sanitized

---

## 🐛 Known Limitations

### **1. No Context Clearing**
**Issue:** Once context is set in localStorage, it persists forever  
**Impact:** User may see stale profile/section from previous session  
**Workaround:** Import new geometry with fresh metadata  
**Fix:** Add "Clear neck context" button in export dialog (future)

### **2. No Manual Override**
**Issue:** User cannot manually specify profile/section in export dialog  
**Impact:** Cannot override incorrect detected context  
**Workaround:** Clear localStorage manually via DevTools  
**Fix:** Add manual input fields for profile/section (future)

### **3. Single-Path Assumption**
**Issue:** Only checks `paths[0].meta` for metadata  
**Impact:** Multi-path geometries may have different metadata per path  
**Workaround:** Ensure critical metadata in first path  
**Fix:** Merge metadata from all paths or prompt user to select (future)

### **4. No NeckLab Integration Yet**
**Issue:** NeckLab doesn't actually pass query params or embed metadata  
**Impact:** Context extraction relies on manual geometry tagging  
**Workaround:** Manually add metadata to geometry JSON  
**Fix:** Implement NeckLab → CompareLab integration (B20+)

---

## 🚀 Future Enhancements

### **Phase 2: Enhanced Context Management**
1. **Clear context button** in export dialog
2. **Manual profile/section input** fields with autocomplete
3. **Context history** dropdown (last 5 profiles used)
4. **Multi-path metadata** support with selection UI

### **Phase 3: NeckLab Integration**
5. **"Compare in CompareLab"** button in NeckLab
6. **Auto-embed metadata** in NeckLab geometry exports
7. **Bi-directional sync** (CompareLab → NeckLab round-trip)
8. **Profile library** integration with preset system

### **Phase 4: Advanced Features**
9. **Regex-based context extraction** from filenames
10. **AI-powered profile detection** from geometry shape
11. **Context validation** against known profile library
12. **Export analytics** tracking most-used profiles/sections

---

## 📚 Related Documentation

- [EXPORT_DRAWER_INTEGRATION_PHASE1.md](./EXPORT_DRAWER_INTEGRATION_PHASE1.md) - Export template system
- [TEMPLATE_ENGINE_QUICKREF.md](./TEMPLATE_ENGINE_QUICKREF.md) - Token reference
- [UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md](./UNIFIED_PRESET_SYSTEM_PHASE1_COMPLETE.md) - Preset backend

---

## ✅ Verification

**Modified Files:**
- ✅ `packages/client/src/views/CompareLabView.vue` (neck context extraction)

**Key Functions Added:**
- ✅ `extractNeckContext()` - Multi-source context extraction with 4-level priority
- ✅ `NECK_PROFILE_KEY` / `NECK_SECTION_KEY` - LocalStorage persistence
- ✅ Route query parameter reading via `useRoute()`
- ✅ Geometry metadata parsing (`paths[0].meta`)
- ✅ Source string parsing (`source: "NeckLab:Profile:Section"`)
- ✅ Context watchers (geometry change, dialog open, component mount)

**UI Changes:**
- ✅ Blue info badge when context detected
- ✅ Amber warning when no context
- ✅ Profile/section values displayed inline
- ✅ Token resolution includes neck context

---

**Status:** ✅ Neck Context Wiring Complete  
**Next:** Extension Validation + State Persistence  
**Impact:** Export filenames now properly include neck profile and section information, enabling organized file management and traceability.
