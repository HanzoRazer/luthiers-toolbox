<script setup lang="ts">
/**
 * CamWorkspaceView.vue
 * CAM Workspace — Phase 1: Neck Pipeline Wizard
 *
 * Step layout (left sidebar):
 *   Step 0 — Machine context
 *   Step 1 — OP10 Truss rod
 *   Step 2 — OP40 Profile roughing
 *   Step 3 — OP45 Profile finishing
 *   Step 4 — OP50 Fret slots
 *   Step 5 — Summary + full download
 *
 * Centre: G-code preview (updates per-step)
 * Right:  Shared neck config (scale, frets, material, preset)
 */

import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAgenticEvents } from '@/composables/useAgenticEvents'
import { useContextTools } from '@/composables/useContextTools'
import NeckOpPanel       from '@/components/cam/NeckOpPanel.vue'

import GcodePreviewPanel from '@/components/cam/GcodePreviewPanel.vue'
import GateStatusBadge   from '@/components/cam/GateStatusBadge.vue'
import type { GateResult } from '@/components/cam/GateStatusBadge.vue'

// E-1: Agentic Spine event emission
const { emitViewRendered, emitArtifactCreated, emitParameterChanged } = useAgenticEvents()

// ── Machine info type ─────────────────────────────────────────────────────────
interface MachineInfo {
  machine_id: string
  name: string
  envelope: { x_mm: number; y_mm: number; z_mm: number }
  z_travel_mm: number
  safe_z_mm: number
  spindle_rpm_min: number
  spindle_rpm_max: number
  dialect: string
  tool_change_style: string
}

const emit = defineEmits<{ toast: [msg: string] }>()

// E-1: Emit view_rendered on mount
onMounted(() => {
  emitViewRendered('cam_workspace')
})

// ── Step list ─────────────────────────────────────────────────────────────────
const STEPS = [
  { id: 0, label: 'Machine',    op: null              },
  { id: 1, label: 'OP10 Truss', op: 'truss_rod'       },
  { id: 2, label: 'OP40 Rough', op: 'profile_rough'   },
  { id: 3, label: 'OP45 Finish',op: 'profile_finish'  },
  { id: 4, label: 'OP50 Frets', op: 'fret_slots'      },
  { id: 5, label: 'Summary',    op: null              },
] as const

type StepId = 0 | 1 | 2 | 3 | 4 | 5
type OpId   = 'truss_rod' | 'profile_rough' | 'profile_finish' | 'fret_slots'

const activeStep = ref<StepId>(0)
const contextTools = useContextTools('cam')
const toolsOpen = ref(false)

// ── Machine context ───────────────────────────────────────────────────────────
const machineId  = ref('bcam_2030a')
const strictMode = ref(false)
const machines = ref<MachineInfo[]>([])
const machinesLoading = ref(false)

// Selected machine computed for specs display
const selectedMachine = computed(() =>
  machines.value.find(m => m.machine_id === machineId.value) ?? null
)

// Fetch machines on mount
async function fetchMachines() {
  machinesLoading.value = true
  try {
    const res = await fetch('/api/cam-workspace/machines')
    if (!res.ok) return
    const data = await res.json()
    if (data.machines) {
      machines.value = data.machines
      // Pre-select bcam_2030a if available
      if (machines.value.some(m => m.machine_id === 'bcam_2030a')) {
        machineId.value = 'bcam_2030a'
      } else if (machines.value.length > 0) {
        machineId.value = machines.value[0].machine_id
      }
    }
  } catch { /* network error */ }
  finally { machinesLoading.value = false }
}

// ── Shared neck config ────────────────────────────────────────────────────────
const neckConfig = reactive<Record<string, any>>({
  scale_length_mm:       628.65,
  fret_count:            22,
  nut_width_mm:          43.0,
  heel_width_mm:         56.0,
  material:              'maple',
  preset:                null,
  truss_rod:             { width_mm: 6.35, depth_mm: 9.525, length_mm: 406.4, start_offset_mm: 12.7 },
  profile_carving:       { profile_type: 'c_shape', depth_at_nut_mm: 20.0, depth_at_12th_mm: 22.0, depth_at_heel_mm: 25.0, finish_allowance_mm: 0.75 },
  fret_slots:            { slot_width_mm: 0.584, slot_depth_mm: 3.5, fretboard_thickness_mm: 6.35, compound_radius: false, radius_at_nut_mm: 254.0, radius_at_heel_mm: 406.4 },
  include_truss_rod:     true,
  include_profile_rough: true,
  include_profile_finish:true,
  include_fret_slots:    true,
})

