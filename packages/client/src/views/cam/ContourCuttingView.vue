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
import { ref, computed, onUnmounted } from 'vue'
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

// Contour is always closed for profile cutting — open profiles not supported by this UI
const isClosed = true

// ---- Cut side — Inside/Outside served; On-Line is not modelled by ProfileDesignV1 ----
const cutSides = [
  { id: 'outside', name: 'Outside', served: true },
  { id: 'inside', name: 'Inside', served: true },
  { id: 'on-line', name: 'On Line', served: false },
] as const
const cutType = ref<'outside' | 'inside'>('outside')

// ---- Tool / depth ----
const toolDiameter = ref(6.0)   // mm (backend 0.5-50)
const cutDepth = ref(19)        // mm (backend 0.5-100)
const stepdown = ref(3.0)       // mm (0.1-20)

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
const feedRate = ref(1500)       // mm/min (100-10000)
const plungeRate = ref(500)      // mm/min (50-2000)
const safeHeight = ref(5)        // mm (1-50)
const retractHeight = ref(10)    // mm — exposed now (#12)
const climbMilling = ref(true)   // exposed now (#12)
const spindleSpeed = ref(18000)  // rpm — informational only (engine has no spindle field)

// ---- State ----
const loading = ref(false)
const result = ref<ProfilingIntentResponse | null>(null)
const blocked = ref<{ message: string; issues: string[]; riskLevel?: string } | null>(null)
const errorMsg = ref<string | null>(null)
let abortController: AbortController | null = null

// Cleanup on unmount
onUnmounted(() => {
  abortController?.abort()
})

// ---- Validation ----

function isFinitePositive(n: number): boolean {
  return Number.isFinite(n) && n > 0
}

function isFiniteNonNegative(n: number): boolean {
  return Number.isFinite(n) && n >= 0
}

/** Compute signed polygon area (shoelace formula). Positive = CCW, Negative = CW. */
function signedPolygonArea(points: ProfilePointV1[]): number {
  let area = 0
  for (let i = 0; i < points.length; i++) {
    const a = points[i]
    const b = points[(i + 1) % points.length]
    area += a.x * b.y - b.x * a.y
  }
  return area / 2
}

/** Check for zero-length edges (consecutive duplicate points). */
function hasZeroLengthEdge(points: ProfilePointV1[]): boolean {
  for (let i = 0; i < points.length; i++) {
    const a = points[i]
    const b = points[(i + 1) % points.length]
    if (a.x === b.x && a.y === b.y) return true
  }
  return false
}

