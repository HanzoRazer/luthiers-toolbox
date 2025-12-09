<template>
  <div class="instrument-geometry-panel">
    <div class="panel-header">
      <h2>Instrument Geometry Designer</h2>
      <p class="subtitle">
        Fretboard CAM with Feasibility Analysis (Waves 15-16)
      </p>
    </div>

    <!-- Main Layout: Left Controls + Right Preview -->
    <div class="layout-grid">
      <!-- ===== LEFT PANEL: Controls ===== -->
      <div class="controls-panel">
        <!-- Model Selection -->
        <section class="control-section">
          <h3>Instrument Model</h3>
          <select
            v-model="store.selectedModelId"
            @change="handleModelChange"
            class="select-input"
          >
            <option
              v-for="model in INSTRUMENT_MODELS"
              :key="model.id"
              :value="model.id"
            >
              {{ model.display_name }}
            </option>
          </select>

          <div class="model-info">
            <div class="info-row">
              <span class="label">Scale Length:</span>
              <span class="value"
                >{{ store.selectedModel.scale_length_mm.toFixed(1) }} mm</span
              >
            </div>
            <div class="info-row">
              <span class="label">Frets:</span>
              <span class="value">{{ store.selectedModel.num_frets }}</span>
            </div>
            <div class="info-row">
              <span class="label">Nut Width:</span>
              <span class="value"
                >{{ store.selectedModel.nut_width_mm.toFixed(1) }} mm</span
              >
            </div>
            <div class="info-row">
              <span class="label">Bridge Width:</span>
              <span class="value"
                >{{ store.selectedModel.bridge_width_mm.toFixed(1) }} mm</span
              >
            </div>
          </div>
        </section>

        <!-- Fretboard Parameters -->
        <section class="control-section">
          <h3>Fretboard Geometry</h3>

          <div class="input-group">
            <label>Base Radius (Nut)</label>
            <input
              type="number"
              v-model.number="store.fretboardSpec.base_radius_inches"
              step="0.5"
              min="7"
              max="20"
              class="number-input"
            />
            <span class="unit">"</span>
          </div>

          <div class="input-group">
            <label>End Radius (Heel)</label>
            <input
              type="number"
              v-model.number="store.fretboardSpec.end_radius_inches"
              step="0.5"
              min="7"
              max="20"
              class="number-input"
            />
            <span class="unit">"</span>
          </div>

          <div class="input-group">
            <label>Slot Width</label>
            <input
              type="number"
              v-model.number="store.fretboardSpec.slot_width_mm"
              step="0.05"
              min="0.4"
              max="1.0"
              class="number-input"
            />
            <span class="unit">mm</span>
          </div>

          <div class="input-group">
            <label>Slot Depth</label>
            <input
              type="number"
              v-model.number="store.fretboardSpec.slot_depth_mm"
              step="0.1"
              min="2.0"
              max="4.0"
              class="number-input"
            />
            <span class="unit">mm</span>
          </div>

          <div class="input-group">
            <label>Material</label>
            <select
              v-model="store.fretboardSpec.material_id"
              class="select-input"
            >
              <option value="rosewood">Rosewood</option>
              <option value="maple">Maple</option>
              <option value="ebony">Ebony</option>
              <option value="pau_ferro">Pau Ferro</option>
            </select>
          </div>
        </section>

        <!-- Fan-Fret Controls (Wave 16) -->
        <section class="control-section">
          <h3>
            <label class="checkbox-label">
              <input
                type="checkbox"
                v-model="store.fanFretEnabled"
                class="checkbox-input"
              />
              Fan-Fret (Multi-Scale)
            </label>
          </h3>

          <div v-if="store.fanFretEnabled" class="fan-fret-controls">
            <div class="input-group">
              <label>Treble Scale</label>
              <input
                type="number"
                v-model.number="store.trebleScaleLength"
                step="1"
                min="610"
                max="685"
                class="number-input"
              />
              <span class="unit">mm</span>
            </div>

            <div class="input-group">
              <label>Bass Scale</label>
              <input
                type="number"
                v-model.number="store.bassScaleLength"
                step="1"
                min="610"
                max="685"
                class="number-input"
              />
              <span class="unit">mm</span>
            </div>

            <div class="info-banner warning">
              ⚠️ Fan-fret CAM generation not yet implemented (Wave 16 roadmap)
            </div>
          </div>
        </section>

        <!-- Generate Button -->
        <section class="control-section">
          <button
            @click="handleGeneratePreview"
            :disabled="store.isLoadingPreview || store.fanFretEnabled"
            class="btn-primary btn-large"
          >
            <span v-if="store.isLoadingPreview">⏳ Generating...</span>
            <span v-else>🚀 Generate CAM Preview</span>
          </button>

          <div v-if="store.previewError" class="error-banner">
            ❌ {{ store.previewError }}
          </div>
        </section>
      </div>

      <!-- ===== RIGHT PANEL: Preview & Results ===== -->
      <div class="preview-panel">
        <!-- Loading State -->
        <div v-if="store.isLoadingPreview" class="loading-state">
          <div class="spinner"></div>
          <p>Generating CAM toolpaths and feasibility analysis...</p>
        </div>

        <!-- Preview Content -->
        <div v-else-if="store.previewResponse" class="preview-content">
          <!-- Feasibility Header -->
          <section class="feasibility-header">
            <div
              class="risk-badge"
              :style="{ backgroundColor: store.riskColor }"
            >
              {{ store.riskLabel }}
            </div>
            <div class="score-display">
              Score: {{ store.feasibility.overall_score.toFixed(1) }}
            </div>
            <div class="status-flags">
              <span v-if="store.feasibility.is_feasible" class="flag-good"
                >✓ Feasible</span
              >
              <span v-else class="flag-bad">✗ Not Feasible</span>

              <span v-if="store.feasibility.needs_review" class="flag-warning"
                >⚠ Needs Review</span
              >
            </div>
          </section>

          <!-- Recommendations -->
          <section
            v-if="store.feasibility.recommendations.length > 0"
            class="recommendations"
          >
            <h4>Recommendations</h4>
            <ul>
              <li
                v-for="(rec, idx) in store.feasibility.recommendations"
                :key="idx"
              >
                {{ rec }}
              </li>
            </ul>
          </section>

          <!-- Fretboard SVG Preview -->
          <section class="fretboard-preview">
            <h4>Fretboard Preview ({{ store.toolpaths.length }} frets)</h4>
            <FretboardPreviewSvg
              :spec="store.fretboardSpec"
              :toolpaths="store.toolpaths"
              :width="700"
              :height="200"
              :show-labels="true"
              :show-inlays="true"
              :show-risk-legend="true"
              :risk-coloring="true"
            />
          </section>

          <!-- Statistics -->
          <section class="statistics-grid">
            <div class="stat-card">
              <div class="stat-label">Total Time</div>
              <div class="stat-value">
                {{ formatTime(store.statistics.total_time_s) }}
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-label">Total Cost</div>
              <div class="stat-value">
                ${{ store.statistics.total_cost_usd.toFixed(2) }}
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-label">Energy</div>
              <div class="stat-value">
                {{ store.statistics.total_energy_kwh.toFixed(3) }} kWh
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-label">Cut Length</div>
              <div class="stat-value">
                {{ store.statistics.total_length_mm.toFixed(1) }} mm
              </div>
            </div>
          </section>

          <!-- DXF/G-code Previews -->
          <section class="code-previews">
            <div class="preview-column">
              <h4>DXF Preview</h4>
              <pre class="code-preview">{{
                store.previewResponse.dxf_preview
              }}</pre>
              <button @click="store.downloadDxf" class="btn-secondary">
                📥 Download DXF
              </button>
            </div>

            <div class="preview-column">
              <h4>G-code Preview</h4>
              <pre class="code-preview">{{
                store.previewResponse.gcode_preview
              }}</pre>
              <button @click="store.downloadGcode" class="btn-secondary">
                📥 Download G-code
              </button>
            </div>
          </section>

          <!-- Toolpath Details Table -->
          <section class="toolpath-table">
            <h4>Toolpath Details ({{ store.toolpaths.length }} slots)</h4>
            <div class="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Fret #</th>
                    <th>Position (mm)</th>
                    <th>Width (mm)</th>
                    <th>Depth (mm)</th>
                    <th>Feed (mm/min)</th>
                    <th>RPM</th>
                    <th>Time (s)</th>
                    <th>Cost ($)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="tp in store.toolpaths"
                    :key="tp.fret_number"
                    :class="{ 'row-highlight': tp.fret_number % 12 === 0 }"
                  >
                    <td>{{ tp.fret_number }}</td>
                    <td>{{ tp.position_mm.toFixed(2) }}</td>
                    <td>{{ tp.width_mm.toFixed(2) }}</td>
                    <td>{{ tp.depth_mm.toFixed(2) }}</td>
                    <td>{{ tp.feed_rate }}</td>
                    <td>{{ tp.spindle_rpm }}</td>
                    <td>{{ tp.cut_time_s.toFixed(1) }}</td>
                    <td>{{ tp.cost_usd.toFixed(3) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <div class="empty-icon">🎸</div>
          <h3>No Preview Generated</h3>
          <p>
            Configure your instrument model and click "Generate CAM Preview" to
            begin.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import {
  useInstrumentGeometryStore,
  INSTRUMENT_MODELS,
} from "@/stores/instrumentGeometryStore";
import FretboardPreviewSvg from "@/components/FretboardPreviewSvg.vue";

const store = useInstrumentGeometryStore();

// ============================================================================
// Handlers
// ============================================================================

function handleModelChange() {
  // Model change already handled by store reactivity
  console.log("Model changed to:", store.selectedModelId);
}

async function handleGeneratePreview() {
  await store.generatePreview();
}

function formatTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  console.log("InstrumentGeometryPanel mounted");
  // Auto-load default model
  store.selectModel("strat_25_5");
});
</script>