function applyPatch(patch: Record<string, any>) {
  for (const [k, v] of Object.entries(patch)) {
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      neckConfig[k] = { ...(neckConfig[k] ?? {}), ...v }
    } else {
      neckConfig[k] = v
    }
    // E-1: Emit parameter changed event
    emitParameterChanged(k, v)
  }
  // Trigger re-evaluate
  evaluateDebounced()
}

function applyPreset(preset: string | null) {
  neckConfig.preset = preset
  if (preset === 'les_paul') {
    neckConfig.scale_length_mm = 628.65
    neckConfig.fret_count      = 22
    neckConfig.material        = 'mahogany'
    neckConfig.nut_width_mm    = 43.0
    neckConfig.heel_width_mm   = 56.0
    neckConfig.profile_carving = { profile_type: 'c_shape', depth_at_nut_mm: 20.0, depth_at_12th_mm: 22.0, depth_at_heel_mm: 25.0, finish_allowance_mm: 0.75 }
  } else if (preset === 'strat') {
    neckConfig.scale_length_mm = 647.7
    neckConfig.fret_count      = 22
    neckConfig.material        = 'maple'
    neckConfig.nut_width_mm    = 42.0
    neckConfig.heel_width_mm   = 54.0
    neckConfig.profile_carving = { profile_type: 'c_shape', depth_at_nut_mm: 19.5, depth_at_12th_mm: 21.5, depth_at_heel_mm: 24.0, finish_allowance_mm: 0.75 }
  }
  evaluateDebounced()
}

// ── Gate evaluation (debounced 300ms) ─────────────────────────────────────────
const gates = reactive<Record<string, GateResult | null>>({
  truss_rod: null, profile_rough: null, profile_finish: null, fret_slots: null,
})
const gateLoading = ref(false)
let evalTimer: ReturnType<typeof setTimeout> | null = null

function evaluateDebounced() {
  if (evalTimer) clearTimeout(evalTimer)
  evalTimer = setTimeout(runEvaluate, 300)
}

async function runEvaluate() {
  gateLoading.value = true
  try {
    const res = await fetch('/api/cam-workspace/neck/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        machine:     { machine_id: machineId.value },
        neck:        { ...neckConfig },
        strict_mode: strictMode.value,
      }),
    })
    if (!res.ok) return
    const data = await res.json()
    if (data.gates) {
      for (const [op, g] of Object.entries(data.gates)) {
        gates[op] = g as GateResult
      }
    }
  } catch { /* network — leave stale gate */ }
  finally { gateLoading.value = false }
}

// On mount: fetch machines then evaluate
onMounted(async () => {
  await fetchMachines()
  evaluateDebounced()
})

// ── Per-op generated G-code ───────────────────────────────────────────────────
const opGcodes = reactive<Record<string, string>>({})
const opTimes  = reactive<Record<string, number>>({})
const opsDone  = computed(() => Object.keys(opGcodes).filter(k => opGcodes[k]))

function onOpGenerated(op: OpId, gcode: string, cycleTime: number) {
  opGcodes[op] = gcode
  // E-1: Emit artifact created event for G-code generation
  emitArtifactCreated('cam_gcode', 0.9, { operation: op, cycleTime })
  opTimes[op]  = cycleTime
}

// Active G-code for preview: current op's output or summary
const previewGcode = computed(() => {
  const step = STEPS[activeStep.value]
  if (step.op) return opGcodes[step.op] ?? ''
  if (activeStep.value === 5) return fullGcode.value
  return ''
})

const previewOp = computed(() => STEPS[activeStep.value].label ?? '')
const previewTime = computed(() => {
  const step = STEPS[activeStep.value]
  if (step.op) return opTimes[step.op as string] ?? 0
  if (activeStep.value === 5) return totalTime.value
  return 0
})

