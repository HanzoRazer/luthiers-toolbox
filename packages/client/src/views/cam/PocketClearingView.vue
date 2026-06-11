<script setup lang="ts">
/**
 * PocketClearingView - Adaptive Pocket-Clearing Toolpath Generator
 *
 * Wired to the CamIntentV1 Pocketing lane (Dev Order 8J):
 *   POST /api/cam/pocketing/intent-gcode
 *
 * Geometry is entered EXPLICITLY (boundary polygon + optional islands), mirroring
 * how DrillingView (8I) enters holes — the intent endpoint takes an explicit
 * boundary, not a DXF/SVG file. Four UI affordances the backend cannot serve from
 * this lane are honestly gated rather than faked (the pocketing analogs of
 * drilling's "tapping coming soon"):
 *   - DXF/SVG upload      -> not consumed by the intent lane (explicit entry instead)
 *   - Adaptive / Offset   -> the adapter serves only strategy in {Spiral, Lanes}
 *   - Spindle speed        -> pocketing context has no spindle field (engine fixes S18000)
 *   - Stepover            -> clamped to the engine's 30-70% range (not 10-90%)
 */
import { ref, computed } from 'vue'
import {
  generatePocketingGcode,
  PocketingIntentError,
  type PocketingIntentRequest,
  type PocketingIntentResponse,
  type PocketPointV1,
} from '../../api/pocketing'

// ---- Geometry (the "what") — explicit entry, like DrillingView's holes[] ----
// Default: a 100 x 60 mm rectangular pocket.
const boundary = ref<PocketPointV1[]>([
  { x: 0, y: 0 },
  { x: 100, y: 0 },
  { x: 100, y: 60 },
  { x: 0, y: 60 },
])
const islands = ref<PocketPointV1[][]>([])

// ---- Strategy (the L.1 path pattern) — only Spiral / Lanes are served ----
const strategies = [
  { id: 'Spiral', name: 'Spiral', description: 'Inside-out spiral pattern', served: true },
  { id: 'Lanes', name: 'Lanes (Zigzag)', description: 'Parallel passes', served: true },
  { id: 'adaptive', name: 'Adaptive', description: 'Engine-managed load (not yet selectable)', served: false },
  { id: 'offset', name: 'Offset', description: 'Contour offset (not yet selectable)', served: false },
] as const
const selectedStrategy = ref<'Spiral' | 'Lanes'>('Spiral')

// ---- Design scalars ----
const toolDiameter = ref(6.0)   // mm  (backend 0.5-50)
const pocketDepth = ref(10)     // mm  (backend 0-200)
const stepover = ref(50)        // %   (backend 30-70 — clamped in the control)
const roughingOnly = ref(false)
const finishAllowance = ref(0.3) // mm  (backend 0-5)

// ---- Context (the "how") ----
const stepdown = ref(3.0)       // mm
const feedRate = ref(1500)      // mm/min
const plungeRate = ref(500)     // mm/min
const safeHeight = ref(5)       // mm
const spindleSpeed = ref(18000) // rpm — informational only (engine fixes 18000)

// ---- State ----
const loading = ref(false)
const result = ref<PocketingIntentResponse | null>(null)
// A feasibility block (409) — surfaced reason + report, not a thrown-away error.
const blocked = ref<{ message: string; issues: string[]; riskLevel?: string } | null>(null)
// A validation/generation/dependency error (422/400/503) or transport failure.
const errorMsg = ref<string | null>(null)

const effectiveStepover = computed(() => (stepover.value / 100) * toolDiameter.value)
const hasGcode = computed(() => !!result.value?.gcode)

// ---- Boundary / island editing ----
function addBoundaryPoint() {
  boundary.value.push({ x: 0, y: 0 })
}
function removeBoundaryPoint(i: number) {
  if (boundary.value.length > 3) boundary.value.splice(i, 1)
}
function addIsland() {
  // Default: a small 20 x 20 mm square island near the pocket centre.
  islands.value.push([
    { x: 40, y: 20 },
    { x: 60, y: 20 },
    { x: 60, y: 40 },
    { x: 40, y: 40 },
  ])
}
function removeIsland(i: number) {
  islands.value.splice(i, 1)
}
function addIslandPoint(islIdx: number) {
  islands.value[islIdx].push({ x: 0, y: 0 })
}
function removeIslandPoint(islIdx: number, ptIdx: number) {
  if (islands.value[islIdx].length > 3) islands.value[islIdx].splice(ptIdx, 1)
}

