<script setup lang="ts">
/**
 * G-Code Explainer Panel (Wave 12)
 *
 * Explains G-code line by line:
 * - Motion commands
 * - Coordinate changes
 * - Risk annotations
 */
import { ref } from "vue";
import { useCamAdvisorStore } from "@/stores/camAdvisorStore";

const store = useCamAdvisorStore();

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────

const gcodeText = ref<string>("");
const safeZ = ref<number>(5.0);

// ─────────────────────────────────────────────────────────────────────────────
// Actions
// ─────────────────────────────────────────────────────────────────────────────

async function explain() {
  if (!gcodeText.value.trim()) return;
  await store.explainGcode(gcodeText.value, safeZ.value);
}

function loadSampleGcode() {
  gcodeText.value = `; Sample G-code for testing
G21 ; Set units to mm
G90 ; Absolute positioning
G17 ; XY plane
M3 S12000 ; Spindle ON at 12000 RPM
G0 Z5.0 ; Rapid to safe height
G0 X0 Y0 ; Rapid to start
G1 Z-1.5 F500 ; Plunge
G1 X50 Y0 F1200 ; Cut line
G1 X50 Y30
G1 X0 Y30
G1 X0 Y0
G0 Z5.0 ; Retract
M5 ; Spindle OFF
M30 ; Program end`;
}

function riskClass(risk?: string | null): string {
  if (!risk) return "text-slate-400";
  const r = risk.toLowerCase();
  if (r === "high") return "text-red-400 font-semibold";
  if (r === "medium") return "text-amber-300";
  return "text-emerald-300";
}

function overallRiskClass(risk: string | null): string {
  if (!risk) return "text-slate-300";
  const r = risk.toLowerCase();
  if (r === "high") return "text-red-400 font-bold";
  if (r === "medium") return "text-amber-400 font-semibold";
  return "text-emerald-400";
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Input Form -->
    <div class="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
      <h2 class="mb-2 text-lg font-semibold text-slate-50">
        G-Code Explainer 2.0
      </h2>
      <p class="mb-3 text-xs text-slate-300">
        Paste G-code below to get line-by-line explanations and risk markers.
      </p>

      <div class="mb-3 flex items-center gap-2">
        <label class="text-xs text-slate-200">Safe Z (mm):</label>
        <input
          v-model.number="safeZ"
          type="number"
          step="0.5"
          min="0"
          class="w-20 rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-50"
        />
        <button
          type="button"
          class="ml-auto rounded bg-slate-700 px-2 py-1 text-xs text-slate-200 hover:bg-slate-600"
          @click="loadSampleGcode"
        >
          Load Sample
        </button>
      </div>

      <textarea
        v-model="gcodeText"
        rows="12"
        class="w-full rounded-md border border-slate-700 bg-slate-950/70 p-2 text-xs font-mono text-slate-100"
        placeholder="Paste G-code here..."
      />

      <div class="mt-3 flex items-center gap-3">
        <button
          type="button"
          class="rounded-md bg-sky-500 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-sky-400 disabled:opacity-60"
          :disabled="store.gcode.loading || !gcodeText.trim()"
          @click="explain"
        >
          {{ store.gcode.loading ? "Analyzing G-code..." : "Explain G-code" }}
        </button>

        <p v-if="store.gcode.lastError" class="text-xs text-red-400">
          {{ store.gcode.lastError }}
        </p>

        <p
          v-if="store.gcode.overallRisk"
          class="ml-auto text-xs text-slate-300"
        >
          Overall risk:
          <span :class="overallRiskClass(store.gcode.overallRisk)">
            {{ store.gcode.overallRisk?.toUpperCase() }}
          </span>
        </p>
      </div>
    </div>

    <!-- Explanation Results -->
    <div
      v-if="store.gcode.lines.length"
      class="max-h-[500px] overflow-y-auto rounded-xl border border-slate-700 bg-slate-950/80 p-3"
    >
      <h3 class="mb-2 text-sm font-semibold text-slate-50">
        G-code Explanation ({{ store.gcode.lines.length }} lines)
      </h3>
      <div class="space-y-1 text-xs font-mono">
        <div
          v-for="line in store.gcode.lines"
          :key="line.line_number"
          class="flex gap-2 border-b border-slate-800/60 pb-1"
        >
          <span class="w-8 flex-shrink-0 text-right text-slate-500">
            {{ line.line_number }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="text-slate-200 truncate" :title="line.raw">
              {{ line.raw || "(empty)" }}
            </div>
            <div :class="['text-[0.7rem]', riskClass(line.risk)]">
              → {{ line.explanation }}
              <span v-if="line.risk" class="ml-1">[{{ line.risk }}]</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!store.gcode.loading"
      class="rounded-xl border border-dashed border-slate-700 bg-slate-900/30 p-8 text-center"
    >
      <p class="text-sm text-slate-400">
        Paste G-code above and click "Explain G-code" to see line-by-line
        analysis.
      </p>
    </div>
  </div>
</template>