// ── Summary / full download ───────────────────────────────────────────────────
const fullGcode       = ref('')
const fullDownloading = ref(false)

const totalTime = computed(() =>
  Object.values(opTimes).reduce((s, t) => s + t, 0)
)

const allGatesPass = computed(() =>
  Object.values(gates).every(g => g !== null && g.overall_risk !== 'RED')
)

async function generateFull() {
  fullDownloading.value = true
  fullGcode.value = ''
  try {
    const res = await fetch('/api/cam-workspace/neck/generate-full', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        machine:     { machine_id: machineId.value },
        neck:        { ...neckConfig },
        strict_mode: strictMode.value,
      }),
    })
    if (!res.ok) {
      emit('toast', `Full generate failed: ${res.status}`)
      return
    }
    const text = await res.text()
    fullGcode.value = text
    // Trigger download
    const blob = new Blob([text], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    const mat  = neckConfig.material ?? 'maple'
    const scale = (neckConfig.scale_length_mm ?? 628.65).toFixed(0)
    a.href = url; a.download = `neck_${mat}_${scale}mm.nc`; a.click()
    URL.revokeObjectURL(url)
    emit('toast', 'Full neck program downloaded')
  } finally { fullDownloading.value = false }
}

// ── Overall status for step dots ──────────────────────────────────────────────
const OP_STEP_MAP: Record<number, string> = { 1:'truss_rod', 2:'profile_rough', 3:'profile_finish', 4:'fret_slots' }

function stepStatus(id: number): 'done' | 'warn' | 'ok' | 'idle' {
  const op = OP_STEP_MAP[id]
  if (!op) return 'idle'
  if (opGcodes[op]) return 'done'
  const g = gates[op]
  if (!g) return 'idle'
  if (g.overall_risk === 'RED') return 'warn'
  return 'ok'
}
</script>

