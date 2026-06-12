<script setup lang="ts">
/**
 * ContourCuttingView - Contour / Profile Cutting Toolpath Generator
 *
 * Wired to the CamIntentV1 Profiling lane (Dev Order 8H):
 *   POST /api/cam/profiling/intent-gcode
 *
 * Contour-cutting IS perimeter profiling with holding tabs — there is no separate
 * /api/cam/contour lane, so this view maps onto ProfileDesignV1 (contour, inside/
 * outside, tool, tabs, finishing). Geometry is entered EXPLICITLY (contour polygon),
 * as DrillingView/PocketClearingView do — the intent endpoint takes points, not a file.
 *
 * Four affordances ProfileDesignV1 cannot serve are honestly gated (not faked):
 *   - DXF/SVG import   -> lane takes an explicit contour, not a file
 *   - "On Line" cut    -> ProfileDesignV1 models only is_outside (inside/outside)
 *   - "Tangent" lead-in-> backend models a lead_in_radius only (arc=radius, direct=0)
 *   - Spindle speed    -> profiling context has no spindle field
 */
import { ref, computed } from 'vue'
import {
  generateProfilingGcode,
  ProfilingIntentError,
  type ProfilingIntentRequest,
  type ProfilingIntentResponse,
  type ProfilePointV1,
} from '../../api/profiling'

// ---- Geometry (the "what") — explicit entry; default a 100 x 60 mm rectangle ----
const contour = ref<ProfilePointV1[]>([
  { x: 0, y: 0 },
  { x: 100, y: 0 },
  { x: 100, y: 60 },
  { x: 0, y: 60 },
])
const isClosed = ref(true)

// ---- Cut side — Inside/Outside served; On-Line is not modelled by ProfileDesignV1 ----
const cutSides = [
  { id: 'outside', name: 'Outside', served: true },
  { id: 'inside', name: 'Inside', served: true },
  { id: 'on-line', name: 'On Line', served: false },
] as const
const cutType = ref<'outside' | 'inside'>('outside')

// ---- Tool / depth ----
const toolDiameter = ref(6.0)   // mm (backend 0-50)
const cutDepth = ref(19)        // mm (backend 0-100)
const stepdown = ref(3.0)       // mm

// ---- Tabs (map 1:1 to ProfileDesignV1) ----
const tabsEnabled = ref(true)
const tabWidth = ref(8)          // mm (backend 1-30)
const tabHeight = ref(2)         // mm (backend 0.5-10)
const tabCount = ref(4)          // backend 0-20

// ---- Finishing ----
const finishingPass = ref(true)
const finishingAllowance = ref(0.3) // mm (backend 0-5)

// ---- Lead-in — Arc/Direct served (as a radius); Tangent not modelled ----
const leadIns = [
  { id: 'arc', name: 'Arc', served: true },
  { id: 'direct', name: 'Direct', served: true },
  { id: 'tangent', name: 'Tangent', served: false },
] as const
const leadIn = ref<'arc' | 'direct'>('arc')
const leadInRadius = ref(5)      // mm (backend 0-25); used when leadIn === 'arc'

// ---- Context (feeds/speeds) ----
const feedRate = ref(1500)       // mm/min
const plungeRate = ref(500)      // mm/min
const safeHeight = ref(5)        // mm
const spindleSpeed = ref(18000)  // rpm — informational only (engine has no spindle field)

// ---- State ----
const loading = ref(false)
const result = ref<ProfilingIntentResponse | null>(null)
const blocked = ref<{ message: string; issues: string[]; riskLevel?: string } | null>(null)
const errorMsg = ref<string | null>(null)

const hasGcode = computed(() => !!result.value?.gcode)

function addPoint() {
  contour.value.push({ x: 0, y: 0 })
}
function removePoint(i: number) {
  if (contour.value.length > 3) contour.value.splice(i, 1)
}

function buildRequest(): ProfilingIntentRequest {
  return {
    mode: 'router_3axis',
    units: 'mm',
    tool_id: 'profile:intent',
    design: {
      contour: contour.value.map(p => ({ x: p.x, y: p.y })),
      is_closed: isClosed.value,
      is_outside: cutType.value === 'outside',
      tool_diameter_mm: toolDiameter.value,
      cut_depth_mm: cutDepth.value,
      use_tabs: tabsEnabled.value,
      tab_count: tabsEnabled.value ? tabCount.value : 0,
      tab_width_mm: tabWidth.value,
      tab_height_mm: tabHeight.value,
      finishing_pass: finishingPass.value,
      finishing_allowance_mm: finishingAllowance.value,
    },
    context: {
      stepdown_mm: stepdown.value,
      feed_rate_mm_min: feedRate.value,
      plunge_rate_mm_min: plungeRate.value,
      safe_z_mm: safeHeight.value,
      // Lead-in is a radius: Arc uses the radius, Direct plunges (radius 0).
      lead_in_radius_mm: leadIn.value === 'arc' ? leadInRadius.value : 0,
    },
  }
}

