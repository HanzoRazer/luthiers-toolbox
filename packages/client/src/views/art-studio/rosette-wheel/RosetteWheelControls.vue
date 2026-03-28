<script setup lang="ts">
/**
 * RosetteWheelControls — Right panel controls
 * Extracted from RosetteWheelView for decomposition
 */
import { computed } from "vue";
import { useRosetteWheelStore } from "@/stores/useRosetteWheelStore";
import type { SymmetryMode } from "@/types/rosetteDesigner";

const store = useRosetteWheelStore();

// ── Props ───────────────────────────────────────────────────────────────
const props = defineProps<{
  segAng: number;
}>();

// ── Emits ───────────────────────────────────────────────────────────────
const emit = defineEmits<{
  (e: "fillRing", ri: number): void;
}>();

// ── Ring definitions from store ─────────────────────────────────────────
const ringDefs = computed(() => store.ringDefs);

// ── Symmetry mode labels ────────────────────────────────────────────────
const SYM_MODES: { mode: SymmetryMode; label: string; icon: string }[] = [
  { mode: "none", label: "None", icon: "·" },
  { mode: "rotational", label: "Rot ×N", icon: "⟳" },
  { mode: "bilateral", label: "Mirror", icon: "↔" },
  { mode: "quadrant", label: "Quad ×4", icon: "✦" },
];
</script>

<template>
  <aside class="rd-panel rd-panel-right">
    <!-- Segment controls -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Segments</label>
      <div class="rd-stepper">
        <button class="rd-btn-sm" @click="store.decrSegs()" :disabled="store.numSegs <= store.segOptions[0]">−</button>
        <span class="rd-stepper-val">{{ store.numSegs }}</span>
        <button class="rd-btn-sm" @click="store.incrSegs()" :disabled="store.numSegs >= store.segOptions[store.segOptions.length - 1]">+</button>
      </div>
    </div>

    <!-- Symmetry -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Symmetry</label>
      <div class="rd-sym-btns">
        <button
          v-for="sm in SYM_MODES"
          :key="sm.mode"
          class="rd-btn-sym"
          :class="{ active: store.symMode === sm.mode }"
          @click="store.setSymMode(sm.mode)"
          :title="sm.label"
        >
          {{ sm.icon }} {{ sm.label }}
        </button>
      </div>
    </div>

    <!-- Ring toggles -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Rings</label>
      <div class="rd-ring-toggles">
        <label
          v-for="(rd, ri) in ringDefs"
          :key="ri"
          class="rd-ring-toggle"
          :style="{ borderColor: rd.dot_color }"
        >
          <input type="checkbox" :checked="store.ringActive[ri]" @change="store.toggleRing(ri)" />
          <span class="rd-ring-dot" :style="{ backgroundColor: rd.dot_color }"></span>
          {{ rd.label.split(' ').slice(-1)[0] }}
        </label>
      </div>
    </div>

    <!-- Display toggles -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Display</label>
      <div class="rd-toggle-pills">
        <button class="rd-pill" :class="{ active: store.showTabs }" @click="store.toggleTabs()">
          Extension Tabs
        </button>
        <button class="rd-pill" :class="{ active: store.showAnnotations }" @click="store.toggleAnnotations()">
          Drafting (Ctrl+D)
        </button>
      </div>
    </div>

    <!-- Actions -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Actions</label>
      <div class="rd-action-btns">
        <button class="rd-btn" @click="emit('fillRing', 2)" :disabled="!store.selectedTile">Fill Main Channel</button>
        <button class="rd-btn" @click="store.clearAll()">Clear All</button>
        <button class="rd-btn" @click="store.exportDesignSvg()">Export Design SVG</button>
        <button class="rd-btn" @click="store.exportDraftingSvg()">Export Drafting SVG</button>
        <button class="rd-btn" @click="store.exportJSON()">Export .rsd</button>
        <button class="rd-btn" @click="store.resetDesign()">Reset Design</button>
      </div>
    </div>

    <!-- Cell info -->
    <div class="rd-control-group" v-if="store.hoveredCell">
      <label class="rd-ctrl-label">Cell Info</label>
      <div class="rd-cell-info">
        <template v-if="ringDefs[store.hoveredCell.ri]">
          <div><strong>Zone:</strong> {{ ringDefs[store.hoveredCell.ri].label }}</div>
          <div><strong>Seg:</strong> {{ store.hoveredCell.si + 1 }}/{{ store.numSegs }}</div>
          <div><strong>Angle:</strong> {{ segAng.toFixed(1) }}°</div>
          <div><strong>Tile:</strong> {{ store.grid[`${store.hoveredCell.ri}-${store.hoveredCell.si}`] || 'empty' }}</div>
        </template>
      </div>
    </div>

    <!-- Keyboard shortcuts legend -->
    <div class="rd-control-group">
      <label class="rd-ctrl-label">Shortcuts</label>
      <div class="rd-shortcuts">
        <div><kbd>Esc</kbd> Deselect tile</div>
        <div><kbd>Del</kbd> Clear hovered cell</div>
        <div><kbd>Ctrl+Z</kbd> Undo</div>
        <div><kbd>Ctrl+Shift+Z</kbd> Redo</div>
        <div><kbd>Ctrl+D</kbd> Drafting mode</div>
        <div><kbd>Ctrl+S</kbd> Save</div>
        <div><kbd>Ctrl+E</kbd> Export SVG</div>
        <div><kbd>Ctrl+B</kbd> BOM tab</div>
        <div><kbd>Ctrl+M</kbd> MFG tab</div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.rd-panel {
  width: 280px;
  min-width: 240px;
  background: #141210;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.rd-panel-right {
  border-left: 1px solid rgba(200, 146, 42, 0.12);
  padding: 0.75rem;
  gap: 0.75rem;
}

