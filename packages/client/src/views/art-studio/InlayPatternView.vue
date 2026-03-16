<script setup lang="ts">
/**
 * @deprecated Use InlayWorkspaceShell at /art-studio/inlay-workspace (Stage 1: Pattern Library).
 * InlayPatternView — Marquetry Pattern Generator
 *
 * Endpoints:
 *   GET  /api/art/inlay-patterns
 *   POST /api/art/inlay-patterns/generate
 *   POST /api/art/inlay-patterns/export
 *   POST /api/art/inlay-patterns/bom
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useInlayHistoryStore, type InlaySnapshot } from "@/stores/useInlayHistoryStore";
import { MeasurementTool, type Measurement, type Point3D } from "@/util/measurementTool";
import InlayMeasurePanel from "@/components/art/inlay_patterns/InlayMeasurePanel.vue";
import InlayBomPanel from "@/components/art/inlay_patterns/InlayBomPanel.vue";

const API_BASE = "/api/art/inlay-patterns";
const history = useInlayHistoryStore();

// ── Generator list ─────────────────────────────────────────────────────
interface GeneratorInfo {
  shape: string;
  name: string;
  description: string;
  is_linear: boolean;
}
const generators = ref<GeneratorInfo[]>([]);

// ── Form state ─────────────────────────────────────────────────────────
const shape = ref("herringbone");
const params = ref<Record<string, unknown>>({});
const materials = ref<string[]>(["mop", "ebony", "koa"]);
const bgMaterial = ref("ebony");
const includeOffsets = ref(false);
const maleOffsetMm = ref(0.1);
const pocketOffsetMm = ref(0.1);

// ── Response state ─────────────────────────────────────────────────────
const loading = ref(false);
const error = ref("");
const previewSvg = ref("");
const resultMeta = ref<{
  shape: string;
  width_mm: number;
  height_mm: number;
  element_count: number;
  warnings: string[];
} | null>(null);

// ── BOM state ──────────────────────────────────────────────────────────
const bomEntries = ref<
  { shape_type: string; material_key: string; count: number; area_mm2: number }[]
>([]);
const bomTotal = ref<{ total_pieces: number; total_area_mm2: number } | null>(null);

// ── Export state ───────────────────────────────────────────────────────
const exportFormat = ref<"svg" | "dxf" | "layered_svg">("svg");
const exporting = ref(false);

// ── Measurement tool ───────────────────────────────────────────────────
const measureTool = new MeasurementTool({ units: "mm", precision: 2 });
const measureMode = ref(false);
const measurements = ref<Measurement[]>([]);
const pendingMeasureStart = ref<Point3D | null>(null);

function toggleMeasureMode(): void {
  measureMode.value = !measureMode.value;
  if (!measureMode.value) {
    measureTool.cancel();
    pendingMeasureStart.value = null;
  }
}

function onSvgClick(event: MouseEvent): void {
  if (!measureMode.value) return;
  const target = event.currentTarget as SVGElement | null;
  if (!target) return;
  const rect = target.getBoundingClientRect();
  const viewBox = target.getAttribute("viewBox");
  let xMm: number;
  let yMm: number;
  if (viewBox) {
    const parts = viewBox.split(/[\s,]+/).map(Number);
    const [vbX, vbY, vbW, vbH] = parts;
    xMm = vbX + ((event.clientX - rect.left) / rect.width) * vbW;
    yMm = vbY + ((event.clientY - rect.top) / rect.height) * vbH;
  } else {
    xMm = event.clientX - rect.left;
    yMm = event.clientY - rect.top;
  }
  const point: Point3D = { x: xMm, y: yMm, z: 0 };
  if (!measureTool.hasPendingStart()) {
    measureTool.setStart(point);
    pendingMeasureStart.value = point;
  } else {
    const m = measureTool.complete(point);
    pendingMeasureStart.value = null;
    if (m) {
      measurements.value = measureTool.getMeasurements();
    }
  }
}

function removeMeasurement(id: string): void {
  measureTool.remove(id);
  measurements.value = measureTool.getMeasurements();
}

function clearMeasurements(): void {
  measureTool.clear();
  measurements.value = [];
  pendingMeasureStart.value = null;
}

// ── Snapshot helpers (undo / redo) ─────────────────────────────────────
function captureSnapshot(): InlaySnapshot {
  return {
    shape: shape.value,
    params: { ...params.value },
    materials: [...materials.value],
    bgMaterial: bgMaterial.value,
    includeOffsets: includeOffsets.value,
    maleOffsetMm: maleOffsetMm.value,
    pocketOffsetMm: pocketOffsetMm.value,
    timestamp: Date.now(),
  };
}

function applySnapshot(snap: InlaySnapshot): void {
  shape.value = snap.shape;
  params.value = { ...snap.params };
  materials.value = [...snap.materials];
  bgMaterial.value = snap.bgMaterial;
  includeOffsets.value = snap.includeOffsets;
  maleOffsetMm.value = snap.maleOffsetMm;
  pocketOffsetMm.value = snap.pocketOffsetMm;
}

function handleUndo(): void {
  const restored = history.undo(captureSnapshot());
  if (restored) {
    applySnapshot(restored);
    generatePreview();
  }
}

function handleRedo(): void {
  const restored = history.redo(captureSnapshot());
  if (restored) {
    applySnapshot(restored);
    generatePreview();
  }
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────
function onKeyDown(e: KeyboardEvent): void {
  const mod = e.ctrlKey || e.metaKey;
  if (mod && e.key === "z" && !e.shiftKey) { e.preventDefault(); handleUndo(); }
  else if (mod && e.key === "z" && e.shiftKey) { e.preventDefault(); handleRedo(); }
  else if (mod && e.key === "y") { e.preventDefault(); handleRedo(); }
}

onMounted(() => window.addEventListener("keydown", onKeyDown));
onUnmounted(() => window.removeEventListener("keydown", onKeyDown));

// ── API calls ──────────────────────────────────────────────────────────
async function loadGenerators(): Promise<void> {
  try {
    const resp = await fetch(API_BASE);
    if (!resp.ok) return;
    const data = await resp.json();
    generators.value = data.generators ?? [];
  } catch { /* informational */ }
}

