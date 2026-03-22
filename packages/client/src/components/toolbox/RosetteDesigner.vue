<template>
  <div class="rosette-designer-redesign">
    <!-- Educational Banner -->
    <div class="info-banner">
      <span class="banner-icon">ℹ️</span>
      <div class="banner-text">
        <strong>About Rosettes:</strong> Rosettes are decorative wood inlays hand-assembled from strips around the soundhole. 
        This tool helps you design the pattern and optionally export a channel routing path.
      </div>
    </div>

    <!-- Main Layout: Canvas (Left) + Controls (Right) -->
    <div class="designer-layout">
      <!-- LEFT: Visual Design Canvas (60%) -->
      <div class="canvas-panel">
        <RosetteCanvas 
          :soundhole-diameter="dimensions.soundholeDiameter"
          :rosette-width="dimensions.rosetteWidth"
          :symmetry-count="dimensions.symmetryCount"
          :show-grid="showGrid"
          :initial-segments="segments"
          @segments-changed="handleSegmentsChanged"
        />
      </div>

      <!-- RIGHT: Design Controls (40%) -->
      <div class="controls-panel">
        <!-- Dimensions Section -->
        <div class="control-section">
          <h4>📐 Dimensions</h4>
          <div class="input-group">
            <label>
              Soundhole Diameter (mm):
              <input
                v-model.number="dimensions.soundholeDiameter"
                type="number"
                step="1"
                min="50"
                max="120"
              >
            </label>
            <label>
              Rosette Width (mm):
              <input
                v-model.number="dimensions.rosetteWidth"
                type="number"
                step="1"
                min="10"
                max="40"
              >
            </label>
            <label>
              Channel Depth (mm):
              <input
                v-model.number="dimensions.channelDepth"
                type="number"
                step="0.1"
                min="0.5"
                max="3"
              >
            </label>
            <label>
              Radial Segments:
              <input
                v-model.number="dimensions.symmetryCount"
                type="number"
                step="1"
                min="8"
                max="32"
              >
            </label>
            <label class="checkbox-label">
              <input
                v-model="showGrid"
                type="checkbox"
              >
              Show symmetry guides
            </label>
          </div>
        </div>

        <!-- Pattern Templates Section -->
        <div class="control-section">
          <PatternTemplates 
            :selected-template="selectedTemplate"
            @template-selected="handleTemplateSelected"
            @template-applied="handleTemplateApplied"
          />
        </div>

        <!-- Materials Section -->
        <div class="control-section">
          <MaterialPalette 
            :selected-material="selectedMaterial"
            :strip-width="currentStripWidth"
            @material-selected="handleMaterialSelected"
          />
        </div>

        <!-- Export Section (De-emphasized) -->
        <div class="control-section export-section">
          <h4>📤 Export (Optional)</h4>
          <p class="export-hint">
            Export pattern image for reference, or optional channel routing path for CNC.
          </p>
          <div class="export-buttons">
            <button
              class="btn-secondary"
              @click="exportPatternImage"
            >
              📷 Pattern Image
            </button>
            <button
              class="btn-secondary"
              @click="exportDimensionSheet"
            >
              📄 Dimension Sheet
            </button>
            <button
              class="btn-secondary"
              @click="exportChannelPath"
            >
              🔧 Channel Path
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Messages -->
    <div
      v-if="status"
      class="status-bar"
      :class="statusClass"
    >
      {{ status }}
    </div>
  </div>
</template>

<script setup lang="ts">
import RosetteCanvas from '../rosette/RosetteCanvas.vue'
import MaterialPalette from '../rosette/MaterialPalette.vue'
import PatternTemplates from '../rosette/PatternTemplates.vue'
import {
  useRosetteDesignerState,
  useRosetteDesignerExport,
  type AnyTemplate,
} from './composables'

// State management
const {
  dimensions,
  showGrid,
  selectedTemplate,
  selectedMaterial,
  currentStripWidth,
  segments,
  status,
  statusClass,
  handleSegmentsChanged,
  handleTemplateSelected,
  handleMaterialSelected,
  applyTemplate,
} = useRosetteDesignerState()

// Export functions
const {
  exportPatternImage,
  exportDimensionSheet,
  exportChannelPath,
} = useRosetteDesignerExport(
  dimensions,
  status,
  segments,
  selectedTemplate,
  selectedMaterial
)

function handleTemplateApplied(template: AnyTemplate) {
  applyTemplate(template)
}
</script>

<style scoped>
.rosette-designer-redesign {
  padding: 1rem;
  max-width: 1600px;
  margin: 0 auto;
}

.info-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.info-banner h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.info-banner p {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  opacity: 0.95;
}

.designer-layout {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.canvas-panel {
  flex: 6;
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  min-height: 600px;
}

.controls-panel {
  flex: 4;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.control-section {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.control-section h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.dimension-inputs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.input-group label {
  font-size: 0.9rem;
  color: #4a5568;
  font-weight: 500;
}

.input-group input {
  padding: 0.5rem;
  border: 1px solid #cbd5e0;
  border-radius: 4px;
  font-size: 0.95rem;
  font-family: 'Courier New', monospace;
  transition: border-color 0.2s;
}

.input-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.checkbox-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.checkbox-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-group label {
  font-size: 0.9rem;
  color: #4a5568;
  cursor: pointer;
}

.export-section {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border: 1px dashed #cbd5e0;
}

.export-section h4 {
  color: #718096;
  border-bottom-color: #cbd5e0;
}

.export-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn {
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #cbd5e0;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-tertiary {
  background: white;
  color: #718096;
  border: 1px solid #cbd5e0;
}

.btn-tertiary:hover {
  background: #f7fafc;
  border-color: #a0aec0;
}

.status-bar {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.9rem;
  text-align: center;
  transition: all 0.3s;
}

.status-bar.success {
  background: #c6f6d5;
  color: #22543d;
  border: 1px solid #9ae6b4;
}

.status-bar.error {
  background: #fed7d7;
  color: #742a2a;
  border: 1px solid #fc8181;
}

.status-bar.info {
  background: #bee3f8;
  color: #2c5282;
  border: 1px solid #90cdf4;
}

@media (max-width: 1200px) {
  .designer-layout {
    flex-direction: column;
  }
  
  .canvas-panel,
  .controls-panel {
    flex: 1;
    width: 100%;
  }
}
</style>

