<script setup lang="ts">
/**
 * DrillingView - Drilling Operations Toolpath Generator
 * Generate drilling toolpaths for holes and peck drilling.
 *
 * Wired to the CamIntentV1 Drilling lane (Dev Order 8I):
 *   POST /api/cam/drilling/intent-gcode
 *
 * Tapping is not yet supported by the backend (DrillingDesignV1 models only
 * peck_drilling: bool); its UI control is disabled with a "coming soon" note
 * rather than faking a path the engine cannot serve.
 */
import { ref, computed } from 'vue'
import {
  generateDrillingGcode,
  DrillingIntentError,
  type DrillingIntentRequest,
  type DrillingIntentResponse,
} from '../../api/drilling'

const drillType = ref<'standard' | 'peck'>('standard')
const holeDiameter = ref(6.0)
const holeDepth = ref(10)
const peckDepth = ref(3)
const retractHeight = ref(2)
const feedRate = ref(300)
const spindleSpeed = ref(3000)

// Hole positions
const holes = ref([
  { x: 50, y: 50 },
  { x: 100, y: 50 },
  { x: 150, y: 50 },
])

const loading = ref(false)
const result = ref<DrillingIntentResponse | null>(null)
// A feasibility block (409) — surfaced reason + the report, not a thrown-away error.
const blocked = ref<{ message: string; issues: string[]; riskLevel?: string } | null>(null)
// A validation/generation error (422/400) or transport failure.
const errorMsg = ref<string | null>(null)

const hasGcode = computed(() => !!result.value?.gcode)

function addHole() {
  holes.value.push({ x: 0, y: 0 })
}

function removeHole(index: number) {
  holes.value.splice(index, 1)
}

function buildRequest(): DrillingIntentRequest {
  return {
    mode: 'router_3axis',
    units: 'mm',
    tool_id: 'drill:intent',
    design: {
      holes: holes.value.map(h => ({ x: h.x, y: h.y })),
      hole_depth_mm: holeDepth.value,
      hole_diameter_mm: holeDiameter.value,
      peck_drilling: drillType.value === 'peck',
      peck_depth_mm: peckDepth.value,
    },
    context: {
      feed_rate_mm_min: feedRate.value,
      spindle_rpm: spindleSpeed.value,
      retract_height_mm: retractHeight.value,
    },
  }
}

