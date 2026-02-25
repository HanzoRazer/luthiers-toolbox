<script setup lang="ts">
/**
 * ArtStudioRelief - Relief carving pipeline view.
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import { onMounted } from 'vue'
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import CamPipelineRunner from '@/components/cam/CamPipelineRunner.vue'
import CamIssuesList from '@/components/cam/CamIssuesList.vue'
import type { PipelineOp } from '@/api/pipeline'

import {
  useArtStudioReliefState,
  useArtStudioReliefBackplot,
  useArtStudioReliefRisk,
  useArtStudioReliefPresets,
  useArtStudioReliefPipeline,
  type LocalPresetPayload
} from './art_studio_relief/composables'

// =============================================================================
// RELIEF PIPELINE OPS
// =============================================================================

const reliefOps: PipelineOp[] = [
  {
    id: 'relief_map',
    op: 'ReliefMapFromHeightfield',
    input: {
      heightmap_path: 'workspace/art/relief/demo_relief_heightmap.png',
      units: 'mm',
      z_min: 0.0,
      z_max: -3.0,
      sample_pitch_xy: 0.3,
      smooth_sigma: 0.4
    }
  } as any,
  {
    id: 'relief_rough',
    op: 'ReliefRoughing',
    from_op: 'relief_map',
    input: {
      tool_d: 3.0,
      stepdown: 0.7,
      stepover: 0.6,
      safe_z: 4.0,
      z_clearance: 1.0,
      feed_xy: 800.0,
      feed_z: 300.0
    }
  } as any,
  {
    id: 'relief_finish',
    op: 'ReliefFinishing',
    from_op: 'relief_map',
    input: {
      tool_d: 2.0,
      scallop_height: 0.06,
      stepdown: 0.4,
      safe_z: 4.0,
      feed_xy: 600.0,
      feed_z: 250.0,
      pattern: 'RasterX'
    }
  } as any,
  {
    id: 'relief_post',
    op: 'PostProcess',
    from_op: 'relief_finish',
    input: {
      post_preset: 'GRBL'
    }
  } as any,
  {
    id: 'relief_sim',
    op: 'Simulate',
    from_op: 'relief_post',
    input: {
      stock_thickness: 5.0
    }
  } as any
]

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  reliefHeightmapPath,
  results,
  selectedPathOpId,
  selectedOverlayOpId,
  showToolpath,
  focusPoint,
  selectedIssueIndex,
  backplotLoops,
  lastRiskAnalytics,
  lastRiskReportError,
  lastRiskReportId,
  noteEditorVisible,
  noteDraft,
  noteSaving,
  noteSaveError,
  activePresetName,
  activePresetConfig
} = useArtStudioReliefState()

// Backplot computed values
const { backplotMoves, backplotOverlays, simIssues } = useArtStudioReliefBackplot(
  results,
  selectedPathOpId,
  selectedOverlayOpId
)

// Risk analytics
const { computeRiskAnalytics, buildReliefBackplotSnapshot } = useArtStudioReliefRisk(
  results,
  selectedPathOpId,
  selectedOverlayOpId
)

// Presets
const { loadReliefPresetFromStorage, applyLocalPreset, reloadLabPreset } =
  useArtStudioReliefPresets(activePresetName, activePresetConfig, reliefOps)

// Pipeline handlers
const {
  handleRun,
  handleRunSuccess,
  handleRunError,
  openNoteEditor,
  cancelNoteEditor,
  saveNote,
  handleIssueFocusRequest
} = useArtStudioReliefPipeline(
  reliefHeightmapPath,
  results,
  focusPoint,
  selectedIssueIndex,
  lastRiskAnalytics,
  lastRiskReportError,
  lastRiskReportId,
  noteEditorVisible,
  noteDraft,
  noteSaving,
  noteSaveError,
  computeRiskAnalytics,
  buildReliefBackplotSnapshot
)

// =============================================================================
// LIFECYCLE
// =============================================================================

onMounted(() => {
  loadReliefPresetFromStorage(false)
})
</script>

<template>
  <div class="p-6 space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Art Studio – Relief Carving
      </h1>
      <p class="text-sm text-gray-600">
        Relief carving pipeline from heightmap to roughing, finishing, post, and simulation,
        with full risk and geometry history.
      </p>
      <div class="text-xs text-gray-500">
        Heightmap:
        <span class="font-mono">{{ reliefHeightmapPath }}</span>
      </div>
      
      <!-- Preset controls -->
      <section class="mt-2 flex flex-wrap items-center gap-3">
        <button
          type="button"
          class="text-xs px-2 py-1 border rounded bg-white hover:bg-gray-50"
          @click="reloadLabPreset"
        >
          Reload Lab preset
        </button>

        <p
          v-if="activePresetName"
          class="text-xs text-gray-500"
        >
          Active preset:
          <span class="font-semibold">{{ activePresetName }}</span>
        </p>
      </section>
    </header>

    <!-- Relief pipeline runner -->
    <section class="border rounded bg-white p-4 space-y-3">
      <CamPipelineRunner
        :default-design="{
          source: 'heightmap',
          heightmap_path: reliefHeightmapPath,
        }"
        :default-ops="reliefOps"
        :show-gcode="true"
        :show-results="true"
        @run="handleRun"
        @run-success="handleRunSuccess"
        @run-error="handleRunError"
      >
        <template #toolbar>
          <span class="text-[11px] text-gray-500">
            Use this lane to prototype relief strategies; every run will log a snapshot into the Job Risk Timeline.
          </span>
        </template>
      </CamPipelineRunner>

      <!-- Risk summary line -->
      <div
        v-if="lastRiskAnalytics || lastRiskReportError"
        class="text-[11px] mt-2 flex flex-wrap items-center justify-between gap-2"
      >
        <div
          v-if="lastRiskAnalytics"
          class="text-gray-600"
        >
          Risk score:
          <span class="font-semibold">
            {{ lastRiskAnalytics.risk_score.toFixed(1) }}
          </span>
          · Extra time:
          <span class="font-semibold">
            {{ lastRiskAnalytics.total_extra_time_human }}
          </span>
          · Issues:
          <span class="font-semibold">
            {{ lastRiskAnalytics.total_issues }}
          </span>
          <span
            v-if="lastRiskReportId"
            class="ml-2 text-gray-400"
          >
            (snapshot {{ lastRiskReportId.slice(0, 8) }}…)
          </span>
        </div>
        <div
          v-if="lastRiskReportError"
          class="text-red-600"
        >
          {{ lastRiskReportError }}
        </div>
      </div>
    </section>

    <!-- Snapshot notes -->
    <section
      v-if="lastRiskReportId"
      class="border rounded p-3 bg-white text-[11px] space-y-2"
    >
      <div class="flex items-center justify-between">
        <span class="font-semibold text-gray-700">
          Snapshot notes
        </span>
        <button
          type="button"
          class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
          @click="openNoteEditor"
        >
          Attach / edit note
        </button>
      </div>

      <div
        v-if="noteEditorVisible"
        class="space-y-2 mt-1"
      >
        <textarea
          v-model="noteDraft"
          rows="3"
          class="w-full border rounded px-2 py-1 text-[11px] font-mono"
          placeholder="Example: Switched to RasterX finishing, reduced scallop height, slowed feed in high curvature zones."
        />
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-white hover:bg-gray-100"
            :disabled="noteSaving"
            @click="cancelNoteEditor"
          >
            Cancel
          </button>
          <button
            type="button"
            class="border rounded px-2 py-0.5 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300"
            :disabled="noteSaving"
            @click="saveNote"
          >
            {{ noteSaving ? "Saving…" : "Save note" }}
          </button>
        </div>
        <div
          v-if="noteSaveError"
          class="text-[10px] text-red-600"
        >
          {{ noteSaveError }}
        </div>
      </div>
    </section>

    <!-- Backplot + issues -->
    <section
      v-if="results"
      class="border rounded p-4 bg-white space-y-3"
    >
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">
          Backplot & Issues
        </h2>
        <div class="flex items-center gap-2 text-[11px] text-gray-600">
          <label class="flex items-center gap-1">
            <input
              v-model="showToolpath"
              type="checkbox"
              class="align-middle"
            >
            <span>Show toolpath</span>
          </label>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <CamBackplotViewer
          v-model:show-toolpath="showToolpath"
          :loops="backplotLoops"
          :moves="backplotMoves"
          :overlays="backplotOverlays"
          :focus-point="focusPoint"
          :focus-zoom="0.4"
        />

        <CamIssuesList
          v-model:selected-index="selectedIssueIndex"
          :issues="simIssues"
          title="Simulation Issues"
          @focus-request="handleIssueFocusRequest"
        />
      </div>
    </section>
  </div>
</template>
