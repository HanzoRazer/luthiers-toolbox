<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Relief Kernel Lab - Development Prototyping

Phase 24.6: Dynamic scallop (slope-aware spacing)
Phase 24.7: Relief Preset Comparator (Safe/Standard/Aggressive)

Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

Features:
- Rapid relief toolpath prototyping with canvas preview
- Dynamic scallop optimizer (slope-aware stepover)
- Preset comparison testing (Safe/Standard/Aggressive)
- Stock thickness control for material removal simulation
- Load hotspot visualization (orange, intensity-based)
- Thin floor zone detection (red circles)
- Snapshot persistence to Risk Timeline
-->

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed, onMounted } from "vue";
import ParametersGrid from './relief_kernel_lab/ParametersGrid.vue'
import RunButtonsPanel from './relief_kernel_lab/RunButtonsPanel.vue'
import PresetComparisonTable from './relief_kernel_lab/PresetComparisonTable.vue'
import SimBridgeResultsPanel from './relief_kernel_lab/SimBridgeResultsPanel.vue'

// Phase 24.7: Preset definitions for comparison
const PRESETS = {
  Safe: {
    scallop_height: 0.03,
    stepdown: 0.25,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.9,
    high_load_index: 1.6,
    med_load_index: 1.2,
  },
  Standard: {
    scallop_height: 0.05,
    stepdown: 0.4,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.7,
    high_load_index: 2.0,
    med_load_index: 1.5,
  },
  Aggressive: {
    scallop_height: 0.08,
    stepdown: 0.6,
    use_dynamic_scallop: true,
    min_floor_thickness: 0.5,
    high_load_index: 2.6,
    med_load_index: 1.9,
  },
};

type ComparisonRow = {
  name: string;
  est_time_s: number;
  risk_score: number;
  thin_floor_count: number;
  high_load_count: number;
  avg_floor_thickness: number;
  min_floor_thickness: number;
  max_load_index: number;
};

const file = ref<File | null>(null);
const map = ref<any>(null);
const result = ref<any>(null);

const toolD = ref(6.0);
const stepdown = ref(2.0);
const scallop = ref(0.05);
const stockThickness = ref(5.0); // Phase 24.4
const units = ref<"mm" | "inch">("mm"); // Units selector
const useDynamicScallop = ref(false); // Phase 24.6

// Phase 24.7: Comparison state
const comparisons = ref<ComparisonRow[]>([]);
const isComparing = ref(false);
const selectedComparisonName = ref<string | null>(null);

const canvas = ref<HTMLCanvasElement | null>(null);
let ctx: CanvasRenderingContext2D | null = null;

// Relief sim bridge output (Phase 24.4)
const reliefSimBridgeOut = ref<{
  issues: Array<{
    type: string;
    severity: string;
    x: number;
    y: number;
    z?: number;
    extra_time_s?: number;
    note?: string;
    meta?: Record<string, any>;
  }>;
  overlays: Array<{
    type: string;
    x: number;
    y: number;
    z?: number;
    intensity?: number;
    severity?: string;
    meta?: Record<string, any>;
  }>;
  stats: {
    avg_floor_thickness: number;
    min_floor_thickness: number;
    max_load_index: number;
    avg_load_index: number;
    total_removed_volume: number;
    cell_count: number;
  };
  risk_score: number;
  meta?: Record<string, any>;
} | null>(null);

onMounted(() => {
  if (canvas.value) {
    ctx = canvas.value.getContext("2d");
  }
});

async function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (!target.files?.length) return;
  file.value = target.files[0];
  await loadHeightmap();
}

async function loadHeightmap() {
  if (!file.value) return;
  const formData = new FormData();
  formData.append("file", file.value);
  
  try {
    const uploadRes = await api("/api/upload/heightmap", {
      method: "POST",
      body: formData,
    });
    const { path } = await uploadRes.json();

    const res = await api("/api/cam/relief/map_from_heightfield", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        heightmap_path: path,
        units: units.value,
        z_min: 0.0,
        z_max: -3.0,
        sample_pitch_xy: 0.3,
        smooth_sigma: 0.4
      }),
    });
    map.value = await res.json();
  } catch (err: any) {
    console.error("Failed to load heightmap:", err);
    alert(`Failed to load heightmap: ${err.message || err}`);
  }
}

