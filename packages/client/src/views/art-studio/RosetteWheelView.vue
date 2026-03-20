<script setup lang="ts">
/**
 * RosetteWheelView — Active rosette designer
 * Embedded in SoundholeRosetteShell (Stage 1)
 * Also directly routed at /art-studio/rosette-designer
 *
 * Note: Large file (1,241 lines) by design —
 * wheel canvas, tile library, BOM, and MFG
 * checks are intentionally unified here.
 */
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRosetteWheelStore } from "@/stores/useRosetteWheelStore";
import type {
  SymmetryMode,
  TileDef,
  MfgFlag,
  RecipePreset,
  BomMaterialEntry,
  BomRingEntry,
} from "@/types/rosetteDesigner";

const store = useRosetteWheelStore();

// ── SVG canvas refs ────────────────────────────────────────────────────
const svgContainer = ref<HTMLDivElement | null>(null);
const wheelSvg = ref<SVGSVGElement | null>(null);

// ── Rename modal ───────────────────────────────────────────────────────
const showRenameModal = ref(false);
const renameInput = ref("");

// ── Import file input ref ──────────────────────────────────────────────
const importFileInput = ref<HTMLInputElement | null>(null);

// ── Drag ghost ─────────────────────────────────────────────────────────
const ghostPos = ref({ x: 0, y: 0 });
const ghostVisible = ref(false);

// ── SVG geometry constants ─────────────────────────────────────────────
const CX = 310;
const CY = 310;
const SVG_W = 620;
const SVG_H = 620;

// ── Computed helpers ───────────────────────────────────────────────────
const segAng = computed(() => 360 / store.numSegs);

const hoveredCellKey = computed<string | null>(() => {
  if (!store.hoveredCell) return null;
  return `${store.hoveredCell.ri}-${store.hoveredCell.si}`;
});

// ── Ring definitions from store (once loaded) ──────────────────────────
const ringDefs = computed(() => store.ringDefs);

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

// ── SVG math helpers ───────────────────────────────────────────────────
function rad(deg: number) { return deg * Math.PI / 180; }
function ptOnCircle(r: number, deg: number): [number, number] {
  const a = rad(deg - 90);
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
}
function fmt(n: number) { return n.toFixed(3); }

function arcCellPath(r1: number, r2: number, a1: number, a2: number): string {
  const [x1i, y1i] = ptOnCircle(r1, a1);
  const [x1o, y1o] = ptOnCircle(r2, a1);
  const [x2o, y2o] = ptOnCircle(r2, a2);
  const [x2i, y2i] = ptOnCircle(r1, a2);
  const lg = (a2 - a1) > 180 ? 1 : 0;
  return `M ${fmt(x1i)} ${fmt(y1i)} L ${fmt(x1o)} ${fmt(y1o)} A ${r2} ${r2} 0 ${lg} 1 ${fmt(x2o)} ${fmt(y2o)} L ${fmt(x2i)} ${fmt(y2i)} A ${r1} ${r1} 0 ${lg} 0 ${fmt(x1i)} ${fmt(y1i)} Z`;
}

function tabPathD(rI: number, rO: number, mid: number, halfW: number): string {
  const [x1, y1] = ptOnCircle(rI, mid - halfW);
  const [x2, y2] = ptOnCircle(rO, mid - halfW);
  const [x3, y3] = ptOnCircle(rO, mid + halfW);
  const [x4, y4] = ptOnCircle(rI, mid + halfW);
  return `M ${fmt(x1)} ${fmt(y1)} L ${fmt(x2)} ${fmt(y2)} L ${fmt(x3)} ${fmt(y3)} L ${fmt(x4)} ${fmt(y4)} Z`;
}

