<template>
  <div class="dxf-preflight">
    <h2>🔍 DXF Preflight Validator</h2>
    <p class="subtitle">
      Validate DXF files before CAM import — catch issues early!
    </p>

    <!-- File Upload Section -->
    <div class="upload-section">
      <label class="file-upload">
        <input
          ref="fileInput"
          type="file"
          accept=".dxf"
          @change="handleFileSelect"
        >
        <span class="upload-button">📁 Choose DXF File</span>
      </label>
      <span
        v-if="selectedFile"
        class="file-info"
      >
        {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})
      </span>
      <button
        v-if="selectedFile"
        :disabled="validating"
        class="validate-btn"
        @click="validateFile"
      >
        {{ validating ? '⏳ Validating...' : '✅ Validate DXF' }}
      </button>
    </div>

    <!-- Validation Report -->
    <div
      v-if="report"
      class="report"
    >
      <!-- Header Summary -->
      <div
        class="report-header"
        :class="{ 'cam-ready': report.cam_ready, 'has-issues': !report.cam_ready }"
      >
        <h3>
          <span v-if="report.cam_ready">✅ CAM-Ready</span>
          <span v-else>⚠️ Issues Found</span>
        </h3>
        <div class="stats">
          <span
            v-if="report.errors_count > 0"
            class="stat error"
          >{{ report.errors_count }} Error(s)</span>
          <span
            v-if="report.warnings_count > 0"
            class="stat warning"
          >{{ report.warnings_count }} Warning(s)</span>
          <span
            v-if="report.info_count > 0"
            class="stat info"
          >{{ report.info_count }} Info</span>
        </div>
      </div>

      <!-- File Info -->
      <div class="section">
        <h4>📄 File Information</h4>
        <table class="info-table">
          <tr>
            <td>Filename:</td>
            <td><strong>{{ report.filename }}</strong></td>
          </tr>
          <tr>
            <td>Size:</td>
            <td>{{ formatFileSize(report.filesize_bytes) }}</td>
          </tr>
          <tr>
            <td>DXF Version:</td>
            <td>
              <span :class="{ 'version-ok': report.dxf_version === 'AC1009', 'version-warning': report.dxf_version !== 'AC1009' }">
                {{ report.dxf_version }}
                <span v-if="report.dxf_version === 'AC1009'"> (R12 ✓)</span>
                <span v-else> (Not R12)</span>
              </span>
            </td>
          </tr>
          <tr>
            <td>Units:</td>
            <td>
              <span :class="{ 'units-unknown': report.units === 'unknown' }">
                {{ report.units === 'unknown' ? 'Unknown ⚠️' : report.units.toUpperCase() }}
              </span>
            </td>
          </tr>
        </table>
      </div>

      <!-- Geometry Summary -->
      <div class="section">
        <h4>📐 Geometry Summary</h4>
        <div class="geometry-grid">
          <div class="geom-stat">
            <span class="geom-label">Lines:</span>
            <span class="geom-value">{{ report.geometry.lines }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Arcs:</span>
            <span class="geom-value">{{ report.geometry.arcs }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Circles:</span>
            <span class="geom-value">{{ report.geometry.circles }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Polylines:</span>
            <span class="geom-value">{{ report.geometry.polylines }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">LWPolylines:</span>
            <span class="geom-value">{{ report.geometry.lwpolylines }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Splines:</span>
            <span
              class="geom-value"
              :class="{ 'warn-value': report.geometry.splines > 0 }"
            >
              {{ report.geometry.splines }}
            </span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Ellipses:</span>
            <span
              class="geom-value"
              :class="{ 'warn-value': report.geometry.ellipses > 0 }"
            >
              {{ report.geometry.ellipses }}
            </span>
          </div>
          <div class="geom-stat">
            <span class="geom-label">Text:</span>
            <span class="geom-value">{{ report.geometry.text }}</span>
          </div>
          <div class="geom-stat">
            <span class="geom-label"><strong>Total:</strong></span>
            <span class="geom-value"><strong>{{ report.geometry.total }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Layers -->
      <div class="section">
        <h4>🗂️ Layers ({{ report.layers.length }})</h4>
        <div class="layers-list">
          <div
            v-for="layer in report.layers"
            :key="layer.name"
            class="layer-item"
          >
            <span class="layer-name">{{ layer.name }}</span>
            <span class="layer-count">{{ layer.entity_count }} entities</span>
            <span class="layer-types">{{ layer.geometry_types.join(', ') }}</span>
            <span
              v-if="layer.frozen"
              class="layer-badge frozen"
            >Frozen</span>
            <span
              v-if="layer.locked"
              class="layer-badge locked"
            >Locked</span>
          </div>
        </div>
      </div>

      <!-- Issues -->
      <div
        v-if="report.issues.length > 0"
        class="section"
      >
        <h4>🔍 Issues ({{ report.issues.length }})</h4>
        <div class="issues-list">
          <div
            v-for="(issue, idx) in report.issues"
            :key="idx"
            class="issue-item"
            :class="`severity-${issue.severity}`"
          >
            <div class="issue-header">
              <span class="issue-icon">
                <span v-if="issue.severity === 'error'">❌</span>
                <span v-else-if="issue.severity === 'warning'">⚠️</span>
                <span v-else>ℹ️</span>
              </span>
              <span class="issue-category">[{{ issue.category }}]</span>
              <span class="issue-message">{{ issue.message }}</span>
            </div>
            <div
              v-if="issue.details"
              class="issue-details"
            >
              {{ issue.details }}
            </div>
            <div
              v-if="issue.fix_available"
              class="issue-fix"
            >
              <span class="fix-icon">🔧</span>
              <span class="fix-desc">{{ issue.fix_description }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommended Actions -->
      <div class="section">
        <h4>💡 Recommended Actions</h4>
        <ul class="recommendations">
          <li
            v-for="(action, idx) in report.recommended_actions"
            :key="idx"
          >
            {{ action }}
          </li>
        </ul>
      </div>

      <!-- Auto-Fix Section -->
      <div
        v-if="hasFixableIssues"
        class="section"
      >
        <h4>🔧 Auto-Fix</h4>
        <p>Select fixes to apply automatically:</p>
        <div class="fix-options">
          <label v-if="!report.cam_ready && report.dxf_version !== 'AC1009'">
            <input
              v-model="fixes.convert_to_r12"
              type="checkbox"
            >
            Convert to R12 format
          </label>
          <label v-if="hasOpenPolylines">
            <input
              v-model="fixes.close_open_polylines"
              type="checkbox"
            >
            Close open polylines (0.1mm tolerance)
          </label>
          <label v-if="report.units === 'unknown'">
            <input
              v-model="fixes.set_units_mm"
              type="checkbox"
            >
            Set units to millimeters
          </label>
          <label v-if="report.geometry.splines > 0">
            <input
              v-model="fixes.explode_splines"
              type="checkbox"
              disabled
            >
            Explode splines (coming soon)
          </label>
        </div>
        <button
          :disabled="!hasSelectedFixes || autoFixing"
          class="auto-fix-btn"
          @click="applyAutoFix"
        >
          {{ autoFixing ? '⏳ Applying Fixes...' : '🔧 Apply Selected Fixes' }}
        </button>
      </div>

      <!-- Fixed DXF Download -->
      <div
        v-if="fixedDxf"
        class="section fixed-section"
      >
        <h4>✅ Fixed DXF Ready!</h4>
        <p><strong>Fixes Applied:</strong></p>
        <ul>
          <li
            v-for="(fix, idx) in appliedFixes"
            :key="idx"
          >
            {{ fix }}
          </li>
        </ul>
        <button
          class="download-btn"
          @click="downloadFixedDxf"
        >
          💾 Download Fixed DXF
        </button>
        <button
          class="validate-btn"
          @click="validateFixedDxf"
        >
          🔄 Re-Validate Fixed DXF
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="error"
      class="error-box"
    >
      <strong>❌ Error:</strong> {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'

interface ValidationIssue {
  severity: 'error' | 'warning' | 'info'
  category: string
  message: string
  details?: string
  fix_available: boolean
  fix_description?: string
}

interface GeometrySummary {
  lines: number
  arcs: number
  circles: number
  polylines: number
  lwpolylines: number
  splines: number
  ellipses: number
  text: number
  other: number
  total: number
}

interface LayerInfo {
  name: string
  entity_count: number
  geometry_types: string[]
  color?: number
  frozen: boolean
  locked: boolean
}

interface ValidationReport {
  filename: string
  filesize_bytes: number
  dxf_version: string
  units: string
  issues: ValidationIssue[]
  errors_count: number
  warnings_count: number
  info_count: number
  geometry: GeometrySummary
  layers: LayerInfo[]
  cam_ready: boolean
  recommended_actions: string[]
}

const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const validating = ref(false)
const report = ref<ValidationReport | null>(null)
const error = ref<string | null>(null)

const fixes = ref({
  convert_to_r12: false,
  close_open_polylines: false,
  set_units_mm: false,
  explode_splines: false
})

const fixedDxf = ref<string | null>(null)
const appliedFixes = ref<string[]>([])
const autoFixing = ref(false)

const hasFixableIssues = computed(() => {
  if (!report.value) return false
  return report.value.issues.some(i => i.fix_available)
})

const hasOpenPolylines = computed(() => {
  if (!report.value) return false
  return report.value.issues.some(i => i.message.includes('Open'))
})

const hasSelectedFixes = computed(() => {
  return fixes.value.convert_to_r12 || fixes.value.close_open_polylines || 
         fixes.value.set_units_mm || fixes.value.explode_splines
})

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    report.value = null
    error.value = null
    fixedDxf.value = null
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

async function validateFile() {
  if (!selectedFile.value) return
  
  validating.value = true
  error.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const response = await api('/api/dxf/preflight/validate', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`Validation failed: ${errText}`)
    }
    
    report.value = await response.json()
  } catch (err: any) {
    error.value = err.message || 'Validation failed'
    console.error('Validation error:', err)
  } finally {
    validating.value = false
  }
}

async function applyAutoFix() {
  if (!selectedFile.value || !hasSelectedFixes.value) return
  
  autoFixing.value = true
  error.value = null
  
  try {
    // Read file as base64
    const reader = new FileReader()
    const fileBase64 = await new Promise<string>((resolve, reject) => {
      reader.onload = () => {
        const result = reader.result as string
        const base64 = result.split(',')[1] // Remove data:... prefix
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(selectedFile.value!)
    })
    
    // Build fix list
    const fixList: string[] = []
    if (fixes.value.convert_to_r12) fixList.push('convert_to_r12')
    if (fixes.value.close_open_polylines) fixList.push('close_open_polylines')
    if (fixes.value.set_units_mm) fixList.push('set_units_mm')
    if (fixes.value.explode_splines) fixList.push('explode_splines')
    
    const response = await api('/api/dxf/preflight/auto_fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dxf_base64: fileBase64,
        filename: selectedFile.value.name,
        fixes: fixList
      })
    })
    
    if (!response.ok) {
      const errText = await response.text()
      throw new Error(`Auto-fix failed: ${errText}`)
    }
    
    const result = await response.json()
    fixedDxf.value = result.fixed_dxf_base64
    appliedFixes.value = result.fixes_applied
    report.value = result.validation_report
    
  } catch (err: any) {
    error.value = err.message || 'Auto-fix failed'
    console.error('Auto-fix error:', err)
  } finally {
    autoFixing.value = false
  }
}

function downloadFixedDxf() {
  if (!fixedDxf.value || !selectedFile.value) return
  
  const bytes = Uint8Array.from(atob(fixedDxf.value), c => c.charCodeAt(0))
  const blob = new Blob([bytes], { type: 'application/dxf' })
  const url = URL.createObjectURL(blob)
  
  const a = document.createElement('a')
  a.href = url
  a.download = selectedFile.value.name.replace('.dxf', '_fixed.dxf')
  a.click()
  
  URL.revokeObjectURL(url)
}

async function validateFixedDxf() {
  if (!fixedDxf.value || !selectedFile.value) return
  
  validating.value = true
  error.value = null
  
  try {
    const response = await api('/api/dxf/preflight/validate_base64', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dxf_base64: fixedDxf.value,
        filename: selectedFile.value.name.replace('.dxf', '_fixed.dxf')
      })
    })
    
    if (!response.ok) {
      throw new Error('Re-validation failed')
    }
    
    report.value = await response.json()
  } catch (err: any) {
    error.value = err.message
  } finally {
    validating.value = false
  }
}
</script>

<style scoped>
.dxf-preflight {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h2 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #7f8c8d;
  font-size: 1.1rem;
  margin-bottom: 2rem;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px dashed #dee2e6;
}

.file-upload input[type="file"] {
  display: none;
}

.upload-button {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #2980b9;
}

.file-info {
  color: #2c3e50;
  font-weight: 500;
}

.validate-btn, .auto-fix-btn, .download-btn {
  padding: 0.75rem 1.5rem;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.validate-btn:hover, .auto-fix-btn:hover, .download-btn:hover {
  background: #229954;
}

.validate-btn:disabled, .auto-fix-btn:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.report {
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  overflow: hidden;
}

.report-header {
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-header.cam-ready {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border-bottom: 3px solid #28a745;
}

.report-header.has-issues {
  background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
  border-bottom: 3px solid #ffc107;
}

.stats {
  display: flex;
  gap: 1rem;
}

.stat {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 600;
}

.stat.error {
  background: #f8d7da;
  color: #721c24;
}

.stat.warning {
  background: #fff3cd;
  color: #856404;
}

.stat.info {
  background: #d1ecf1;
  color: #0c5460;
}

.section {
  padding: 1.5rem;
  border-bottom: 1px solid #dee2e6;
}

.section:last-child {
  border-bottom: none;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
}

.info-table td {
  padding: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.info-table td:first-child {
  font-weight: 600;
  width: 150px;
  color: #7f8c8d;
}

.version-ok {
  color: #27ae60;
  font-weight: 600;
}

.version-warning {
  color: #e67e22;
  font-weight: 600;
}

.units-unknown {
  color: #e74c3c;
  font-weight: 600;
}

.geometry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.geom-stat {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.warn-value {
  color: #e67e22;
  font-weight: 600;
}

.layers-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.layer-name {
  font-weight: 600;
  min-width: 150px;
}

.layer-count {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.layer-types {
  color: #95a5a6;
  font-size: 0.85rem;
  font-style: italic;
}

.layer-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 600;
}

.layer-badge.frozen {
  background: #d6eaf8;
  color: #1f618d;
}

.layer-badge.locked {
  background: #fadbd8;
  color: #943126;
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.issue-item {
  padding: 1rem;
  border-left: 4px solid;
  border-radius: 4px;
}

.issue-item.severity-error {
  background: #f8d7da;
  border-color: #dc3545;
}

.issue-item.severity-warning {
  background: #fff3cd;
  border-color: #ffc107;
}

.issue-item.severity-info {
  background: #d1ecf1;
  border-color: #17a2b8;
}

.issue-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.issue-category {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.85rem;
}

.issue-details {
  margin-left: 2rem;
  color: #6c757d;
  font-size: 0.9rem;
}

.issue-fix {
  margin-top: 0.5rem;
  margin-left: 2rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 4px;
  font-size: 0.9rem;
}

.fix-icon {
  margin-right: 0.5rem;
}

.recommendations {
  list-style: none;
  padding: 0;
}

.recommendations li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.recommendations li:before {
  content: "→ ";
  color: #3498db;
  font-weight: 600;
  margin-right: 0.5rem;
}

.fix-options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
}

.fix-options label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.fix-options input[type="checkbox"]:disabled + span {
  color: #95a5a6;
}

.fixed-section {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
}

.error-box {
  padding: 1rem;
  background: #f8d7da;
  border: 1px solid #dc3545;
  border-radius: 6px;
  color: #721c24;
  margin-top: 1rem;
}
</style>
