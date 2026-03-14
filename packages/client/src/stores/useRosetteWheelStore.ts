/**
 * Rosette Wheel Store — Interactive Wheel Designer
 *
 * Full state management for the rosette wheel (tile-grid) designer.
 * Snapshot-based undo/redo (max 50 states), BOM, MFG intelligence,
 * 8 recipes, drag-drop, save/load, dual SVG export.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type {
  SymmetryMode,
  RosetteDesignState,
  RingDef,
  TileDef,
  TileCategory,
  BomResponse,
  MfgCheckResponse,
  RecipePreset,
  CellInfoResponse,
} from "@/types/rosetteDesigner";
import * as artRosetteWheel from "@/sdk/endpoints/artRosetteWheel";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_HISTORY = 50;
const SEG_OPTIONS = [6, 8, 10, 12, 16, 20, 24];

// ---------------------------------------------------------------------------
// Snapshot type (for undo/redo)
// ---------------------------------------------------------------------------

interface DesignSnapshot {
  num_segs: number;
  sym_mode: SymmetryMode;
  grid: Record<string, string>;
  ring_active: boolean[];
  show_tabs: boolean;
  show_annotations: boolean;
  design_name: string;
  timestamp: number;
}


// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useRosetteWheelStore = defineStore("rosetteWheel", () => {
  // ── Catalog ──────────────────────────────────────────────────────────────
  const tiles = ref<Record<string, TileDef>>({});
  const categories = ref<TileCategory[]>([]);
  const ringDefs = ref<RingDef[]>([]);
  const segOptions = ref<number[]>(SEG_OPTIONS);
  const recipes = ref<RecipePreset[]>([]);
  const catalogLoaded = ref(false);

  // ── Design state ─────────────────────────────────────────────────────────
  const numSegs = ref(12);
  const symMode = ref<SymmetryMode>("none");
  const grid = ref<Record<string, string>>({});
  const ringActive = ref<boolean[]>([true, true, true, true, true]);
  const showTabs = ref(true);
  const showAnnotations = ref(false);
  const designName = ref("Untitled Design");
  const activeRecipeId = ref<string | null>(null);

  // ── Selection / Interaction ──────────────────────────────────────────────
  const selectedTile = ref<string | null>("maple");
  const hoveredCell = ref<{ ri: number; si: number } | null>(null);
  const cellInfo = ref<CellInfoResponse | null>(null);
  const activeTab = ref<"tiles" | "library" | "bom" | "mfg">("tiles");

  // ── Drag state ───────────────────────────────────────────────────────────
  const isDragging = ref(false);
  const dragTileId = ref<string | null>(null);

  // ── BOM ──────────────────────────────────────────────────────────────────
  const bom = ref<BomResponse | null>(null);
  const bomLoading = ref(false);

  // ── MFG ──────────────────────────────────────────────────────────────────
  const mfgResult = ref<MfgCheckResponse | null>(null);
  const mfgLoading = ref(false);
  const showMfgOverlay = ref(true);

  // ── SVG Preview ──────────────────────────────────────────────────────────
  const previewSvg = ref("");
  const previewLoading = ref(false);

  // ── Undo / Redo ──────────────────────────────────────────────────────────
  const undoStack = ref<DesignSnapshot[]>([]);
  const redoStack = ref<DesignSnapshot[]>([]);
  const canUndo = computed(() => undoStack.value.length > 0);
  const canRedo = computed(() => redoStack.value.length > 0);

  // ── Saved designs ────────────────────────────────────────────────────────
  const savedDesigns = ref<Record<string, RosetteDesignState>>({});

  // ── Toast ────────────────────────────────────────────────────────────────
  const toastMessage = ref("");
  const toastVisible = ref(false);
  let toastTimer: ReturnType<typeof setTimeout> | null = null;

  // ── Computed ─────────────────────────────────────────────────────────────
  const filledCellCount = computed(() => Object.keys(grid.value).length);
  const totalCellCount = computed(() => ringDefs.value.length * numSegs.value);
  const fillPercent = computed(() =>
    totalCellCount.value > 0
      ? Math.round((filledCellCount.value / totalCellCount.value) * 100)
      : 0
  );
  const mfgBadge = computed(() => {
    if (!mfgResult.value) return null;
    const { error_count, warning_count, info_count } = mfgResult.value;
    if (error_count > 0) return { text: `${error_count}`, cls: "badge-error" };
    if (warning_count > 0) return { text: `${warning_count}`, cls: "badge-warn" };
    if (info_count > 0) return { text: `${info_count}`, cls: "badge-info" };
    return { text: "✓", cls: "badge-ok" };
  });

  // ── Snapshot helpers ─────────────────────────────────────────────────────
  function _snap(): DesignSnapshot {
    return {
      num_segs: numSegs.value,
      sym_mode: symMode.value,
      grid: { ...grid.value },
      ring_active: [...ringActive.value],
      show_tabs: showTabs.value,
      show_annotations: showAnnotations.value,
      design_name: designName.value,
      timestamp: Date.now(),
    };
  }

  function pushUndo() {
    undoStack.value.push(_snap());
    if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift();
    redoStack.value = [];
  }

  function _applySnap(snap: DesignSnapshot) {
    numSegs.value = snap.num_segs;
    symMode.value = snap.sym_mode;
    grid.value = { ...snap.grid };
    ringActive.value = [...snap.ring_active];
    showTabs.value = snap.show_tabs;
    showAnnotations.value = snap.show_annotations;
    designName.value = snap.design_name;
  }

  function undo() {
    if (!canUndo.value) return;
    redoStack.value.push(_snap());
    _applySnap(undoStack.value.pop()!);
  }

  function redo() {
    if (!canRedo.value) return;
    undoStack.value.push(_snap());
    _applySnap(redoStack.value.pop()!);
  }

  // ── Toast ────────────────────────────────────────────────────────────────
  function showToast(msg: string, duration = 2500) {
    toastMessage.value = msg;
    toastVisible.value = true;
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastVisible.value = false; }, duration);
  }

  // ── Catalog / Init ───────────────────────────────────────────────────────
  async function loadCatalog() {
    if (catalogLoaded.value) return;
    try {
      const [catalog, recipeList] = await Promise.all([
        artRosetteWheel.fetchCatalog(),
        artRosetteWheel.fetchRecipes(),
      ]);
      tiles.value = catalog.tile_map;
      categories.value = catalog.categories;
      ringDefs.value = catalog.ring_defs;
      segOptions.value = catalog.seg_options;
      recipes.value = recipeList.recipes;
      catalogLoaded.value = true;
    } catch (err) {
      console.error("Failed to load rosette designer catalog:", err);
    }
  }

  // ── Place tile ───────────────────────────────────────────────────────────
  async function placeTile(ri: number, si: number, tileId: string) {
    pushUndo();
    try {
      const resp = await artRosetteWheel.placeTile({
        ring_idx: ri, seg_idx: si, tile_id: tileId,
        num_segs: numSegs.value, sym_mode: symMode.value,
        grid: grid.value, ring_active: ringActive.value,
      });
      grid.value = resp.grid;
      refreshMfg();
      if (activeTab.value === "bom") refreshBom();
    } catch (err) {
      console.error("Place tile failed:", err);
    }
  }

  async function clearCell(ri: number, si: number) {
    await placeTile(ri, si, "clear");
  }

  function fillRing(ri: number, tileId: string) {
    if (!tileId) return;
    pushUndo();
    const g = { ...grid.value };
    for (let s = 0; s < numSegs.value; s++) {
      if (ringActive.value[ri]) g[`${ri}-${s}`] = tileId;
    }
    grid.value = g;
    refreshMfg();
  }

  function clearAll() {
    pushUndo();
    grid.value = {};
    activeRecipeId.value = null;
    refreshMfg();
    showToast("Design cleared");
  }

  // ── Segment controls ────────────────────────────────────────────────────
  function setNumSegs(n: number) {
    if (n === numSegs.value) return;
    if (!segOptions.value.includes(n)) return;
    pushUndo();
    numSegs.value = n;
    grid.value = {};
    refreshMfg();
  }

  function incrSegs() {
    const i = segOptions.value.indexOf(numSegs.value);
    if (i < segOptions.value.length - 1) setNumSegs(segOptions.value[i + 1]);
  }

  function decrSegs() {
    const i = segOptions.value.indexOf(numSegs.value);
    if (i > 0) setNumSegs(segOptions.value[i - 1]);
  }

  // ── Symmetry ─────────────────────────────────────────────────────────────
  function setSymMode(mode: SymmetryMode) { symMode.value = mode; }

  // ── Ring toggles ─────────────────────────────────────────────────────────
  function toggleRing(ri: number) {
    pushUndo();
    const a = [...ringActive.value];
    a[ri] = !a[ri];
    ringActive.value = a;
  }

  function toggleTabs() { showTabs.value = !showTabs.value; }
  function toggleAnnotations() { showAnnotations.value = !showAnnotations.value; }
  function selectTile(id: string | null) { selectedTile.value = id; }

  // ── Drag & Drop ──────────────────────────────────────────────────────────
  function startDrag(tileId: string) { isDragging.value = true; dragTileId.value = tileId; }
  function endDrag() { isDragging.value = false; dragTileId.value = null; }

  // ── Hover ────────────────────────────────────────────────────────────────
  function setHoveredCell(ri: number, si: number) { hoveredCell.value = { ri, si }; }
  function clearHoveredCell() { hoveredCell.value = null; cellInfo.value = null; }

  // ── BOM ──────────────────────────────────────────────────────────────────
  async function refreshBom() {
    bomLoading.value = true;
    try {
      bom.value = await artRosetteWheel.computeBom({
        num_segs: numSegs.value, grid: grid.value, ring_active: ringActive.value,
      });
    } catch (err) { console.error("BOM refresh failed:", err); }
    finally { bomLoading.value = false; }
  }

  async function exportBomCsv() {
    try {
      const csvStr = await artRosetteWheel.exportBomCsv({
        num_segs: numSegs.value, grid: grid.value,
        ring_active: ringActive.value, design_name: designName.value,
      });
      const blob = new Blob([csvStr], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${designName.value || "rosette"}_bom.csv`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("BOM exported as CSV");
    } catch (err) { console.error("BOM CSV export failed:", err); }
  }

  // ── MFG ──────────────────────────────────────────────────────────────────
  async function refreshMfg() {
    mfgLoading.value = true;
    try {
      mfgResult.value = await artRosetteWheel.runMfgCheck({
        num_segs: numSegs.value,
        grid: grid.value, ring_active: ringActive.value,
      });
    } catch (err) { console.error("MFG check failed:", err); }
    finally { mfgLoading.value = false; }
  }

  async function applyMfgAutoFix() {
    pushUndo();
    try {
      const resp = await artRosetteWheel.applyMfgAutoFix({
        num_segs: numSegs.value,
        grid: grid.value, ring_active: ringActive.value,
      });
      grid.value = resp.grid;
      await refreshMfg();
      showToast("Auto-fix applied");
    } catch (err) { console.error("MFG auto-fix failed:", err); }
  }

  // ── Recipes ──────────────────────────────────────────────────────────────
  function loadRecipe(recipe: RecipePreset) {
    pushUndo();
    numSegs.value = recipe.num_segs;
    symMode.value = recipe.sym_mode;
    grid.value = { ...recipe.grid };
    ringActive.value = [...recipe.ring_active];
    activeRecipeId.value = recipe.id;
    designName.value = recipe.name;
    refreshMfg();
    showToast(`Loaded recipe: ${recipe.name}`);
  }

  // ── Save / Load ──────────────────────────────────────────────────────────
  function captureState(): RosetteDesignState {
    return {
      version: 3,
      design_name: designName.value,
      num_segs: numSegs.value,
      sym_mode: symMode.value,
      grid: { ...grid.value },
      ring_active: [...ringActive.value],
      show_tabs: showTabs.value,
      show_annotations: showAnnotations.value,
    };
  }

  function loadDesign(state: RosetteDesignState, recipeId?: string | null) {
    pushUndo();
    designName.value = state.design_name;
    numSegs.value = state.num_segs;
    symMode.value = state.sym_mode;
    grid.value = { ...state.grid };
    ringActive.value = [...state.ring_active];
    showTabs.value = state.show_tabs;
    showAnnotations.value = state.show_annotations;
    activeRecipeId.value = recipeId ?? null;
    refreshMfg();
  }

  function saveToSession() {
    const state = captureState();
    const key = designName.value || "Untitled Design";
    savedDesigns.value = { ...savedDesigns.value, [key]: state };
    try { localStorage.setItem("rosette-designs", JSON.stringify(savedDesigns.value)); }
    catch { /* quota exceeded */ }
    showToast(`Saved: ${key}`);
  }

  function loadSavedDesigns() {
    try {
      const raw = localStorage.getItem("rosette-designs");
      if (raw) savedDesigns.value = JSON.parse(raw);
    } catch { /* corrupt data */ }
  }

  function deleteSavedDesign(name: string) {
    const d = { ...savedDesigns.value };
    delete d[name];
    savedDesigns.value = d;
    try { localStorage.setItem("rosette-designs", JSON.stringify(savedDesigns.value)); }
    catch { /* non-critical */ }
    showToast(`Deleted: ${name}`);
  }

  function exportJSON() {
    const state = captureState();
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${designName.value || "rosette"}.rsd`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Design exported as .rsd");
  }

  async function importJSON(file: File): Promise<void> {
    const text = await file.text();
    let state: RosetteDesignState;
    try { state = JSON.parse(text); }
    catch { showToast("Invalid file format"); return; }
    if (!state.version || !state.grid || !state.ring_active) {
      showToast("Not a valid rosette design file");
      return;
    }
    loadDesign(state);
    showToast(`Imported: ${state.design_name}`);
  }

  // ── SVG export ───────────────────────────────────────────────────────────
  async function exportDesignSvg() {
    try {
      const blob = await artRosetteWheel.exportSvg({
        num_segs: numSegs.value, grid: grid.value,
        ring_active: ringActive.value, show_tabs: showTabs.value,
        show_annotations: false, width: 620, height: 620,
        design_name: designName.value, with_annotations: false,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${designName.value || "rosette"}_design.svg`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("Design SVG exported");
    } catch (err) { console.error("SVG export failed:", err); }
  }

  async function exportDraftingSvg() {
    try {
      const blob = await artRosetteWheel.exportSvg({
        num_segs: numSegs.value, grid: grid.value,
        ring_active: ringActive.value, show_tabs: showTabs.value,
        show_annotations: true, width: 620, height: 620,
        design_name: designName.value, with_annotations: true,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${designName.value || "rosette"}_drafting.svg`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("Drafting SVG exported");
    } catch (err) { console.error("Drafting SVG export failed:", err); }
  }

  // ── Rename / Reset ───────────────────────────────────────────────────────
  function rename(newName: string) { designName.value = newName; showToast(`Renamed to: ${newName}`); }

  function resetDesign() {
    pushUndo();
    numSegs.value = 12; symMode.value = "none"; grid.value = {};
    ringActive.value = [true, true, true, true, true];
    showTabs.value = true; showAnnotations.value = false;
    designName.value = "Untitled Design"; activeRecipeId.value = null;
    refreshMfg();
  }

  return {
    tiles, categories, ringDefs, segOptions, recipes, catalogLoaded, loadCatalog,
    numSegs, symMode, grid, ringActive, showTabs, showAnnotations, designName, activeRecipeId,
    selectedTile, hoveredCell, cellInfo, activeTab,
    isDragging, dragTileId,
    filledCellCount, totalCellCount, fillPercent, mfgBadge,
    bom, bomLoading, refreshBom, exportBomCsv,
    mfgResult, mfgLoading, showMfgOverlay, refreshMfg, applyMfgAutoFix,
    previewSvg, previewLoading,
    undoStack, redoStack, canUndo, canRedo, undo, redo,
    savedDesigns, saveToSession, loadSavedDesigns, deleteSavedDesign,
    placeTile, clearCell, fillRing, clearAll,
    setNumSegs, incrSegs, decrSegs, setSymMode,
    toggleRing, toggleTabs, toggleAnnotations,
    selectTile, startDrag, endDrag,
    setHoveredCell, clearHoveredCell,
    loadRecipe, loadDesign, captureState,
    exportJSON, importJSON, exportDesignSvg, exportDraftingSvg,
    rename, resetDesign,
    toastMessage, toastVisible, showToast,
  };
});
