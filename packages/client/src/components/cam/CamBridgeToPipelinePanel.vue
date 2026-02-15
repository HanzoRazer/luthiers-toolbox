<template>
  <div class="border rounded p-3 bg-gray-50">
    <h3 class="text-sm font-semibold mb-2">
      Save as Pipeline Preset
    </h3>

    <div class="space-y-2 text-xs">
      <div>
        <label class="block text-gray-600 mb-1">Preset Name</label>
        <input
          v-model="name"
          type="text"
          placeholder="e.g., Bridge Pocket (6-pin)"
          class="w-full border rounded px-2 py-1"
        >
      </div>

      <div>
        <label class="block text-gray-600 mb-1">Post ID</label>
        <input
          v-model="postIdLocal"
          type="text"
          placeholder="e.g., GRBL"
          class="w-full border rounded px-2 py-1"
        >
      </div>

      <div>
        <label class="block text-gray-600 mb-1">Machine ID</label>
        <input
          v-model="machineIdLocal"
          type="text"
          placeholder="e.g., router_1"
          class="w-full border rounded px-2 py-1"
        >
      </div>

      <button
        type="button"
        :disabled="!canSave || saving"
        class="w-full bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        @click="savePreset"
      >
        {{ saving ? "Saving..." : "Save preset" }}
      </button>

      <p
        v-if="error"
        class="text-red-600 text-xs"
      >
        {{ error }}
      </p>
      <p
        v-if="success"
        class="text-green-600 text-xs"
      >
        ✓ Saved as preset ID: {{ successId }}
      </p>

      <details
        v-if="canSave"
        class="mt-3"
      >
        <summary class="cursor-pointer text-gray-600 text-xs">
          Preview Spec
        </summary>
        <pre class="mt-2 bg-white border rounded p-2 text-xs overflow-auto max-h-64">{{ prettySpec }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from "vue";

interface MachineLimits {
  x: number;
  y: number;
  z: number;
}

interface MachineCamDefaults {
  rapid_feed: number;
  plunge_feed: number;
}

interface Machine {
  id: string;
  name: string;
  limits?: MachineLimits;
  cam_defaults?: MachineCamDefaults;
}

const props = defineProps<{
  machine: Machine | null;
  adaptiveUnits: string;
  toolD: number;
  stepoverPct: number;
  stepdown: number;
  feedXY: number;
  geometryLayer: string;
  selectedPostId: string | null;
}>();

const name = ref("");
const saving = ref(false);
const error = ref("");
const success = ref(false);
const successId = ref("");

const postIdLocal = ref(props.selectedPostId || "");
const machineIdLocal = ref(props.machine?.id || "");

const canSave = computed(() => {
  return (
    name.value.trim().length > 0 &&
    postIdLocal.value.trim().length > 0 &&
    machineIdLocal.value.trim().length > 0 &&
    props.geometryLayer.trim().length > 0
  );
});

const spec = computed(() => {
  const stepoverFraction = props.stepoverPct / 100.0;
  return {
    ops: [
      {
        kind: "dxf_preflight",
        params: {
          profile: "bridge",
          cam_layer_prefix: "CAM_",
          debug: true,
        },
      },
      {
        kind: "adaptive_plan",
        params: {
          geometry_layer: props.geometryLayer,
          tool_d: props.toolD,
          stepover: stepoverFraction,
          stepdown: props.stepdown,
          feed_xy: props.feedXY,
        },
      },
      {
        kind: "adaptive_plan_run",
        params: {},
      },
      {
        kind: "export_post",
        params: {
          endpoint: "/cam/roughing_gcode",
        },
      },
      {
        kind: "simulate_gcode",
        params: {},
      },
    ],
    tool_d: props.toolD,
    units: props.adaptiveUnits,
    geometry_layer: props.geometryLayer,
    auto_scale: false,
    cam_layer_prefix: "CAM_",
    machine_id: machineIdLocal.value,
    post_id: postIdLocal.value,
  };
});

const prettySpec = computed(() => {
  return JSON.stringify(spec.value, null, 2);
});

async function savePreset() {
  if (!canSave.value) return;

  saving.value = true;
  error.value = "";
  success.value = false;
  successId.value = "";

  try {
    const body = {
      name: name.value.trim(),
      description: `Bridge lab preset: ${props.geometryLayer}, tool=${props.toolD}mm, stepover=${props.stepoverPct}%`,
      spec: spec.value,
    };

    const response = await api("/api/cam/pipeline/presets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const data = await response.json();
    successId.value = data.id || data.preset_id || "unknown";
    success.value = true;
  } catch (err: any) {
    error.value = err.message || "Failed to save preset";
  } finally {
    saving.value = false;
  }
}
</script>