// ── Cell fill ──────────────────────────────────────────────────────────
function cellFill(tileId: string): string {
  if (!tileId || tileId === "clear") return "none";
  const tile = store.tiles[tileId];
  if (!tile) return "#888";
  if (tile.type === "solid") return tile.color || "#888";
  return `url(#pat-${tile.type})`;
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

// ── Import handler ─────────────────────────────────────────────────────
function triggerImport() {
  importFileInput.value?.click();
}

function onImportFile(ev: Event) {
  const target = ev.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    store.importJSON(file);
    target.value = "";
  }
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

// ── Symmetry mode labels ───────────────────────────────────────────────
const SYM_MODES: { mode: SymmetryMode; label: string; icon: string }[] = [
  { mode: "none", label: "None", icon: "·" },
  { mode: "rotational", label: "Rot ×N", icon: "⟳" },
  { mode: "bilateral", label: "Mirror", icon: "↔" },
  { mode: "quadrant", label: "Quad ×4", icon: "✦" },
];

// ── Guide circle radii ────────────────────────────────────────────────
const GUIDE_CIRCLES = [
  { r: 150, dash: false, tab: false },
  { r: 190, dash: false, tab: false },
  { r: 200, dash: true, tab: true },
  { r: 210, dash: false, tab: false },
  { r: 300, dash: false, tab: false },
  { r: 312, dash: true, tab: true },
  { r: 320, dash: false, tab: false },
  { r: 350, dash: false, tab: false },
];
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

        <!-- LIBRARY TAB -->
        <div v-if="store.activeTab === 'library'" class="rd-tab-content">
          <h3 class="rd-section-title">Recipe Presets</h3>
          <div class="rd-recipe-list">
            <div
              v-for="recipe in store.recipes"
              :key="recipe.id"
              class="rd-recipe-card"
              :class="{ active: store.activeRecipeId === recipe.id }"
              @click="store.loadRecipe(recipe)"
            >
              <div class="rd-recipe-header">
                <strong>{{ recipe.name }}</strong>
                <span class="rd-recipe-segs">{{ recipe.num_segs }} seg</span>
              </div>
              <p class="rd-recipe-desc">{{ recipe.desc }}</p>
              <div class="rd-recipe-tags">
                <span v-for="tag in recipe.tags" :key="tag" class="rd-tag">{{ tag }}</span>
              </div>
            </div>
          </div>

          <h3 class="rd-section-title" style="margin-top: 1rem">Saved Designs</h3>
          <div v-if="Object.keys(store.savedDesigns).length === 0" class="rd-empty">
            No saved designs yet
          </div>
          <div v-else class="rd-saved-list">
            <div
              v-for="(state, name) in store.savedDesigns"
              :key="name"
              class="rd-saved-card"
            >
              <span class="rd-saved-name" @click="store.loadDesign(state)">{{ name }}</span>
              <button class="rd-btn-xs rd-btn-danger" @click="store.deleteSavedDesign(String(name))">✕</button>
            </div>
          </div>

          <div class="rd-import-section">
            <button class="rd-btn" @click="triggerImport">📂 Import .rsd</button>
            <input
              ref="importFileInput"
              type="file"
              accept=".rsd,.json"
              style="display: none"
              @change="onImportFile"
            />
          </div>
        </div>

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

      <!-- ── CENTER: SVG WHEEL CANVAS ─────────────────────────────── -->
      <main class="rd-canvas" ref="svgContainer">
        <svg
          ref="wheelSvg"
          :viewBox="`0 0 ${SVG_W} ${SVG_H}`"
          :width="SVG_W"
          :height="SVG_H"
          class="rd-wheel-svg"
          xmlns="http://www.w3.org/2000/svg"
        >
          <!-- Pattern defs -->
          <defs>
            <!-- Abalone gradient + pattern -->
            <linearGradient id="g-abalone" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#6ae0d0"/><stop offset="28%" stop-color="#50c8e8"/>
              <stop offset="55%" stop-color="#8860d0"/><stop offset="78%" stop-color="#50e890"/>
              <stop offset="100%" stop-color="#60b8e8"/>
            </linearGradient>
            <pattern id="pat-abalone" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
              <rect width="28" height="28" fill="url(#g-abalone)" opacity="0.88"/>
              <ellipse cx="9" cy="9" rx="7" ry="4" fill="rgba(255,255,255,0.18)" transform="rotate(-30,9,9)"/>
              <ellipse cx="20" cy="20" rx="5" ry="3" fill="rgba(255,255,255,0.12)" transform="rotate(20,20,20)"/>
            </pattern>
            <!-- MOP -->
            <linearGradient id="g-mop" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="#f0f0ee"/><stop offset="45%" stop-color="#e8ddf8"/>
              <stop offset="100%" stop-color="#d8f0ee"/>
            </linearGradient>
            <pattern id="pat-mop" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
              <rect width="18" height="18" fill="url(#g-mop)"/>
              <line x1="0" y1="9" x2="18" y2="9" stroke="rgba(200,190,220,0.28)" stroke-width="0.5"/>
              <line x1="9" y1="0" x2="9" y2="18" stroke="rgba(200,190,220,0.2)" stroke-width="0.5"/>
            </pattern>
            <!-- Burl -->
            <pattern id="pat-burl" x="0" y="0" width="22" height="15" patternUnits="userSpaceOnUse">
              <rect width="22" height="15" fill="#C8A048"/>
              <ellipse cx="6" cy="7" rx="4.5" ry="2.5" fill="none" stroke="#a07828" stroke-width="1" opacity="0.55"/>
              <ellipse cx="15" cy="5" rx="3.5" ry="2" fill="none" stroke="#b09030" stroke-width="0.8" opacity="0.5"/>
            </pattern>
            <!-- Herringbone -->
            <pattern id="pat-herringbone" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
              <rect width="20" height="20" fill="#C09850"/>
              <line x1="-2" y1="12" x2="8" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
              <line x1="2" y1="16" x2="14" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
              <line x1="7" y1="20" x2="20" y2="4" stroke="#7a5c28" stroke-width="2.8"/>
              <line x1="10" y1="-2" x2="22" y2="14" stroke="#5a3c10" stroke-width="2.8"/>
              <line x1="5" y1="-2" x2="20" y2="16" stroke="#5a3c10" stroke-width="2.8"/>
              <line x1="-2" y1="4" x2="12" y2="20" stroke="#5a3c10" stroke-width="2.8"/>
            </pattern>
            <!-- Checker -->
            <pattern id="pat-checker" x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
              <rect width="14" height="14" fill="#f0e8d8"/>
              <rect x="0" y="0" width="7" height="7" fill="#1a1a1a"/>
              <rect x="7" y="7" width="7" height="7" fill="#1a1a1a"/>
            </pattern>
            <!-- Celtic -->
            <pattern id="pat-celtic" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
              <rect width="24" height="24" fill="#1a3a2a"/>
              <path d="M4,4 Q12,12 20,4 Q12,0 4,4Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
              <path d="M4,20 Q12,12 20,20 Q12,24 4,20Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
              <circle cx="12" cy="12" r="3" fill="none" stroke="#50c880" stroke-width="1.5"/>
            </pattern>
            <!-- Diagonal -->
            <pattern id="pat-diagonal" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
              <rect width="12" height="12" fill="#c8922a"/>
              <line x1="-2" y1="10" x2="10" y2="-2" stroke="#8B5a10" stroke-width="3.5"/>
              <line x1="4" y1="14" x2="14" y2="4" stroke="#8B5a10" stroke-width="3.5"/>
            </pattern>
            <!-- Dots -->
            <pattern id="pat-dots" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
              <rect width="12" height="12" fill="#f5e6c8"/>
              <circle cx="6" cy="6" r="2.4" fill="#1a1a1a"/>
            </pattern>
            <!-- BWB stripes -->
            <pattern id="pat-stripes" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="9" height="3" fill="#111"/>
              <rect x="0" y="3" width="9" height="3" fill="#eee"/>
              <rect x="0" y="6" width="9" height="3" fill="#111"/>
            </pattern>
            <!-- RBR stripes -->
            <pattern id="pat-stripes2" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="9" height="3" fill="#cc0033"/>
              <rect x="0" y="3" width="9" height="3" fill="#111"/>
              <rect x="0" y="6" width="9" height="3" fill="#cc0033"/>
            </pattern>
            <!-- WBW stripes -->
            <pattern id="pat-stripes3" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="9" height="3" fill="#eee"/>
              <rect x="0" y="3" width="9" height="3" fill="#111"/>
              <rect x="0" y="6" width="9" height="3" fill="#eee"/>
            </pattern>
            <!-- Soundhole gradient -->
            <radialGradient id="g-soundhole" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stop-color="#060402"/>
              <stop offset="100%" stop-color="#0d0905"/>
            </radialGradient>
            <!-- MFG hatch pattern -->
            <pattern id="pat-mfg-hatch" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(255,40,40,0.55)" stroke-width="3"/>
            </pattern>
          </defs>

          <!-- Outer decorative ring -->
          <circle :cx="CX" :cy="CY" r="354" fill="none" stroke="rgba(200,146,42,0.12)" stroke-width="8"/>

          <!-- Soundhole -->
          <circle :cx="CX" :cy="CY" r="148" fill="url(#g-soundhole)" stroke="rgba(200,146,42,0.45)" stroke-width="1.2"/>

          <!-- Ring backgrounds -->
          <template v-for="(rd, ri) in ringDefs" :key="`bg-${ri}`">
            <path
              :d="arcCellPath(rd.r1, rd.r2, 0, 359.999)"
              :fill="rd.has_tabs && store.ringActive[ri] ? '#12282e' : store.ringActive[ri] ? rd.color : 'rgba(20,18,14,0.5)'"
              :opacity="store.ringActive[ri] ? 1 : 0.35"
              stroke="none"
            />
          </template>

          <!-- Cells (interactive) -->
          <template v-for="(rd, ri) in ringDefs" :key="`cells-${ri}`">
            <template v-for="si in store.numSegs" :key="`cell-${ri}-${si - 1}`">
              <path
                :d="arcCellPath(rd.r1, rd.r2, (si - 1) * segAng, si * segAng)"
                :fill="store.grid[`${ri}-${si - 1}`] ? cellFill(store.grid[`${ri}-${si - 1}`]) : 'none'"
                :stroke="hoveredCellKey === `${ri}-${si - 1}` ? 'rgba(255,220,100,0.8)' : 'rgba(200,146,42,0.22)'"
                :stroke-width="hoveredCellKey === `${ri}-${si - 1}` ? 2 : 0.5"
                class="rd-cell"
                :class="{ 'rd-cell-active': store.ringActive[ri] }"
                @click="onCellClick(ri, si - 1)"
                @mouseenter="onCellEnter(ri, si - 1)"
                @mouseleave="onCellLeave()"
                @mouseup="onCellDrop(ri, si - 1)"
              />
            </template>
          </template>

          <!-- Extension tabs (Main Channel) -->
          <template v-if="store.showTabs">
            <template v-for="(rd, ri) in ringDefs" :key="`tabs-${ri}`">
              <template v-if="rd.has_tabs && store.ringActive[ri]">
                <template v-for="si in store.numSegs" :key="`tab-${ri}-${si - 1}`">
                  <!-- Outer tab -->
                  <path
                    :d="tabPathD(rd.r2, rd.tab_outer_r, ((si - 1) + 0.5) * segAng, rd.tab_ang_width / 2)"
                    :fill="store.grid[`${ri}-${si - 1}`]
                      ? cellFill(store.grid[`${ri}-${si - 1}`])
                      : ((si - 1) % 2 === 0 ? rd.tab_fill_even : rd.tab_fill_odd)"
                    stroke="#1a1a2e"
                    stroke-width="0.7"
                    opacity="0.92"
                  />
                  <!-- Inner tab -->
                  <path
                    :d="tabPathD(rd.tab_inner_r, rd.r1, ((si - 1) + 0.5) * segAng, rd.tab_ang_width / 2)"
                    :fill="store.grid[`${ri}-${si - 1}`]
                      ? cellFill(store.grid[`${ri}-${si - 1}`])
                      : ((si - 1) % 2 === 0 ? rd.tab_fill_even : rd.tab_fill_odd)"
                    stroke="#1a1a2e"
                    stroke-width="0.7"
                    opacity="0.85"
                  />
                </template>
              </template>
            </template>
          </template>

          <!-- MFG Overlay -->
          <template v-if="store.showMfgOverlay && store.mfgResult">
            <template v-for="mc in mfgOverlayCells" :key="`mfg-${mc.ri}-${mc.si}`">
              <path
                v-if="ringDefs[mc.ri]"
                :d="arcCellPath(ringDefs[mc.ri].r1, ringDefs[mc.ri].r2,
                  mc.si * segAng, (mc.si + 1) * segAng)"
                fill="url(#pat-mfg-hatch)"
                stroke="rgba(255,40,40,0.7)"
                stroke-width="1.5"
                pointer-events="none"
              />
            </template>
          </template>

          <!-- Guide circles -->
          <template v-for="gc in GUIDE_CIRCLES" :key="`guide-${gc.r}`">
            <circle
              :cx="CX" :cy="CY" :r="gc.r"
              fill="none"
              :stroke="gc.tab ? 'rgba(200,146,42,0.18)' : 'rgba(200,146,42,0.38)'"
              :stroke-width="gc.tab ? 0.4 : 0.7"
              :stroke-dasharray="gc.dash ? '2,3' : 'none'"
            />
          </template>

          <!-- Radial lines -->
          <template v-for="si in store.numSegs" :key="`radial-${si}`">
            <line
              :x1="ptOnCircle(150, (si - 1) * segAng)[0]"
              :y1="ptOnCircle(150, (si - 1) * segAng)[1]"
              :x2="ptOnCircle(350, (si - 1) * segAng)[0]"
              :y2="ptOnCircle(350, (si - 1) * segAng)[1]"
              stroke="rgba(200,146,42,0.28)"
              stroke-width="0.55"
            />
          </template>

          <!-- Center crosshair -->
          <line :x1="CX - 14" :y1="CY" :x2="CX + 14" :y2="CY" stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>
          <line :x1="CX" :y1="CY - 14" :x2="CX" :y2="CY + 14" stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>
          <circle :cx="CX" :cy="CY" r="4" fill="none" stroke="rgba(200,146,42,0.55)" stroke-width="0.8"/>

          <!-- Annotations (drafting overlay) -->
          <template v-if="store.showAnnotations">
            <rect x="0" y="0" :width="SVG_W" :height="SVG_H" fill="#f5f0e8" opacity="0.85"/>
            <!-- Diameter dims -->
            <g v-for="dim in [
              { r: 350, label: 'Ø 7.00″', yOff: -15 },
              { r: 300, label: 'Ø 6.00″', yOff: -10 },
              { r: 150, label: 'Ø 3.00″', yOff: 20 },
            ]" :key="dim.r">
              <line :x1="CX - dim.r" :y1="CY + dim.yOff" :x2="CX + dim.r" :y2="CY + dim.yOff"
                stroke="#1a1a2e" stroke-width="0.7"/>
              <text :x="CX" :y="CY + dim.yOff - 5" fill="#1a1a2e" font-family="monospace"
                font-size="8" text-anchor="middle">{{ dim.label }}</text>
            </g>
            <!-- Segment label -->
            <text :x="CX" :y="CY + 180" fill="#1a1a2e" font-family="monospace" font-size="8"
              text-anchor="middle">
              {{ store.numSegs }} EQUAL DIVISIONS × {{ segAng.toFixed(1) }}°
            </text>
            <!-- Section line -->
            <line x1="30" :y1="CY" :x2="SVG_W - 30" :y2="CY" stroke="#1a1a2e" stroke-width="0.8"
              stroke-dasharray="8,4,2,4"/>
          </template>
        </svg>
      </main>

      <!-- ── RIGHT PANEL (CONTROLS / INSPECTOR) ──────────────────── -->
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
            <button class="rd-btn" @click="fillRingWithSelected(2)" :disabled="!store.selectedTile">Fill Main Channel</button>
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
.rd-panel-right {
  border-right: none;
  border-left: 1px solid rgba(200, 146, 42, 0.12);
  padding: 0.75rem;
  gap: 0.75rem;
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

/* ── RECIPE LIBRARY ───────────────────────────────────────────────── */
.rd-section-title { font-size: 0.8rem; color: #c89a2a; margin: 0 0 0.5rem; }
.rd-recipe-list { display: flex; flex-direction: column; gap: 0.5rem; }
.rd-recipe-card {
  background: rgba(200, 146, 42, 0.06);
  border: 1px solid rgba(200, 146, 42, 0.12);
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.rd-recipe-card:hover { border-color: rgba(200, 146, 42, 0.35); }
.rd-recipe-card.active { border-color: #c89a2a; }
.rd-recipe-header { display: flex; justify-content: space-between; align-items: center; }
.rd-recipe-segs { font-size: 0.65rem; color: #887a66; }
.rd-recipe-desc { font-size: 0.7rem; color: #a09888; margin: 0.25rem 0; }
.rd-recipe-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.rd-tag { font-size: 0.6rem; padding: 1px 6px; background: rgba(200, 146, 42, 0.12); border-radius: 8px; color: #c89a2a; }

.rd-saved-list { display: flex; flex-direction: column; gap: 4px; }
.rd-saved-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  background: rgba(200, 146, 42, 0.06);
  border-radius: 4px;
}
.rd-saved-name { cursor: pointer; font-size: 0.75rem; }
.rd-saved-name:hover { color: #c89a2a; }
.rd-import-section { margin-top: 0.75rem; }

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

/* ── CANVAS ───────────────────────────────────────────────────────── */
.rd-canvas {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d0b08;
  overflow: auto;
  padding: 1rem;
}

.rd-wheel-svg { max-width: 100%; max-height: 100%; }

.rd-cell { cursor: pointer; transition: stroke 0.1s; }
.rd-cell.rd-cell-active:hover { stroke: rgba(255, 220, 100, 0.7) !important; stroke-width: 2 !important; }

/* ── CONTROLS ─────────────────────────────────────────────────────── */
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
.rd-btn-xs { padding: 1px 6px; font-size: 0.65rem; border: none; background: none; color: #887a66; cursor: pointer; }
.rd-btn-danger { color: #ff6060; }
.rd-btn-danger:hover { color: #ff3030; }

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
.rd-drafting .rd-canvas { background: #e8e0d0; }

/* ── MISC ──────────────────────────────────────────────────────────── */
.rd-loading, .rd-empty { font-size: 0.75rem; color: #887a66; text-align: center; padding: 1rem; }
</style>
