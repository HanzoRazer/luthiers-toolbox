<template>
  <div class="dxf-to-gcode">
    <h1>DXF → G-code (GRBL)</h1>
    <p class="subtitle">Shop-floor quick path: upload DXF, set params, download G-code</p>

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
        @change="handleFileSelect"
        style="display: none"
      />

      <div v-if="!dxfFile" class="upload-prompt">
        <p><strong>Drop DXF here</strong> or <button @click="($refs.fileInput as HTMLInputElement).click()" class="link-btn">browse</button></p>
        <p class="hint">DXF R12/R2000 format</p>
      </div>

      <div v-else class="file-info">
        <span class="filename">{{ dxfFile.name }}</span>
        <span class="filesize">({{ (dxfFile.size / 1024).toFixed(1) }} KB)</span>
        <button @click="clearFile" class="clear-btn">×</button>
      </div>
    </div>

    <!-- CAM Parameters -->
    <div class="params-section">
      <h2>CAM Parameters</h2>
      <div class="params-grid">
        <div class="param">
          <label>Tool Diameter (mm)</label>
          <input v-model.number="params.tool_d" type="number" step="0.5" min="0.5" max="25" />
        </div>
        <div class="param">
          <label>Stepover (0-1)</label>
          <input v-model.number="params.stepover" type="number" step="0.05" min="0.1" max="0.9" />
        </div>
        <div class="param">
          <label>Stepdown (mm)</label>
          <input v-model.number="params.stepdown" type="number" step="0.5" min="0.5" max="10" />
        </div>
        <div class="param">
          <label>Target Depth (mm)</label>
          <input v-model.number="params.z_rough" type="number" step="0.5" max="0" />
        </div>
        <div class="param">
          <label>Feed XY (mm/min)</label>
          <input v-model.number="params.feed_xy" type="number" step="100" min="100" max="5000" />
        </div>
        <div class="param">
          <label>Feed Z (mm/min)</label>
          <input v-model.number="params.feed_z" type="number" step="50" min="50" max="1000" />
        </div>
        <div class="param">
          <label>Safe Z (mm)</label>
          <input v-model.number="params.safe_z" type="number" step="1" min="1" max="50" />
        </div>
        <div class="param">
          <label>Layer Name</label>
          <input v-model="params.layer_name" type="text" />
        </div>
      </div>
    </div>

    <!-- Generate Button -->
    <div class="action-section">
      <button
        @click="generateGcode"
        :disabled="!dxfFile || isGenerating"
        class="btn-generate"
      >
        {{ isGenerating ? 'Generating...' : 'Generate G-code' }}
      </button>
    </div>

    <!-- Result -->
    <div v-if="result" class="result-section">
      <div class="result-header">
        <span class="risk" :class="result.decision?.risk_level?.toLowerCase()">
          {{ result.decision?.risk_level || 'N/A' }}
        </span>
        <span class="run-id">Run: {{ result.run_id }}</span>
        <button @click="copyRunId" class="copy-btn" title="Copy Run ID">Copy</button>
        <span v-if="!result.rmos_persisted" class="not-persisted">RMOS not persisted</span>
      </div>

      <div v-if="result.decision?.warnings?.length" class="warnings">
        <strong>Warnings:</strong>
        <ul>
          <li v-for="(w, i) in result.decision.warnings" :key="i">{{ w }}</li>
        </ul>
      </div>

      <button
        @click="downloadGcode"
        :disabled="!canDownload"
        class="btn-download"
      >
        Download G-code (.nc)
      </button>

      <button
        @click="downloadOperatorPack"
        :disabled="!canDownloadOperatorPack"
        class="btn-operator-pack"
        title="Downloads input.dxf + plan.json + manifest.json + output.nc"
      >
        Download Operator Pack (.zip)
      </button>

      <div v-if="result && !result.gcode?.inline" class="attachment-hint">
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
    <div v-if="error" class="error">
      <strong>Error:</strong> {{ error }}
      <button @click="error = null" class="clear-btn">×</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const fileInput = ref<HTMLInputElement | null>(null)
const isDragOver = ref(false)
const dxfFile = ref<File | null>(null)
const isGenerating = ref(false)
const result = ref<any>(null)
const error = ref<string | null>(null)
const abortController = ref<AbortController | null>(null)

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

const canDownloadOperatorPack = computed(() => {
  const runId = (result.value?.run_id || '').trim()
  return !!runId && !isGenerating.value
})

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

  try {
    const res = await fetch(`/api/rmos/runs_v2/${encodeURIComponent(runId)}/operator-pack`, {
      method: 'GET',
    })

    if (!res.ok) {
      let msg = `HTTP ${res.status}`
      try {
        const t = await res.text()
        if (t) msg = t
      } catch {}
      throw new Error(msg)
    }

    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `operator_pack_${runId}.zip`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e: any) {
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

.action-section {
  margin-bottom: 2rem;
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

.result-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.risk {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.875rem;
}

.risk.green {
  background: #d1fae5;
  color: #065f46;
}

.risk.yellow {
  background: #fef3c7;
  color: #92400e;
}

.risk.red {
  background: #fee2e2;
  color: #991b1b;
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
</style>