/** Validate the request before sending. Returns array of error messages. */
function validateRequest(req: ProfilingIntentRequest): string[] {
  const errors: string[] = []
  const { design, context } = req

  // Contour validation
  if (!Array.isArray(design.contour) || design.contour.length < 3) {
    errors.push('Contour must contain at least 3 points.')
  } else {
    // Check all points are valid numbers
    for (let i = 0; i < design.contour.length; i++) {
      const p = design.contour[i]
      if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) {
        errors.push(`Point ${i + 1} has invalid coordinates.`)
        break
      }
    }

    // Check for zero-length edges
    if (hasZeroLengthEdge(design.contour)) {
      errors.push('Contour has consecutive duplicate points.')
    }

    // Check for near-zero area (degenerate polygon)
    if (design.is_closed && Math.abs(signedPolygonArea(design.contour)) < 0.001) {
      errors.push('Contour area must be greater than zero.')
    }
  }

  // Tool validation
  if (!isFinitePositive(design.tool_diameter_mm) || design.tool_diameter_mm < 0.5 || design.tool_diameter_mm > 50) {
    errors.push('Tool diameter must be between 0.5 and 50 mm.')
  }

  // Depth validation
  if (!isFinitePositive(design.cut_depth_mm) || design.cut_depth_mm < 0.5 || design.cut_depth_mm > 100) {
    errors.push('Cut depth must be between 0.5 and 100 mm.')
  }

  // Tab validation (when enabled)
  if (design.use_tabs && design.tab_count > 0) {
    if (design.tab_height_mm >= design.cut_depth_mm) {
      errors.push('Tab height must be less than cut depth.')
    }
    if (design.tab_width_mm < 1 || design.tab_width_mm > 30) {
      errors.push('Tab width must be between 1 and 30 mm.')
    }
    if (design.tab_height_mm < 0.5 || design.tab_height_mm > 10) {
      errors.push('Tab height must be between 0.5 and 10 mm.')
    }
  }

  // Finishing validation
  if (design.finishing_pass && (design.finishing_allowance_mm < 0 || design.finishing_allowance_mm > 5)) {
    errors.push('Finishing allowance must be between 0 and 5 mm.')
  }

  // Feed/speed validation
  if (!isFinitePositive(context.feed_rate_mm_min)) {
    errors.push('Feed rate must be a positive number.')
  }
  if (!isFinitePositive(context.plunge_rate_mm_min)) {
    errors.push('Plunge rate must be a positive number.')
  }
  if (!isFinitePositive(context.stepdown_mm)) {
    errors.push('Stepdown must be a positive number.')
  }
  if (!isFinitePositive(context.safe_z_mm)) {
    errors.push('Safe height must be a positive number.')
  }

  // Lead-in radius validation
  if (context.lead_in_radius_mm !== undefined && !isFiniteNonNegative(context.lead_in_radius_mm)) {
    errors.push('Lead-in radius must be a non-negative number.')
  }

  return errors
}

// ---- Computed validation state ----
const validationErrors = computed(() => validateRequest(buildRequest()))
const canGenerate = computed(() => !loading.value && validationErrors.value.length === 0)
const hasGcode = computed(() => !!result.value?.gcode)

// ---- Result summary with defensive access ----
const resultSummary = computed(() => {
  const md = result.value?.metadata
  if (!md) return null
  return {
    passes: Number.isFinite(md.pass_count) ? md.pass_count : 0,
    tabs: Number.isFinite(md.tab_count) ? md.tab_count : 0,
    length: Number.isFinite(md.total_length_mm) ? md.total_length_mm : 0,
    timeMinutes: Number.isFinite(md.estimated_time_seconds) ? md.estimated_time_seconds / 60 : 0,
  }
})

// ---- Point management ----

function addPoint() {
  // Add new point near the last point for convenience
  const last = contour.value[contour.value.length - 1]
  contour.value.push({ x: last?.x ?? 0, y: (last?.y ?? 0) + 10 })
}

function removePoint(i: number) {
  if (contour.value.length > 3) contour.value.splice(i, 1)
}

// Clamp point values on blur to ensure valid numbers
function clampPoint(p: ProfilePointV1) {
  if (!Number.isFinite(p.x)) p.x = 0
  if (!Number.isFinite(p.y)) p.y = 0
}

// ---- Request building with normalization ----

function buildRequest(): ProfilingIntentRequest {
  const useTabs = tabsEnabled.value
  const finishing = finishingPass.value

  return {
    mode: 'router_3axis',
    units: 'mm',
    // tool_id left undefined — backend uses default tool
    design: {
      contour: contour.value.map(p => ({
        x: Number.isFinite(p.x) ? p.x : 0,
        y: Number.isFinite(p.y) ? p.y : 0,
      })),
      is_closed: isClosed,
      is_outside: cutType.value === 'outside',
      tool_diameter_mm: toolDiameter.value,
      cut_depth_mm: cutDepth.value,
      // Normalize: zero out tab fields when tabs disabled
      use_tabs: useTabs,
      tab_count: useTabs ? tabCount.value : 0,
      tab_width_mm: useTabs ? tabWidth.value : 0,
      tab_height_mm: useTabs ? tabHeight.value : 0,
      // Normalize: zero out finishing allowance when finishing disabled
      finishing_pass: finishing,
      finishing_allowance_mm: finishing ? finishingAllowance.value : 0,
    },
    context: {
      stepdown_mm: stepdown.value,
      feed_rate_mm_min: feedRate.value,
      plunge_rate_mm_min: plungeRate.value,
      safe_z_mm: safeHeight.value,
      retract_z_mm: retractHeight.value,
      climb_milling: climbMilling.value,
      // Lead-in is a radius: Arc uses the radius, Direct plunges (radius 0).
      lead_in_radius_mm: leadIn.value === 'arc' ? leadInRadius.value : 0,
    },
  }
}

