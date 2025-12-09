<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
Relief Kernel Lab - Development Prototyping

Part of Phase 24.0-24.4: Relief Carving System with Sim Bridge Integration
Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025

Features:
- Rapid relief toolpath prototyping with canvas preview
- Stock thickness control for material removal simulation
- Load hotspot visualization (orange, intensity-based)
- Thin floor zone detection (red circles)
- Snapshot persistence to Risk Timeline
-->

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";

const file = ref<File | null>(null);
const map = ref<any>(null);
const result = ref<any>(null);

const toolD = ref(6.0);
const stepdown = ref(2.0);
const scallop = ref(0.05);
const stockThickness = ref(5.0); // Phase 24.4
const useDynamicScallop = ref(false); // Phase 24.6

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
    cell_count: number;
    avg_floor_thickness: number;
    min_floor_thickness: number;
    max_load_index: number;
    avg_load_index: number;
    total_removed_volume: number;
  };
} | null>(null);

onMounted(() => {
  if (canvas.value) {
    ctx = canvas.value.getContext("2d");
    // Set canvas actual pixel dimensions
    if (canvas.value) {
      canvas.value.width = 800;
      canvas.value.height = 600;
    }
  }
});

const overlaysHigh = computed(
  () =>
    result.value?.overlays?.filter((o: any) => o.severity === "high").length || 0
);

function onFile(e: Event) {
  const target = e.target as HTMLInputElement;
  file.value = target.files?.[0] || null;
}