async function runFinish() {
  if (!map.value) return;
  const payload = {
    z_grid: map.value.z_grid,
    origin_x: map.value.origin_x,
    origin_y: map.value.origin_y,
    cell_size_xy: map.value.cell_size_xy,
    units: map.value.units,
    tool_d: toolD.value,
    stepdown: stepdown.value,
    scallop_height: scallop.value,
    safe_z: 4.0,
    feed_xy: 600.0,
    feed_z: 250.0,
    pattern: "RasterX",
    // Phase 24.6: Dynamic scallop parameters
    use_dynamic_scallop: useDynamicScallop.value,
    slope_low_deg: 10.0,
    slope_high_deg: 50.0,
    scallop_min: 0.03,
    scallop_max: 0.08,
  };
  
  try {
    const res = await api("/api/cam/relief/finishing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    result.value = await res.json();
    
    // Call relief sim bridge (Phase 24.4)
    await runSimBridge();
    
    drawCanvas();
  } catch (err: any) {
    console.error("Failed to generate finishing:", err);
    alert(`Failed: ${err.message || err}`);
  }
}

async function runSimBridge() {
  if (!result.value || !map.value) return;
  
  const simPayload = {
    z_grid_original: map.value.z_grid,
    origin_x: map.value.origin_x,
    origin_y: map.value.origin_y,
    cell_size_xy: map.value.cell_size_xy,
    units: map.value.units,
    moves: result.value.moves,
    tool_d: toolD.value,
    stock_thickness: stockThickness.value,
    min_floor_thickness: 0.5,
    high_load_index: 2.0,
    med_load_index: 1.5,
  };

  try {
    const res = await api("/api/cam/relief/sim_bridge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(simPayload),
    });
    reliefSimBridgeOut.value = await res.json();
    drawCanvas();
  } catch (err: any) {
    console.error("Failed sim bridge:", err);
    alert(`Sim bridge failed: ${err.message || err}`);
  }
}

// Phase 24.7: Run preset comparison
async function runPresetComparison() {
  if (!map.value) {
    alert("Load a heightmap first");
    return;
  }

  isComparing.value = true;
  comparisons.value = [];

  for (const [name, preset] of Object.entries(PRESETS)) {
    try {
      // Step 1: Generate finishing with preset params
      const finishPayload = {
        z_grid: map.value.z_grid,
        origin_x: map.value.origin_x,
        origin_y: map.value.origin_y,
        cell_size_xy: map.value.cell_size_xy,
        units: map.value.units,
        tool_d: toolD.value,
        stepdown: preset.stepdown,
        scallop_height: preset.scallop_height,
        safe_z: 4.0,
        feed_xy: 600.0,
        feed_z: 250.0,
        pattern: "RasterX",
        use_dynamic_scallop: preset.use_dynamic_scallop,
        slope_low_deg: 10.0,
        slope_high_deg: 50.0,
        scallop_min: 0.03,
        scallop_max: 0.08,
      };

      const finishRes = await api("/api/cam/relief/finishing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finishPayload),
      });
      const finishOut = await finishRes.json();

      // Step 2: Run sim bridge with preset thresholds
      const simPayload = {
        z_grid_original: map.value.z_grid,
        origin_x: map.value.origin_x,
        origin_y: map.value.origin_y,
        cell_size_xy: map.value.cell_size_xy,
        units: map.value.units,
        moves: finishOut.moves,
        tool_d: toolD.value,
        stock_thickness: stockThickness.value,
        min_floor_thickness: preset.min_floor_thickness,
        high_load_index: preset.high_load_index,
        med_load_index: preset.med_load_index,
      };

      const simRes = await api("/api/cam/relief/sim_bridge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(simPayload),
      });
      const simOut = await simRes.json();

      // Step 3: Compute comparison metrics
      const thin_floor_count = simOut.issues.filter(
        (i: any) => i.type === "thin_floor"
      ).length;
      const high_load_count = simOut.issues.filter(
        (i: any) => i.type === "high_load"
      ).length;

      comparisons.value.push({
        name,
        est_time_s: finishOut.stats.est_time_s,
        risk_score: simOut.risk_score,
        thin_floor_count,
        high_load_count,
        avg_floor_thickness: simOut.stats.avg_floor_thickness,
        min_floor_thickness: simOut.stats.min_floor_thickness,
        max_load_index: simOut.stats.max_load_index,
      });
    } catch (err: any) {
      console.error(`Failed preset ${name}:`, err);
      alert(`Failed preset ${name}: ${err.message || err}`);
    }
  }

  isComparing.value = false;
}