// ---- API call ----

async function generateToolpath() {
  // Cancel any in-flight request
  abortController?.abort()
  abortController = new AbortController()

  const request = buildRequest()
  const errors = validateRequest(request)

  result.value = null
  blocked.value = null
  errorMsg.value = null

  if (errors.length > 0) {
    errorMsg.value = errors.join(' ')
    return
  }

  loading.value = true
  try {
    result.value = await generateProfilingGcode(request, abortController.signal)
  } catch (e) {
    if (e instanceof ProfilingIntentError) {
      if (e.code === 'ABORTED') {
        // Request was cancelled, don't show error
        return
      }
      if (e.status === 409) {
        const feas = e.feasibility || {}
        // Fix #13: properly extract issues as strings
        const rawIssues = feas.issues
        let issueStrings: string[] = []
        if (Array.isArray(rawIssues)) {
          issueStrings = rawIssues.map((iss: unknown) => {
            if (typeof iss === 'string') return iss
            if (iss && typeof iss === 'object') {
              const obj = iss as Record<string, unknown>
              return obj.message ? String(obj.message) : JSON.stringify(iss)
            }
            return String(iss)
          })
        }
        blocked.value = {
          message: e.message,
          issues: issueStrings,
          riskLevel: typeof feas.risk_level === 'string' ? feas.risk_level : undefined,
        }
      } else {
        errorMsg.value = `${e.code}: ${e.message}`
      }
    } else {
      errorMsg.value = e instanceof Error ? e.message : 'Unexpected error'
    }
  } finally {
    loading.value = false
  }
}

// ---- Download ----

