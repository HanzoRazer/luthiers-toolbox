# Keyboard Hints System — Developer Guide

> **Bundle 03** | Version 1.0 | 2026-01-02

## Overview

The keyboard hints system provides user-controllable visibility of keyboard shortcut documentation in UI panels. It uses localStorage for persistence across sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Component (e.g., SnapshotComparePanel.vue)                 │
│  ┌─────────────────┐    ┌──────────────────────────────┐    │
│  │ showKeyboardHints│───▶│ v-if="showKeyboardHints"     │    │
│  │ ref<boolean>     │    │ (conditional hint rendering) │    │
│  └────────┬────────┘    └──────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │ localStorage     │                                        │
│  │ "compare.show…"  │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Pattern

### 1. State Declaration

```typescript
// Unique key per feature area (namespace.feature pattern)
const KEYBOARD_HINTS_KEY = "compare.showKeyboardHints";

// Default to true (visible) for discoverability
const showKeyboardHints = ref(true);
```

### 2. Persistence (onMounted + watch)

```typescript
onMounted(() => {
  // Restore preference from localStorage
  const saved = localStorage.getItem(KEYBOARD_HINTS_KEY);
  if (saved !== null) {
    showKeyboardHints.value = saved === "true";
  }
});

// Persist on change
watch(showKeyboardHints, (val) => {
  localStorage.setItem(KEYBOARD_HINTS_KEY, String(val));
});
```

### 3. Template Structure

```vue
<div class="keyboard-hints-row">
  <!-- Toggle control -->
  <label class="hint-toggle">
    <input type="checkbox" v-model="showKeyboardHints" />
    Show keyboard hints
  </label>

  <!-- Conditional hint display -->
  <div v-if="showKeyboardHints" class="hint-text">
    <kbd>[</kbd> / <kbd>]</kbd> step <strong>Right</strong>
    <span class="hint-sep">·</span>
    <kbd>Shift</kbd>+<kbd>[</kbd> / <kbd>]</kbd> step <strong>Left</strong>
  </div>
</div>
```

### 4. Required CSS Classes

```css
.keyboard-hints-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0;
  flex-wrap: wrap;
}

.hint-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  user-select: none;
}

.hint-toggle input[type="checkbox"] {
  margin: 0;
  cursor: pointer;
}

.hint-text {
  font-size: 12px;
  color: #555;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.hint-text kbd {
  background: #f3f3f3;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 2px 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  color: #333;
  box-shadow: 0 1px 1px rgba(0,0,0,0.08);
}

.hint-text strong {
  font-weight: 600;
}

.hint-sep {
  color: #999;
  margin: 0 4px;
}
```

## localStorage Key Naming Convention

Use namespaced keys to avoid collisions:

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{panel}.showKeyboardHints` | `compare.showKeyboardHints` | Panel-specific hints |
| `{panel}.{feature}` | `editor.autoSave` | Feature toggles |
| `ui.{preference}` | `ui.sidebarCollapsed` | Global UI state |

## Adding Hints to a New Panel

1. **Define the key constant** (top of script):
   ```typescript
   const MY_HINTS_KEY = "myPanel.showKeyboardHints";
   const showKeyboardHints = ref(true);
   ```

2. **Add persistence** (in onMounted + watch):
   ```typescript
   // In onMounted:
   const saved = localStorage.getItem(MY_HINTS_KEY);
   if (saved !== null) showKeyboardHints.value = saved === "true";

   // Separate watch:
   watch(showKeyboardHints, (val) => {
     localStorage.setItem(MY_HINTS_KEY, String(val));
   });
   ```

3. **Add template markup** (copy from pattern above)

4. **Copy CSS classes** (or import from shared stylesheet)

## Keyboard Shortcut Documentation Format

Use semantic HTML for accessibility:

```vue
<!-- Good: semantic, accessible -->
<kbd>Ctrl</kbd>+<kbd>S</kbd> Save

<!-- Avoid: non-semantic -->
<b>Ctrl+S</b> Save
```

### Common Shortcut Patterns

| Shortcut | Markup |
|----------|--------|
| Single key | `<kbd>Esc</kbd>` |
| Modifier + key | `<kbd>Ctrl</kbd>+<kbd>S</kbd>` |
| Key range | `<kbd>[</kbd> / <kbd>]</kbd>` |
| With action | `<kbd>Enter</kbd> to confirm` |

## Testing

### Manual Verification

1. Open panel with hints enabled (default)
2. Verify hints visible
3. Uncheck toggle → hints hide
4. Refresh page → preference persists
5. Check toggle → hints show
6. Refresh page → preference persists

### Automated Test Pattern

```typescript
import { mount } from "@vue/test-utils";
import SnapshotComparePanel from "./SnapshotComparePanel.vue";

describe("Keyboard Hints", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("shows hints by default", () => {
    const wrapper = mount(SnapshotComparePanel);
    expect(wrapper.find(".hint-text").exists()).toBe(true);
  });

  it("persists preference to localStorage", async () => {
    const wrapper = mount(SnapshotComparePanel);
    await wrapper.find(".hint-toggle input").setValue(false);
    expect(localStorage.getItem("compare.showKeyboardHints")).toBe("false");
  });

  it("restores preference from localStorage", () => {
    localStorage.setItem("compare.showKeyboardHints", "false");
    const wrapper = mount(SnapshotComparePanel);
    expect(wrapper.find(".hint-text").exists()).toBe(false);
  });
});
```

## Accessibility Notes

- `<kbd>` elements are recognized by screen readers
- Toggle uses native checkbox (keyboard accessible)
- Label wraps checkbox for larger click target
- `user-select: none` on label prevents accidental text selection

## Related Files

| File | Purpose |
|------|---------|
| [SnapshotComparePanel.vue](../components/art/SnapshotComparePanel.vue) | Reference implementation |
| [ringFocus.ts](../utils/ringFocus.ts) | Ring diagnostic utilities (Bundle 32.3.1) |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial implementation (Bundle 03) |
