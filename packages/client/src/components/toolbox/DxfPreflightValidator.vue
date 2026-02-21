<template>
  <div :class="styles.dxfPreflight">
    <h2>DXF Preflight Validator</h2>
    <p :class="styles.subtitle">
      Validate DXF files before CAM import — catch issues early!
    </p>

    <!-- File Upload Section -->
    <div :class="styles.uploadSection">
      <label :class="styles.fileUpload">
        <input
          ref="fileInput"
          type="file"
          accept=".dxf"
          @change="handleFileSelect"
        >
        <span :class="styles.uploadButton">Choose DXF File</span>
      </label>
      <span
        v-if="selectedFile"
        :class="styles.fileInfo"
      >
        {{ selectedFile.name }} ({{ formatFileSize(selectedFile.size) }})
      </span>
      <button
        v-if="selectedFile"
        :disabled="validating"
        :class="styles.validateBtn"
        @click="validateFile"
      >
        {{ validating ? 'Validating...' : 'Validate DXF' }}
      </button>
    </div>

    <!-- Validation Report -->
    <div
      v-if="report"
      :class="styles.report"
    >
      <!-- Header Summary -->
      <div :class="report.cam_ready ? styles.reportHeaderCamReady : styles.reportHeaderHasIssues">
        <h3>
          <span v-if="report.cam_ready">CAM-Ready</span>
          <span v-else>Issues Found</span>
        </h3>
        <div :class="styles.stats">
          <span
            v-if="report.errors_count > 0"
            :class="styles.statError"
          >{{ report.errors_count }} Error(s)</span>
          <span
            v-if="report.warnings_count > 0"
            :class="styles.statWarning"
          >{{ report.warnings_count }} Warning(s)</span>
          <span
            v-if="report.info_count > 0"
            :class="styles.statInfo"
          >{{ report.info_count }} Info</span>
        </div>
      </div>

      <!-- File Info -->
      <div :class="styles.section">
        <h4>File Information</h4>
        <table :class="styles.infoTable">
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
              <span :class="{ [styles.versionOk]: report.dxf_version === 'AC1009', [styles.versionWarning]: report.dxf_version !== 'AC1009' }">
                {{ report.dxf_version }}
                <span v-if="report.dxf_version === 'AC1009'"> (R12)</span>
                <span v-else> (Not R12)</span>
              </span>
            </td>
          </tr>
          <tr>
            <td>Units:</td>
            <td>
              <span :class="{ [styles.unitsUnknown]: report.units === 'unknown' }">
                {{ report.units === 'unknown' ? 'Unknown' : report.units.toUpperCase() }}
              </span>
            </td>
          </tr>
        </table>
      </div>

      <!-- Geometry Summary -->
      <div :class="styles.section">
        <h4>Geometry Summary</h4>
        <div :class="styles.geometryGrid">
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Lines:</span>
            <span :class="styles.geomValue">{{ report.geometry.lines }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Arcs:</span>
            <span :class="styles.geomValue">{{ report.geometry.arcs }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Circles:</span>
            <span :class="styles.geomValue">{{ report.geometry.circles }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Polylines:</span>
            <span :class="styles.geomValue">{{ report.geometry.polylines }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">LWPolylines:</span>
            <span :class="styles.geomValue">{{ report.geometry.lwpolylines }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Splines:</span>
            <span
              :class="[styles.geomValue, { [styles.warnValue]: report.geometry.splines > 0 }]"
            >
              {{ report.geometry.splines }}
            </span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Ellipses:</span>
            <span
              :class="[styles.geomValue, { [styles.warnValue]: report.geometry.ellipses > 0 }]"
            >
              {{ report.geometry.ellipses }}
            </span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel">Text:</span>
            <span :class="styles.geomValue">{{ report.geometry.text }}</span>
          </div>
          <div :class="styles.geomStat">
            <span :class="styles.geomLabel"><strong>Total:</strong></span>
            <span :class="styles.geomValue"><strong>{{ report.geometry.total }}</strong></span>
          </div>
        </div>
      </div>

      <!-- Layers -->
      <div :class="styles.section">
        <h4>Layers ({{ report.layers.length }})</h4>
        <div :class="styles.layersList">
          <div
            v-for="layer in report.layers"
            :key="layer.name"
            :class="styles.layerItem"
          >
            <span :class="styles.layerName">{{ layer.name }}</span>
            <span :class="styles.layerCount">{{ layer.entity_count }} entities</span>
            <span :class="styles.layerTypes">{{ layer.geometry_types.join(', ') }}</span>
            <span
              v-if="layer.frozen"
              :class="styles.layerBadgeFrozen"
            >Frozen</span>
            <span
              v-if="layer.locked"
              :class="styles.layerBadgeLocked"
            >Locked</span>
          </div>
        </div>
      </div>

      <!-- Issues -->
      <div
        v-if="report.issues.length > 0"
        :class="styles.section"
      >
        <h4>Issues ({{ report.issues.length }})</h4>
        <div :class="styles.issuesList">
          <div
            v-for="(issue, idx) in report.issues"
            :key="idx"
            :class="[styles.issueItem, {
              [styles.severityError]: issue.severity === 'error',
              [styles.severityWarning]: issue.severity === 'warning',
              [styles.severityInfo]: issue.severity === 'info'
            }]"
          >
            <div :class="styles.issueHeader">
              <span :class="styles.issueIcon">
                <span v-if="issue.severity === 'error'">X</span>
                <span v-else-if="issue.severity === 'warning'">!</span>
                <span v-else>i</span>
              </span>
              <span :class="styles.issueCategory">[{{ issue.category }}]</span>
              <span :class="styles.issueMessage">{{ issue.message }}</span>
            </div>
            <div
              v-if="issue.details"
              :class="styles.issueDetails"
            >
              {{ issue.details }}
            </div>
            <div
              v-if="issue.fix_available"
              :class="styles.issueFix"
            >
              <span :class="styles.fixIcon">Fix:</span>
              <span :class="styles.fixDesc">{{ issue.fix_description }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommended Actions -->
      <div :class="styles.section">
        <h4>Recommended Actions</h4>
        <ul :class="styles.recommendations">
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
        :class="styles.section"
      >
        <h4>Auto-Fix</h4>
        <p>Select fixes to apply automatically:</p>
        <div :class="styles.fixOptions">
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
          :class="styles.autoFixBtn"
          @click="applyAutoFix"
        >
          {{ autoFixing ? 'Applying Fixes...' : 'Apply Selected Fixes' }}
        </button>
      </div>

      <!-- Fixed DXF Download -->
      <div
        v-if="fixedDxf"
        :class="[styles.section, styles.fixedSection]"
      >
        <h4>Fixed DXF Ready!</h4>
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
          :class="styles.downloadBtn"
          @click="downloadFixedDxf"
        >
          Download Fixed DXF
        </button>
        <button
          :class="styles.validateBtn"
          @click="validateFixedDxf"
        >
          Re-Validate Fixed DXF
        </button>
      </div>
    </div>

    <!-- Error Display -->
    <div
      v-if="error"
      :class="styles.errorBox"
    >
      <strong>Error:</strong> {{ error }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from '@/services/apiBase';
import { ref, computed } from 'vue'
import styles from './DxfPreflightValidator.module.css'

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
