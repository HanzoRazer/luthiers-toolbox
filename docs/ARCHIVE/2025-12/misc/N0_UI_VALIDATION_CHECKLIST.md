# N.0 Smart Post Configurator - UI Validation Checklist

**Date:** January 2025  
**Status:** ✅ API Validation Complete (18/18 tests passed)  
**Next:** Manual UI Testing

---

## ✅ API Validation Results

All automated tests passed:

| Category | Tests | Status |
|----------|-------|--------|
| Server Health | 1/1 | ✅ |
| Builtin Posts | 6/6 | ✅ |
| Token System | 1/1 | ✅ |
| Create Custom Post | 1/1 | ✅ |
| Validation System | 2/2 | ✅ |
| Update Post | 2/2 | ✅ |
| Builtin Protection | 2/2 | ✅ |
| ID Validation | 1/1 | ✅ |
| Delete Post | 2/2 | ✅ |
| **TOTAL** | **18/18** | **✅ 100%** |

---

## 📋 Manual UI Validation Checklist

### **Step 1: Access the UI**

**URL:** http://localhost:5173/cam-dashboard

- [ ] CAM Dashboard loads successfully
- [ ] "Post Processors" card visible
- [ ] Card shows "N.0" version badge
- [ ] Card shows "NEW" badge
- [ ] Description reads: "Create and manage custom CNC post-processor configurations"

**Action:** Click "Post Processors" card

---

### **Step 2: PostManager Grid View**

**URL:** http://localhost:5173/lab/posts

- [ ] PostManager page loads
- [ ] Header shows "Post Processor Manager"
- [ ] Subtitle reads: "Create, edit, and manage custom CNC post-processor configurations"
- [ ] Search bar visible
- [ ] "Create Post" button visible
- [ ] Grid layout displays posts (responsive)

**Builtin Posts Display:**
- [ ] 5 builtin posts visible: GRBL, Mach4, LinuxCNC, PathPilot, MASSO
- [ ] Each has blue border/background
- [ ] Each shows "Built-in" badge
- [ ] Each shows post name and description
- [ ] Edit/delete buttons visible but may be disabled

**Action:** Try to click "Delete" on GRBL post

**Expected:** Button should either be:
- Disabled (grayed out), OR
- Show error message: "Cannot delete builtin post"

---

### **Step 3: Create Custom Post**

**Action:** Click "Create Post" button

**PostEditor Modal Opens:**
- [ ] Modal overlay appears
- [ ] Modal title: "Create Post"
- [ ] Form fields visible:
  - [ ] Post ID (text input, required)
  - [ ] Name (text input, required)
  - [ ] Description (textarea, optional)
  - [ ] Header lines (array editor)
  - [ ] Footer lines (array editor)
  - [ ] Metadata section (controller family, dialect, checkboxes)
- [ ] Token reference section visible (shows 10 tokens)
- [ ] "Validate" button visible
- [ ] "Save" button visible
- [ ] "Cancel" button visible

**Fill Form:**
```
ID: MY_CUSTOM_HAAS
Name: My Custom Haas Post
Description: Testing N.0 Smart Post Configurator UI

Header:
  G90
  G21
  G17
  M6 T{{TOOL_NUMBER}}

Footer:
  M30
  (Generated: {{DATE}})

Metadata:
  Controller Family: haas
  G-code Dialect: Fanuc
  Supports Arcs: ✓
  Has Tool Changer: ✓
```

**Action:** Click "Validate" button

**Expected:**
- [ ] Validation succeeds
- [ ] Message shows: "Valid: true, Warnings: 0, Errors: 0" (or similar)

**Action:** Click "Save" button

**Expected:**
- [ ] Modal closes
- [ ] Grid refreshes
- [ ] New post "MY_CUSTOM_HAAS" appears in grid
- [ ] Does NOT have "Built-in" badge
- [ ] Has standard border (not blue)
- [ ] Edit and Delete buttons enabled

---

### **Step 4: Edit Custom Post**

**Action:** Click "Edit" button on "MY_CUSTOM_HAAS" post

**PostEditor Modal Opens:**
- [ ] Modal title: "Edit Post"
- [ ] Post ID field is DISABLED (read-only)
- [ ] Name field shows: "My Custom Haas Post"
- [ ] Description shows current text
- [ ] Header lines show previous values
- [ ] Footer lines show previous values
- [ ] Metadata shows previous values

**Modify:**
- Change description to: "Updated description via UI"
- Add header line: "(Modified via PostEditor)"

**Action:** Click "Update" button

**Expected:**
- [ ] Modal closes
- [ ] Grid refreshes
- [ ] Post card shows updated description
- [ ] Post still appears in grid

---

### **Step 5: Token Helper Validation**

**Action:** Click "Edit" on "MY_CUSTOM_HAAS" again

