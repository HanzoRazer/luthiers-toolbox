<template>
  <div :class="shared.pageDark">
    <div :class="styles.header">
      <h1>Nut Slot CAM Preview</h1>
      <p :class="styles.subtitle">
        Toolpath visualization (experimental, no export)
      </p>
    </div>

    <div :class="styles.layout">
      <!-- ===== LEFT: Input Panel ===== -->
      <div :class="styles.inputPanel">
        <section :class="shared.controlSection">
          <div :class="styles.sectionHeader">
            <h3>Parameters</h3>
            <button
              :class="styles.defaultsBtn"
              @click="store.loadDefaults"
            >
              Load Defaults
            </button>
          </div>

          <!-- Nut Dimensions -->
          <div :class="shared.inputRow">
            <label>Nut Width</label>
            <input
              v-model.number="store.nutWidthMm"
              type="number"
              step="0.5"
              min="20"
              max="60"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Strings</label>
            <input
              v-model.number="store.numStrings"
              type="number"
              step="1"
              min="1"
              max="12"
              :class="shared.inputNumber"
            >
          </div>

          <div :class="shared.inputRow">
            <label>Edge Offset (Treble)</label>
            <input
              v-model.number="store.edgeOffsetTrebleMm"
              type="number"
              step="0.1"
              min="0"
              max="10"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Edge Offset (Bass)</label>
            <input
              v-model.number="store.edgeOffsetBassMm"
              type="number"
              step="0.1"
              min="0"
              max="10"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <!-- Slot Dimensions -->
          <h4 :class="styles.subheader">Slot Geometry</h4>

          <div :class="shared.inputRow">
            <label>Slot Length</label>
            <input
              v-model.number="store.slotLengthMm"
              type="number"
              step="0.5"
              min="1"
              max="10"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Slot Depth</label>
            <input
              v-model.number="store.slotDepthMm"
              type="number"
              step="0.1"
              min="0.1"
              max="5"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Slot Width</label>
            <input
              v-model.number="store.slotWidthMm"
              type="number"
              step="0.01"
              min="0.1"
              max="2"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <!-- Stock & Tool -->
          <h4 :class="styles.subheader">Stock & Tool</h4>

          <div :class="shared.inputRow">
            <label>Stock Thickness</label>
            <input
              v-model.number="store.stockThicknessMm"
              type="number"
              step="0.5"
              min="2"
              max="15"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Tool Diameter</label>
            <input
              v-model.number="store.toolDiameterMm"
              type="number"
              step="0.01"
              min="0.1"
              max="2"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <div :class="shared.inputRow">
            <label>Safe Z</label>
            <input
              v-model.number="store.safeZMm"
              type="number"
              step="0.5"
              min="1"
              max="20"
              :class="shared.inputNumber"
            >
            <span :class="shared.unit">mm</span>
          </div>

          <!-- Generate Button -->
          <button
            :disabled="store.previewLoading"
            :class="shared.btnLarge"
            @click="store.generatePreview"
          >
            <span v-if="store.previewLoading">Generating...</span>
            <span v-else>Generate Preview</span>
          </button>

          <!-- Error -->
          <div
            v-if="store.previewError"
            :class="shared.bannerError"
          >
            {{ store.previewError }}
          </div>
        </section>
      </div>

      <!-- ===== RIGHT: Preview Panel ===== -->
      <div :class="styles.previewPanel">
        <!-- Gate Banner -->
        <div
          v-if="store.hasPreview"
          :class="styles.gateBanner"
          :style="{ backgroundColor: store.gateBgColor, borderColor: store.gateColor }"
        >
          <span
            :class="styles.gateBadge"
            :style="{ backgroundColor: store.gateBgColor, color: store.gateTextColor }"
          >
            {{ store.gate?.toUpperCase() }}
          </span>
          <span :class="styles.gateLabel">
            {{ gateMessage }}
          </span>
        </div>

        <!-- SVG Preview -->
        <div
          v-if="store.hasPreview"
          :class="styles.svgContainer"
          :style="{ borderColor: store.gateColor }"
        >
          <svg
            :viewBox="svgViewBox"
            :class="styles.svg"
            preserveAspectRatio="xMidYMid meet"
          >
            <!-- Background -->
            <rect
              :x="0"
              :y="0"
              :width="store.nutWidthMm"
              :height="store.slotLengthMm"
              fill="#1a1a2e"
              stroke="#333"
              stroke-width="0.2"
            />

            <!-- Slot paths -->
            <g v-for="tp in store.toolpaths" :key="tp.slot_index">
              <line
                :x1="tp.x_mm"
                :y1="0"
                :x2="tp.x_mm"
                :y2="store.slotLengthMm"
                :stroke="store.gateColor"
                :stroke-width="Math.max(tp.slot_width_mm, 0.3)"
                stroke-linecap="round"
              />
              <!-- Slot number label -->
              <text
                :x="tp.x_mm"
                :y="-0.8"
                :class="styles.slotLabel"
                text-anchor="middle"
                :font-size="fontSize"
                fill="#888"
              >
                {{ tp.string_number }}
              </text>
            </g>

            <!-- Nut outline -->
            <rect
              :x="0"
              :y="0"
              :width="store.nutWidthMm"
              :height="store.slotLengthMm"
              fill="none"
              stroke="#666"
              stroke-width="0.3"
            />
          </svg>

          <div :class="styles.axisLabels">
            <span>X: string-to-string (mm)</span>
            <span>Y: slot length (mm)</span>
          </div>
        </div>

        <!-- Statistics -->
        <div
          v-if="store.statistics"
          :class="styles.statsGrid"
        >
          <div :class="styles.statCard">
            <div :class="styles.statLabel">Total Slots</div>
            <div :class="styles.statValue">{{ store.statistics.total_slots }}</div>
          </div>
          <div :class="styles.statCard">
            <div :class="styles.statLabel">Max Depth</div>
            <div :class="styles.statValue">{{ store.statistics.max_depth_mm.toFixed(2) }} mm</div>
          </div>
          <div :class="styles.statCard">
            <div :class="styles.statLabel">Tool</div>
            <div :class="styles.statValue">{{ store.toolDiameterMm }} mm</div>
          </div>
          <div :class="styles.statCard">
            <div :class="styles.statLabel">Safe Z</div>
            <div :class="styles.statValue">{{ store.safeZMm }} mm</div>
          </div>
        </div>

        <!-- Warnings -->
        <div
          v-if="store.warnings.length > 0"
          :class="styles.messageSection"
        >
          <h4 :class="styles.messageSectionTitle">
            <span :class="styles.warningIcon">&#9888;</span>
            Warnings ({{ store.warnings.length }})
          </h4>
          <ul :class="styles.messageList">
            <li
              v-for="(warning, idx) in store.warnings"
              :key="idx"
              :class="styles.warningItem"
            >
              {{ warning }}
            </li>
          </ul>
        </div>

        <!-- Errors -->
        <div
          v-if="store.errors.length > 0"
          :class="styles.messageSection"
        >
          <h4 :class="styles.messageSectionTitle">
            <span :class="styles.errorIcon">&#10006;</span>
            Errors ({{ store.errors.length }})
          </h4>
          <ul :class="styles.messageList">
            <li
              v-for="(error, idx) in store.errors"
              :key="idx"
              :class="styles.errorItem"
            >
              {{ error }}
            </li>
          </ul>
        </div>

        <!-- Empty State -->
        <div
          v-if="!store.hasPreview && !store.previewLoading"
          :class="styles.emptyState"
        >
          <div :class="styles.emptyIcon">&#9881;</div>
          <h3>No Preview Generated</h3>
          <p>Configure parameters and click "Generate Preview" to visualize toolpaths.</p>
        </div>

        <!-- Loading State -->
        <div
          v-if="store.previewLoading"
          :class="styles.loadingState"
        >
          <div :class="shared.spinner" />
          <p>Generating toolpath preview...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useNutSlotCamStore } from "@/stores/useNutSlotCamStore";
import shared from "@/styles/dark-theme-shared.module.css";
import styles from "./NutSlotPreviewView.module.css";

const store = useNutSlotCamStore();

const svgViewBox = computed(() => {
  const padding = 2;
  const width = store.nutWidthMm + padding * 2;
  const height = store.slotLengthMm + padding * 2;
  return `${-padding} ${-padding} ${width} ${height}`;
});

const fontSize = computed(() => {
  return Math.max(0.8, store.nutWidthMm / 40);
});

const gateMessage = computed(() => {
  switch (store.gate) {
    case "green":
      return "Preview safe — all parameters within bounds";
    case "yellow":
      return "Preview has warnings — review before proceeding";
    case "red":
      return "Preview blocked — unsafe parameters detected";
    default:
      return "";
  }
});
</script>