function sanitizeFilename(name: string): string {
  // Remove characters that are illegal in filenames on Windows/Mac/Linux
  return name
    .replace(/[<>:"/\\|?*]/g, '_')
    .split('')
    .map((char) => (char.charCodeAt(0) < 32 ? '_' : char))
    .join('')
    .slice(0, 200)
}

function downloadGcode() {
  if (!result.value?.gcode) return
  const blob = new Blob([result.value.gcode], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const runId = result.value.run_id ? sanitizeFilename(result.value.run_id) : 'toolpath'
  a.download = `contour_${runId}.nc`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="contour-cutting-view">
    <div class="header">
      <h1>Contour Cutting</h1>
      <p class="subtitle">Perimeter profiling toolpaths with holding tabs (RMOS feasibility)</p>
      <p class="mode-note">
        This tool supports profiling-backed contour cutting with explicit point entry,
        inside/outside cuts, arc/direct lead-ins, and optional holding tabs.
      </p>
    </div>

    <div class="content">
      <!-- Geometry + cut side -->
      <div class="panel geometry-panel" role="region" aria-label="Contour geometry">
        <h3 id="contour-heading">Contour (mm)</h3>
        <div class="point-list" role="list" aria-labelledby="contour-heading">
          <div v-for="(p, i) in contour" :key="`c-${i}`" class="point-row" role="listitem">
            <input
              type="number"
              v-model.number="p.x"
              step="1"
              inputmode="decimal"
              :aria-label="`Point ${i + 1} X coordinate`"
              @blur="clampPoint(p)"
            />
            <input
              type="number"
              v-model.number="p.y"
              step="1"
              inputmode="decimal"
              :aria-label="`Point ${i + 1} Y coordinate`"
              @blur="clampPoint(p)"
            />
            <button
              class="mini-btn"
              @click="removePoint(i)"
              :disabled="contour.length <= 3"
              :aria-label="`Remove point ${i + 1}`"
            >✕</button>
          </div>
        </div>
        <button class="add-btn" @click="addPoint" aria-label="Add new point to contour">+ Add point</button>

        <!-- Honest gate: the lane takes an explicit contour, not a file -->
        <div class="gated-affordance" role="note">
          <span class="gated-label">DXF / SVG import</span>
          <span class="soon-tag">coming soon</span>
          <p class="gated-note">This lane takes an explicit contour; file-derived contours aren't wired yet.</p>
        </div>

        <h3 id="cut-side-heading">Cut Side</h3>
        <div class="seg-buttons" role="radiogroup" aria-labelledby="cut-side-heading">
          <button
            v-for="s in cutSides"
            :key="s.id"
            role="radio"
            :aria-checked="cutType === s.id"
            :class="{ active: cutType === s.id, disabled: !s.served }"
            :disabled="!s.served"
            :title="s.served ? '' : 'Not modelled by the profiling engine (inside/outside only)'"
            @click="s.served && (cutType = s.id as 'outside' | 'inside')"
          >
            {{ s.name }}<span v-if="!s.served" class="soon-tag">soon</span>
          </button>
        </div>

        <h3 id="lead-in-heading">Lead-In</h3>
        <div class="seg-buttons" role="radiogroup" aria-labelledby="lead-in-heading">
          <button
            v-for="l in leadIns"
            :key="l.id"
            role="radio"
            :aria-checked="leadIn === l.id"
            :class="{ active: leadIn === l.id, disabled: !l.served }"
            :disabled="!l.served"
            :title="l.served ? '' : 'Engine models a lead-in radius only (arc/direct)'"
            @click="l.served && (leadIn = l.id as 'arc' | 'direct')"
          >
            {{ l.name }}<span v-if="!l.served" class="soon-tag">soon</span>
          </button>
        </div>
        <div v-if="leadIn === 'arc'" class="form-group">
          <label for="lead-in-radius">Lead-In Radius (mm)</label>
          <input id="lead-in-radius" type="number" v-model.number="leadInRadius" step="0.5" min="0" max="25" inputmode="decimal" />
        </div>
      </div>

      <!-- Parameters -->
      <div class="panel params-panel" role="region" aria-label="Cutting parameters">
        <h3>Tool &amp; Depth</h3>
        <div class="form-row">
          <div class="form-group">
            <label for="tool-diameter">Tool Diameter (mm)</label>
            <input id="tool-diameter" type="number" v-model.number="toolDiameter" step="0.1" min="0.5" max="50" inputmode="decimal" />
          </div>
          <div class="form-group">
            <label for="cut-depth">Cut Depth (mm)</label>
            <input id="cut-depth" type="number" v-model.number="cutDepth" step="0.5" min="0.5" max="100" inputmode="decimal" />
          </div>
        </div>
        <div class="form-group">
          <label for="stepdown">Stepdown (mm)</label>
          <input id="stepdown" type="number" v-model.number="stepdown" step="0.5" min="0.1" max="20" inputmode="decimal" />
        </div>

        <h3>Holding Tabs</h3>
        <div class="form-group checkbox-group">
          <label><input type="checkbox" v-model="tabsEnabled" /> Enable holding tabs</label>
        </div>
        <div v-if="tabsEnabled" class="form-row">
          <div class="form-group">
            <label for="tab-width">Tab Width (mm)</label>
            <input id="tab-width" type="number" v-model.number="tabWidth" step="1" min="1" max="30" inputmode="decimal" />
          </div>
          <div class="form-group">
            <label for="tab-height">Tab Height (mm)</label>
            <input id="tab-height" type="number" v-model.number="tabHeight" step="0.5" min="0.5" max="10" inputmode="decimal" />
          </div>
        </div>
        <div v-if="tabsEnabled" class="form-group">
          <label for="tab-count">Tab Count</label>
          <input id="tab-count" type="number" v-model.number="tabCount" step="1" min="1" max="20" inputmode="numeric" />
        </div>

        <h3>Finishing</h3>
        <div class="form-row">
          <div class="form-group checkbox-group">
            <label><input type="checkbox" v-model="finishingPass" /> Finishing pass</label>
          </div>
          <div class="form-group">
            <label for="finishing-allowance">Allowance (mm)</label>
            <input id="finishing-allowance" type="number" v-model.number="finishingAllowance" step="0.1" min="0" max="5" :disabled="!finishingPass" inputmode="decimal" />
          </div>
        </div>

        <h3>Feeds &amp; Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label for="feed-rate">Feed Rate (mm/min)</label>
            <input id="feed-rate" type="number" v-model.number="feedRate" step="100" min="100" max="10000" inputmode="numeric" />
          </div>
          <div class="form-group">
            <label for="plunge-rate">Plunge Rate (mm/min)</label>
            <input id="plunge-rate" type="number" v-model.number="plungeRate" step="50" min="50" max="2000" inputmode="numeric" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for="safe-height">Safe Height (mm)</label>
            <input id="safe-height" type="number" v-model.number="safeHeight" step="1" min="1" max="50" inputmode="decimal" />
          </div>
          <div class="form-group">
            <label for="retract-height">Retract Height (mm)</label>
            <input id="retract-height" type="number" v-model.number="retractHeight" step="1" min="1" max="100" inputmode="decimal" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group checkbox-group">
            <label><input type="checkbox" v-model="climbMilling" /> Climb milling</label>
            <span class="hint">vs conventional</span>
          </div>
          <div class="form-group">
            <label for="spindle-speed">Spindle Speed (RPM)</label>
            <input id="spindle-speed" type="number" v-model.number="spindleSpeed" disabled title="Profiling engine has no spindle field" />
            <span class="hint">not consumed by the profiling engine</span>
          </div>
        </div>
      </div>

      <!-- Result -->
      <div class="panel preview-panel" role="region" aria-label="Toolpath result">
        <h3>Result</h3>
        <div class="preview-container" aria-live="polite">
          <div v-if="loading" class="loading">Generating toolpath…</div>

          <div v-else-if="blocked" class="state-block blocked">
            <span class="icon" aria-hidden="true">🚫</span>
            <p class="state-title">Feasibility blocked</p>
            <p class="state-msg">{{ blocked.message }}</p>
            <ul v-if="blocked.issues.length" class="issue-list">
              <li v-for="(iss, i) in blocked.issues" :key="i">{{ iss }}</li>
            </ul>
            <p v-if="blocked.riskLevel" class="risk">Risk: {{ blocked.riskLevel }}</p>
          </div>

          <div v-else-if="errorMsg" class="state-block error">
            <span class="icon" aria-hidden="true">⚠️</span>
            <p class="state-title">Error</p>
            <p class="state-msg">{{ errorMsg }}</p>
          </div>

          <div v-else-if="resultSummary" class="state-block ok">
            <span class="icon" aria-hidden="true">✅</span>
            <p class="state-title">Toolpath generated</p>
            <p class="state-msg">
              {{ resultSummary.passes }} pass(es) ·
              {{ resultSummary.tabs }} tab(s) ·
              {{ resultSummary.length.toFixed(0) }}mm ·
              ~{{ resultSummary.timeMinutes.toFixed(1) }} min
            </p>
            <ul v-if="result?.issues?.length" class="issue-list soft">
              <li v-for="(iss, i) in result.issues" :key="i">{{ iss.code }}: {{ iss.message }}</li>
            </ul>
          </div>

          <div v-else class="placeholder">
            <span class="icon" aria-hidden="true">✂️</span>
            <p>Configure the contour and generate a toolpath</p>
          </div>
        </div>

        <!-- Validation errors shown inline -->
        <div v-if="validationErrors.length > 0 && !loading" class="validation-errors" role="alert">
          <p v-for="(err, i) in validationErrors" :key="i">{{ err }}</p>
        </div>

        <div class="action-buttons">
          <button
            class="btn btn-primary"
            @click="generateToolpath"
            :disabled="!canGenerate"
            :title="validationErrors.length > 0 ? validationErrors[0] : ''"
          >
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
.mode-note { font-size: 0.85rem; color: #60a5fa; margin: 0.75rem 0 0; padding: 0.75rem; background: #1e293b; border-radius: 0.5rem; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 320px 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.point-list { display: flex; flex-direction: column; gap: 0.4rem; }
.point-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 0.4rem; align-items: center; }
.point-row input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; font-size: 0.875rem; }
.mini-btn { padding: 0.4rem 0.6rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #aaa; cursor: pointer; font-size: 0.875rem; min-width: 2rem; }
.mini-btn:hover:not(:disabled) { background: #3a2626; border-color: #774444; color: #e5a5a5; }
.mini-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.add-btn { margin-top: 0.5rem; padding: 0.5rem 0.75rem; background: #262626; border: 1px dashed #444; border-radius: 0.375rem; color: #60a5fa; cursor: pointer; font-size: 0.875rem; }
.add-btn:hover { background: #1e3a5f; }

.gated-affordance { margin-top: 1rem; padding: 0.75rem; background: #161616; border: 1px dashed #333; border-radius: 0.5rem; }
.gated-label { font-size: 0.875rem; color: #888; }
.gated-note { font-size: 0.75rem; color: #666; margin: 0.4rem 0 0; }

.seg-buttons { display: flex; gap: 0.5rem; }
.seg-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; font-size: 0.875rem; min-height: 2.5rem; }
.seg-buttons button.active { background: #2563eb; border-color: #2563eb; }
.seg-buttons button.disabled { opacity: 0.5; cursor: not-allowed; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.checkbox-group label { display: flex; align-items: center; gap: 0.4rem; color: #e5e5e5; cursor: pointer; }
.form-group input[type="number"] { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; font-size: 0.875rem; }
.form-group input:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { font-size: 0.75rem; color: #60a5fa; margin-left: 0.25rem; }

.soon-tag { display: inline-block; margin-left: 0.4rem; font-size: 0.625rem; text-transform: uppercase; letter-spacing: 0.04em; background: #3a3a1a; color: #d4c468; padding: 0.125rem 0.375rem; border-radius: 0.25rem; }

.preview-container { min-height: 200px; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; padding: 1rem; overflow: auto; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }

.state-block { text-align: center; }
.state-block .icon { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; }
.state-title { font-weight: 600; margin: 0 0 0.4rem; }
.state-msg { font-size: 0.875rem; color: #bbb; margin: 0; }
.state-block.ok .state-title { color: #4ade80; }
.state-block.blocked .state-title { color: #f87171; }
.state-block.error .state-title { color: #fbbf24; }
.issue-list { text-align: left; margin: 0.6rem 0 0; padding-left: 1.1rem; font-size: 0.8rem; color: #f8a5a5; }
.issue-list.soft { color: #d4c468; }
.risk { font-size: 0.8rem; color: #888; margin: 0.4rem 0 0; }

.validation-errors { margin-bottom: 1rem; padding: 0.75rem; background: #2d1f1f; border: 1px solid #5c3a3a; border-radius: 0.5rem; }
.validation-errors p { margin: 0 0 0.25rem; font-size: 0.8rem; color: #f8a5a5; }
.validation-errors p:last-child { margin-bottom: 0; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; min-height: 2.75rem; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; cursor: not-allowed; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
@media (max-width: 600px) {
  .form-row { grid-template-columns: 1fr; }
  .seg-buttons { flex-direction: column; }
}
</style>