<template>
  <div class="caw-layout">

    <!-- Left: step sidebar -->
    <nav class="caw-steps">
      <div class="caw-steps-header">CAM Workspace</div>

      <div v-for="s in STEPS" :key="s.id"
        class="caw-step" :class="{
          active: activeStep === s.id,
          done:   s.op && opGcodes[s.op],
          warn:   s.op && gates[s.op]?.overall_risk === 'RED',
        }"
        @click="activeStep = s.id as StepId">
        <div class="step-num">
          <span v-if="s.op && opGcodes[s.op]" class="step-done-icon">✓</span>
          <span v-else-if="s.op && gates[s.op]?.overall_risk === 'RED'" class="step-warn-icon">!</span>
          <span v-else>{{ s.id }}</span>
        </div>
        <div class="step-lbl">{{ s.label }}</div>
        <div v-if="s.op" class="step-gate-dot"
          :class="gates[s.op]?.overall_risk?.toLowerCase() ?? 'idle'">
        </div>
      </div>

      <!-- Machine info at bottom -->
      <div class="caw-machine-info">
        <div class="mi-label">Machine</div>
        <div class="mi-val">{{ machineId }}</div>
      </div>
    </nav>

    <!-- Centre: op panels + G-code preview -->
    <div class="caw-centre">

      <!-- Step 0: Machine context -->
      <div v-show="activeStep === 0" class="caw-step-body">
        <div class="step-body-header">Machine Context</div>
        <div class="step-body-content">
          <div class="step-section">
            <div class="sec-lbl">Machine</div>
            <div class="field-row">
              <label class="fld-k">Profile</label>
              <select class="fld-v sel" v-model="machineId" @change="evaluateDebounced()" :disabled="machinesLoading">
                <option v-if="machinesLoading" value="">Loading...</option>
                <option v-for="m in machines" :key="m.machine_id" :value="m.machine_id">
                  {{ m.name }}
                </option>
              </select>
            </div>
            <div class="machine-spec-grid" v-if="selectedMachine">
              <div class="ms-row"><span class="ms-k">Envelope</span><span class="ms-v">{{ selectedMachine.envelope.x_mm }} × {{ selectedMachine.envelope.y_mm }} × {{ selectedMachine.envelope.z_mm }} mm</span></div>
              <div class="ms-row"><span class="ms-k">Z travel</span><span class="ms-v">{{ selectedMachine.z_travel_mm }} mm</span></div>
              <div class="ms-row"><span class="ms-k">Safe Z</span><span class="ms-v">{{ selectedMachine.safe_z_mm }} mm</span></div>
              <div class="ms-row"><span class="ms-k">Spindle</span><span class="ms-v">{{ selectedMachine.spindle_rpm_min.toLocaleString() }} – {{ selectedMachine.spindle_rpm_max.toLocaleString() }} RPM</span></div>
              <div class="ms-row"><span class="ms-k">Post</span><span class="ms-v">{{ selectedMachine.dialect.toUpperCase() }}  {{ selectedMachine.tool_change_style }}</span></div>
            </div>
            <div class="machine-spec-grid" v-else-if="!machinesLoading">
              <div class="ms-row"><span class="ms-k">Status</span><span class="ms-v">No machine selected</span></div>
            </div>
          </div>

          <div class="step-section">
            <div class="sec-lbl">Validation mode</div>
            <div class="field-row">
              <label class="fld-k">Verify everything</label>
              <input type="checkbox" v-model="strictMode" @change="evaluateDebounced()" />
            </div>
            <div class="fld-hint" v-if="strictMode">
              Strict mode: all warnings treated as errors. Recommended for first runs.
            </div>
          </div>

          <button class="next-btn" @click="activeStep = 1">Begin → OP10 Truss Rod</button>
        </div>
      </div>

      <!-- Steps 1–4: Op panels + preview split -->
      <template v-for="s in STEPS.slice(1,5)" :key="s.id">
        <div v-show="activeStep === s.id" class="caw-op-split">
          <!-- Left half: NeckOpPanel -->
          <div class="caw-op-left">
            <NeckOpPanel
              :op="s.op as OpId"
              :neck-config="neckConfig"
              :machine-id="machineId"
              :gate-result="gates[s.op] ?? null"
              :gate-loading="gateLoading"
              :strict-mode="strictMode"
              @generate="onOpGenerated"
              @update:neck-config="applyPatch"
              @toast="emit('toast', $event)"
            />
          </div>
          <!-- Right half: G-code preview -->
          <div class="caw-op-right">
            <GcodePreviewPanel
              :gcode="opGcodes[s.op] ?? ''"
              :op-name="s.label"
              :cycle-time-secs="opTimes[s.op] ?? 0"
              :filename="`${s.op}.nc`"
              @toast="emit('toast', $event)"
            />
          </div>
        </div>
      </template>

      <!-- Step 5: Summary -->
      <div v-show="activeStep === 5" class="caw-step-body">
        <div class="step-body-header">Summary &amp; Download</div>
        <div class="step-body-content">

          <!-- Op status table -->
          <div class="step-section">
            <div class="sec-lbl">Operations</div>
            <div class="summary-table">
              <div v-for="s in STEPS.slice(1,5)" :key="s.id" class="summary-row">
                <span class="sum-op">{{ s.label }}</span>
                <GateStatusBadge :gate="gates[s.op!]" :compact="true" />
                <span class="sum-status" :class="opGcodes[s.op!] ? 'done' : 'pending'">
                  {{ opGcodes[s.op!] ? '✓ generated' : '— pending' }}
                </span>
                <span class="sum-time" v-if="opTimes[s.op!]">
                  {{ Math.round(opTimes[s.op!]) }}s
                </span>
              </div>
            </div>
          </div>

          <!-- Total time -->
          <div class="step-section" v-if="totalTime > 0">
            <div class="sec-lbl">Estimated total cycle time</div>
            <div class="total-time">
              {{ Math.floor(totalTime / 60) }}m {{ Math.round(totalTime % 60) }}s
              <span class="total-hint">(cutting time only, excludes tool changes)</span>
            </div>
          </div>

          <!-- Download -->
          <div class="step-section">
            <div class="sec-lbl">Full program</div>
            <div v-if="!allGatesPass" class="sum-gate-warn">
              One or more operations have RED gates. Fix before downloading.
            </div>
            <button class="dl-btn"
              :disabled="!allGatesPass || fullDownloading"
              @click="generateFull">
              <span v-if="fullDownloading" class="gen-spin"></span>
              <span v-else>↓ Generate &amp; Download full .nc program</span>
            </button>
            <div class="sum-note">
              The full program assembles all enabled ops with M1 tool-change pauses
              and GRBL header/footer for the BCAMCNC 2030A.
            </div>
          </div>

          <!-- Full G-code preview once generated -->
          <div class="full-preview" v-if="fullGcode">
            <GcodePreviewPanel
              :gcode="fullGcode"
              op-name="Full Program"
              :cycle-time-secs="totalTime"
              filename="neck_full.nc"
              @toast="emit('toast', $event)"
            />
          </div>
        </div>
      </div>

    </div>

    <!-- Right: shared neck config panel -->
    <aside class="caw-right">
      <div class="sec-lbl" style="padding: 10px 13px 4px">Neck spec</div>

      <div class="right-section">
        <div class="sec-sublbl">Preset</div>
        <div class="preset-row">
          <button v-for="p in ['les_paul','strat',null]" :key="String(p)"
            class="preset-btn" :class="{ on: neckConfig.preset === p }"
            @click="applyPreset(p)">
            {{ p === 'les_paul' ? 'LP' : p === 'strat' ? 'Strat' : 'Custom' }}
          </button>
        </div>
      </div>

      <div class="right-section">
        <div class="sec-sublbl">Scale &amp; Frets</div>
        <div class="field-row">
          <label class="fld-k">Scale</label>
          <input class="fld-v num" type="number" step="0.1" min="580" max="680"
            v-model.number="neckConfig.scale_length_mm"
            @change="evaluateDebounced()" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Frets</label>
          <input class="fld-v num" type="number" step="1" min="20" max="24"
            v-model.number="neckConfig.fret_count"
            @change="evaluateDebounced()" />
        </div>
      </div>

      <div class="right-section">
        <div class="sec-sublbl">Material</div>
        <select class="fld-v sel" style="width:100%; margin: 0 13px; width: calc(100% - 26px)"
          v-model="neckConfig.material"
          @change="evaluateDebounced()">
          <option value="maple">Maple</option>
          <option value="mahogany">Mahogany</option>
          <option value="rosewood">Rosewood</option>
          <option value="walnut">Walnut</option>
        </select>
      </div>

      <div class="right-section">
        <div class="sec-sublbl">Ops enabled</div>
        <div v-for="(label, key) in {
          include_truss_rod:     'OP10 Truss rod',
          include_profile_rough: 'OP40 Roughing',
          include_profile_finish:'OP45 Finishing',
          include_fret_slots:    'OP50 Fret slots',
        }" :key="key" class="field-row">
          <label class="fld-k">{{ label }}</label>
          <input type="checkbox"
            :checked="neckConfig[key]"
            @change="applyPatch({ [key]: ($event.target as HTMLInputElement).checked })" />
        </div>
      </div>

      <!-- Gate summary always visible -->
      <div class="right-section gate-summary">
        <div class="sec-sublbl">Gate summary</div>
        <div v-for="s in STEPS.slice(1,5)" :key="s.id" class="gs-row">
          <span class="gs-op">{{ s.op!.replace('_',' ') }}</span>
          <GateStatusBadge :gate="gates[s.op!]" :loading="gateLoading" :compact="true" />
        </div>
      </div>
    </aside>

    <div class="context-tools">
      <button
        class="tools-toggle"
        @click="toolsOpen = !toolsOpen">
        ⚙ Tools ({{ contextTools.tools.value.length }})
      </button>
      <div v-if="toolsOpen" class="tools-panel">
        <p class="tools-hint">
          Context-aware calculators will appear here
          as modules mature.
        </p>
        <ul>
          <li v-for="t in contextTools.tools.value"
              :key="t">{{ t }}</li>
        </ul>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.caw-layout {
  display: grid;
  grid-template-columns: 140px 1fr 200px;
  height: 100%;
  background: var(--w0);
}