.rd-control-group { display: flex; flex-direction: column; gap: 4px; }
.rd-ctrl-label { font-size: 0.65rem; color: #887a66; text-transform: uppercase; letter-spacing: 0.05em; }

.rd-stepper { display: flex; align-items: center; gap: 0.5rem; }
.rd-stepper-val { font-size: 1.1rem; font-weight: 600; min-width: 2rem; text-align: center; color: #c89a2a; }

.rd-sym-btns { display: flex; flex-wrap: wrap; gap: 3px; }
.rd-btn-sym {
  padding: 3px 8px;
  font-size: 0.65rem;
  border: 1px solid rgba(200, 146, 42, 0.2);
  border-radius: 4px;
  background: none;
  color: #a09888;
  cursor: pointer;
}
.rd-btn-sym.active { border-color: #c89a2a; color: #c89a2a; background: rgba(200, 146, 42, 0.1); }

.rd-ring-toggles { display: flex; flex-direction: column; gap: 3px; }
.rd-ring-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  cursor: pointer;
  padding: 2px 4px;
  border-left: 3px solid;
  border-radius: 2px;
}
.rd-ring-dot { width: 8px; height: 8px; border-radius: 50%; }

.rd-toggle-pills { display: flex; flex-wrap: wrap; gap: 4px; }
.rd-pill {
  padding: 3px 10px;
  font-size: 0.65rem;
  border: 1px solid rgba(200, 146, 42, 0.2);
  border-radius: 12px;
  background: none;
  color: #a09888;
  cursor: pointer;
}
.rd-pill.active { border-color: #c89a2a; color: #c89a2a; background: rgba(200, 146, 42, 0.1); }

.rd-action-btns { display: flex; flex-direction: column; gap: 4px; }

.rd-cell-info { font-size: 0.7rem; background: rgba(200, 146, 42, 0.06); padding: 0.4rem; border-radius: 4px; }

.rd-shortcuts { font-size: 0.65rem; color: #887a66; }
.rd-shortcuts div { margin-bottom: 2px; }
.rd-shortcuts kbd {
  background: rgba(200, 146, 42, 0.12);
  padding: 1px 4px;
  border-radius: 2px;
  font-family: monospace;
  font-size: 0.6rem;
  color: #c89a2a;
}

.rd-btn {
  padding: 5px 12px;
  font-size: 0.7rem;
  border: 1px solid rgba(200, 146, 42, 0.3);
  border-radius: 4px;
  background: rgba(200, 146, 42, 0.08);
  color: #c89a2a;
  cursor: pointer;
  transition: background 0.15s;
}
.rd-btn:hover { background: rgba(200, 146, 42, 0.18); }
.rd-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.rd-btn-sm {
  padding: 3px 8px;
  font-size: 0.7rem;
  border: 1px solid rgba(200, 146, 42, 0.25);
  border-radius: 3px;
  background: none;
  color: #c89a2a;
  cursor: pointer;
}
.rd-btn-sm:hover { background: rgba(200, 146, 42, 0.12); }
.rd-btn-sm:disabled { opacity: 0.35; cursor: not-allowed; }
</style>