function drawCanvas() {
  if (!ctx || !canvas.value || !map.value) return;

  const w = map.value.width;
  const h = map.value.height;
  canvas.value.width = w;
  canvas.value.height = h;

  // Background
  ctx.fillStyle = "#111";
  ctx.fillRect(0, 0, w, h);

  // Geometry outline (gray)
  ctx.strokeStyle = "#666";
  ctx.lineWidth = 1;
  ctx.strokeRect(0, 0, w, h);

  // Toolpath (blue)
  if (result.value?.moves) {
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 1;
    ctx.beginPath();
    let started = false;
    for (const m of result.value.moves) {
      if (m.x !== undefined && m.y !== undefined) {
        const px = (m.x - map.value.origin_x) / map.value.cell_size_xy;
        const py = (m.y - map.value.origin_y) / map.value.cell_size_xy;
        if (!started) {
          ctx.moveTo(px, py);
          started = true;
        } else {
          ctx.lineTo(px, py);
        }
      }
    }
    ctx.stroke();
  }

  // Phase 24.4: Draw sim bridge overlays
  if (reliefSimBridgeOut.value?.overlays) {
    for (const ov of reliefSimBridgeOut.value.overlays) {
      const px = (ov.x - map.value.origin_x) / map.value.cell_size_xy;
      const py = (ov.y - map.value.origin_y) / map.value.cell_size_xy;

      if (ov.type === "load_hotspot") {
        const intensity = ov.intensity ?? 0.5;
        const alpha = Math.min(intensity, 1.0);
        ctx.fillStyle = `rgba(255, 140, 0, ${alpha})`;
        ctx.fillRect(px - 1, py - 1, 2, 2);
      }
    }
  }

  // Phase 24.4: Draw sim bridge issues (thin floor zones)
  if (reliefSimBridgeOut.value?.issues) {
    for (const issue of reliefSimBridgeOut.value.issues) {
      const px = (issue.x - map.value.origin_x) / map.value.cell_size_xy;
      const py = (issue.y - map.value.origin_y) / map.value.cell_size_xy;

      if (issue.type === "thin_floor") {
        ctx.strokeStyle = "#ef4444";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.stroke();
      }
    }
  }
}

// Phase 24.4: Push snapshot to risk timeline
async function pushSnapshot() {
  if (!reliefSimBridgeOut.value || !result.value || !map.value) {
    alert("Run finishing + sim bridge first");
    return;
  }

  const snapshot = {
    pipeline_id: "ReliefKernelLab",
    op_id: "relief_finish_proto",
    risk_score: reliefSimBridgeOut.value.risk_score,
    total_issues: reliefSimBridgeOut.value.issues.length,
    critical_count: reliefSimBridgeOut.value.issues.filter(
      (i) => i.severity === "critical"
    ).length,
    avg_floor_thickness: reliefSimBridgeOut.value.stats.avg_floor_thickness,
    min_floor_thickness: reliefSimBridgeOut.value.stats.min_floor_thickness,
    max_load_index: reliefSimBridgeOut.value.stats.max_load_index,
    avg_load_index: reliefSimBridgeOut.value.stats.avg_load_index,
    total_removed_volume: reliefSimBridgeOut.value.stats.total_removed_volume,
    stock_thickness: stockThickness.value,
    meta: {
      tool_d: toolD.value,
      stepdown: stepdown.value,
      scallop: scallop.value,
      use_dynamic_scallop: useDynamicScallop.value,
    },
  };

  try {
    await api("/api/cam/jobs/risk_report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(snapshot),
    });
    alert("✓ Snapshot pushed to Risk Timeline");
  } catch (err: any) {
    console.error("Failed to push snapshot:", err);
    alert(`Failed to push: ${err.message || err}`);
  }
}

