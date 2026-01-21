<script setup lang="ts">
/**
 * CAM Advisor Panel (Wave 12)
 *
 * Form panel for cut operation analysis:
 * - Tool/material selection
 * - Feed/RPM/DOC parameters
 * - Physics advisories display
 * - Recommended changes
 */
import { ref, computed } from "vue";
import {
  useCamAdvisorStore,
  type CutOperationPayload,
} from "@/stores/camAdvisorStore";
import PhysicsSummaryBadges from "./PhysicsSummaryBadges.vue";

const store = useCamAdvisorStore();

// ─────────────────────────────────────────────────────────────────────────────
// Form state
// ─────────────────────────────────────────────────────────────────────────────

const toolId = ref("endmill-6mm");
const materialId = ref("hardwood-maple");
const toolKind = ref<"router_bit" | "saw_blade">("router_bit");
const feedMmMin = ref(1000);
const rpm = ref(12000);
const depthOfCutMm = ref(1.0);
const widthOfCutMm = ref<number | null>(null);
const machineId = ref<string | null>(null);

// ─────────────────────────────────────────────────────────────────────────────
// Computed
// ─────────────────────────────────────────────────────────────────────────────

const hasResults = computed(
  () => !!store.physics || store.advisories.length > 0
);

// ─────────────────────────────────────────────────────────────────────────────
// Actions
// ─────────────────────────────────────────────────────────────────────────────

async function analyze() {
  const payload: CutOperationPayload = {
    tool_id: toolId.value,
    material_id: materialId.value,
    tool_kind: toolKind.value,
    feed_mm_min: Number(feedMmMin.value),
    rpm: Number(rpm.value),
    depth_of_cut_mm: Number(depthOfCutMm.value),
    width_of_cut_mm: widthOfCutMm.value ?? undefined,
    machine_id: machineId.value ?? undefined,
  };

  await store.analyzeOperation(payload);
}

function severityIcon(severity: string): string {
  switch (severity) {
    case "error":
      return "⛔";
    case "warning":
      return "⚠️";
    case "info":
    default:
      return "ℹ️";
  }
}

function severityClass(severity: string): string {
  switch (severity) {
    case "error":
      return "text-red-400";
    case "warning":
      return "text-amber-400";
    case "info":
    default:
      return "text-sky-400";
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Input Form -->
    <div class="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
      <h2 class="mb-2 text-lg font-semibold text-slate-50">
        CAM Advisor – Operation Analysis
      </h2>
      <p class="mb-4 text-xs text-slate-300">
        Enter tool and cut parameters to get physics-based advisories and
        recommendations.
      </p>

      <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div>
          <label class="block text-xs font-medium text-slate-200">Tool ID</label>
          <input
            v-model="toolId"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
            placeholder="e.g., endmill-6mm"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">Material ID</label>
          <input
            v-model="materialId"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
            placeholder="e.g., hardwood-maple"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">Tool Kind</label>
          <select
            v-model="toolKind"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
          >
            <option value="router_bit">
              Router Bit
            </option>
            <option value="saw_blade">
              Saw Blade
            </option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">Machine ID (optional)</label>
          <input
            v-model="machineId"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
            placeholder="e.g., shapeoko-3"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">Feed (mm/min)</label>
          <input
            v-model.number="feedMmMin"
            type="number"
            min="1"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">RPM</label>
          <input
            v-model.number="rpm"
            type="number"
            min="1"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">Depth of Cut (mm)</label>
          <input
            v-model.number="depthOfCutMm"
            type="number"
            step="0.01"
            min="0.01"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
          >
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-200">
            Width of Cut (mm, optional)
          </label>
          <input
            v-model.number="widthOfCutMm"
            type="number"
            step="0.01"
            class="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
            placeholder="Leave empty for full width"
          >
        </div>
      </div>

      <div class="mt-4 flex items-center gap-3">
        <button
          type="button"
          class="rounded-md bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-emerald-400 disabled:opacity-60"
          :disabled="store.loading"
          @click="analyze"
        >
          {{ store.loading ? "Analyzing..." : "Analyze Operation" }}
        </button>

        <p
          v-if="store.lastError"
          class="text-xs text-red-400"
        >
          {{ store.lastError }}
        </p>
      </div>
    </div>

    <!-- Results -->
    <div
      v-if="hasResults"
      class="space-y-4"
    >
      <!-- Physics Summary -->
      <div
        v-if="store.physics"
        class="rounded-xl border border-slate-700 bg-slate-900/60 p-4"
      >
        <h3 class="mb-2 text-sm font-semibold text-slate-50">
          Physics Summary
        </h3>
        <PhysicsSummaryBadges :physics="store.physics" />
      </div>

      <!-- Recommended Changes -->
      <div
        v-if="store.recommendedChanges"
        class="rounded-xl border border-slate-700 bg-slate-900/60 p-4"
      >
        <h3 class="mb-2 text-sm font-semibold text-slate-50">
          Recommended Changes
        </h3>
        <pre
          class="overflow-x-auto rounded bg-slate-950 p-2 text-xs text-slate-200"
        >{{ JSON.stringify(store.recommendedChanges, null, 2) }}</pre>
      </div>

      <!-- Advisories -->
      <div
        v-if="store.advisories.length"
        class="rounded-xl border border-slate-700 bg-slate-900/60 p-4"
      >
        <h3 class="mb-2 text-sm font-semibold text-slate-50">
          Advisories
          <span
            v-if="store.errorCount"
            class="ml-2 text-red-400"
          >({{ store.errorCount }} errors)</span>
          <span
            v-if="store.warningCount"
            class="ml-2 text-amber-400"
          >({{ store.warningCount }} warnings)</span>
        </h3>
        <ul class="space-y-2 text-xs">
          <li
            v-for="(adv, idx) in store.advisories"
            :key="idx"
            class="flex items-start gap-2 rounded bg-slate-950/50 p-2"
          >
            <span class="text-base">{{ severityIcon(adv.severity) }}</span>
            <div>
              <span
                :class="severityClass(adv.severity)"
                class="font-semibold uppercase"
              >
                {{ adv.severity }}
              </span>
              <span class="text-slate-100"> — {{ adv.message }}</span>
              <pre
                v-if="adv.context"
                class="mt-1 text-[0.65rem] text-slate-400"
              >{{ JSON.stringify(adv.context, null, 2) }}</pre>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
