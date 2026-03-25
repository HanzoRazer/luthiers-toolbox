<script setup lang="ts">
/**
 * NeckOpPanel.vue
 *
 * Configuration + gate + generate for one neck operation.
 * Used four times in CamWorkspaceView (OP10, OP40, OP45, OP50).
 *
 * The parent provides:
 *   - neckConfig (shared NeckConfigIn state)
 *   - machineId
 *   - gateResult (live from evaluate, debounced 300ms by parent)
 *   - gateLoading (while evaluate in-flight)
 *
 * This component fires:
 *   - generate(op, gcode, cycleTime)   — user pressed Generate
 *   - update:neckConfig(patch)         — any slider changed
 */

import { ref, computed } from 'vue'
import GateStatusBadge from './GateStatusBadge.vue'
import type { GateResult } from './GateStatusBadge.vue'

// ── Op descriptors ────────────────────────────────────────────────────────────
type OpId = 'truss_rod' | 'profile_rough' | 'profile_finish' | 'fret_slots'

interface OpMeta {
  id:      OpId
  label:   string
  toolNum: number
  toolDesc: string
  color:   string
}

const OP_META: Record<OpId, OpMeta> = {
  truss_rod:     { id: 'truss_rod',     label: 'OP10 — Truss Rod',       toolNum: 2, toolDesc: 'T2  1/8" Flat End Mill',   color: '#5b8fa8' },
  profile_rough: { id: 'profile_rough', label: 'OP40 — Profile Roughing', toolNum: 1, toolDesc: 'T1  1/4" Ball End',        color: '#b8962e' },
  profile_finish:{ id: 'profile_finish',label: 'OP45 — Profile Finishing',toolNum: 3, toolDesc: 'T3  3/8" Ball End',        color: '#90c080' },
  fret_slots:    { id: 'fret_slots',    label: 'OP50 — Fret Slots',       toolNum: 4, toolDesc: 'T4  0.023" Kerf Saw',      color: '#a080c0' },
}

// ── Props / emits ─────────────────────────────────────────────────────────────
const props = defineProps<{
  op:          OpId
  neckConfig:  Record<string, any>
  machineId:   string
  gateResult:  GateResult | null
  gateLoading: boolean
  strictMode?: boolean
}>()

const emit = defineEmits<{
  generate:        [op: OpId, gcode: string, cycleTime: number]
  'update:neckConfig': [patch: Record<string, any>]
  toast:           [msg: string]
}>()

const meta = computed(() => OP_META[props.op])

// ── Local generate state ──────────────────────────────────────────────────────
const generating = ref(false)
const gcode      = ref('')
const cycleTime  = ref(0)
const genError   = ref('')

const canGenerate = computed(() =>
  props.gateResult !== null &&
  props.gateResult.overall_risk !== 'RED' &&
  !generating.value
)

