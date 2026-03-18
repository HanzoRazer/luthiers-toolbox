<script setup lang="ts">
/**
 * CamWorkspaceView — 5-step wizard: Machine context → OP10/40/45/50 → Summary.
 * Uses GateStatusBadge and GcodePreviewPanel. Mock GREEN gate on Generate.
 */
import { ref, computed } from 'vue';
import GateStatusBadge from '@/components/cam/GateStatusBadge.vue';
import GcodePreviewPanel from '@/components/cam/GcodePreviewPanel.vue';

const activeStep = ref(0);
const strictMode = ref(false);
const selectedMachine = ref('BCAM 2030A');

// Per-op state (mock: generate sets GREEN + sample gcode)
const op10 = ref<{ risk: 'GREEN' | 'YELLOW' | 'RED' | null; errors: string[]; warnings: string[]; gcode: string | null; cycleTime: number | null }>({
  risk: null,
  errors: [],
  warnings: [],
  gcode: null,
  cycleTime: null,
});
const op40 = ref({ ...op10.value });
const op45 = ref({ ...op10.value });
const op50 = ref({ ...op10.value });

const steps = [
  { id: 0, title: 'Machine context' },
  { id: 1, title: 'OP10 — Truss Rod Channel' },
  { id: 2, title: 'OP40 — Roughing Profile' },
  { id: 3, title: 'OP45 — Finishing Profile' },
  { id: 4, title: 'OP50 — Fret Slots' },
  { id: 5, title: 'Summary' },
];

const canNext = computed(() => {
  if (activeStep.value >= 5) return false;
  if (activeStep.value === 0) return true;
  const op = [op10, op40, op45, op50][activeStep.value - 1];
  return op.value.gcode != null;
});

function generate(op: typeof op10) {
  op.value = {
    risk: 'GREEN',
    errors: [],
    warnings: [],
    gcode: '; Mock G-code\nG21\nG0 Z10\nG0 X0 Y0\nM30',
    cycleTime: 120,
  };
}

function next() {
  if (activeStep.value < 5) activeStep.value++;
}
function prev() {
  if (activeStep.value > 0) activeStep.value--;
}
function acknowledgeYellow(op: typeof op10) {
  op.value.risk = 'GREEN';
}

function downloadFull() {
  const parts = [op10.value.gcode, op40.value.gcode, op45.value.gcode, op50.value.gcode].filter(Boolean);
  if (parts.length === 0) return;
  const blob = new Blob([parts.join('\n\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'full_program.nc';
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="cam-workspace">
    <h1 class="page-title">CAM Workspace</h1>
    <div class="step-indicators">
      <button
        v-for="s in steps"
        :key="s.id"
        type="button"
        class="step-dot"
        :class="{ active: activeStep === s.id }"
        :title="s.title"
        @click="activeStep = s.id"
      >
        {{ s.id + 1 }}
      </button>
    </div>

    <!-- Step 0: Machine context -->
    <section v-show="activeStep === 0" class="step-panel">
      <h2>Machine context</h2>
      <div class="field">
        <label>Machine</label>
        <select v-model="selectedMachine" class="select">
          <option>BCAM 2030A</option>
        </select>
      </div>
      <div class="specs">
        <p><strong>Work envelope:</strong> 2030 × 3050 × 305 mm</p>
        <p><strong>Spindle range:</strong> 6k–24k RPM</p>
        <p><strong>Dialect:</strong> Fanuc-style</p>
      </div>
      <div class="field">
        <label class="toggle-label">
          <input v-model="strictMode" type="checkbox" />
          First run / new setup
        </label>
        <span class="tooltip" title="Treats all warnings as errors">ⓘ</span>
      </div>
      <div class="nav-buttons">
        <button type="button" @click="next">Next →</button>
      </div>
    </section>

    <!-- Steps 1–4: Ops -->
    <template v-for="(opRef, idx) in [op10, op40, op45, op50]" :key="idx">
      <section v-show="activeStep === idx + 1" class="step-panel">
        <h2>{{ steps[idx + 1].title }}</h2>
        <p class="op-spec">Tool: {{ ['6mm endmill', '6mm endmill', '3mm ball', '0.6mm slitting saw'][idx] }}</p>
        <p class="params">Depth: — mm · Stepover: — % · RPM: —</p>
        <GateStatusBadge
          :risk="opRef.risk"
          :errors="opRef.errors"
          :warnings="opRef.warnings"
          @override="acknowledgeYellow(opRef)"
        />
        <GcodePreviewPanel
          :gcode="opRef.gcode"
          :filename="`op${[10, 40, 45, 50][idx]}.nc`"
          :cycle-time-seconds="opRef.cycleTime"
        />
        <div class="action-row">
          <button type="button" @click="generate(opRef)">Generate</button>
          <button type="button" :disabled="!canNext" @click="next">Next →</button>
        </div>
      </section>
    </template>

    <!-- Step 5: Summary -->
    <section v-show="activeStep === 5" class="step-panel">
      <h2>Summary</h2>
      <div class="summary-ops">
        <p><GateStatusBadge :risk="op10.risk" :errors="op10.errors" :warnings="op10.warnings" /> OP10</p>
        <p><GateStatusBadge :risk="op40.risk" :errors="op40.errors" :warnings="op40.warnings" /> OP40</p>
        <p><GateStatusBadge :risk="op45.risk" :errors="op45.errors" :warnings="op45.warnings" /> OP45</p>
        <p><GateStatusBadge :risk="op50.risk" :errors="op50.errors" :warnings="op50.warnings" /> OP50</p>
      </div>
      <div class="action-row">
        <button type="button" @click="downloadFull">Download full program</button>
        <button type="button" disabled title="Coming in Phase 4">Send to RMOS queue</button>
      </div>
      <div class="nav-buttons">
        <button type="button" @click="prev">← Back</button>
      </div>
    </section>

    <div v-if="activeStep > 0 && activeStep < 5" class="nav-buttons">
      <button type="button" @click="prev">← Back</button>
    </div>
  </div>
</template>

<style scoped>
.cam-workspace { max-width: 900px; margin: 0 auto; padding: 1rem; }
.page-title { font-size: 1.5rem; margin-bottom: 1rem; }
.step-indicators { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.step-dot { width: 2rem; height: 2rem; border-radius: 50%; border: 1px solid #e2e8f0; background: #fff; cursor: pointer; }
.step-dot.active { background: #2563eb; color: #fff; border-color: #2563eb; }
.step-panel { border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
.specs, .params, .op-spec { font-size: 0.875rem; color: #64748b; margin: 0.5rem 0; }
.field { margin: 0.75rem 0; }
.select { padding: 0.35rem 0.5rem; }
.toggle-label { display: inline-flex; align-items: center; gap: 0.5rem; }
.tooltip { margin-left: 0.25rem; opacity: 0.7; cursor: help; }
.action-row, .nav-buttons { display: flex; gap: 0.5rem; margin-top: 1rem; }
.summary-ops p { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