async function generateToolpath() {
  loading.value = true
  result.value = null
  blocked.value = null
  errorMsg.value = null
  try {
    result.value = await generateDrillingGcode(buildRequest())
  } catch (e) {
    if (e instanceof DrillingIntentError && e.status === 409) {
      // Feasibility block — the real backend said no. Surface why.
      const feas = e.feasibility || {}
      blocked.value = {
        message: e.message,
        issues: Array.isArray(feas.issues) ? feas.issues : [],
        riskLevel: feas.risk_level,
      }
    } else if (e instanceof DrillingIntentError) {
      // 422 (bad input) / 400 (generation failure).
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
  a.download = `drilling_${result.value.run_id || 'toolpath'}.nc`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="drilling-view">
    <div class="header">
      <h1>Drilling Operations</h1>
      <p class="subtitle">Generate drilling, peck drilling, and tapping toolpaths</p>
    </div>

    <div class="content">
      <div class="panel params-panel">
        <h3>Drill Type</h3>
        <div class="type-buttons">
          <button :class="{ active: drillType === 'standard' }" @click="drillType = 'standard'">Standard</button>
          <button :class="{ active: drillType === 'peck' }" @click="drillType = 'peck'">Peck Drill</button>
          <button class="disabled" disabled title="Tapping is not yet supported by the toolpath engine">
            Tapping
            <span class="soon-tag">coming soon</span>
          </button>
        </div>

        <h3>Hole Parameters</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Hole Diameter (mm)</label>
            <input type="number" v-model.number="holeDiameter" step="0.5" />
          </div>
          <div class="form-group">
            <label>Hole Depth (mm)</label>
            <input type="number" v-model.number="holeDepth" step="0.5" />
          </div>
        </div>
        <div v-if="drillType === 'peck'" class="form-group">
          <label>Peck Depth (mm)</label>
          <input type="number" v-model.number="peckDepth" step="0.5" />
        </div>

        <h3>Feeds & Speeds</h3>
        <div class="form-row">
          <div class="form-group">
            <label>Feed Rate (mm/min)</label>
            <input type="number" v-model.number="feedRate" step="50" />
          </div>
          <div class="form-group">
            <label>Spindle (RPM)</label>
            <input type="number" v-model.number="spindleSpeed" step="500" />
          </div>
        </div>
      </div>

      <div class="panel holes-panel">
        <h3>Hole Positions</h3>
        <div class="holes-list">
          <div v-for="(hole, index) in holes" :key="index" class="hole-row">
            <span class="hole-num">#{{ index + 1 }}</span>
            <input type="number" v-model.number="hole.x" placeholder="X" />
            <input type="number" v-model.number="hole.y" placeholder="Y" />
            <button class="remove-btn" @click="removeHole(index)">×</button>
          </div>
        </div>
        <button class="add-btn" @click="addHole">+ Add Hole</button>
        <p class="hole-count">{{ holes.length }} holes</p>
      </div>

      <div class="panel preview-panel">
        <h3>Preview</h3>
        <div class="preview-container">
          <div v-if="loading" class="loading">Generating...</div>

          <!-- 409: real feasibility block from the backend -->
          <div v-else-if="blocked" class="blocked">
            <span class="icon">⛔</span>
            <p class="blocked-title">Blocked by feasibility check</p>
            <p class="detail">{{ blocked.message }}</p>
            <ul v-if="blocked.issues.length" class="issue-list">
              <li v-for="(issue, i) in blocked.issues" :key="i">{{ issue }}</li>
            </ul>
            <p v-if="blocked.riskLevel" class="detail">Risk: {{ blocked.riskLevel }}</p>
          </div>

          <!-- 422 / 400 / transport error -->
          <div v-else-if="errorMsg" class="error">
            <span class="icon">⚠️</span>
            <p class="detail">{{ errorMsg }}</p>
          </div>

          <!-- 200: real generated toolpath -->
          <div v-else-if="result" class="generated">
            <span class="icon">✅</span>
            <p>{{ result.metadata.hole_count }} holes · {{ result.metadata.total_depth_mm }}mm total</p>
            <p class="detail">~{{ Math.round(result.metadata.estimated_time_seconds) }}s · risk {{ result.metadata.risk_level }}</p>
            <ul v-if="result.issues.length" class="issue-list warn">
              <li v-for="(issue, i) in result.issues" :key="i">{{ issue.code }}: {{ issue.message }}</li>
            </ul>
          </div>

          <div v-else class="placeholder">
            <span class="icon">🔩</span>
            <p>{{ holes.length }} × Ø{{ holeDiameter }}mm holes</p>
            <p class="detail">Depth: {{ holeDepth }}mm</p>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn btn-primary" @click="generateToolpath" :disabled="loading">
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
.drilling-view { min-height: 100vh; background: #0a0a0a; color: #e5e5e5; padding: 2rem; }
.header { max-width: 1400px; margin: 0 auto 2rem; }
.header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; }
.subtitle { color: #888; margin: 0; }

.content { max-width: 1400px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; }
.panel { background: #1a1a1a; border-radius: 0.75rem; padding: 1.5rem; }
.panel h3 { font-size: 0.875rem; font-weight: 600; color: #888; text-transform: uppercase; margin: 0 0 1rem; }
.panel h3:not(:first-child) { margin-top: 1.5rem; }

.type-buttons { display: flex; gap: 0.5rem; }
.type-buttons button { flex: 1; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; cursor: pointer; }
.type-buttons button.active { background: #2563eb; border-color: #2563eb; }
.type-buttons button.disabled, .type-buttons button:disabled { opacity: 0.5; cursor: not-allowed; display: flex; flex-direction: column; gap: 0.125rem; align-items: center; }
.soon-tag { font-size: 0.625rem; color: #888; text-transform: uppercase; letter-spacing: 0.03em; }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.875rem; color: #888; margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; background: #262626; border: 1px solid #333; border-radius: 0.375rem; color: #e5e5e5; }

.holes-list { max-height: 250px; overflow-y: auto; }
.hole-row { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }
.hole-num { width: 2rem; font-size: 0.75rem; color: #888; }
.hole-row input { flex: 1; padding: 0.375rem; background: #262626; border: 1px solid #333; border-radius: 0.25rem; color: #e5e5e5; font-size: 0.875rem; }
.remove-btn { background: none; border: none; color: #666; cursor: pointer; font-size: 1rem; }
.add-btn { width: 100%; padding: 0.5rem; background: #262626; border: 1px dashed #444; border-radius: 0.375rem; color: #888; cursor: pointer; margin-top: 0.5rem; }
.hole-count { font-size: 0.75rem; color: #60a5fa; margin-top: 0.5rem; }

.preview-container { aspect-ratio: 1; background: #0d0d0d; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.placeholder { text-align: center; color: #666; }
.placeholder .icon, .blocked .icon, .error .icon, .generated .icon { font-size: 3rem; display: block; margin-bottom: 0.5rem; }
.detail { font-size: 0.75rem; color: #888; }

.blocked, .error, .generated { text-align: center; padding: 0.5rem; }
.blocked { color: #f87171; }
.error { color: #fbbf24; }
.generated { color: #4ade80; }
.blocked-title { font-weight: 600; margin: 0 0 0.25rem; }
.issue-list { list-style: none; padding: 0; margin: 0.5rem 0 0; font-size: 0.7rem; text-align: left; max-height: 120px; overflow-y: auto; }
.issue-list li { padding: 0.125rem 0; color: #f87171; }
.issue-list.warn li { color: #fbbf24; }

.action-buttons { display: flex; gap: 0.75rem; }
.btn { flex: 1; padding: 0.75rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #2563eb; color: #fff; }
.btn-primary:disabled { background: #333; color: #666; }
.btn-secondary { background: #262626; color: #e5e5e5; border: 1px solid #333; }

@media (max-width: 1200px) { .content { grid-template-columns: 1fr; } }
</style>