/* ── Step sidebar ───────────────────────────────────────────────────────────── */
.caw-steps {
  background: var(--w1);
  border-right: 1px solid var(--w3);
  display: flex; flex-direction: column;
  overflow-y: auto;
}
.caw-steps-header {
  padding: 10px 12px 6px;
  font-size: 8px; letter-spacing: 1.2px; text-transform: uppercase;
  color: var(--br3); border-bottom: 1px solid var(--w3);
}
.caw-step {
  display: flex; align-items: center; gap: 7px;
  padding: 8px 12px; cursor: pointer;
  border-left: 2px solid transparent;
  border-bottom: 1px solid var(--w2);
  transition: all .1s;
}
.caw-step:hover { background: var(--w2); }
.caw-step.active { border-left-color: var(--br); background: rgba(184,150,46,.06); }
.caw-step.done   { border-left-color: var(--green2); }
.caw-step.warn   { border-left-color: var(--red); }

.step-num {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--w3); display: flex; align-items: center; justify-content: center;
  font-size: 8px; color: var(--dim); flex-shrink: 0;
}
.caw-step.active .step-num { background: var(--br); color: #0f0d0a; }
.caw-step.done   .step-num { background: var(--green2); color: #0f0d0a; }
.caw-step.warn   .step-num { background: var(--red);    color: #fff; }
.step-done-icon  { color: inherit; font-size: 8px; }
.step-warn-icon  { color: inherit; font-size: 9px; font-weight: 700; }

.step-lbl { font-size: 9px; color: var(--dim); flex: 1; }
.caw-step.active .step-lbl { color: var(--br2); }

.step-gate-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
  background: var(--w4);
}
.step-gate-dot.green  { background: var(--green2); }
.step-gate-dot.yellow { background: var(--amber);  }
.step-gate-dot.red    { background: var(--red);    }
.step-gate-dot.idle   { background: var(--w4);     }

.caw-machine-info {
  margin-top: auto; padding: 10px 12px;
  border-top: 1px solid var(--w3);
}
.mi-label { font-size: 7px; color: var(--dim3); letter-spacing: 1px; text-transform: uppercase; }
.mi-val   { font-size: 8px; color: var(--v1); margin-top: 2px; font-family: var(--mono); }

/* ── Centre ─────────────────────────────────────────────────────────────────── */
.caw-centre { overflow: hidden; display: flex; flex-direction: column; }

/* Step 0 / Step 5 body */
.caw-step-body { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
.step-body-header {
  padding: 10px 16px 8px; border-bottom: 1px solid var(--w3);
  font-family: var(--serif); font-size: 13px; font-style: italic; color: var(--v1);
  background: var(--w1);
}
.step-body-content {
  padding: 12px 16px; display: flex; flex-direction: column; gap: 14px;
}
.step-section { display: flex; flex-direction: column; gap: 7px; }
.sec-lbl {
  font-size: 7px; letter-spacing: 1.4px; text-transform: uppercase; color: var(--br3);
}
.machine-spec-grid { display: flex; flex-direction: column; gap: 3px; }
.ms-row { display: flex; gap: 8px; }
.ms-k   { font-size: 9px; color: var(--dim); width: 70px; }
.ms-v   { font-size: 9px; color: var(--v1); font-family: var(--mono); }

.field-row { display: flex; align-items: center; gap: 6px; }
.fld-k { font-size: 9px; color: var(--dim); flex: 1; }
.fld-v {
  padding: 3px 6px; background: var(--w2); border: 1px solid var(--w3);
  border-radius: 2px; color: var(--v1); font-size: 9px; font-family: var(--mono);
  outline: none;
}
.fld-v:focus { border-color: var(--br3); }
.fld-v.sel { width: auto; }
.fld-v.num { width: 70px; }
.fld-u { font-size: 8px; color: var(--dim3); }
.fld-hint { font-size: 8px; color: var(--amber); line-height: 1.5; }

.next-btn {
  align-self: flex-start; padding: 7px 16px;
  background: none; border: 1px solid var(--br3); border-radius: 3px;
  color: var(--br2); font-family: var(--mono); font-size: 9px;
  letter-spacing: .5px; text-transform: uppercase; cursor: pointer;
  transition: all .12s; margin-top: 4px;
}
.next-btn:hover { background: var(--br); color: #0f0d0a; }

/* ── Op split (steps 1–4) ───────────────────────────────────────────────────── */
.caw-op-split {
  flex: 1; display: grid; grid-template-columns: 260px 1fr;
  overflow: hidden;
}
.caw-op-left  { border-right: 1px solid var(--w3); overflow-y: auto; background: var(--w1); }
.caw-op-right { overflow: hidden; }

/* ── Summary step ───────────────────────────────────────────────────────────── */
.summary-table { display: flex; flex-direction: column; gap: 5px; }
.summary-row {
  display: grid; grid-template-columns: 130px 1fr 100px 50px;
  align-items: center; gap: 8px;
  padding: 5px 8px; background: var(--w2); border-radius: 3px;
}
.sum-op   { font-size: 9px; color: var(--dim); font-family: var(--mono); }
.sum-status      { font-size: 8px; }
.sum-status.done { color: var(--green2); }
.sum-status.pending { color: var(--dim3); }
.sum-time { font-size: 8px; color: var(--dim3); text-align: right; }

.total-time  { font-size: 13px; color: var(--v1); font-family: var(--mono); }
.total-hint  { font-size: 8px; color: var(--dim3); margin-left: 8px; }

.sum-gate-warn {
  font-size: 9px; color: var(--red); padding: 5px 8px;
  background: rgba(200,72,72,.07); border-radius: 3px;
}
.dl-btn {
  padding: 9px 0; width: 100%; background: var(--br); border: 1px solid var(--br);
  border-radius: 3px; color: #0f0d0a; font-family: var(--mono); font-size: 9px;
  letter-spacing: .5px; text-transform: uppercase; cursor: pointer;
  font-weight: 600; transition: all .12s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.dl-btn:hover:not(:disabled) { background: var(--br2); }
.dl-btn:disabled { opacity: .4; cursor: not-allowed; }
.sum-note { font-size: 8px; color: var(--dim3); line-height: 1.6; }
.full-preview { height: 300px; border-top: 1px solid var(--w3); }
.gen-spin {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1.5px solid rgba(0,0,0,.2); border-top-color: rgba(0,0,0,.8);
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Right panel ────────────────────────────────────────────────────────────── */
.caw-right {
  background: var(--w1); border-left: 1px solid var(--w3);
  overflow-y: auto; display: flex; flex-direction: column;
}
.right-section {
  padding: 8px 13px; border-bottom: 1px solid var(--w3);
  display: flex; flex-direction: column; gap: 5px;
}
.sec-sublbl {
  font-size: 7px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--dim3);
  margin-bottom: 2px;
}
.preset-row { display: flex; gap: 5px; }
.preset-btn {
  flex: 1; padding: 4px 0; background: none; border: 1px solid var(--w3);
  border-radius: 2px; font-size: 8px; color: var(--dim); cursor: pointer;
  font-family: var(--mono); transition: all .1s;
}
.preset-btn.on { border-color: var(--br3); color: var(--br2); background: rgba(184,150,46,.07); }
.preset-btn:hover { border-color: var(--w4); color: var(--v1); }

.gate-summary { gap: 5px; }
.gs-row { display: flex; align-items: center; justify-content: space-between; }
.gs-op  { font-size: 8px; color: var(--dim); text-transform: capitalize; }

.context-tools { padding: 8px 12px; border-top: 1px solid var(--w3); background: var(--w1); }
.tools-toggle { padding: 4px 8px; font-size: 8px; color: var(--dim); background: none; border: 1px solid var(--w3); border-radius: 3px; cursor: pointer; }
.tools-panel { margin-top: 6px; padding: 8px; border: 1px solid var(--w3); border-radius: 3px; }
.tools-hint { font-size: 8px; color: var(--dim3); margin: 0 0 6px 0; }
.context-tools ul { margin: 0; padding-left: 16px; font-size: 8px; color: var(--dim); }
</style>