function buildRequest(): PocketingIntentRequest {
  return {
    mode: 'router_3axis',
    units: 'mm',
    tool_id: 'pocketing:intent',
    design: {
      boundary: boundary.value.map(p => ({ x: p.x, y: p.y })),
      islands: islands.value.map(isl => ({ boundary: isl.map(p => ({ x: p.x, y: p.y })) })),
      pocket_depth_mm: pocketDepth.value,
      tool_diameter_mm: toolDiameter.value,
      stepover_percent: stepover.value,
      roughing_only: roughingOnly.value,
      finish_pass: !roughingOnly.value,
      finish_allowance_mm: finishAllowance.value,
    },
    context: {
      strategy: selectedStrategy.value,
      stepdown_mm: stepdown.value,
      feed_rate_mm_min: feedRate.value,
      plunge_rate_mm_min: plungeRate.value,
      safe_z_mm: safeHeight.value,
    },
  }
}

async function generateToolpath() {
  loading.value = true
  result.value = null
  blocked.value = null
  errorMsg.value = null
  try {
    result.value = await generatePocketingGcode(buildRequest())
  } catch (e) {
    if (e instanceof PocketingIntentError && e.status === 409) {
      // Feasibility block — the real backend said no. Surface why; do not fake through.
      const feas = e.feasibility || {}
      blocked.value = {
        message: e.message,
        issues: Array.isArray(feas.issues) ? feas.issues : [],
        riskLevel: feas.risk_level,
      }
    } else if (e instanceof PocketingIntentError) {
      // 422 (bad input) / 400 (generation failure) / 503 (dependency unavailable).
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
  a.download = `pocketing_${result.value.run_id || 'toolpath'}.nc`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="pocket-clearing-view">
    <div class="header">
      <h1>Pocket Clearing</h1>
      <p class="subtitle">Adaptive pocket-clearing toolpaths (L.1 core) with RMOS feasibility</p>
    </div>

    <div class="content">
      <!-- Geometry + strategy panel -->
      <div class="panel geometry-panel">
        <h3>Pocket Boundary (mm)</h3>
        <div class="point-list">
          <div v-for="(p, i) in boundary" :key="`b-${i}`" class="point-row">
            <input type="number" v-model.number="p.x" step="1" aria-label="boundary x" />
            <input type="number" v-model.number="p.y" step="1" aria-label="boundary y" />
            <button class="mini-btn" @click="removeBoundaryPoint(i)" :disabled="boundary.length <= 3">✕</button>
          </div>
        </div>
        <button class="add-btn" @click="addBoundaryPoint">+ Add point</button>

        <h3>Islands (no-cut regions)</h3>
        <div v-for="(isl, islIdx) in islands" :key="`isl-${islIdx}`" class="island-block">
          <div class="island-head">
            <span>Island {{ islIdx + 1 }}</span>
            <button class="mini-btn" @click="removeIsland(islIdx)">Remove island</button>
          </div>
          <div class="point-list">
            <div v-for="(p, ptIdx) in isl" :key="`isl-${islIdx}-${ptIdx}`" class="point-row">
              <input type="number" v-model.number="p.x" step="1" aria-label="island x" />
              <input type="number" v-model.number="p.y" step="1" aria-label="island y" />
              <button class="mini-btn" @click="removeIslandPoint(islIdx, ptIdx)" :disabled="isl.length <= 3">✕</button>
            </div>
          </div>
          <button class="add-btn" @click="addIslandPoint(islIdx)">+ Add point</button>
        </div>
        <button class="add-btn" @click="addIsland">+ Add island</button>

        <!-- Honest gate: the intent lane does not consume a DXF/SVG file -->
        <div class="gated-affordance">
          <span class="gated-label">DXF / SVG import</span>
          <span class="soon-tag">coming soon</span>
          <p class="gated-note">This lane takes an explicit boundary; file-derived boundaries are not yet wired.</p>
        </div>

        <h3>Strategy</h3>
        <div class="strategy-list">
          <button
            v-for="s in strategies"
            :key="s.id"
            class="strategy-btn"
            :class="{ active: selectedStrategy === s.id, disabled: !s.served }"
            :disabled="!s.served"
            :title="s.served ? '' : 'Not yet served by the toolpath engine'"
            @click="s.served && (selectedStrategy = s.id as 'Spiral' | 'Lanes')"
          >
            <span class="strategy-name">
              {{ s.name }}<span v-if="!s.served" class="soon-tag">coming soon</span>
            </span>
            <span class="strategy-desc">{{ s.description }}</span>
          </button>
        </div>
      </div>

      <!-- Parameters panel -->
      <div class="panel params-panel">
        <h3>Tool &amp; Pocket</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Tool Diameter (mm)</label>
            <input type="number" v-model.number="toolDiameter" step="0.1" min="0.5" max="50" />
          </div>
          <div class="form-group">
            <label>Stepover (%)</label>
            <input type="number" v-model.number="stepover" step="5" min="30" max="70" />
            <span class="hint">{{ effectiveStepover.toFixed(2) }}mm · engine range 30–70%</span>
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Stepdown (mm)</label>
            <input type="number" v-model.number="stepdown" step="0.5" min="0.1" max="20" />
          </div>
          <div class="form-group">
            <label>Pocket Depth (mm)</label>
            <input type="number" v-model.number="pocketDepth" step="0.5" min="0.5" max="200" />
          </div>
        </div>

        <h3>Finishing</h3>
        <div class="form-row">
          <div class="form-group checkbox-group">
            <label><input type="checkbox" v-model="roughingOnly" /> Roughing only (skip finish pass)</label>
          </div>
          <div class="form-group">
            <label>Finish Allowance (mm)</label>
            <input type="number" v-model.number="finishAllowance" step="0.1" min="0" max="5" :disabled="roughingOnly" />
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
            <input type="number" v-model.number="spindleSpeed" disabled title="Engine runs a fixed 18000 RPM" />
            <span class="hint">fixed at 18000 — not yet configurable</span>
          </div>
        </div>
      </div>

      <!-- Result panel -->
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
              Area {{ result.metadata.pocket_area_mm2.toFixed(0) }}mm² ·
              {{ result.metadata.island_count }} island(s) ·
              ~{{ (result.metadata.estimated_time_seconds / 60).toFixed(1) }} min
            </p>
            <ul v-if="result.issues.length" class="issue-list soft">
              <li v-for="(iss, i) in result.issues" :key="i">{{ iss.code }}: {{ iss.message }}</li>
            </ul>
          </div>

          <div v-else class="placeholder">
            <span class="icon">⚙️</span>
            <p>Configure the pocket and generate a toolpath</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="loading || boundary.length < 3">
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
.pocket-clearing-view {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e5e5e5;
  padding: 2rem;
}

.header {
  max-width: 1400px;
  margin: 0 auto 2rem;
}

.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 320px 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #1a1a1a;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.panel h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem;
}

.panel h3:not(:first-child) { margin-top: 1.5rem; }

.point-list { display: flex; flex-direction: column; gap: 0.4rem; }
.point-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 0.4rem; align-items: center; }
.point-row input {
  width: 100%;
  padding: 0.4rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #e5e5e5;
  font-size: 0.85rem;
}
.mini-btn {
  padding: 0.3rem 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #aaa;
  cursor: pointer;
  font-size: 0.75rem;
}
.mini-btn:hover:not(:disabled) { background: #3a2626; border-color: #774444; color: #e5a5a5; }
.mini-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.add-btn {
  margin-top: 0.5rem;
  padding: 0.4rem 0.75rem;
  background: #262626;
  border: 1px dashed #444;
  border-radius: 0.375rem;
  color: #60a5fa;
  cursor: pointer;
  font-size: 0.8rem;
}
.add-btn:hover { background: #1e3a5f; }

.island-block {
  margin-bottom: 0.75rem;
  padding: 0.6rem;
  background: #151515;
  border: 1px solid #2a2a2a;
  border-radius: 0.5rem;
}
.island-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.8rem; color: #aaa; }

.gated-affordance {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #161616;
  border: 1px dashed #333;
  border-radius: 0.5rem;
}
.gated-label { font-size: 0.85rem; color: #888; }
.gated-note { font-size: 0.72rem; color: #666; margin: 0.4rem 0 0; }

.strategy-list { display: flex; flex-direction: column; gap: 0.5rem; }
.strategy-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0.75rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.5rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.strategy-btn:hover:not(.disabled) { background: #333; border-color: #444; }
.strategy-btn.active { background: #1e3a5f; border-color: #60a5fa; }
.strategy-btn.disabled { opacity: 0.5; cursor: not-allowed; }
.strategy-name { font-weight: 500; color: #e5e5e5; display: flex; align-items: center; gap: 0.4rem; }
.strategy-desc { font-size: 0.75rem; color: #888; }

.soon-tag {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #3a3a1a;
  color: #d4c468;
  padding: 0.1rem 0.35rem;
  border-radius: 0.25rem;
}

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.checkbox-group label { display: flex; align-items: center; gap: 0.4rem; color: #e5e5e5; }
.form-group input[type="number"] {
  width: 100%;
  padding: 0.5rem;
  background: #262626;
  border: 1px solid #333;
  border-radius: 0.375rem;
  color: #e5e5e5;
  font-size: 0.875rem;
}
.form-group input:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { font-size: 0.72rem; color: #60a5fa; }

.preview-container {
  aspect-ratio: 4/3;
  background: #0d0d0d;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  padding: 1rem;
  overflow: auto;
}
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