**Token Reference Section:**
- [ ] Shows "Available Tokens" heading
- [ ] Lists 10 tokens with syntax and descriptions:
  - [ ] {{POST_ID}} - Post-processor identifier
  - [ ] {{UNITS}} - Units (mm or inch)
  - [ ] {{DATE}} - ISO 8601 timestamp
  - [ ] {{TOOL_DIAMETER}} - Tool diameter
  - [ ] {{TOOL_NUMBER}} - Tool number (for tool changers)
  - [ ] {{MATERIAL}} - Material name
  - [ ] {{MACHINE_ID}} - Machine profile ID
  - [ ] {{FEED_XY}} - Cutting feed rate
  - [ ] {{FEED_Z}} - Plunge feed rate
  - [ ] {{SPINDLE_RPM}} - Spindle speed

**Test Token Usage:**
- Add to header: "S{{SPINDLE_RPM}} M3 (Spindle)"
- Add to footer: "(Material: {{MATERIAL}})"

**Action:** Click "Update"

**Expected:**
- [ ] Update succeeds
- [ ] Tokens preserved in header/footer (not expanded yet)

---

### **Step 6: Validation System**

**Action:** Click "Create Post" again

**Test ID Validation:**
- Enter ID: "GRBL_CUSTOM"
- Fill other required fields

**Action:** Click "Validate"

**Expected:**
- [ ] Validation FAILS
- [ ] Error message: "Post ID cannot start with reserved prefixes: ['GRBL', 'Mach4', 'LinuxCNC', 'PathPilot', 'MASSO']"

**Fix:**
- Change ID to: "CUSTOM_GRBL"

**Action:** Click "Validate" again

**Expected:**
- [ ] Validation SUCCEEDS
- [ ] No errors shown

**Action:** Click "Cancel" (don't save)

---

### **Step 7: Search Functionality**

**Back on PostManager grid:**

**Action:** Type "GRBL" in search bar

**Expected:**
- [ ] Only GRBL post visible (filters out others)
- [ ] Search is case-insensitive

**Action:** Clear search, type "custom"

**Expected:**
- [ ] Only "MY_CUSTOM_HAAS" visible
- [ ] Builtin posts hidden

**Action:** Clear search

**Expected:**
- [ ] All posts visible again (5 builtin + 1 custom)

---

### **Step 8: Delete Custom Post**

**Action:** Click "Delete" button on "MY_CUSTOM_HAAS"

**Expected:**
- [ ] Confirmation modal/dialog appears
- [ ] Message asks: "Are you sure you want to delete..."
- [ ] "Confirm" and "Cancel" buttons visible

**Action:** Click "Confirm"

**Expected:**
- [ ] Modal closes
- [ ] Grid refreshes
- [ ] "MY_CUSTOM_HAAS" post removed from grid
- [ ] Only 5 builtin posts remain

---

### **Step 9: Builtin Post Protection**

**Action:** Try to click "Edit" or "Delete" on GRBL post

**Expected (one of):**
- [ ] Buttons are disabled (grayed out)
- [ ] Clicking shows error: "Cannot edit/delete builtin post"
- [ ] No edit/delete buttons visible for builtin posts

**Action:** Click on GRBL post card (if clickable)

**Expected:**
- [ ] Shows post details (read-only view)
- [ ] OR opens modal with post details (no save button)

---

### **Step 10: Responsive Design**

**Action:** Resize browser window

**Test Layouts:**
- [ ] Desktop (>1024px): Grid shows 3 columns
- [ ] Tablet (768-1024px): Grid shows 2 columns
- [ ] Mobile (<768px): Grid shows 1 column
- [ ] Modal is responsive (max 90vh height, scrollable)
- [ ] Search bar shrinks on mobile
- [ ] All buttons remain accessible

---

## 🎯 Validation Results

### **API Tests: 18/18 ✅**
All automated API tests passed.

### **UI Tests: [ ] / 50+**

**To complete this section:**
1. Go through each step above
2. Check each checkbox as you verify
3. Note any issues or bugs found
4. Document actual vs expected behavior

### **Overall Status:**

- [ ] All UI tests passed
- [ ] Ready for production use
- [ ] Minor issues found (list below)
- [ ] Major issues found (requires fixes)

---

## 🐛 Issues Found (If Any)

**Issue Template:**
```
Issue #: [number]
Component: [PostManager / PostEditor / etc]
Severity: [Low / Medium / High]
Description: [What happened]
Expected: [What should happen]
Steps to Reproduce: [1, 2, 3...]
```

### **Issues:**

*(None yet - complete validation first)*

---

## ✅ Final Sign-Off

**Validated By:** _________________  
**Date:** _________________  
**Result:** ⬜ Pass ⬜ Pass with Minor Issues ⬜ Fail

**Notes:**


---

## 📚 Reference

- **API Documentation:** PHASE5_PART2_N0_SMART_POST_COMPLETE.md
- **Quick Reference:** PHASE5_PART2_N0_QUICKREF.md
- **API Test Results:** test_n0_user_validation.ps1 (18/18 passed)

**Servers Running:**
- Backend: http://localhost:8000 (FastAPI)
- Frontend: http://localhost:5173 (Vite/Vue)

**Test Data:**
- 5 builtin posts (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
- Custom posts stored in: services/api/app/data/posts/custom_posts.json
