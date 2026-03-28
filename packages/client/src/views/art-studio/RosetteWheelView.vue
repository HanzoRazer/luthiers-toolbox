<script setup lang="ts">
/**
 * RosetteWheelView — Active rosette designer
 * Embedded in SoundholeRosetteShell (Stage 1)
 * Also directly routed at /art-studio/rosette-designer
 *
 * Decomposed into sub-components:
 * - RosetteWheelCanvas — SVG wheel rendering
 * - RosetteWheelControls — Right panel controls
 * - RosetteWheelPresets — Library tab (recipes + saved designs)
 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRosetteWheelStore } from "@/stores/useRosetteWheelStore";
import { RosetteWheelCanvas, RosetteWheelControls, RosetteWheelPresets } from "./rosette-wheel";

const store = useRosetteWheelStore();

// ── Rename modal ───────────────────────────────────────────────────────
const showRenameModal = ref(false);
const renameInput = ref("");

// ── Drag ghost ─────────────────────────────────────────────────────────
const ghostPos = ref({ x: 0, y: 0 });
const ghostVisible = ref(false);

// ── Computed helpers ───────────────────────────────────────────────────
const segAng = computed(() => 360 / store.numSegs);

const hoveredCellKey = computed<string | null>(() => {
  if (!store.hoveredCell) return null;
  return `${store.hoveredCell.ri}-${store.hoveredCell.si}`;
});

// ── Tile lookup ────────────────────────────────────────────────────────
function tileColorHex(tileId: string): string {
  const TILE_COLORS: Record<string, string> = {
    abalone: "#50c8c0", mop: "#e8e0f0", burl: "#C8A048",
    herringbone: "#C09850", checker: "#8a8a6a", celtic: "#2a6a4a",
    diagonal: "#c8922a", dots: "#e8d8b8",
    stripes: "#444", stripes2: "#882233", stripes3: "#aaa", clear: "transparent",
  };
  const tile = store.tiles[tileId];
  if (!tile) return "#666";
  if (tile.type === "solid") return tile.color || "#666";
  return TILE_COLORS[tile.type] || "#666";
}

// ── Cell click / hover handlers ────────────────────────────────────────
function onCellClick(ri: number, si: number) {
  if (store.selectedTile) {
    store.placeTile(ri, si, store.selectedTile);
  }
}

function onCellEnter(ri: number, si: number) {
  store.setHoveredCell(ri, si);
}

function onCellLeave() {
  store.clearHoveredCell();
}

function onCellDrop(ri: number, si: number) {
  if (store.dragTileId) {
    store.placeTile(ri, si, store.dragTileId);
    store.endDrag();
    ghostVisible.value = false;
  }
}

// ── Drag handlers ──────────────────────────────────────────────────────
function onTileDragStart(tileId: string, ev: MouseEvent | DragEvent) {
  store.startDrag(tileId);
  ghostVisible.value = true;
  ghostPos.value = { x: ev.clientX, y: ev.clientY };
}

function onGlobalMouseMove(ev: MouseEvent) {
  if (store.isDragging) {
    ghostPos.value = { x: ev.clientX, y: ev.clientY };
  }
}

function onGlobalMouseUp() {
  if (store.isDragging) {
    store.endDrag();
    ghostVisible.value = false;
  }
}

// ── Fill ring (all cells of current tile) ──────────────────────────────
function fillRingWithSelected(ri: number) {
  if (store.selectedTile) {
    store.fillRing(ri, store.selectedTile);
  }
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────
function handleKeydown(ev: KeyboardEvent) {
  if (showRenameModal.value) return;
  const ctrl = ev.ctrlKey || ev.metaKey;

  if (ev.key === "Escape") {
    store.selectTile(null);
    ev.preventDefault();
  } else if (ev.key === "Delete" || ev.key === "Backspace") {
    if (store.hoveredCell) {
      store.clearCell(store.hoveredCell.ri, store.hoveredCell.si);
      ev.preventDefault();
    }
  } else if (ctrl && ev.key === "z" && !ev.shiftKey) {
    store.undo();
    ev.preventDefault();
  } else if (ctrl && (ev.key === "Z" || (ev.key === "z" && ev.shiftKey))) {
    store.redo();
    ev.preventDefault();
  } else if (ctrl && ev.key === "d") {
    store.toggleAnnotations();
    ev.preventDefault();
  } else if (ctrl && ev.key === "s") {
    store.saveToSession();
    ev.preventDefault();
  } else if (ctrl && ev.key === "e") {
    store.exportDesignSvg();
    ev.preventDefault();
  } else if (ctrl && ev.key === "b") {
    store.activeTab = "bom";
    store.refreshBom();
    ev.preventDefault();
  } else if (ctrl && ev.key === "m") {
    store.activeTab = "mfg";
    ev.preventDefault();
  }
}

// ── Rename modal ───────────────────────────────────────────────────────
function openRenameModal() {
  renameInput.value = store.designName;
  showRenameModal.value = true;
  nextTick(() => {
    const inp = document.querySelector(".rename-input") as HTMLInputElement;
    if (inp) { inp.focus(); inp.select(); }
  });
}

function confirmRename() {
  if (renameInput.value.trim()) {
    store.rename(renameInput.value.trim());
  }
  showRenameModal.value = false;
}

function cancelRename() {
  showRenameModal.value = false;
}

// ── Lifecycle ──────────────────────────────────────────────────────────
onMounted(async () => {
  await store.loadCatalog();
  store.loadSavedDesigns();
  store.refreshMfg();
  window.addEventListener("keydown", handleKeydown);
  window.addEventListener("mousemove", onGlobalMouseMove);
  window.addEventListener("mouseup", onGlobalMouseUp);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  window.removeEventListener("mousemove", onGlobalMouseMove);
  window.removeEventListener("mouseup", onGlobalMouseUp);
});

// ── Tab switch triggers BOM refresh ────────────────────────────────────
watch(() => store.activeTab, (tab) => {
  if (tab === "bom") store.refreshBom();
});

// ── MFG overlay cells ──────────────────────────────────────────────────
const mfgOverlayCells = computed(() => {
  if (!store.mfgResult || !store.showMfgOverlay) return [];
  const cells: { ri: number; si: number; sev: string }[] = [];
  for (const flag of store.mfgResult.flags) {
    for (const cell of flag.cells) {
      cells.push({ ri: cell.ri, si: cell.si, sev: flag.sev });
    }
  }
  return cells;
});
</script>

<template>
  <div class="rd-root" :class="{ 'rd-drafting': store.showAnnotations }">

    <!-- ── HEADER BAR ─────────────────────────────────────────────── -->
    <header class="rd-header">
      <div class="rd-header-left">
        <h1 class="rd-title" @click="openRenameModal" title="Click to rename">
          {{ store.designName }} <span class="rd-rename-icon">✎</span>
        </h1>
        <span class="rd-subtitle">Interactive Rosette Designer</span>
      </div>
      <div class="rd-header-center">
        <span class="rd-fill-badge" :title="`${store.filledCellCount}/${store.totalCellCount} cells`">
          {{ store.fillPercent }}% filled
        </span>
        <span
          v-if="store.mfgBadge"
          class="rd-mfg-badge"
          :class="store.mfgBadge.cls"
          :title="`MFG: ${store.mfgResult?.score ?? '–'}/100`"
        >
          {{ store.mfgBadge.text }}
        </span>
      </div>
      <div class="rd-header-right">
        <button class="rd-btn-sm" :disabled="!store.canUndo" @click="store.undo()" title="Undo (Ctrl+Z)">↩</button>
        <button class="rd-btn-sm" :disabled="!store.canRedo" @click="store.redo()" title="Redo (Ctrl+Shift+Z)">↪</button>
        <button class="rd-btn-sm" @click="store.saveToSession()" title="Save (Ctrl+S)">💾</button>
        <button class="rd-btn-sm" @click="store.exportDesignSvg()" title="Export SVG (Ctrl+E)">📁</button>
      </div>
    </header>

    <div class="rd-body">

      <!-- ── LEFT PANEL (4 TABS) ──────────────────────────────────── -->
      <aside class="rd-panel rd-panel-left">
        <div class="rd-tabs">
          <button
            v-for="t in (['tiles', 'library', 'bom', 'mfg'] as const)"
            :key="t"
            class="rd-tab"
            :class="{ active: store.activeTab === t }"
            @click="store.activeTab = t"
          >
            {{ t === 'tiles' ? '🎨 Tiles' : t === 'library' ? '📚 Library' : t === 'bom' ? '📋 BOM' : '🔧 MFG' }}
            <span v-if="t === 'mfg' && store.mfgBadge" class="rd-tab-badge" :class="store.mfgBadge.cls">
              {{ store.mfgBadge.text }}
            </span>
          </button>
        </div>

        <!-- TILES TAB -->
        <div v-if="store.activeTab === 'tiles'" class="rd-tab-content">
          <div v-for="cat in store.categories" :key="cat.label" class="rd-tile-category">
            <h4 class="rd-cat-label">{{ cat.label }}</h4>
            <div class="rd-tile-grid">
              <div
                v-for="tileId in cat.tiles"
                :key="tileId"
                class="rd-tile-swatch"
                :class="{ selected: store.selectedTile === tileId }"
                :title="store.tiles[tileId]?.name"
                :style="{ backgroundColor: tileColorHex(tileId) }"
                @click="store.selectTile(tileId)"
                @mousedown.prevent="onTileDragStart(tileId, $event)"
              >
                <span class="rd-tile-label">{{ store.tiles[tileId]?.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- LIBRARY TAB (extracted component) -->
        <RosetteWheelPresets v-if="store.activeTab === 'library'" />

        <!-- BOM TAB -->
        <div v-if="store.activeTab === 'bom'" class="rd-tab-content">
          <div v-if="store.bomLoading" class="rd-loading">Computing BOM...</div>
          <div v-else-if="!store.bom" class="rd-empty">No BOM data</div>
          <div v-else class="rd-bom">
            <div class="rd-bom-summary">
              <div class="rd-bom-stat">{{ store.bom.material_count }} materials</div>
              <div class="rd-bom-stat">{{ store.bom.total_pieces }} pieces</div>
              <div class="rd-bom-stat">{{ store.bom.total_arc_inches.toFixed(2) }}" total arc</div>
              <div class="rd-bom-stat">{{ store.bom.fill_percent }}% filled</div>
            </div>

            <h4 class="rd-bom-heading">Materials</h4>
            <div v-for="mat in store.bom.materials" :key="mat.tile_id" class="rd-bom-mat-card">
              <div class="rd-bom-mat-header">
                <span class="rd-bom-dot" :style="{ backgroundColor: mat.tile_color_hex }"></span>
                <strong>{{ mat.tile_name }}</strong>
                <span class="rd-bom-count">{{ mat.pieces }} pc</span>
              </div>
              <div v-for="pr in mat.per_ring" :key="pr.ring_label" class="rd-bom-ring-detail">
                {{ pr.ring_label }}: {{ pr.count }} pc, {{ pr.arc_total_inches.toFixed(3) }}" arc
              </div>
              <div class="rd-bom-procurement">
                <span v-for="(strip, i) in mat.procurement_strips" :key="i" class="rd-bom-strip">
                  {{ strip }}
                </span>
              </div>
            </div>

            <h4 class="rd-bom-heading">Rings</h4>
            <div v-for="ring in store.bom.rings" :key="ring.label" class="rd-bom-ring-card">
              <span class="rd-bom-dot" :style="{ backgroundColor: ring.dot_color }"></span>
              <strong>{{ ring.label }}</strong>
              <span>{{ ring.filled }}/{{ ring.total_cells }} cells</span>
              <span>{{ ring.depth_inches }}″ depth</span>
            </div>

            <div class="rd-bom-actions">
              <button class="rd-btn" @click="store.exportBomCsv()">📊 Export BOM CSV</button>
            </div>
          </div>
        </div>

        <!-- MFG TAB -->
        <div v-if="store.activeTab === 'mfg'" class="rd-tab-content">
          <div v-if="store.mfgLoading" class="rd-loading">Running checks...</div>
          <div v-else-if="!store.mfgResult" class="rd-empty">No MFG data</div>
          <div v-else class="rd-mfg">
            <div class="rd-mfg-score" :class="`score-${store.mfgResult.score_class}`">
              <span class="rd-mfg-score-num">{{ store.mfgResult.score }}</span>
              <span class="rd-mfg-score-label">/100</span>
            </div>
            <div class="rd-mfg-counts">
              <span class="rd-mfg-count err" v-if="store.mfgResult.error_count">{{ store.mfgResult.error_count }} errors</span>
              <span class="rd-mfg-count warn" v-if="store.mfgResult.warning_count">{{ store.mfgResult.warning_count }} warnings</span>
              <span class="rd-mfg-count info" v-if="store.mfgResult.info_count">{{ store.mfgResult.info_count }} info</span>
              <span class="rd-mfg-count ok" v-if="store.mfgResult.passing_count">{{ store.mfgResult.passing_count }} passing</span>
            </div>

            <label class="rd-checkbox">
              <input type="checkbox" v-model="store.showMfgOverlay" />
              Show overlay on wheel
            </label>

            <div v-for="flag in store.mfgResult.flags" :key="flag.id" class="rd-mfg-flag" :class="`sev-${flag.sev}`">
              <div class="rd-mfg-flag-header">
                <span class="rd-mfg-sev-icon">{{ flag.sev === 'error' ? '🔴' : flag.sev === 'warning' ? '🟡' : 'ℹ️' }}</span>
                <strong>{{ flag.title }}</strong>
              </div>
              <p class="rd-mfg-flag-desc">{{ flag.desc }}</p>
              <p v-if="flag.fix" class="rd-mfg-flag-fix">💡 {{ flag.fix }}</p>
              <button v-if="flag.has_auto_fix" class="rd-btn-sm" @click="store.applyMfgAutoFix()">Auto-fix</button>
            </div>
          </div>
        </div>
      </aside>

      <!-- ── CENTER: SVG WHEEL CANVAS (extracted component) ────────── -->
      <RosetteWheelCanvas
        :hovered-cell-key="hoveredCellKey"
        :mfg-overlay-cells="mfgOverlayCells"
        @cell-click="onCellClick"
        @cell-enter="onCellEnter"
        @cell-leave="onCellLeave"
        @cell-drop="onCellDrop"
      />

      <!-- ── RIGHT PANEL (extracted component) ───────────────────── -->
      <RosetteWheelControls
        :seg-ang="segAng"
        @fill-ring="fillRingWithSelected"
      />
    </div>

    <!-- ── TOAST ──────────────────────────────────────────────────── -->
    <Transition name="toast">
      <div v-if="store.toastVisible" class="rd-toast">{{ store.toastMessage }}</div>
    </Transition>

    <!-- ── RENAME MODAL ───────────────────────────────────────────── -->
    <div v-if="showRenameModal" class="rd-modal-overlay" @click.self="cancelRename">
      <div class="rd-modal">
        <h3>Rename Design</h3>
        <input
          class="rename-input rd-input"
          v-model="renameInput"
          @keydown.enter="confirmRename"
          @keydown.escape="cancelRename"
        />
        <div class="rd-modal-btns">
          <button class="rd-btn" @click="confirmRename">Rename</button>
          <button class="rd-btn rd-btn-secondary" @click="cancelRename">Cancel</button>
        </div>
      </div>
    </div>

    <!-- ── DRAG GHOST ─────────────────────────────────────────────── -->
    <div
      v-if="store.isDragging && store.dragTileId"
      class="rd-drag-ghost"
      :style="{ left: ghostPos.x + 'px', top: ghostPos.y + 'px', backgroundColor: tileColorHex(store.dragTileId) }"
    ></div>
  </div>
</template>

<style scoped>
/* ── ROOT LAYOUT ──────────────────────────────────────────────────── */
.rd-root {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0d0b08;
  color: #e8e0d0;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

.rd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: #1a1814;
  border-bottom: 1px solid rgba(200, 146, 42, 0.2);
}

