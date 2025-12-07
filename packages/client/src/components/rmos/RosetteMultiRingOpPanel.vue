<template>
  <div class="space-y-3 border rounded-lg p-3">
    <header class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">Multi-Ring Saw Batch Op</h2>
        <p class="text-xs text-gray-500">
          Configure tool & material, then preview risk and G-code.
        </p>
      </div>
      <button
        class="text-xs border rounded px-2 py-1 hover:bg-gray-100"
        :disabled="loading"
        @click="previewBatch"
      >
        {{ loading ? 'Previewing…' : 'Preview risk & G-code' }}
      </button>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
      <div class="space-y-2">
        <label class="block">
          Tool id
          <input
            v-model="localBatchOp.tool_id"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
        <label class="block">
          Material
          <input
            v-model="localBatchOp.material"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
        <label class="block">
          Workholding
          <input
            v-model="localBatchOp.workholding"
            type="text"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
      </div>

      <div class="space-y-2">
        <label class="block">
          Slice thickness (mm)
          <input
            v-model.number="localBatchOp.slice_thickness_mm"
            type="number"
            step="0.01"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
        <label class="block">
          Passes
          <input
            v-model.number="localBatchOp.passes"
            type="number"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
        <label class="block">
          Radial step (mm)
          <input
            v-model.number="localBatchOp.radial_step_mm"
            type="number"
            step="0.1"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
        <label class="block">
          Rings
          <input
            v-model.number="localBatchOp.num_rings"
            type="number"
            class="mt-1 w-full border rounded px-2 py-1"
          />
        </label>
      </div>

      <div class="space-y-1">
        <p class="font-semibold">Batch geometry</p>
        <p>Mode: circle_param</p>
        <p>Center: ({{ localBatchOp.base_circle.center_x_mm }}, {{ localBatchOp.base_circle.center_y_mm }})</p>
        <p>Base radius: {{ localBatchOp.base_circle.radius_mm }} mm</p>
        <p class="mt-2">
          <span class="font-semibold">Overall risk:</span>
          <span :class="riskBadgeClass">{{ preview?.overall_risk_grade ?? '—' }}</span>
        </p>
      </div>
    </div>

    <div v-if="preview" class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
      <div>
        <h3 class="font-semibold mb-1">Slices / Rings Risk</h3>
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b">
              <th class="text-left p-1">Idx</th>
              <th class="text-left p-1">Kind</th>
              <th class="text-left p-1">Offset</th>
              <th class="text-left p-1">Grade</th>
              <th class="text-left p-1">Rim m/min</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="s in preview.slice_risks"
              :key="s.index"
              class="border-b last:border-0"
            >
              <td class="p-1">{{ s.index }}</td>
              <td class="p-1">{{ s.kind }}</td>
              <td class="p-1">{{ s.offset_mm.toFixed(2) }}</td>
              <td class="p-1">
                <span
                  :class="[
                    'px-1 py-0.5 rounded text-xs',
                    s.risk_grade === 'RED'
                      ? 'bg-red-100 text-red-700'
                      : s.risk_grade === 'YELLOW'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-green-100 text-green-700',
                  ]"
                >
                  {{ s.risk_grade }}
                </span>
              </td>
              <td class="p-1">{{ s.rim_speed_m_min.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div>
        <h3 class="font-semibold mb-1">G-code Preview</h3>
        <textarea
          class="w-full h-48 border rounded px-2 py-1 font-mono text-[10px]"
          readonly
        >{{ preview.gcode }}</textarea>
      </div>
    </div>

    <p v-if="error" class="text-xs text-red-600">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, ref } from 'vue';
import type { SawSliceBatchOpCircle, SliceRiskSummary, RiskGrade } from '@/models/rmos';

const props = defineProps<{
  batchOp: SawSliceBatchOpCircle;
  apiBase?: string;
}>();

const emit = defineEmits<{
  (e: 'update:batchOp', value: SawSliceBatchOpCircle): void;
}>();

const RMOS_API_PREFIX = computed(() => props.apiBase ?? '/rmos');

const localBatchOp = reactive<SawSliceBatchOpCircle>(structuredClone(props.batchOp));
const loading = ref(false);
const error = ref<string | null>(null);

interface BatchPreview {
  op_id: string;
  tool_id: string;
  mode: string;
  material: string;
  workholding: string;
  num_slices: number;
  overall_risk_grade: RiskGrade;
  slice_risks: SliceRiskSummary[];
  gcode: string;
}

const preview = ref<BatchPreview | null>(null);

watch(
  () => props.batchOp,
  (val) => {
    Object.assign(localBatchOp, structuredClone(val));
  },
  { deep: true }
);

watch(
  localBatchOp,
  () => {
    emit('update:batchOp', structuredClone(localBatchOp));
  },
  { deep: true }
);

const riskBadgeClass = computed(() => {
  const grade = preview.value?.overall_risk_grade;
  if (grade === 'RED') return 'px-2 py-0.5 rounded bg-red-100 text-red-700';
  if (grade === 'YELLOW') return 'px-2 py-0.5 rounded bg-yellow-100 text-yellow-700';
  if (grade === 'GREEN') return 'px-2 py-0.5 rounded bg-green-100 text-green-700';
  return 'px-2 py-0.5 rounded bg-gray-100 text-gray-600';
});

async function previewBatch() {
  loading.value = true;
  error.value = null;
  try {
    const res = await fetch(`${RMOS_API_PREFIX.value}/saw-ops/batch/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(localBatchOp),
    });
    if (!res.ok) throw new Error(`Preview failed: ${res.status}`);
    preview.value = (await res.json()) as BatchPreview;
  } catch (err: any) {
    error.value = err?.message ?? String(err);
    preview.value = null;
  } finally {
    loading.value = false;
  }
}
</script>