async function runMap() {
  if (!file.value) return;
  const fd = new FormData();
  fd.append("file", file.value);
  
  // Upload the image first (assuming backend static tmp upload endpoint exists)
  try {
    const upload = await fetch("/api/files/upload", { method: "POST", body: fd });
    const uploadData = await upload.json();
    const path = uploadData.path;
    
    const res = await fetch("/api/cam/relief/map_from_heightfield", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        heightmap_path: path,
        units: "mm",
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
    const res = await fetch("/api/cam/relief/finishing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    result.value = await res.json();
    
    // Call relief sim bridge (Phase 24.4)
    if (result.value?.moves) {
      try {
        const simPayload = {
          moves: result.value.moves,
          stock_thickness: stockThickness.value,
          origin_x: map.value.origin_x,
          origin_y: map.value.origin_y,
          cell_size_xy: map.value.cell_size_xy,
          units: map.value.units,
          min_floor_thickness: 0.6,
          high_load_index: 2.0,
          med_load_index: 1.0,
        };
        
        const simRes = await fetch("/api/cam/relief/sim_bridge", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(simPayload),
        });
        
        if (simRes.ok) {
          reliefSimBridgeOut.value = await simRes.json();
        } else {
          console.warn("Relief sim bridge failed (non-fatal):", simRes.status);
          reliefSimBridgeOut.value = null;
        }
      } catch (simErr: any) {
        console.warn("Relief sim bridge error (non-fatal):", simErr?.message || simErr);
        reliefSimBridgeOut.value = null;
      }
    }
    
    drawPreview();
  } catch (err: any) {
    console.error("Failed to generate finishing toolpath:", err);
    alert(`Failed to generate toolpath: ${err.message || err}`);
  }
}

function drawPreview() {
  if (!ctx || !result.value || !canvas.value) return;
  const w = canvas.value.width;
  const h = canvas.value.height;
  ctx.clearRect(0, 0, w, h);

  // Simplified draw of toolpath moves
  ctx.strokeStyle = "#222";
  ctx.lineWidth = 0.5;
  ctx.beginPath();
  let started = false;
  
  // Draw first 2000 moves (limit for performance)
  for (const mv of result.value.moves.slice(0, 2000)) {
    if (mv.x == null || mv.y == null) continue;
    const x = mv.x * 2;
    const y = h - mv.y * 2;
    if (!started) {
      ctx.moveTo(x, y);
      started = true;
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();

  // Draw overlays (slope hotspots) - limit to 500 for performance
  if (result.value.overlays) {
    for (const ov of result.value.overlays.slice(0, 500)) {
      const x = ov.x * 2;
      const y = h - ov.y * 2;
      ctx.fillStyle =
        ov.severity === "high"
          ? "rgba(255,0,0,0.6)"
          : "rgba(255,165,0,0.4)";
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  
  // Draw sim bridge overlays (Phase 24.4)
  if (reliefSimBridgeOut.value?.overlays) {
    for (const ov of reliefSimBridgeOut.value.overlays.slice(0, 500)) {
      const x = ov.x * 2;
      const y = h - ov.y * 2;
      
      if (ov.type === "load_hotspot") {
        // Orange circles, intensity-based radius
        const radius = 2.0 + 3.0 * (ov.intensity ?? 0.5);
        ctx.fillStyle = "rgba(255,140,0,0.5)";
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fill();
      } else if (ov.type === "thin_floor_zone") {
        // Red circles for thin floor zones
        ctx.fillStyle = "rgba(220,20,20,0.7)";
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

async function pushSnapshot() {
  if (!result.value) return;
  const report = {
    job_id: `relief_lab_${Date.now()}`,
    pipeline_id: "relief_kernel_lab",
    op_id: "ReliefFinishing",
    timestamp: new Date().toISOString(),
    stats: result.value.stats,
    overlays: result.value.overlays,
    meta: {
      source: "ReliefKernelLab",
      tool_d: toolD.value,
      scallop: scallop.value,
      stock_thickness: stockThickness.value, // Phase 24.4
      relief_sim_bridge_stats: reliefSimBridgeOut.value?.stats || null, // Phase 24.4
    }
  };
  
  try {
    await fetch("/api/cam/jobs/report", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    });
    alert("Snapshot pushed to Risk Timeline.");
  } catch (err: any) {
    console.error("Failed to push snapshot:", err);
    alert(`Failed to push snapshot: ${err.message || err}`);
  }
}
</script>

<template>
  <div class="p-4 space-y-4">
    <h2 class="text-xl font-bold">🪶 Relief Kernel Lab</h2>

    <!-- Load Heightmap -->
    <div class="flex items-center space-x-2">
      <input 
        type="file" 
        @change="onFile" 
        accept="image/*"
        class="border rounded px-2 py-1"
      />
      <button 
        @click="runMap" 
        :disabled="!file"
        class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
      >
        Map Heightfield
      </button>
    </div>

    <!-- Parameter Panel -->
    <div v-if="map" class="grid grid-cols-4 gap-2 mt-2">
      <div>
        <label class="block text-xs font-medium">Tool Ø (mm)</label>
        <input 
          v-model.number="toolD" 
          type="number" 
          step="0.1"
          class="w-full border rounded px-2 py-1" 
        />
      </div>
      <div>
        <label class="block text-xs font-medium">Step-down (mm)</label>
        <input 
          v-model.number="stepdown" 
          type="number" 
          step="0.1"
          class="w-full border rounded px-2 py-1" 
        />
      </div>
      <div>
        <label class="block text-xs font-medium">Scallop (mm)</label>
        <input 
          v-model.number="scallop" 
          type="number" 
          step="0.01"
          class="w-full border rounded px-2 py-1" 
        />
      </div>
      <div>
        <label class="block text-xs font-medium">Stock (mm)</label>
        <input 
          v-model.number="stockThickness" 
          type="number" 
          step="0.1"
          class="w-full border rounded px-2 py-1" 
        />
      </div>
      
      <!-- Phase 24.6: Dynamic Scallop Control -->
      <div class="col-span-4 flex items-center gap-2 mt-1">
        <label class="flex items-center gap-1 text-xs text-gray-700">
          <input 
            v-model="useDynamicScallop" 
            type="checkbox" 
            class="align-middle" 
          />
          <span>Use dynamic scallop (slope-aware spacing)</span>
        </label>
      </div>
    </div>

    <!-- Run Buttons -->
    <div v-if="map" class="space-x-2">
      <button 
        @click="runFinish"
        class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
      >
        Generate Finishing
      </button>
      <button 
        @click="pushSnapshot" 
        :disabled="!result"
        class="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-300"
      >
        Save Snapshot
      </button>
    </div>

    <!-- Canvas Preview -->
    <div class="mt-4 relative border rounded bg-gray-100" style="height: 400px;">
      <canvas 
        ref="canvas" 
        class="w-full h-full"
        style="max-width: 100%; max-height: 100%; object-fit: contain;"
      />
      <div 
        v-if="result" 
        class="absolute bottom-2 right-2 text-xs bg-white/90 px-2 py-1 rounded shadow"
      >
        Moves: {{ result.stats.move_count }} |
        Time ≈ {{ result.stats.est_time_s.toFixed(1) }} s |
        Hotspots: {{ overlaysHigh }}
      </div>
    </div>

    <!-- Relief sim bridge stats (Phase 24.4) -->
    <div 
      v-if="reliefSimBridgeOut?.stats" 
      class="text-xs bg-blue-50 border border-blue-200 rounded px-3 py-2 space-y-1"
    >
      <div class="font-semibold text-blue-900">
        Relief Sim Bridge Stats
      </div>
      <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-gray-700">
        <div>
          <span class="text-gray-500">Floor:</span>
          avg {{ reliefSimBridgeOut.stats.avg_floor_thickness.toFixed(2) }} mm,
          min {{ reliefSimBridgeOut.stats.min_floor_thickness.toFixed(2) }} mm
        </div>
        <div>
          <span class="text-gray-500">Load:</span>
          max {{ reliefSimBridgeOut.stats.max_load_index.toFixed(2) }},
          avg {{ reliefSimBridgeOut.stats.avg_load_index.toFixed(2) }}
        </div>
        <div>
          <span class="text-gray-500">Removed:</span>
          {{ reliefSimBridgeOut.stats.total_removed_volume.toFixed(1) }} mm³
        </div>
        <div>
          <span class="text-gray-500">Grid cells:</span>
          {{ reliefSimBridgeOut.stats.cell_count }}
        </div>
        <div class="col-span-2">
          <span class="text-gray-500">Issues:</span>
          {{ reliefSimBridgeOut.issues.length }} (thin floors + high loads)
        </div>
      </div>
    </div>

    <!-- Map Info -->
    <div v-if="map" class="text-xs text-gray-600 mt-2">
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