function selectComparison(name: string) {
  selectedComparisonName.value = name;
}
</script>

<template>
  <div class="p-4 max-w-6xl mx-auto space-y-4">
    <h1 class="text-2xl font-bold">
      Relief Kernel Lab
    </h1>
    <p class="text-sm text-gray-600">
      Phase 24.6: Dynamic scallop optimizer<br>
      Phase 24.7: Preset comparator (Safe/Standard/Aggressive)
    </p>

    <!-- Upload -->
    <div class="border rounded p-3 space-y-2">
      <label class="block text-sm font-medium">Heightmap (PNG/JPEG):</label>
      <input
        type="file"
        accept="image/*"
        @change="onFileChange"
      >
      
      <!-- Units selector (before upload) -->
      <div class="flex items-center gap-2 text-xs">
        <span class="text-gray-600">Units:</span>
        <label class="flex items-center gap-1">
          <input
            v-model="units"
            type="radio"
            value="mm"
          >
          <span>mm</span>
        </label>
        <label class="flex items-center gap-1">
          <input
            v-model="units"
            type="radio"
            value="inch"
          >
          <span>inch</span>
        </label>
        <span class="text-gray-500 ml-2">(Set before uploading)</span>
      </div>
    </div>

    <!-- Parameters -->
    <ParametersGrid
      v-if="map"
      v-model:tool-d="toolD"
      v-model:stepdown="stepdown"
      v-model:scallop="scallop"
      v-model:stock-thickness="stockThickness"
      v-model:use-dynamic-scallop="useDynamicScallop"
      :units="map.units"
    />

    <!-- Run Buttons -->
    <RunButtonsPanel
      v-if="map"
      :has-result="!!result"
      :has-sim-bridge-out="!!reliefSimBridgeOut"
      :is-comparing="isComparing"
      @run-finish="runFinish"
      @run-sim-bridge="runSimBridge"
      @push-snapshot="pushSnapshot"
      @run-preset-comparison="runPresetComparison"
    />

    <!-- Phase 24.7: Comparison Results -->
    <PresetComparisonTable
      v-if="comparisons.length > 0"
      :comparisons="comparisons"
      :selected-name="selectedComparisonName"
      @select="selectComparison"
    />

    <!-- Canvas -->
    <div
      v-if="map"
      class="border rounded p-2 bg-black"
    >
      <canvas
        ref="canvas"
        class="max-w-full h-auto"
      />
    </div>

    <!-- Results -->
    <div
      v-if="result"
      class="text-xs border rounded p-3 space-y-1"
    >
      <div><strong>Moves:</strong> {{ result.moves.length }}</div>
      <div><strong>Length XY:</strong> {{ result.stats.length_xy.toFixed(2) }} mm</div>
      <div><strong>Time Est:</strong> {{ result.stats.est_time_s.toFixed(1) }} s</div>
      <div><strong>Z Range:</strong> {{ result.stats.min_z.toFixed(2) }} to {{ result.stats.max_z.toFixed(2) }} mm</div>
    </div>

    <!-- Sim Bridge Results (Phase 24.4) -->
    <SimBridgeResultsPanel
      v-if="reliefSimBridgeOut"
      :sim-bridge-out="reliefSimBridgeOut"
    />

    <!-- Map Info -->
    <div
      v-if="map"
      class="text-xs text-gray-600 mt-2"
    >
      <div><strong>Map:</strong> {{ map.width }}×{{ map.height }} cells</div>
      <div><strong>Z Range:</strong> {{ map.z_min.toFixed(2) }} to {{ map.z_max.toFixed(2) }} mm</div>
      <div><strong>Cell Size:</strong> {{ map.cell_size_xy.toFixed(2) }} mm</div>
    </div>
  </div>
</template>

<style scoped>
input[type="number"] {
  font-variant-numeric: tabular-nums;
}
</style>
