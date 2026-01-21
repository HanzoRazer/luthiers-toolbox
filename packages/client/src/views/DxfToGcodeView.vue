<template>
  <div class="dxf-to-gcode">
    <h1>DXF → G-code (GRBL)</h1>
    <p class="subtitle">
      Shop-floor quick path: upload DXF, set params, download G-code
    </p>

    <!-- Upload Zone -->
    <div
      class="upload-zone"
      :class="{ 'drag-over': isDragOver, 'has-file': !!dxfFile }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".dxf"
        style="display: none"
        @change="handleFileSelect"
      >

      <div
        v-if="!dxfFile"
        class="upload-prompt"
      >
        <p>
          <strong>Drop DXF here</strong> or <button
            class="link-btn"
            @click="($refs.fileInput as HTMLInputElement).click()"
          >
            browse
          </button>
        </p>
        <p class="hint">
          DXF R12/R2000 format
        </p>
      </div>

      <div
        v-else
        class="file-info"
      >
        <span class="filename">{{ dxfFile.name }}</span>
        <span class="filesize">({{ (dxfFile.size / 1024).toFixed(1) }} KB)</span>
        <button
          class="clear-btn"
          @click="clearFile"
        >
          ×
        </button>
      </div>
    </div>

    <!-- CAM Parameters -->
    <div
      class="params-section"
      :class="{ disabled: isGenerating }"
    >
      <h2>CAM Parameters</h2>
      <div class="params-grid">
        <div class="param">
          <label>Tool Diameter (mm)</label>
          <input
            v-model.number="params.tool_d"
            type="number"
            step="0.5"
            min="0.5"
            max="25"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Stepover (0-1)</label>
          <input
            v-model.number="params.stepover"
            type="number"
            step="0.05"
            min="0.1"
            max="0.9"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Stepdown (mm)</label>
          <input
            v-model.number="params.stepdown"
            type="number"
            step="0.5"
            min="0.5"
            max="10"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Target Depth (mm)</label>
          <input
            v-model.number="params.z_rough"
            type="number"
            step="0.5"
            max="0"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Feed XY (mm/min)</label>
          <input
            v-model.number="params.feed_xy"
            type="number"
            step="100"
            min="100"
            max="5000"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Feed Z (mm/min)</label>
          <input
            v-model.number="params.feed_z"
            type="number"
            step="50"
            min="50"
            max="1000"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Safe Z (mm)</label>
          <input
            v-model.number="params.safe_z"
            type="number"
            step="1"
            min="1"
            max="50"
            :disabled="isGenerating"
          >
        </div>
        <div class="param">
          <label>Layer Name</label>
          <input
            v-model="params.layer_name"
            type="text"
            :disabled="isGenerating"
          >
        </div>
      </div>
    </div>

    <!-- Generate Button -->
    <div class="action-section">
      <button
        :disabled="!dxfFile || isGenerating"
        class="btn-generate"
        @click="generateGcode"
      >
        {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
      </button>
      <p class="generate-hint">
        Uses GRBL profile � Units: mm � Output: .nc
      </p>
    </div>

    <!-- Result -->
    <div
      v-if="result"
      class="result-section"
    >
      <!-- Results Header: Title+Badge -> Run ID/Copy/View/Why? -> Override -> Warnings -> WhyPanel -->
      <div class="results-header">
        <div class="results-title">
          <h2>Result</h2>
          <RiskBadge
            v-if="result.decision?.risk_level"
            :risk-level="result.decision.risk_level"
          />
        </div>

        <div class="result-meta">
          <span class="run-id">Run: {{ result.run_id }}</span>
          <button
            class="copy-btn"
            title="Copy Run ID"
            @click="copyRunId"
          >
            Copy
          </button>
          <button
            v-if="canViewRun"
            class="btn-link"
            title="Open canonical RMOS run record"
            @click="viewRunNewTab"
          >
            View Run <span
              class="ext"
              aria-hidden="true"
            >↗</span>
          </button>
          <span
            v-if="!result.rmos_persisted"
            class="not-persisted"
          >RMOS not persisted</span>
          <button
            v-if="hasExplainability"
            class="btn-link"
            :aria-expanded="showWhy"
            title="Show why this decision happened"
            @click="showWhy = !showWhy"
          >
            Why?
          </button>
        </div>
      </div>

      <!-- Always-visible override banner (if any) -->
      <OverrideBanner
        v-if="result?.override_reason || result?.explanation?.override_reason || result?.decision?.details?.override_reason"
        :reason="result?.override_reason || result?.explanation?.override_reason || result?.decision?.details?.override_reason"
      />

      <div
        v-if="result.decision?.warnings?.length"
        class="warnings"
      >
        <strong>Warnings:</strong>
        <ul>
          <li
            v-for="(w, i) in result.decision.warnings"
            :key="i"
          >
            {{ w }}
          </li>
        </ul>
      </div>

      <!-- Explainability: auto-opens for YELLOW/RED; toggleable via header Why? button -->
      <WhyPanel
        v-if="hasExplainability && showWhy"
        :rules-triggered="triggeredRuleIds"
        :risk-level="riskLevel"
        :show-override-hint="riskLevel === 'YELLOW' && !hasOverrideAttachment"
        :has-override="hasOverrideAttachment"
        class="mt-3"
      />

      <!-- Run-to-run compare (minimal operator UI) -->
      <div
        v-if="hasCompare || compareError"
        class="compare-shell"
      >
        <div class="compare-header-row">
          <h3>Compare with Previous Run</h3>
          <div class="muted">
            {{ previousRunId?.slice(0, 8) }}… → {{ result?.run_id?.slice(0, 8) }}…
          </div>
          <button
            class="btn-clear"
            @click="clearCompare"
          >
            Clear
          </button>
        </div>

        <div
          v-if="compareError"
          class="compare-error"
        >
          {{ compareError }}
        </div>

        <div
          v-else
          class="compare-content"
        >
          <!-- Summary chips -->
          <div
            v-if="compareSummary"
            class="pill-row"
          >
            <template
              v-for="(v, k) in compareSummary"
              :key="k"
            >
              <span
                v-if="v"
                class="pill ok"
              >{{ pillLabel(String(k)) }}</span>
            </template>
            <span
              v-if="Object.values(compareSummary).every((x: any) => !x)"
              class="pill muted"
            >
              No changes detected
            </span>
          </div>

          <!-- Decision -->
          <div
            v-if="compareDecision"
            class="compare-section"
          >
            <div class="section-title">
              Decision
            </div>
            <div class="kv-row">
              <div class="kv-label">
                Risk
              </div>
              <div class="kv-value">
                <span class="pill">{{ compareDecision.before?.risk_level }}</span>
                <span class="arrow">→</span>
                <span class="pill">{{ compareDecision.after?.risk_level }}</span>
              </div>
            </div>
            <div
              v-if="compareDecision.before?.block_reason || compareDecision.after?.block_reason"
              class="kv-row"
            >
              <div class="kv-label">
                Block reason
              </div>
              <div class="kv-value muted">
                {{ compareDecision.before?.block_reason || '—' }}
                <span class="arrow">→</span>
                {{ compareDecision.after?.block_reason || '—' }}
              </div>
            </div>
          </div>

          <!-- Feasibility rules -->
          <div
            v-if="compareFeasibility"
            class="compare-section"
          >
            <div class="section-title">
              Feasibility rules
            </div>
            <div class="kv-row">
              <div class="kv-label">
                Added
              </div>
              <div class="kv-value">
                <span
                  v-if="(compareFeasibility.rules_added || []).length === 0"
                  class="muted"
                >—</span>
                <span
                  v-for="rid in (compareFeasibility.rules_added || [])"
                  :key="rid"
                  class="pill ok"
                >{{ rid }}</span>
              </div>
            </div>
            <div class="kv-row">
              <div class="kv-label">
                Removed
              </div>
              <div class="kv-value">
                <span
                  v-if="(compareFeasibility.rules_removed || []).length === 0"
                  class="muted"
                >—</span>
                <span
                  v-for="rid in (compareFeasibility.rules_removed || [])"
                  :key="rid"
                  class="pill"
                >{{ rid }}</span>
              </div>
            </div>
          </div>

          <!-- Parameter changes -->
          <div class="compare-section">
            <div class="section-title">
              Parameter changes
            </div>
            <div
              v-if="paramDiffRows.length === 0"
              class="muted"
            >
              No parameter changes detected.
            </div>
            <div
              v-else
              class="diff-grid"
            >
              <div class="diff-row diff-head">
                <div>Field</div><div>Previous</div><div>Current</div>
              </div>
              <div
                v-for="row in paramDiffRows"
                :key="row.key"
                class="diff-row"
              >
                <div class="k">
                  {{ row.key }}
                </div>
                <div class="vcell">
                  {{ row.a ?? '—' }}
                </div>
                <div class="vcell">
                  {{ row.b ?? '—' }}
                </div>
              </div>
            </div>
          </div>

          <!-- Deep diff toggle -->
          <button
            class="compare-toggle"
            @click="showDeepCompare = !showDeepCompare"
          >
            <span class="chev">{{ showDeepCompare ? '▾' : '▸' }}</span>
            <span>Show deep diffs</span>
            <span class="muted">(request/feasibility/decision/hashes/attachments)</span>
          </button>
          <pre
            v-if="showDeepCompare"
            class="code"
          >{{ JSON.stringify(compareResult, null, 2) }}</pre>
        </div>
      </div>

      <!-- Action row with risk badge + downloads -->
      <div class="action-row">
        <span
          class="action-risk-badge"
          :class="riskLevel.toLowerCase()"
          title="Decision from feasibility engine (RMOS)"
        >
          {{ riskLevel || 'N/A' }}
        </span>

        <button
          :disabled="!canDownload"
          class="btn-download"
          @click="downloadGcode"
        >
          Download G-code (.nc)
        </button>

        <button
          :disabled="!canDownloadOperatorPack"
          class="btn-operator-pack"
          title="Downloads input.dxf + plan.json + manifest.json + output.nc"
          @click="downloadOperatorPack"
        >
          Download Operator Pack (.zip)
        </button>

        <button
          :disabled="!canCompare"
          class="btn-compare"
          :title="previousRunId ? `Compare ${previousRunId} → ${result?.run_id}` : 'No previous run found yet'"
          @click="compareWithPreviousRun"
        >
          {{ isComparing ? 'Comparing…' : 'Compare w/ Previous' }}
        </button>
      </div>

      <button
        v-if="canViewRun"
        class="btn-view-run"
        title="Open canonical RMOS run record in a new tab"
        @click="viewRunNewTab"
      >
        View Run <span
          class="ext"
          aria-hidden="true"
        >↗</span>
      </button>

      <div
        v-if="result && !result.gcode?.inline"
        class="attachment-hint"
      >
        <p>G-code stored as RMOS attachment (too large for inline).</p>
        <p class="attachment-meta">
          Run ID: <code>{{ result.run_id }}</code>
          <span v-if="gcodeAttachment">
            · SHA: <code>{{ gcodeAttachment.sha256?.slice(0, 12) }}…</code>
            · {{ (gcodeAttachment.size_bytes / 1024).toFixed(1) }} KB
          </span>
        </p>
      </div>
    </div>

    <!-- Error -->
    <div
      v-if="error"
      class="error"
    >
      <strong>Error:</strong> {{ error }}
      <button
        class="clear-btn"
        @click="error = null"
      >
        ×
      </button>
    </div>

    <!-- Override Modal (YELLOW gate) -->
    <div
      v-if="showOverrideModal"
      class="modal-backdrop"
      @click.self="closeOverrideModal"
    >
      <div class="modal">
        <div class="modal-header">
          <h3>Override Required</h3>
          <button
            class="icon-btn"
            :disabled="isSubmittingOverride"
            @click="closeOverrideModal"
          >
            ×
          </button>
        </div>
        <p class="muted">
          This run is <strong>YELLOW</strong>. To download an operator pack, record an override reason for audit.
        </p>

        <label class="field">
          <div class="label">Reason (required)</div>
          <textarea
            v-model="overrideReason"
            rows="4"
            placeholder="Why is it safe to proceed?"
          />
        </label>

        <label class="field">
          <div class="label">Operator (optional)</div>
          <input
            v-model="overrideOperator"
            type="text"
            placeholder="Name / initials"
          >
        </label>

        <div
          v-if="overrideError"
          class="override-error"
        >
          {{ overrideError }}
        </div>

        <div class="modal-actions">
          <button
            class="btn-secondary"
            :disabled="isSubmittingOverride"
            @click="closeOverrideModal"
          >
            Cancel
          </button>
          <button
            class="btn-primary"
            :disabled="isSubmittingOverride"
            @click="submitOverrideAndRetryPack"
          >
            {{ isSubmittingOverride ? 'Submitting...' : 'Submit Override & Download' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { explainRule } from '@/lib/feasibilityRuleRegistry'
import { runs as rmosRuns } from '@/sdk/rmos'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import WhyPanel from '@/components/rmos/WhyPanel.vue'

const router = useRouter()

const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const dxfFile = ref<File | null>(null)
const isGenerating = ref(false)
const result = ref<any>(null)
const error = ref<string | null>(null)
const abortController = ref<AbortController | null>(null)
const previousRunId = ref<string | null>(null)
const isComparing = ref(false)
const compareError = ref<string | null>(null)
const compareResult = ref<any | null>(null)
const showDeepCompare = ref(false)
const showWhy = ref(false)

const params = ref({
  tool_d: 6.0,
  stepover: 0.45,
  stepdown: 1.5,
  z_rough: -3.0,
  feed_xy: 1200,
  feed_z: 300,
  rapid: 3000,
  safe_z: 5.0,
  strategy: 'Spiral',
  layer_name: 'GEOMETRY',
  climb: true,
  smoothing: 0.1,
  margin: 0.0
})

const canDownload = computed(() => result.value?.gcode?.inline && !!result.value?.gcode?.text)

const canCompare = computed(() => {
  const runId = String(result.value?.run_id || '').trim()
  return !!runId && !!previousRunId.value && !isGenerating.value && !isComparing.value
})

const canDownloadOperatorPack = computed(() => {
  const runId = (result.value?.run_id || '').trim()
  return !!runId && !isGenerating.value
})

const riskLevel = computed(() => String(result.value?.decision?.risk_level || '').toUpperCase())
const hasOverrideAttachment = computed(() => {
  const atts = result.value?.attachments || []
  return Array.isArray(atts) && atts.some((a: any) => a?.kind === 'override')
})

// Phase 3.3: Explainability - triggered rules
const triggeredRuleIds = computed<string[]>(() => {
  const ids = result.value?.feasibility?.rules_triggered
  if (!Array.isArray(ids)) return []
  return ids.map((x: any) => String(x).trim().toUpperCase()).filter(Boolean)
})

const triggeredRules = computed(() => {
  return triggeredRuleIds.value.map((rid) => explainRule(rid))
})

const hasExplainability = computed(() => triggeredRuleIds.value.length > 0)

// Auto-open Why on YELLOW/RED when explainability exists; close on GREEN/UNKNOWN
watch([riskLevel, hasExplainability], ([rl, hasExp]) => {
  if (!result.value) return
  if (!hasExp) return
  showWhy.value = rl === 'YELLOW' || rl === 'RED'
}, { immediate: true })

const canViewRun = computed(() => {
  const runId = String(result.value?.run_id || '').trim()
  return !!runId
})

function viewRunNewTab() {
  const runId = String(result.value?.run_id || '').trim()
  if (!runId) return
  const href = router.resolve(`/rmos/runs/${encodeURIComponent(runId)}`).href
  window.open(href, '_blank', 'noopener,noreferrer')
}

async function refreshPreviousRunId(currentRunId: string) {
  // Uses SDK helper. We only need the previous run in the same mode.
  try {
    previousRunId.value = null
    const { items } = await rmosRuns.listRuns({ limit: 20 })
    const list = Array.isArray(items) ? items : []
    // Prefer matching mode (if present in wrapper result, else just "previous by time")
    const mode = String(result.value?.mode || '').trim()

    let filtered = list
    if (mode) {
      filtered = list.filter((it: any) => String(it?.mode || '').trim() === mode)
    }

    // Find current run in list, then pick the next item after it (newest-first).
    const idx = filtered.findIndex((it: any) => String(it?.run_id || '').trim() === currentRunId)
    if (idx >= 0 && idx + 1 < filtered.length) {
      previousRunId.value = String(filtered[idx + 1]?.run_id || '').trim() || null
      return
    }

    // Fallback: take the first run that isn't current
    const alt = filtered.find((it: any) => String(it?.run_id || '').trim() && String(it?.run_id || '').trim() !== currentRunId)
    previousRunId.value = alt ? String(alt.run_id).trim() : null
  } catch {
    // Non-fatal
    previousRunId.value = null
  }
}

async function compareWithPreviousRun() {
  const runId = String(result.value?.run_id || '').trim()
  const prev = String(previousRunId.value || '').trim()
  if (!runId || !prev) return

  isComparing.value = true
  compareError.value = null
  compareResult.value = null
  showDeepCompare.value = false

  try {
    const diffResult = await rmosRuns.compareRuns(prev, runId)
    compareResult.value = diffResult
  } catch (e: any) {
    compareError.value = e?.message || 'Failed to compare runs.'
  } finally {
    isComparing.value = false
  }
}

function clearCompare() {
  compareResult.value = null
  compareError.value = null
  showDeepCompare.value = false
}

// ─── Compare Helpers (Minimal UI) ───────────────────────────────────────────
const hasCompare = computed(() => !!compareResult.value && !compareError.value)
const compareSummary = computed(() => compareResult.value?.summary ?? null)
const compareDecision = computed(() => compareResult.value?.decision_diff ?? null)
const compareFeasibility = computed(() => compareResult.value?.feasibility_diff ?? null)
const compareParamDiff = computed(() => compareResult.value?.param_diff ?? {})
const paramDiffRows = computed(() => {
  const obj = compareParamDiff.value || {}
  return Object.keys(obj).sort().map((k) => ({ key: k, a: obj[k]?.[0], b: obj[k]?.[1] }))
})

function pillLabel(k: string) {
  const map: Record<string, string> = {
    risk_changed: 'Risk changed',
    blocking_changed: 'Block reason changed',
    feasibility_changed: 'Feasibility changed',
    cam_changed: 'CAM changed',
    gcode_changed: 'G-code changed',
    attachments_changed: 'Attachments changed',
    override_changed: 'Override changed',
  }
  return map[k] ?? k
}

const explainSummary = computed(() => {
  const n = triggeredRuleIds.value.length
  if (!n) return null
  const rl = riskLevel.value || 'UNKNOWN'
  return `${n} feasibility rule(s) triggered → ${rl}`
})

// Override Modal state
const showOverrideModal = ref(false)
const overrideReason = ref('')
const overrideOperator = ref('')
const isSubmittingOverride = ref(false)
const overrideError = ref<string | null>(null)

function openOverrideModal() {
  overrideError.value = null
  overrideReason.value = ''
  overrideOperator.value = ''
  showOverrideModal.value = true
}

function closeOverrideModal() {
  if (isSubmittingOverride.value) return
  showOverrideModal.value = false
}

async function refreshRunCanonical(runId: string) {
  try {
    const run = await rmosRuns.getRun(runId)
    
    // Merge strategy: preserve wrapper envelope, patch in canonical fields
    result.value = {
      ...result.value,
      attachments: run.attachments ?? result.value?.attachments,
      hashes: run.hashes ?? result.value?.hashes,
      decision: run.decision ?? result.value?.decision,
      feasibility: run.feasibility ?? result.value?.feasibility,
      mode: run.mode ?? result.value?.mode,
    }
    await refreshPreviousRunId(runId)
  } catch {
    // Non-fatal: refresh failure doesn't block operator action
  }
}

async function onRunProduced(runId: string) {
  // Best-effort: refresh mode + previous run id
  await refreshPreviousRunId(runId)
}

async function submitOverrideAndRetryPack() {
  const runId = String(result.value?.run_id || '').trim()
  if (!runId) return

  const reason = overrideReason.value.trim()
  if (!reason) {
    overrideError.value = 'Please enter an override reason.'
    return
  }

  isSubmittingOverride.value = true
  overrideError.value = null
  try {
    await rmosRuns.addOverride(runId, {
      reason,
      operator: overrideOperator.value.trim() || undefined
    })

    // Canonical refresh from Runs v2 so attachments list is authoritative
    await refreshRunCanonical(runId)

    showOverrideModal.value = false
    await doDownloadOperatorPack() // retry download
  } catch (e: any) {
    overrideError.value = e?.message || 'Override failed.'
  } finally {
    isSubmittingOverride.value = false
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    setFile(target.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    setFile(event.dataTransfer.files[0])
  }
}

const setFile = (file: File) => {
  if (!file.name.toLowerCase().endsWith('.dxf')) {
    error.value = 'Please select a DXF file'
    return
  }
  // Abort any in-flight request
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  // Reset all state for new file
  dxfFile.value = file
  result.value = null
  error.value = null
  isGenerating.value = false
}

const clearFile = () => {
  dxfFile.value = null
  result.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const parseErrorResponse = async (response: Response): Promise<string> => {
  const status = response.status
  try {
    const data = await response.json()
    if (typeof data.detail === 'string') {
      return data.detail
    } else if (Array.isArray(data.detail)) {
      return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ')
    } else if (data.detail) {
      return JSON.stringify(data.detail)
    }
    return `HTTP ${status}`
  } catch {
    // JSON parse failed, try text
    try {
      const text = await response.text()
      return text || `HTTP ${status}`
    } catch {
      return `HTTP ${status}`
    }
  }
}

const generateGcode = async () => {
  if (!dxfFile.value) return

  // Abort any prior in-flight request
  if (abortController.value) {
    abortController.value.abort()
  }
  abortController.value = new AbortController()

  isGenerating.value = true
  error.value = null
  result.value = null

  try {
    const fd = new FormData()
    fd.append('file', dxfFile.value)

    for (const [k, v] of Object.entries(params.value)) {
      if (typeof v === 'boolean') {
        fd.append(k, v ? 'true' : 'false')
      } else {
        fd.append(k, String(v))
      }
    }

    const response = await fetch('/api/rmos/wrap/mvp/dxf-to-grbl', {
      method: 'POST',
      body: fd,
      signal: abortController.value.signal
    })

    if (!response.ok) {
      const errMsg = await parseErrorResponse(response)
      throw new Error(errMsg)
    }

    result.value = await response.json()
    await onRunProduced(String(result.value?.run_id || '').trim())

  } catch (err: any) {
    // Ignore abort errors (user changed file or re-submitted)
    if (err.name === 'AbortError') return
    error.value = err.message || 'Failed to generate G-code'
  } finally {
    isGenerating.value = false
    abortController.value = null
  }
}

const downloadGcode = () => {
  if (!canDownload.value) return

  const blob = new Blob([result.value.gcode.text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const baseName = (dxfFile.value?.name || 'output').replace(/\.dxf$/i, '')
  a.download = `${baseName}_GRBL.nc`
  a.click()
  URL.revokeObjectURL(url)
}

const copyRunId = async () => {
  if (!result.value?.run_id) return
  try {
    await navigator.clipboard.writeText(result.value.run_id)
  } catch {
    // Fallback for older browsers
    const input = document.createElement('input')
    input.value = result.value.run_id
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
  }
}

const gcodeAttachment = computed(() => {
  if (!result.value?.attachments) return null
  return result.value.attachments.find((a: any) => a.kind === 'gcode_output')
})

const downloadOperatorPack = async () => {
  const runId = (result.value?.run_id || '').trim()
  if (!runId) return

  // If YELLOW and no override, prompt modal
  if (riskLevel.value === 'YELLOW' && !hasOverrideAttachment.value) {
    openOverrideModal()
    return
  }

  await doDownloadOperatorPack()
}

const doDownloadOperatorPack = async () => {
  const runId = (result.value?.run_id || '').trim()
  if (!runId) return

  try {
    const { blob } = await rmosRuns.downloadOperatorPack(runId)
    
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `operator_pack_${runId}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
    // Check if 403 and YELLOW without override — open modal
    if (e?.status === 403 && riskLevel.value === 'YELLOW' && !hasOverrideAttachment.value) {
      openOverrideModal()
      return
    }
    error.value = String(e?.message || e)
  }
}
</script>

<style scoped>
.dxf-to-gcode {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 2rem;
}

.upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
  padding: 2rem;
  text-align: center;
  background: #f9fafb;
  transition: all 0.2s;
  margin-bottom: 2rem;
}

.upload-zone.drag-over {
  border-color: #3b82f6;
  background: #eff6ff;
}

.upload-zone.has-file {
  border-color: #10b981;
  background: #f0fdf4;
}

.upload-prompt p {
  margin: 0.5rem 0;
}

.link-btn {
  background: none;
  border: none;
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  font-size: inherit;
}

.hint {
  color: #9ca3af;
  font-size: 0.875rem;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.filename {
  font-weight: 600;
  color: #059669;
}

.filesize {
  color: #6b7280;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0 0.25rem;
}

.clear-btn:hover {
  color: #dc2626;
}

.params-section {
  margin-bottom: 2rem;
}

.params-section.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.params-section h2 {
  font-size: 1.125rem;
  margin-bottom: 1rem;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.param {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.param label {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 500;
}

.param input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
}

.param input:disabled {
  background: #f3f4f6;
  cursor: not-allowed;
}

.action-section {
  margin-bottom: 2rem;
}

.generate-hint {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #9ca3af;
}

.btn-generate {
  width: 100%;
  padding: 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-generate:hover:not(:disabled) {
  background: #2563eb;
}

.btn-generate:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.result-section {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

/* Risk Banner - prominent at top */
.risk-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.risk-banner.green {
  background: #d1fae5;
  border: 1px solid #10b981;
}

.risk-banner.yellow {
  background: #fef3c7;
  border: 1px solid #f59e0b;
}

.risk-banner.red {
  background: #fee2e2;
  border: 1px solid #ef4444;
}

.risk-label {
  font-weight: 700;
  font-size: 1rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.5);
}

.risk-banner.green .risk-label {
  color: #065f46;
}

.risk-banner.yellow .risk-label {
  color: #92400e;
}

.risk-banner.red .risk-label {
  color: #991b1b;
}

.risk-text {
  font-size: 0.875rem;
  color: #374151;
}

.results-header {
  margin-bottom: 1rem;
}

.results-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.results-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.mt-3 {
  margin-top: 0.75rem;
}

.run-id {
  font-family: monospace;
  font-size: 0.875rem;
  color: #6b7280;
}

.copy-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  color: #374151;
}

.copy-btn:hover {
  background: #d1d5db;
}

.view-run-link {
  font-size: 0.75rem;
  color: #3b82f6;
  text-decoration: none;
}

.view-run-link:hover {
  text-decoration: underline;
}

.not-persisted {
  color: #f59e0b;
  font-size: 0.875rem;
}

.warnings {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 0.375rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.warnings ul {
  margin: 0.5rem 0 0 1.25rem;
  padding: 0;
}

.warnings li {
  color: #92400e;
  font-size: 0.875rem;
}

.btn-download {
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-download:hover:not(:disabled) {
  background: #059669;
}

.btn-download:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-operator-pack {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  margin-left: 0.5rem;
}

.btn-operator-pack:hover:not(:disabled) {
  background: #2563eb;
}

.btn-operator-pack:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.attachment-hint {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 0.375rem;
  padding: 0.75rem;
  margin-top: 1rem;
}

.attachment-hint p {
  margin: 0;
  font-size: 0.875rem;
  color: #92400e;
}

.attachment-meta {
  margin-top: 0.5rem !important;
}

.attachment-meta code {
  background: #fde68a;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.error {
  background: #fee2e2;
  border: 1px solid #fca5a5;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #991b1b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Override Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 50;
}

.modal {
  width: 100%;
  max-width: 560px;
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.125rem;
}

.icon-btn {
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  color: #6b7280;
}

.icon-btn:hover {
  color: #374151;
}

.muted {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0 0 16px 0;
}

.field {
  display: block;
  margin-top: 12px;
}

.field .label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 6px;
  font-weight: 500;
}

.field textarea,
.field input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.field textarea:focus,
.field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.override-error {
  margin-top: 12px;
  color: #b91c1c;
  font-size: 0.875rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Phase 3.3: Explainability Card */
.explain-card {
  margin: 1rem 0;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #fff;
}

.explain-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.explain-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.explain-summary {
  font-size: 0.875rem;
  opacity: 0.75;
}

.explain-list {
  margin: 0.75rem 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.5rem;
}

.explain-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-wrap: wrap;
}

.rule-pill {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid #d1d5db;
}

.rule-pill[data-level="RED"] {
  color: #b91c1c;
  border-color: #fca5a5;
  background: #fef2f2;
}

.rule-pill[data-level="YELLOW"] {
  color: #92400e;
  border-color: #fcd34d;
  background: #fefce8;
}

.rule-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.75rem;
  opacity: 0.9;
}

.rule-summary {
  font-size: 0.875rem;
  opacity: 0.9;
}

.rule-hint {
  font-size: 0.75rem;
  opacity: 0.7;
  font-style: italic;
}

.explain-hint {
  margin-top: 0.75rem;
  font-size: 0.8125rem;
  opacity: 0.8;
}

.explain-hint-ok {
  color: #059669;
}

.btn-view-run {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  background: #e5e7eb;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  color: #374151;
  opacity: 0.9;
}

.btn-view-run:hover {
  background: #d1d5db;
}

.btn-link {
  padding: 0 4px;
  font-size: 13px;
  background: none;
  border: none;
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  opacity: 0.85;
}

.btn-link:hover {
  opacity: 1;
}

.ext {
  display: inline-block;
  margin-left: 4px;
  font-size: 12px;
  opacity: 0.8;
  transform: translateY(-1px);
}

/* Action row with risk badge + download buttons */
.action-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.action-risk-badge {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  cursor: help;
}

.action-risk-badge.green {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.action-risk-badge.yellow {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}

.action-risk-badge.red {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}

.btn-compare {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-compare:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-compare:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── Minimal Compare UI ──────────────────────────────────────────────────── */
.compare-shell {
  margin-top: 1.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 1rem;
  background: #fafafa;
  padding: 1rem;
}

.compare-header-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.compare-header-row h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.compare-content {
  margin-top: 0.75rem;
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.pill {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: #e5e7eb;
  font-size: 0.75rem;
  font-weight: 500;
}

.pill.ok {
  background: #d1fae5;
  color: #065f46;
}

.pill.muted {
  background: #f3f4f6;
  color: #9ca3af;
}

.compare-section {
  margin-top: 1rem;
}

.section-title {
  font-weight: 700;
  font-size: 0.8125rem;
  margin-bottom: 0.5rem;
}

.kv-row {
  display: grid;
  grid-template-columns: 8rem 1fr;
  gap: 0.75rem;
  margin: 0.375rem 0;
  align-items: start;
}

.kv-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.kv-value {
  font-size: 0.8125rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.arrow {
  color: #9ca3af;
}

.diff-grid {
  display: grid;
  gap: 0.5rem;
}

.diff-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.75rem;
  align-items: start;
}

.diff-head {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.vcell {
  font-size: 0.75rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 0.5rem;
  word-break: break-word;
}

.compare-toggle {
  width: 100%;
  text-align: left;
  margin-top: 1rem;
  padding: 0.625rem 0.875rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 0.875rem;
  cursor: pointer;
  display: flex;
  gap: 0.625rem;
  align-items: center;
  font-size: 0.8125rem;
}

.compare-toggle:hover {
  background: #f9fafb;
}

.chev {
  width: 1.125rem;
  display: inline-block;
}

.compare-error {
  color: #b91c1c;
  margin-top: 0.75rem;
}

.muted {
  color: #9ca3af;
}

.code {
  margin-top: 0.75rem;
  padding: 1rem;
  background: #1f2937;
  color: #f9fafb;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

</style>