async function generatePreview(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    history.pushState(captureSnapshot());
    const resp = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shape: shape.value,
        params: params.value,
        materials: materials.value,
        bg_material: bgMaterial.value,
        include_offsets: includeOffsets.value,
        male_offset_mm: maleOffsetMm.value,
        pocket_offset_mm: pocketOffsetMm.value,
      }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Failed to generate pattern");
    }
    const data = await resp.json();
    previewSvg.value = data.svg ?? "";
    resultMeta.value = {
      shape: data.shape,
      width_mm: data.width_mm,
      height_mm: data.height_mm,
      element_count: data.element_count,
      warnings: data.warnings ?? [],
    };
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to generate pattern";
  } finally {
    loading.value = false;
  }
}

async function fetchBom(): Promise<void> {
  try {
    const resp = await fetch(`${API_BASE}/bom`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shape: shape.value, params: params.value, materials: materials.value }),
    });
    if (!resp.ok) return;
    const data = await resp.json();
    bomEntries.value = data.entries ?? [];
    bomTotal.value = { total_pieces: data.total_pieces, total_area_mm2: data.total_area_mm2 };
  } catch { /* supplemental */ }
}

async function exportPattern(): Promise<void> {
  exporting.value = true;
  try {
    const resp = await fetch(`${API_BASE}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        shape: shape.value, params: params.value, format: exportFormat.value,
        materials: materials.value, bg_material: bgMaterial.value,
        male_offset_mm: maleOffsetMm.value, pocket_offset_mm: pocketOffsetMm.value,
      }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Export failed");
    }
    const disposition = resp.headers.get("content-disposition") || "";
    const m = disposition.match(/filename="?([^"]+)"?/);
    const ext = exportFormat.value === "dxf" ? "dxf" : "svg";
    const filename = m?.[1] ?? `inlay-${shape.value}.${ext}`;
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Export failed";
  } finally {
    exporting.value = false;
  }
}

onMounted(() => loadGenerators());

// ── Computed ───────────────────────────────────────────────────────────
const currentGenerator = computed(() =>
  generators.value.find((g) => g.shape === shape.value) ?? null,
);

const paramsJson = computed({
  get: () => JSON.stringify(params.value, null, 2),
  set: (val: string) => { try { params.value = JSON.parse(val); } catch { /* typing */ } },
});
</script>

<template>
  <div class="inlay-pattern-view">
    <header class="view-header">
      <h1>Inlay Pattern Generator</h1>
      <p class="subtitle">
        22 marquetry generators · SVG preview · DXF R12 export · BOM
      </p>
    </header>

    <div class="view-body">
      <!-- Left: Controls -->
      <div class="control-panel">
        <section class="panel-section">
          <h3>Pattern</h3>
          <select v-model="shape">
            <option
              v-for="gen in generators"
              :key="gen.shape"
              :value="gen.shape"
            >
              {{ gen.name }}
            </option>
          </select>
          <p
            v-if="currentGenerator"
            class="hint"
          >
            {{ currentGenerator.description }}
          </p>
        </section>

        <section class="panel-section">
          <h3>Parameters</h3>
          <textarea
            v-model="paramsJson"
            rows="5"
            :placeholder="'{&quot;repeat_mm&quot;: 12}'"
          />
        </section>

        <section class="panel-section">
          <h3>Materials</h3>
          <label>
            Mat 1
            <input
              v-model="materials[0]"
              type="text"
            >
          </label>
          <label>
            Mat 2
            <input
              v-model="materials[1]"
              type="text"
            >
          </label>
          <label>
            Mat 3
            <input
              v-model="materials[2]"
              type="text"
            >
          </label>
          <label>
            Background
            <input
              v-model="bgMaterial"
              type="text"
            >
          </label>
        </section>

        <section class="panel-section">
          <h3>CNC Offsets</h3>
          <label>
            <input
              v-model="includeOffsets"
              type="checkbox"
            >
            Include offset geometry
          </label>
          <template v-if="includeOffsets">
            <label>
              Male offset (mm)
              <input
                v-model.number="maleOffsetMm"
                type="number"
                step="0.01"
                min="0"
              >
            </label>
            <label>
              Pocket offset (mm)
              <input
                v-model.number="pocketOffsetMm"
                type="number"
                step="0.01"
                min="0"
              >
            </label>
          </template>
        </section>

        <section class="panel-section actions">
          <button
            :disabled="loading"
            class="btn btn-primary"
            @click="generatePreview"
          >
            {{ loading ? "Generating…" : "Generate" }}
          </button>
          <button
            class="btn btn-secondary"
            @click="fetchBom"
          >
            BOM
          </button>
        </section>

        <section class="panel-section">
          <h3>Export</h3>
          <div class="export-row">
            <select v-model="exportFormat">
              <option value="svg">
                SVG
              </option>
              <option value="dxf">
                DXF R12
              </option>
              <option value="layered_svg">
                Layered SVG
              </option>
            </select>
            <button
              :disabled="exporting || !previewSvg"
              class="btn btn-secondary"
              @click="exportPattern"
            >
              {{ exporting ? "…" : "Export" }}
            </button>
          </div>
        </section>
      </div>

      <!-- Right: Preview + Tools -->
      <div class="preview-panel">
        <div class="preview-toolbar">
          <button
            :disabled="!history.canUndo"
            class="tool-btn"
            title="Undo (Ctrl+Z)"
            @click="handleUndo"
          >
            ↩ Undo
          </button>
          <button
            :disabled="!history.canRedo"
            class="tool-btn"
            title="Redo (Ctrl+Shift+Z)"
            @click="handleRedo"
          >
            ↪ Redo
          </button>
          <span class="toolbar-divider" />
          <button
            class="tool-btn"
            :class="{ active: measureMode }"
            title="Measure distances on the preview"
            @click="toggleMeasureMode"
          >
            📏 Measure
          </button>
          <button
            v-if="measurements.length > 0"
            class="tool-btn"
            @click="clearMeasurements"
          >
            Clear
          </button>
        </div>

        <div
          v-if="error"
          class="error-banner"
        >
          {{ error }}
        </div>

        <div
          class="svg-container"
          :class="{ 'measure-cursor': measureMode }"
        >
          <!-- eslint-disable-next-line vue/no-v-html -- SVG from trusted backend -->
          <div
            v-if="previewSvg"
            class="svg-preview"
            @click="onSvgClick"
            v-html="previewSvg"
          />
          <div
            v-else
            class="svg-placeholder"
          >
            Select a pattern and click Generate
          </div>
        </div>

        <InlayMeasurePanel
          :measurements="measurements"
          :pending-start="!!pendingMeasureStart"
          @remove="removeMeasurement"
          @clear="clearMeasurements"
        />

        <div
          v-if="resultMeta"
          class="result-meta"
        >
          <span>{{ resultMeta.element_count }} elements</span>
          <span>{{ resultMeta.width_mm.toFixed(1) }} × {{ resultMeta.height_mm.toFixed(1) }} mm</span>
          <span
            v-for="w in resultMeta.warnings"
            :key="w"
            class="warning-badge"
          >
            ⚠ {{ w }}
          </span>
        </div>

        <InlayBomPanel
          :entries="bomEntries"
          :total="bomTotal"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.inlay-pattern-view { display: flex; flex-direction: column; height: 100%; padding: 1rem; gap: 1rem; }
.view-header h1 { margin: 0; font-size: 1.5rem; }
.subtitle { margin: 0.25rem 0 0; color: var(--color-text-secondary, #888); font-size: 0.85rem; }
.view-body { display: flex; flex: 1; gap: 1rem; min-height: 0; }
.control-panel { width: 280px; flex-shrink: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; }
.panel-section { background: var(--color-bg-secondary, #1e1e2e); border-radius: 6px; padding: 0.75rem; }
.panel-section h3 { margin: 0 0 0.5rem; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--color-text-secondary, #aaa); }
.panel-section select,
.panel-section input,
.panel-section textarea { width: 100%; padding: 0.35rem 0.5rem; border: 1px solid var(--color-border, #444); border-radius: 4px; background: var(--color-bg-primary, #111); color: var(--color-text-primary, #eee); font-size: 0.85rem; }
.panel-section textarea { resize: vertical; font-family: monospace; font-size: 0.8rem; }
.panel-section label { display: block; font-size: 0.8rem; margin-bottom: 0.3rem; }
.hint { margin: 0.25rem 0 0; font-size: 0.75rem; color: var(--color-text-secondary, #888); }
.actions { display: flex; gap: 0.5rem; }
.btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--color-accent, #3b82f6); color: #fff; flex: 1; }
.btn-secondary { background: var(--color-bg-tertiary, #333); color: var(--color-text-primary, #eee); }
.export-row { display: flex; gap: 0.5rem; }
.export-row select { flex: 1; }
.preview-panel { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; min-width: 0; }
.preview-toolbar { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem; background: var(--color-bg-secondary, #1e1e2e); border-radius: 6px; }
.tool-btn { padding: 0.3rem 0.6rem; background: var(--color-bg-tertiary, #333); color: var(--color-text-primary, #eee); border: 1px solid var(--color-border, #444); border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
.tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.tool-btn.active { background: var(--color-accent, #3b82f6); border-color: var(--color-accent, #3b82f6); color: #fff; }
.toolbar-divider { width: 1px; height: 1.2rem; background: var(--color-border, #444); }
.error-banner { background: #f87171; color: #fff; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.85rem; }
.svg-container { flex: 1; min-height: 200px; background: var(--color-bg-secondary, #1e1e2e); border-radius: 6px; overflow: auto; display: flex; align-items: center; justify-content: center; }
.svg-container.measure-cursor { cursor: crosshair; }
.svg-preview { max-width: 100%; max-height: 100%; padding: 1rem; }
.svg-preview :deep(svg) { max-width: 100%; height: auto; }
.svg-placeholder { color: var(--color-text-secondary, #888); font-size: 0.9rem; }
.result-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: var(--color-text-secondary, #aaa); padding: 0.3rem 0; }
.warning-badge { color: #fbbf24; }
</style>