.rd-header-left { display: flex; align-items: baseline; gap: 0.75rem; }
.rd-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #c89a2a;
  cursor: pointer;
  margin: 0;
}
.rd-rename-icon { font-size: 0.8rem; opacity: 0.5; }
.rd-subtitle { font-size: 0.75rem; color: #887a66; }

.rd-header-center { display: flex; gap: 0.75rem; align-items: center; }
.rd-fill-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: rgba(200, 146, 42, 0.15);
  border-radius: 10px;
  color: #c89a2a;
}

.rd-mfg-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.badge-error { background: rgba(220, 40, 40, 0.25); color: #ff6060; }
.badge-warn { background: rgba(220, 180, 40, 0.25); color: #eec830; }
.badge-info { background: rgba(80, 160, 220, 0.2); color: #88c8ee; }
.badge-ok { background: rgba(60, 200, 80, 0.2); color: #60c060; }

.rd-header-right { display: flex; gap: 0.4rem; }

/* ── BODY LAYOUT ──────────────────────────────────────────────────── */
.rd-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ── PANELS ───────────────────────────────────────────────────────── */
.rd-panel {
  width: 280px;
  min-width: 240px;
  background: #141210;
  border-right: 1px solid rgba(200, 146, 42, 0.12);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ── TABS ─────────────────────────────────────────────────────────── */
.rd-tabs {
  display: flex;
  border-bottom: 1px solid rgba(200, 146, 42, 0.15);
}
.rd-tab {
  flex: 1;
  padding: 0.5rem 0.25rem;
  background: none;
  border: none;
  color: #887a66;
  font-size: 0.7rem;
  cursor: pointer;
  position: relative;
}
.rd-tab.active { color: #c89a2a; border-bottom: 2px solid #c89a2a; }
.rd-tab-badge { font-size: 0.6rem; margin-left: 2px; }

.rd-tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

/* ── TILE PALETTE ─────────────────────────────────────────────────── */
.rd-tile-category { margin-bottom: 0.75rem; }
.rd-cat-label { font-size: 0.7rem; color: #887a66; margin: 0 0 0.3rem; text-transform: uppercase; letter-spacing: 0.05em; }
.rd-tile-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.rd-tile-swatch {
  aspect-ratio: 1;
  border-radius: 4px;
  border: 2px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  position: relative;
  transition: border-color 0.15s;
}
.rd-tile-swatch:hover { border-color: rgba(200, 146, 42, 0.5); }
.rd-tile-swatch.selected { border-color: #c89a2a; box-shadow: 0 0 6px rgba(200, 146, 42, 0.4); }
.rd-tile-label {
  font-size: 0.55rem;
  color: #fff;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  padding: 1px 3px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 2px;
  margin-bottom: 2px;
}

/* ── BOM ──────────────────────────────────────────────────────────── */
.rd-bom-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-bottom: 0.75rem; }
.rd-bom-stat { font-size: 0.7rem; padding: 4px 6px; background: rgba(200, 146, 42, 0.08); border-radius: 4px; text-align: center; }
.rd-bom-heading { font-size: 0.75rem; color: #c89a2a; margin: 0.5rem 0 0.3rem; }
.rd-bom-mat-card {
  border: 1px solid rgba(200, 146, 42, 0.1);
  border-radius: 4px;
  padding: 0.4rem;
  margin-bottom: 0.4rem;
  font-size: 0.7rem;
}
.rd-bom-mat-header { display: flex; align-items: center; gap: 6px; }
.rd-bom-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.rd-bom-count { margin-left: auto; color: #887a66; }
.rd-bom-ring-detail { font-size: 0.65rem; color: #a09888; padding-left: 16px; }
.rd-bom-procurement { font-size: 0.6rem; color: #887a66; padding-left: 16px; margin-top: 2px; }
.rd-bom-strip { display: block; }
.rd-bom-ring-card {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  padding: 3px 0;
  border-bottom: 1px solid rgba(200, 146, 42, 0.06);
}
.rd-bom-actions { margin-top: 0.75rem; }

/* ── MFG ──────────────────────────────────────────────────────────── */
.rd-mfg-score {
  text-align: center;
  padding: 0.5rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}
.rd-mfg-score-num { font-size: 2rem; font-weight: 700; }
.rd-mfg-score-label { font-size: 0.9rem; color: #887a66; }
.score-good { background: rgba(60, 200, 80, 0.1); color: #60c060; }
.score-ok { background: rgba(220, 180, 40, 0.1); color: #eec830; }
.score-bad { background: rgba(220, 40, 40, 0.1); color: #ff6060; }

.rd-mfg-counts { display: flex; gap: 0.5rem; justify-content: center; margin-bottom: 0.5rem; font-size: 0.7rem; }
.rd-mfg-count.err { color: #ff6060; }
.rd-mfg-count.warn { color: #eec830; }
.rd-mfg-count.info { color: #88c8ee; }
.rd-mfg-count.ok { color: #60c060; }

.rd-mfg-flag {
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 0.4rem;
  font-size: 0.7rem;
}
.sev-error { background: rgba(220, 40, 40, 0.08); border-left: 3px solid #ff6060; }
.sev-warning { background: rgba(220, 180, 40, 0.08); border-left: 3px solid #eec830; }
.sev-info { background: rgba(80, 160, 220, 0.06); border-left: 3px solid #88c8ee; }
.rd-mfg-flag-header { display: flex; gap: 6px; align-items: center; margin-bottom: 4px; }
.rd-mfg-sev-icon { font-size: 0.8rem; }
.rd-mfg-flag-desc { color: #a09888; margin: 2px 0; }
.rd-mfg-flag-fix { color: #c89a2a; font-style: italic; margin: 2px 0; }

.rd-checkbox { font-size: 0.7rem; display: flex; align-items: center; gap: 6px; cursor: pointer; margin: 4px 0; }

/* ── BUTTONS ──────────────────────────────────────────────────────── */
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
.rd-btn-secondary { border-color: rgba(200, 146, 42, 0.15); color: #887a66; }
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

/* ── TOAST ─────────────────────────────────────────────────────────── */
.rd-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: #2a2418;
  border: 1px solid rgba(200, 146, 42, 0.3);
  color: #e8e0d0;
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 0.8rem;
  z-index: 1000;
  pointer-events: none;
}
.toast-enter-active, .toast-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

/* ── MODAL ─────────────────────────────────────────────────────────── */
.rd-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
}
.rd-modal {
  background: #1a1814;
  border: 1px solid rgba(200, 146, 42, 0.3);
  border-radius: 8px;
  padding: 1.5rem;
  min-width: 300px;
}
.rd-modal h3 { margin: 0 0 0.75rem; color: #c89a2a; font-size: 1rem; }
.rd-input {
  width: 100%;
  padding: 6px 10px;
  background: #0d0b08;
  border: 1px solid rgba(200, 146, 42, 0.3);
  border-radius: 4px;
  color: #e8e0d0;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}
.rd-modal-btns { display: flex; gap: 0.5rem; }

/* ── DRAG GHOST ────────────────────────────────────────────────────── */
.rd-drag-ghost {
  position: fixed;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 2px solid rgba(255, 220, 100, 0.7);
  opacity: 0.8;
  pointer-events: none;
  z-index: 999;
  transform: translate(-14px, -14px);
}

/* ── DRAFTING MODE ─────────────────────────────────────────────────── */
.rd-drafting :deep(.rd-canvas) { background: #e8e0d0; }

/* ── MISC ──────────────────────────────────────────────────────────── */
.rd-loading, .rd-empty { font-size: 0.75rem; color: #887a66; text-align: center; padding: 1rem; }
</style>
