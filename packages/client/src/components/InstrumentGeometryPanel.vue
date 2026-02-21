<template>
  <div :class="shared.pageDark">
    <div :class="styles.panelHeader">
      <h2>Instrument Geometry Designer</h2>
      <p :class="styles.subtitle">
        Fretboard CAM with Feasibility Analysis (Waves 15-16)
      </p>
    </div>

    <!-- Main Layout: Left Controls + Right Preview -->
    <div :class="shared.layoutGrid">
      <!-- ===== LEFT PANEL: Controls ===== -->
      <div :class="shared.controlsPanel">
        <!-- Model Selection -->
        <section :class="shared.controlSection">
          <h3>Instrument Model</h3>
          <select
            v-model="store.selectedModelId"
            :class="shared.selectDark"
            @change="handleModelChange"
          >
            <option
              v-for="model in INSTRUMENT_MODELS"
              :key="model.id"
              :value="model.id"
            >
              {{ model.display_name }}
            </option>
          </select>

          <div :class="styles.modelInfo">
            <div :class="styles.infoRow">
              <span :class="styles.infoRowLabel">Scale Length:</span>
              <span :class="styles.infoRowValue">{{ store.selectedModel.scale_length_mm.toFixed(1) }} mm</span>
            </div>
            <div :class="styles.infoRow">
              <span :class="styles.infoRowLabel">Frets:</span>
              <span :class="styles.infoRowValue">{{ store.selectedModel.num_frets }}</span>
            </div>
            <div :class="styles.infoRow">
              <span :class="styles.infoRowLabel">Nut Width:</span>
              <span :class="styles.infoRowValue">{{ store.selectedModel.nut_width_mm.toFixed(1) }} mm</span>
            </div>
            <div :class="styles.infoRow">
              <span :class="styles.infoRowLabel">Bridge Width:</span>
              <span :class="styles.infoRowValue">{{ store.selectedModel.bridge_width_mm.toFixed(1) }} mm</span>
            </div>
          </div>
        </section>

        <!-- Fretboard Parameters -->
        <section :class="shared.controlSection">
          <h3>Fretboard Geometry</h3>

          <div :class="shared.inputRow">
            <label>Base Radius (Nut)</label>
            <input
              v-model.number="store.fretboardSpec.base_radius_inches"
              type="number"
              step="0.5"
              min="7"
              max="20"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">"</span>
          </div>

          <div :class="shared.inputRow">
            <label>End Radius (Heel)</label>
            <input
              v-model.number="store.fretboardSpec.end_radius_inches"
              type="number"
              step="0.5"
              min="7"
              max="20"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">"</span>
          </div>

          <div :class="shared.inputRow">
            <label>Slot Width</label>
            <input
              v-model.number="store.fretboardSpec.slot_width_mm"
              type="number"
              step="0.05"
              min="0.4"
              max="1.0"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Slot Depth</label>
            <input
              v-model.number="store.fretboardSpec.slot_depth_mm"
              type="number"
              step="0.1"
              min="2.0"
              max="4.0"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Material</label>
            <select
              v-model="store.fretboardSpec.material_id"
              :class="shared.selectDark"
            >
              <option value="rosewood">
                Rosewood
              </option>
              <option value="maple">
                Maple
              </option>
              <option value="ebony">
                Ebony
              </option>
              <option value="pau_ferro">
                Pau Ferro
              </option>
            </select>
          </div>
        </section>

        <!-- Fan-Fret Controls (Wave 16) -->
        <section :class="shared.controlSection">
          <h3>
            <label :class="shared.checkboxLabel">
              <input
                v-model="store.fanFretEnabled"
                type="checkbox"
                :class="shared.checkboxInput"
              >
              Fan-Fret (Multi-Scale)
            </label>
          </h3>

          <div
            v-if="store.fanFretEnabled"
            :class="styles.fanFretControls"
          >
            <div :class="shared.inputRow">
              <label>Treble Scale</label>
              <input
                v-model.number="store.trebleScaleLength"
                type="number"
                step="1"
                min="610"
                max="685"
                :class="shared.inputNumber"
              >
              <span :class="shared.unit">mm</span>
            </div>

            <div :class="shared.inputRow">
              <label>Bass Scale</label>
              <input
                v-model.number="store.bassScaleLength"
                type="number"
                step="1"
                min="610"
                max="685"
                :class="shared.inputNumber"
              >
              <span :class="shared.unit">mm</span>
            </div>

            <div :class="shared.inputRow">
              <label>Perpendicular Fret</label>
              <input
                v-model.number="store.perpendicularFret"
                type="number"
                step="1"
                min="0"
                :max="store.selectedModel.num_frets"
                :class="shared.inputNumber"
              >
              <span :class="shared.unit">fret #</span>
            </div>

            <div :class="shared.bannerInfo">
              ℹ️ Fan-fret CAM with per-fret risk analysis (Wave 19)
            </div>
          </div>
        </section>

        <!-- Generate Button -->
        <section :class="shared.controlSection">
          <button
            :disabled="store.isLoadingPreview"
            :class="shared.btnLarge"
            @click="handleGeneratePreview"
          >
            <span v-if="store.isLoadingPreview">⏳ Generating...</span>
            <span v-else>🚀 Generate CAM Preview</span>
          </button>

          <div
            v-if="store.previewError"
            :class="shared.bannerError"
          >
            ❌ {{ store.previewError }}
          </div>
        </section>
      </div>

      <!-- ===== RIGHT PANEL: Preview & Results ===== -->
      <div :class="styles.previewPanel">
        <!-- Loading State -->
        <div
          v-if="store.isLoadingPreview"
          :class="shared.loadingState"
        >
          <div :class="shared.spinner" />
          <p>Generating CAM toolpaths and feasibility analysis...</p>
        </div>

        <!-- Preview Content -->
        <div
          v-else-if="store.previewResponse"
          :class="styles.previewContent"
        >
          <!-- Feasibility Header -->
          <section :class="styles.feasibilityHeader">
            <div
              :class="styles.riskBadge"
              :style="{ backgroundColor: store.riskColor }"
            >
              {{ store.riskLabel }}
            </div>
            <div :class="styles.scoreDisplay">
              Score: {{ store.feasibility.overall_score.toFixed(1) }}
            </div>
            <div :class="styles.statusFlags">
              <span
                v-if="store.feasibility.is_feasible"
                :class="shared.flagGood"
              >✓ Feasible</span>
              <span
                v-else
                :class="shared.flagBad"
              >✗ Not Feasible</span>

              <span
                v-if="store.feasibility.needs_review"
                :class="shared.flagWarning"
              >⚠ Needs Review</span>
            </div>
          </section>

          <!-- Recommendations -->
          <section
            v-if="store.feasibility.recommendations.length > 0"
            :class="styles.recommendations"
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
          <section :class="styles.fretboardPreview">
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
          <section :class="shared.statsGrid">
            <div :class="shared.statCard">
              <div :class="shared.statLabel">
                Total Time
              </div>
              <div :class="shared.statValue">
                {{ formatTime(store.statistics.total_time_s) }}
              </div>
            </div>

            <div :class="shared.statCard">
              <div :class="shared.statLabel">
                Total Cost
              </div>
              <div :class="shared.statValue">
                ${{ store.statistics.total_cost_usd.toFixed(2) }}
              </div>
            </div>

            <div :class="shared.statCard">
              <div :class="shared.statLabel">
                Energy
              </div>
              <div :class="shared.statValue">
                {{ store.statistics.total_energy_kwh.toFixed(3) }} kWh
              </div>
            </div>

            <div :class="shared.statCard">
              <div :class="shared.statLabel">
                Cut Length
              </div>
              <div :class="shared.statValue">
                {{ store.statistics.total_length_mm.toFixed(1) }} mm
              </div>
            </div>
          </section>

          <!-- DXF/G-code Previews -->
          <section :class="styles.codePreviews">
            <div :class="styles.previewColumn">
              <h4>DXF Preview</h4>
              <pre :class="shared.codePreview">{{
                store.previewResponse.dxf_preview
              }}</pre>
              <button
                :class="shared.btnSecondary"
                @click="store.downloadDxf"
              >
                📥 Download DXF
              </button>
            </div>

            <div :class="styles.previewColumn">
              <h4>G-code Preview</h4>
              <pre :class="shared.codePreview">{{
                store.previewResponse.gcode_preview
              }}</pre>
              <button
                :class="shared.btnSecondary"
                @click="store.downloadGcode"
              >
                📥 Download G-code
              </button>
            </div>
          </section>

          <!-- Toolpath Details Table -->
          <section :class="styles.toolpathTable">
            <h4>Toolpath Details ({{ store.toolpaths.length }} slots)</h4>
            <div :class="shared.tableWrapper">
              <table :class="styles.table">
                <thead :class="styles.tableHead">
                  <tr>
                    <th :class="styles.th">Fret #</th>
                    <th :class="styles.th">Position (mm)</th>
                    <th :class="styles.th">Width (mm)</th>
                    <th :class="styles.th">Depth (mm)</th>
                    <th :class="styles.th">Feed (mm/min)</th>
                    <th :class="styles.th">RPM</th>
                    <th :class="styles.th">Time (s)</th>
                    <th :class="styles.th">Cost ($)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="tp in store.toolpaths"
                    :key="tp.fret_number"
                    :class="[styles.tableRow, tp.fret_number % 12 === 0 && styles.rowHighlight]"
                  >
                    <td :class="styles.td">{{ tp.fret_number }}</td>
                    <td :class="styles.td">{{ tp.position_mm.toFixed(2) }}</td>
                    <td :class="styles.td">{{ tp.width_mm.toFixed(2) }}</td>
                    <td :class="styles.td">{{ tp.depth_mm.toFixed(2) }}</td>
                    <td :class="styles.td">{{ tp.feed_rate }}</td>
                    <td :class="styles.td">{{ tp.spindle_rpm }}</td>
                    <td :class="styles.td">{{ tp.cut_time_s.toFixed(1) }}</td>
                    <td :class="styles.td">{{ tp.cost_usd.toFixed(3) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <!-- Empty State -->
        <div
          v-else
          :class="shared.emptyState"
        >
          <div :class="shared.emptyIcon">
            🎸
          </div>
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
import styles from "./InstrumentGeometryPanel.module.css";
import shared from "@/styles/dark-theme-shared.module.css";

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
