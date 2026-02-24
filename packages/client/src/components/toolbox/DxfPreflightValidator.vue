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
/**
 * DxfPreflightValidator.vue
 *
 * Validates DXF files before CAM import and offers auto-fix capabilities.
 * Uses composables for state management and validation logic.
 */
import { useDxfPreflightState, useDxfPreflightValidation } from './dxf-preflight'
import styles from './DxfPreflightValidator.module.css'

// Initialize state composable
const state = useDxfPreflightState()

// Initialize validation composable with state dependencies
const {
  handleFileSelect,
  formatFileSize,
  validateFile,
  applyAutoFix,
  downloadFixedDxf,
  validateFixedDxf
} = useDxfPreflightValidation(state)

// Destructure state for template access
const {
  selectedFile,
  fileInput,
  validating,
  report,
  error,
  fixes,
  fixedDxf,
  appliedFixes,
  autoFixing,
  hasFixableIssues,
  hasOpenPolylines,
  hasSelectedFixes
} = state
</script>
