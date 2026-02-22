<script setup lang="ts">
/**
 * ArtStudioHeadstock - Headstock logo engraving pipeline view.
 *
 * Features:
 * - Adaptive pocketing, helical entry, post, simulation
 * - Full risk + geometry history
 *
 * REFACTORED: Uses composables for cleaner separation of concerns.
 */
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import CamPipelineRunner from '@/components/cam/CamPipelineRunner.vue'
import CamIssuesList from '@/components/cam/CamIssuesList.vue'

import type { PipelineRunIn, PipelineRunOut } from '@/api/pipeline'
import type { SimIssue } from '@/types/cam'

import {
  HEADSTOCK_OPS,
  useHeadstockState,
  useHeadstockRisk,
  useHeadstockNotes
} from './composables'

// =============================================================================
// COMPOSABLES
// =============================================================================

// State
const {
  headstockDxfPath,
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
  backplotMoves,
  backplotOverlays,
  simIssues
} = useHeadstockState()

// Risk
const { handleRunSuccess } = useHeadstockRisk(
  headstockDxfPath,
  results,
  selectedPathOpId,
  selectedOverlayOpId,
  focusPoint,
  selectedIssueIndex,
  lastRiskAnalytics,
  lastRiskReportError,
  lastRiskReportId,
  noteEditorVisible,
  noteDraft,
  noteSaveError
)

// Notes
const { openNoteEditor, cancelNoteEditor, saveNote } = useHeadstockNotes(
  lastRiskReportId,
  noteEditorVisible,
  noteDraft,
  noteSaving,
  noteSaveError
)

// =============================================================================
// HANDLERS
// =============================================================================

function handleRun(_payload: PipelineRunIn): void {
  // optional no-op
}

function handleRunError(_payload: PipelineRunIn, _err: string): void {
  // optional
}

function handleIssueFocusRequest(payload: { index: number; issue: SimIssue }): void {
  selectedIssueIndex.value = payload.index
  focusPoint.value = {
    x: payload.issue.x,
    y: payload.issue.y
  }
}
</script>

<template>
  <div class="p-6 space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Art Studio – Headstock Logo
      </h1>
      <p class="text-sm text-gray-600">
        Headstock logo engraving pipeline with adaptive pocketing, helical entry, post, simulation,
        and full risk + geometry history.
      </p>
      <div class="text-xs text-gray-500">
        Design DXF:
        <span class="font-mono">{{ headstockDxfPath }}</span>
      </div>
    </header>

    <!-- Pipeline runner -->
    <section class="border rounded bg-white p-4 space-y-3">
      <CamPipelineRunner
        :default-design="{
          source: 'dxf',
          dxf_path: headstockDxfPath,
        }"
        :default-ops="HEADSTOCK_OPS"
        :show-gcode="true"
        :show-results="true"
        @run="handleRun"
        @run-success="handleRunSuccess"
        @run-error="handleRunError"
      >
        <template #toolbar>
          <span class="text-[11px] text-gray-500">
            Tune tool, depth, and feeds; this view will log every run to the Job Risk Timeline.
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
          placeholder="Example: Tweaked logo depth to -0.6 mm and slowed feed near nut after small chatter on prior run."
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
          :focus-zoom="0.45"
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