<style scoped>
.instrument-geometry-panel {
  padding: 20px;
  background: #0a0a0a;
  min-height: 100vh;
  color: #e5e5e5;
}

.panel-header {
  margin-bottom: 24px;
}

.panel-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #fff;
}

.subtitle {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #999;
}

/* ===== Layout Grid ===== */
.layout-grid {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 24px;
}

/* ===== Controls Panel ===== */
.controls-panel {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.control-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-section h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  border-bottom: 1px solid #333;
  padding-bottom: 8px;
}

.select-input {
  width: 100%;
  padding: 10px;
  background: #0a0a0a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #e5e5e5;
  font-size: 14px;
  cursor: pointer;
}

.select-input:focus {
  outline: none;
  border-color: #0ea5e9;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #0a0a0a;
  border-radius: 4px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-row .label {
  color: #999;
}

.info-row .value {
  color: #fff;
  font-weight: 500;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-group label {
  flex: 1;
  font-size: 13px;
  color: #ccc;
}

.number-input {
  width: 80px;
  padding: 6px 8px;
  background: #0a0a0a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #e5e5e5;
  font-size: 13px;
  text-align: right;
}

.number-input:focus {
  outline: none;
  border-color: #0ea5e9;
}

.unit {
  width: 30px;
  font-size: 13px;
  color: #999;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 600;
  margin: 0;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.fan-fret-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 12px;
}

.info-banner {
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  background: #1e3a8a;
  color: #93c5fd;
  border: 1px solid #3b82f6;
}

.info-banner.warning {
  background: #78350f;
  color: #fcd34d;
  border-color: #f59e0b;
}

.error-banner {
  padding: 10px;
  border-radius: 4px;
  font-size: 13px;
  background: #7f1d1d;
  color: #fca5a5;
  border: 1px solid #ef4444;
}

.btn-primary,
.btn-secondary {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #0ea5e9;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #0284c7;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: #444;
  color: #888;
  cursor: not-allowed;
}

.btn-large {
  width: 100%;
  padding: 14px 20px;
  font-size: 16px;
}

.btn-secondary {
  background: #374151;
  color: #e5e5e5;
  font-size: 13px;
  padding: 8px 16px;
}

.btn-secondary:hover {
  background: #4b5563;
}

/* ===== Preview Panel ===== */
.preview-panel {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 24px;
  min-height: 600px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #333;
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  color: #666;
}

.empty-icon {
  font-size: 64px;
}

.empty-state h3 {
  margin: 0;
  font-size: 20px;
  color: #999;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ===== Feasibility Header ===== */
.feasibility-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #0a0a0a;
  border-radius: 6px;
  border: 1px solid #333;
}

.risk-badge {
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

.score-display {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.status-flags {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.flag-good,
.flag-bad,
.flag-warning {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.flag-good {
  background: #065f46;
  color: #6ee7b7;
}

.flag-bad {
  background: #7f1d1d;
  color: #fca5a5;
}

.flag-warning {
  background: #78350f;
  color: #fcd34d;
}

/* ===== Recommendations ===== */
.recommendations {
  padding: 16px;
  background: #0a0a0a;
  border-radius: 6px;
  border: 1px solid #333;
}

.recommendations h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #fff;
}

.recommendations ul {
  margin: 0;
  padding-left: 20px;
}

.recommendations li {
  font-size: 13px;
  color: #ccc;
  margin-bottom: 6px;
}

/* ===== Fretboard Preview ===== */
.fretboard-preview h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #fff;
}

/* ===== Statistics ===== */
.statistics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  padding: 16px;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 6px;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #0ea5e9;
}

/* ===== Code Previews ===== */
.code-previews {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.preview-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-column h4 {
  margin: 0;
  font-size: 15px;
  color: #fff;
}

.code-preview {
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 12px;
  font-family: "Courier New", monospace;
  font-size: 11px;
  color: #10b981;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

/* ===== Toolpath Table ===== */
.toolpath-table h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #fff;
}

.table-wrapper {
  overflow-x: auto;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 6px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #1a1a1a;
  position: sticky;
  top: 0;
}

th {
  padding: 12px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  border-bottom: 1px solid #333;
}

td {
  padding: 10px 16px;
  font-size: 13px;
  color: #ccc;
  border-bottom: 1px solid #222;
}

tbody tr:hover {
  background: #1a1a1a;
}

.row-highlight {
  background: #1e293b !important;
}

.row-highlight:hover {
  background: #334155 !important;
}
</style>