async function generateToolpath() {
  loading.value = true
  result.value = null
  blocked.value = null
  errorMsg.value = null
  try {
    result.value = await generateProfilingGcode(buildRequest())
  } catch (e) {
    if (e instanceof ProfilingIntentError && e.status === 409) {
      const feas = e.feasibility || {}
      blocked.value = {
        message: e.message,
        issues: Array.isArray(feas.issues) ? feas.issues : [],
        riskLevel: feas.risk_level,
      }
    } else if (e instanceof ProfilingIntentError) {
      errorMsg.value = `${e.code}: ${e.message}`
    } else {
      errorMsg.value = e instanceof Error ? e.message : 'Unexpected error'
    }
  } finally {
    loading.value = false
  }
}

function downloadGcode() {
  if (!result.value?.gcode) return
  const blob = new Blob([result.value.gcode], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `contour_${result.value.run_id || 'toolpath'}.nc`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="contour-cutting-view">
    <div class="header">
      <h1>Contour Cutting</h1>
      <p class="subtitle">Perimeter profiling toolpaths with holding tabs (RMOS feasibility)</p>
    </div>

    <div class="content">
      <!-- Geometry + cut side -->
      <div class="panel geometry-panel">
        <h3>Contour (mm)</h3>
        <div class="point-list">
          <div v-for="(p, i) in contour" :key="`c-${i}`" class="point-row">
            <input type="number" v-model.number="p.x" step="1" aria-label="contour x" />
            <input type="number" v-model.number="p.y" step="1" aria-label="contour y" />
            <button class="mini-btn" @click="removePoint(i)" :disabled="contour.length <= 3">✕</button>
          </div>
        </div>
        <button class="add-btn" @click="addPoint">+ Add point</button>
        <div class="form-group checkbox-group">
          <label><input type="checkbox" v-model="isClosed" /> Closed contour</label>
        </div>

        <!-- Honest gate: the lane takes an explicit contour, not a file -->
        <div class="gated-affordance">
          <span class="gated-label">DXF / SVG import</span>
          <span class="soon-tag">coming soon</span>
          <p class="gated-note">This lane takes an explicit contour; file-derived contours aren't wired yet.</p>
        </div>

        <h3>Cut Side</h3>
        <div class="seg-buttons">
          <button
            v-for="s in cutSides"
            :key="s.id"
            :class="{ active: cutType === s.id, disabled: !s.served }"
            :disabled="!s.served"
            :title="s.served ? '' : 'Not modelled by the profiling engine (inside/outside only)'"
            @click="s.served && (cutType = s.id as 'outside' | 'inside')"
          >
            {{ s.name }}<span v-if="!s.served" class="soon-tag">soon</span>
          </button>
        </div>

        <h3>Lead-In</h3>
        <div class="seg-buttons">
          <button
            v-for="l in leadIns"
            :key="l.id"
            :class="{ active: leadIn === l.id, disabled: !l.served }"
            :disabled="!l.served"
            :title="l.served ? '' : 'Engine models a lead-in radius only (arc/direct)'"
            @click="l.served && (leadIn = l.id as 'arc' | 'direct')"
          >
            {{ l.name }}<span v-if="!l.served" class="soon-tag">soon</span>
          </button>
        </div>
        <div v-if="leadIn === 'arc'" class="form-group">
          <label>Lead-In Radius (mm)</label>
          <input type="number" v-model.number="leadInRadius" step="0.5" min="0" max="25" />
        </div>
      </div>

      <!-- Parameters -->
      <div class="panel params-panel">
        <h3>Tool &amp; Depth</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="toolDiameter" step="0.1" min="0.5" max="50" />
          </div>
          <div class="form-group">
            <label>Cut Depth (mm)</label>
            <input type="number" v-model.number="cutDepth" step="0.5" min="0.5" max="100" />
          </div>
        </div>
        <div class="form-group">
          <label>Stepdown (mm)</label>
          <input type="number" v-model.number="stepdown" step="0.5" min="0.1" max="20" />
        </div>

        <h3>Holding Tabs</h3>
        <div class="form-group checkbox-group">
          <label><input type="checkbox" v-model="tabsEnabled" /> Enable holding tabs</label>
        </div>
        <div v-if="tabsEnabled" class="form-row">
          <div class="form-group">
            <label>Tab Width (mm)</label>
            <input type="number" v-model.number="tabWidth" step="1" min="1" max="30" />
          </div>
          <div class="form-group">
            <label>Tab Height (mm)</label>
            <input type="number" v-model.number="tabHeight" step="0.5" min="0.5" max="10" />
          </div>
        </div>
        <div v-if="tabsEnabled" class="form-group">
          <label>Tab Count</label>
          <input type="number" v-model.number="tabCount" step="1" min="1" max="20" />
        </div>

        <h3>Finishing</h3>
        <div class="form-row">
          <div class="form-group checkbox-group">
            <label><input type="checkbox" v-model="finishingPass" /> Finishing pass</label>
          </div>
          <div class="form-group">
            <label>Allowance (mm)</label>
            <input type="number" v-model.number="finishingAllowance" step="0.1" min="0" max="5" :disabled="!finishingPass" />
          </div>
        </div>

        <h3>Feeds &amp; Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="100" min="100" max="10000" />
          </div>
          <div class="form-group">
            <label>Plunge Rate (mm/min)</label>
            <input type="number" v-model.number="plungeRate" step="50" min="50" max="2000" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Safe Height (mm)</label>
            <input type="number" v-model.number="safeHeight" step="1" min="1" max="50" />
          </div>
          <div class="form-group">
            <label>Spindle Speed (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" disabled title="Profiling engine has no spindle field" />
            <span class="hint">not consumed by the profiling engine</span>
          </div>
        </div>
      </div>

      <!-- Result -->
      <div class="panel preview-panel">
        <h3>Result</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating toolpath…</div>

          <div v-else-if="blocked" class="state-block blocked">
            <span class="icon">🚫</span>
            <p class="state-title">Feasibility blocked</p>
            <p class="state-msg">{{ blocked.message }}</p>
            <ul v-if="blocked.issues.length" class="issue-list">
              <li v-for="(iss, i) in blocked.issues" :key="i">{{ iss }}</li>
            </ul>
            <p v-if="blocked.riskLevel" class="risk">Risk: {{ blocked.riskLevel }}</p>
          </div>

          <div v-else-if="errorMsg" class="state-block error">
            <span class="icon">⚠️</span>
            <p class="state-title">Error</p>
            <p class="state-msg">{{ errorMsg }}</p>
          </div>

          <div v-else-if="result" class="state-block ok">
            <span class="icon">✅</span>
            <p class="state-title">Toolpath generated</p>
            <p class="state-msg">
              {{ result.metadata.pass_count }} pass(es) ·
              {{ result.metadata.tab_count }} tab(s) ·
              {{ result.metadata.total_length_mm.toFixed(0) }}mm ·
              ~{{ (result.metadata.estimated_time_seconds / 60).toFixed(1) }} min
            </p>
            <ul v-if="result.issues.length" class="issue-list soft">
              <li v-for="(iss, i) in result.issues" :key="i">{{ iss.code }}: {{ iss.message }}</li>
            </ul>
          </div>

          <div v-else class="placeholder">
            <span class="icon">✂️</span>
            <p>Configure the contour and generate a toolpath</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="loading || contour.length < 3">
            Generate Toolpath
          </button>
          <button class="btn btn-secondary" @click="downloadGcode" :disabled="!hasGcode">
            Download G-code
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contour-cutting-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 320px 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.point-list { display: flex; flex-direction: column; gap: 0.4rem; }
.point-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 0.4rem; align-items: center; }
.point-row input { width: 100%; padding: 0.4rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; font-size: 0.85rem; }
.mini-btn { padding: 0.3rem 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #aaa; cursor: pointer; font-size: 0.75rem; }
.mini-btn:hover:not(:disabled) { background: #3a2626; border-color: #774444; color: #e5a5a5; }
.mini-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.add-btn { margin-top: 0.5rem; padding: 0.4rem 0.75rem; background: #262626; border: 1px dashed #444; border-radius: 0.375rem; color: #60a5fa; cursor: pointer; font-size: 0.8rem; }
.add-btn:hover { background: #1e3a5f; }

.gated-affordance { margin-top: 1rem; padding: 0.75rem; background: #161616; border: 1px dashed #333; border-radius: 0.5rem; }
.gated-label { font-size: 0.85rem; color: #888; }
.gated-note { font-size: 0.72rem; color: #666; margin: 0.4rem 0 0; }

.seg-buttons { display: flex; gap: 0.5rem; }
.seg-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; font-size: 0.85rem; }
.seg-buttons button.active { background: #2563eb; border-color: #2563eb; }
.seg-buttons button.disabled { opacity: 0.5; cursor: not-allowed; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.checkbox-group label { display: flex; align-items: center; gap: 0.4rem; color: #e5e5e5; }
.form-group input[type="number"] { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; font-size: 0.875rem; }
.form-group input:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { font-size: 0.72rem; color: #60a5fa; }

.soon-tag { display: inline-block; margin-left: 0.4rem; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.04em; background: #3a3a1a; color: #d4c468; padding: 0.1rem 0.35rem; border-radius: 0.25rem; }

.preview-container { aspect-ratio: 4/3; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; padding: 1rem; overflow: auto; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }

.state-block { text-align: center; }
.state-block .icon { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
.state-title { font-weight: 600; margin: 0 0 0.4rem; }
.state-msg { font-size: 0.85rem; color: #bbb; margin: 0; }
.state-block.ok .state-title { color: #4ade80; }
.state-block.blocked .state-title { color: #f87171; }
.state-block.error .state-title { color: #fbbf24; }
.issue-list { text-align: left; margin: 0.6rem 0 0; padding-left: 1.1rem; font-size: 0.78rem; color: #f8a5a5; }
.issue-list.soft { color: #d4c468; }
.risk { font-size: 0.78rem; color: #888; margin: 0.4rem 0 0; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