async function onGenerate() {
  generating.value = true
  genError.value   = ''
  gcode.value      = ''

  try {
    const res = await fetch(`/api/cam-workspace/neck/generate/${props.op}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        machine:    { machine_id: props.machineId },
        neck:       props.neckConfig,
        strict_mode: props.strictMode ?? false,
      }),
    })

    if (res.status === 409) {
      const detail = await res.json()
      genError.value = detail.detail?.message ?? 'Gate RED — fix failures before generating'
      emit('toast', genError.value)
      return
    }
    if (!res.ok) {
      genError.value = `Server error ${res.status}`
      return
    }

    const data = await res.json()
    gcode.value    = data.gcode ?? ''
    cycleTime.value = data.cycle_time_seconds ?? 0
    emit('generate', props.op, gcode.value, cycleTime.value)
    emit('toast', `${meta.value.label} generated — ${data.gcode_line_count} lines ≈ ${Math.round(cycleTime.value)}s`)

  } catch (e) {
    genError.value = String(e)
    emit('toast', `Generate failed: ${genError.value}`)
  } finally {
    generating.value = false
  }
}

// ── Slider helpers ────────────────────────────────────────────────────────────
function patch(field: string, value: any) {
  emit('update:neckConfig', { [field]: value })
}
function patchNested(parent: string, field: string, value: any) {
  emit('update:neckConfig', {
    [parent]: { ...(props.neckConfig[parent] ?? {}), [field]: value }
  })
}
</script>

<template>
  <div class="nop-wrap">

    <!-- Op header -->
    <div class="nop-header" :style="{ borderLeftColor: meta.color }">
      <div class="nop-label">{{ meta.label }}</div>
      <div class="nop-tool">{{ meta.toolDesc }}</div>
    </div>

    <!-- Gate status -->
    <div class="nop-gate-section">
      <div class="sec-lbl">Gate</div>
      <GateStatusBadge :gate="gateResult" :loading="gateLoading" :compact="false" />
    </div>

    <!-- YELLOW warning banner -->
    <div v-if="gateResult?.overall_risk === 'YELLOW'" class="nop-warn-banner">
      <div class="warn-icon">⚠</div>
      <div class="warn-body">
        <div class="warn-title">Warnings — review before cutting</div>
        <div v-for="w in gateResult.warnings" :key="w" class="warn-line">{{ w }}</div>
      </div>
    </div>

    <!-- OP10: Truss rod parameters -->
    <template v-if="op === 'truss_rod'">
      <div class="nop-section">
        <div class="sec-lbl">Truss Rod Channel</div>
        <div class="field-row">
          <label class="fld-k">Width</label>
          <input class="fld-v num" type="number" step="0.1" min="4" max="12"
            :value="neckConfig.truss_rod?.width_mm ?? 6.35"
            @input="patchNested('truss_rod','width_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Depth</label>
          <input class="fld-v num" type="number" step="0.1" min="6" max="15"
            :value="neckConfig.truss_rod?.depth_mm ?? 9.525"
            @input="patchNested('truss_rod','depth_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Length</label>
          <input class="fld-v num" type="number" step="1" min="300" max="500"
            :value="neckConfig.truss_rod?.length_mm ?? 406.4"
            @input="patchNested('truss_rod','length_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Nut offset</label>
          <input class="fld-v num" type="number" step="0.5" min="6" max="25"
            :value="neckConfig.truss_rod?.start_offset_mm ?? 12.7"
            @input="patchNested('truss_rod','start_offset_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
      </div>
    </template>

    <!-- OP40/OP45: Profile parameters -->
    <template v-else-if="op === 'profile_rough' || op === 'profile_finish'">
      <div class="nop-section">
        <div class="sec-lbl">Profile Shape</div>
        <div class="field-row">
          <label class="fld-k">Shape</label>
          <select class="fld-v sel"
            :value="neckConfig.profile_carving?.profile_type ?? 'c_shape'"
            @change="patchNested('profile_carving','profile_type', ($event.target as HTMLSelectElement).value)">
            <option value="c_shape">C Shape (Vintage)</option>
            <option value="d_shape">D Shape (Modern)</option>
            <option value="v_shape">V Shape (Vintage Fender)</option>
            <option value="u_shape">U Shape (Baseball)</option>
            <option value="asymmetric">Asymmetric</option>
          </select>
        </div>
        <div class="field-row">
          <label class="fld-k">Depth nut</label>
          <input class="fld-v num" type="number" step="0.5" min="16" max="28"
            :value="neckConfig.profile_carving?.depth_at_nut_mm ?? 20.0"
            @input="patchNested('profile_carving','depth_at_nut_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Depth 12th</label>
          <input class="fld-v num" type="number" step="0.5" min="18" max="30"
            :value="neckConfig.profile_carving?.depth_at_12th_mm ?? 22.0"
            @input="patchNested('profile_carving','depth_at_12th_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Depth heel</label>
          <input class="fld-v num" type="number" step="0.5" min="20" max="35"
            :value="neckConfig.profile_carving?.depth_at_heel_mm ?? 25.0"
            @input="patchNested('profile_carving','depth_at_heel_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div v-if="op === 'profile_finish'" class="field-row">
          <label class="fld-k">Finish allow.</label>
          <input class="fld-v num" type="number" step="0.05" min="0.1" max="1.5"
            :value="neckConfig.profile_carving?.finish_allowance_mm ?? 0.75"
            @input="patchNested('profile_carving','finish_allowance_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
      </div>

      <div class="nop-section">
        <div class="sec-lbl">Neck Dimensions</div>
        <div class="field-row">
          <label class="fld-k">Nut width</label>
          <input class="fld-v num" type="number" step="0.5" min="38" max="50"
            :value="neckConfig.nut_width_mm ?? 43.0"
            @input="patch('nut_width_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Heel width</label>
          <input class="fld-v num" type="number" step="0.5" min="50" max="70"
            :value="neckConfig.heel_width_mm ?? 56.0"
            @input="patch('heel_width_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
      </div>
    </template>

    <!-- OP50: Fret slot parameters -->
    <template v-else-if="op === 'fret_slots'">
      <div class="nop-section">
        <div class="sec-lbl">Fret Slot</div>
        <div class="field-row">
          <label class="fld-k">Kerf width</label>
          <input class="fld-v num" type="number" step="0.001" min="0.4" max="0.8"
            :value="neckConfig.fret_slots?.slot_width_mm ?? 0.584"
            @input="patchNested('fret_slots','slot_width_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Depth</label>
          <input class="fld-v num" type="number" step="0.1" min="2" max="6"
            :value="neckConfig.fret_slots?.slot_depth_mm ?? 3.5"
            @input="patchNested('fret_slots','slot_depth_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Board thickness</label>
          <input class="fld-v num" type="number" step="0.1" min="4" max="8"
            :value="neckConfig.fret_slots?.fretboard_thickness_mm ?? 6.35"
            @input="patchNested('fret_slots','fretboard_thickness_mm', +($event.target as HTMLInputElement).value)" />
          <span class="fld-u">mm</span>
        </div>
        <div class="field-row">
          <label class="fld-k">Compound radius</label>
          <input type="checkbox"
            :checked="neckConfig.fret_slots?.compound_radius ?? false"
            @change="patchNested('fret_slots','compound_radius', ($event.target as HTMLInputElement).checked)" />
        </div>
        <template v-if="neckConfig.fret_slots?.compound_radius">
          <div class="field-row">
            <label class="fld-k">Radius nut</label>
            <input class="fld-v num" type="number" step="1" min="150" max="500"
              :value="neckConfig.fret_slots?.radius_at_nut_mm ?? 254.0"
              @input="patchNested('fret_slots','radius_at_nut_mm', +($event.target as HTMLInputElement).value)" />
            <span class="fld-u">mm</span>
          </div>
          <div class="field-row">
            <label class="fld-k">Radius heel</label>
            <input class="fld-v num" type="number" step="1" min="200" max="600"
              :value="neckConfig.fret_slots?.radius_at_heel_mm ?? 406.4"
              @input="patchNested('fret_slots','radius_at_heel_mm', +($event.target as HTMLInputElement).value)" />
            <span class="fld-u">mm</span>
          </div>
        </template>
      </div>
    </template>

    <!-- Generate button -->
    <div class="nop-gen-section">
      <button class="nop-gen-btn"
        :class="{
          'can-gen':  canGenerate,
          'gate-red': gateResult?.overall_risk === 'RED',
          busy:       generating,
        }"
        :disabled="!canGenerate"
        @click="onGenerate">
        <span v-if="generating" class="gen-spin"></span>
        <span v-else-if="gateResult?.overall_risk === 'RED'">✕ Gate RED — fix issues</span>
        <span v-else-if="gateResult === null">─ Evaluate first</span>
        <span v-else>▶ Generate {{ meta.label }}</span>
      </button>
      <div v-if="genError" class="gen-error">{{ genError }}</div>
    </div>

  </div>
</template>

<style scoped>
.nop-wrap {
  display: flex; flex-direction: column; gap: 0;
  overflow-y: auto;
}

/* Header */
.nop-header {
  padding: 8px 13px; border-left: 3px solid var(--br3);
  border-bottom: 1px solid var(--w3);
}
.nop-label { font-family: var(--mono); font-size: 9px; color: var(--br2); letter-spacing: .6px; text-transform: uppercase; }
.nop-tool  { font-size: 8px; color: var(--dim3); margin-top: 2px; }

/* Gate section */
.nop-gate-section {
  padding: 8px 13px; border-bottom: 1px solid var(--w3);
}

/* Warning banner */
.nop-warn-banner {
  display: flex; gap: 8px;
  padding: 7px 13px; border-bottom: 1px solid var(--w3);
  background: rgba(200,150,48,.06);
}
.warn-icon  { font-size: 12px; flex-shrink: 0; color: var(--amber); }
.warn-title { font-size: 8px; color: var(--amber); letter-spacing: .4px; margin-bottom: 3px; }
.warn-line  { font-size: 8px; color: var(--dim); line-height: 1.5; }
.warn-body  { display: flex; flex-direction: column; gap: 2px; }

/* Section */
.nop-section {
  padding: 8px 13px; border-bottom: 1px solid var(--w3);
  display: flex; flex-direction: column; gap: 6px;
}
.sec-lbl {
  font-size: 7px; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--br3); margin-bottom: 2px;
}

/* Field rows */
.field-row { display: flex; align-items: center; gap: 6px; }
.fld-k { font-size: 9px; color: var(--dim); flex: 1; min-width: 80px; }
.fld-v {
  width: 70px; padding: 3px 6px;
  background: var(--w2); border: 1px solid var(--w3); border-radius: 2px;
  color: var(--v1); font-size: 9px; font-family: var(--mono);
  outline: none;
}
.fld-v:focus { border-color: var(--br3); }
.fld-v.sel { width: auto; flex: 1; }
.fld-u { font-size: 8px; color: var(--dim3); }

/* Generate */
.nop-gen-section {
  padding: 10px 13px; margin-top: auto;
  border-top: 1px solid var(--w3);
  display: flex; flex-direction: column; gap: 5px;
}
.nop-gen-btn {
  width: 100%; padding: 8px 0;
  border: 1px solid var(--w3); border-radius: 3px;
  background: none; font-family: var(--mono); font-size: 9px;
  letter-spacing: .5px; text-transform: uppercase;
  cursor: not-allowed; color: var(--dim3); transition: all .12s;
  display: flex; align-items: center; justify-content: center; gap: 6px;
}
.nop-gen-btn.can-gen {
  border-color: var(--br3); color: var(--br2); cursor: pointer;
}
.nop-gen-btn.can-gen:hover {
  background: var(--br); color: #0f0d0a;
}
.nop-gen-btn.gate-red {
  border-color: var(--red); color: var(--red); cursor: not-allowed;
  opacity: .6;
}
.nop-gen-btn.busy { opacity: .6; cursor: wait; }

.gen-spin {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1.5px solid var(--w4); border-top-color: var(--br);
  animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.gen-error {
  font-size: 8px; color: var(--red); padding: 3px 5px;
  background: rgba(200,72,72,.06); border-radius: 2px;
}
</style>
