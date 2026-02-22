<script setup lang="ts">
import { onMounted } from 'vue'
import LoopsPreviewSvg from './adaptive_kernel/LoopsPreviewSvg.vue'
import KernelOutputPanel from './adaptive_kernel/KernelOutputPanel.vue'

import {
  useAdaptiveKernelState,
  useAdaptiveKernelPayload,
  useAdaptiveKernelPipeline,
  useAdaptiveKernelPreview
} from './adaptive_kernel/composables'

// State
const {
  units,
  toolD,
  stepover,
  stepdown,
  margin,
  strategy,
  feedXY,
  safeZ,
  zRough,
  cornerRadiusMin,
  targetStepover,
  slowdownFeedPct,
  useTrochoids,
  trochoidRadius,
  trochoidPitch,
  loopsText,
  lastRequest,
  result,
  errorMsg,
  busy,
  showPipelineSnippet,
  sentToPipeline,
  showToolpathPreview
} = useAdaptiveKernelState()

// Payload
const { loadDemoLoops, buildPayload, runAdaptive } = useAdaptiveKernelPayload(
  loopsText,
  units,
  toolD,
  stepover,
  stepdown,
  margin,
  strategy,
  feedXY,
  safeZ,
  zRough,
  cornerRadiusMin,
  targetStepover,
  slowdownFeedPct,
  useTrochoids,
  trochoidRadius,
  trochoidPitch,
  lastRequest,
  result,
  errorMsg,
  busy
)

// Pipeline
const { pipelineSnippet, sendToPipelineLab } = useAdaptiveKernelPipeline(
  buildPayload,
  sentToPipeline,
  errorMsg
)

// Preview
const { previewLoops, previewOverlays, viewBox, previewToolpathSegments } =
  useAdaptiveKernelPreview(loopsText, result)

// Initialize with demo loops on mount
onMounted(() => {
  if (!loopsText.value) {
    loadDemoLoops()
  }
})
</script>

<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold">
      Adaptive Kernel Dev Lab
    </h1>
    <p class="text-sm text-gray-600">
      Direct playground for
      <code>/api/cam/pocket/adaptive/plan</code>. Edit loops, adjust parameters,
      inspect stats, and view overlays before wiring into the unified pipeline.
    </p>

    <!-- Controls -->
    <section class="border rounded p-4 bg-white space-y-4">
      <div class="flex items-center justify-between gap-2">
        <h2 class="font-semibold text-lg">
          Parameters
        </h2>
        <button
          class="border rounded px-3 py-1 text-xs hover:bg-gray-50"
          type="button"
          @click="loadDemoLoops"
        >
          Load Demo Rectangle
        </button>
      </div>

      <div class="grid gap-3 md:grid-cols-4 text-sm">
        <label class="flex flex-col gap-1">
          Units
          <select
            v-model="units"
            class="border rounded px-2 py-1"
          >
            <option value="mm">mm</option>
            <option value="inch">inch</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          Tool Ø
          <input
            v-model.number="toolD"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Stepover
          <input
            v-model.number="stepover"
            type="number"
            step="0.01"
            class="border rounded px-2 py-1"
          >
          <span class="text-[10px] text-gray-500">fraction of tool_d</span>
        </label>
        <label class="flex flex-col gap-1">
          Stepdown
          <input
            v-model.number="stepdown"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Margin
          <input
            v-model.number="margin"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Strategy
          <select
            v-model="strategy"
            class="border rounded px-2 py-1"
          >
            <option value="Spiral">Spiral</option>
            <option value="Lanes">Lanes</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          Feed XY
          <input
            v-model.number="feedXY"
            type="number"
            step="10"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Safe Z
          <input
            v-model.number="safeZ"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Rough Z
          <input
            v-model.number="zRough"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
      </div>

      <div class="grid gap-3 md:grid-cols-4 text-sm pt-2">
        <label class="flex flex-col gap-1">
          Corner R min
          <input
            v-model.number="cornerRadiusMin"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Target stepover
          <input
            v-model.number="targetStepover"
            type="number"
            step="0.01"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Slowdown feed %
          <input
            v-model.number="slowdownFeedPct"
            type="number"
            step="1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex items-center gap-2 mt-6 text-sm">
          <input
            v-model="useTrochoids"
            type="checkbox"
          >
          Use trochoids
        </label>
        <label class="flex flex-col gap-1">
          Trochoid R
          <input
            v-model.number="trochoidRadius"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
        <label class="flex flex-col gap-1">
          Trochoid pitch
          <input
            v-model.number="trochoidPitch"
            type="number"
            step="0.1"
            class="border rounded px-2 py-1"
          >
        </label>
      </div>

      <button
        class="border rounded px-4 py-2 text-sm font-semibold hover:bg-gray-50"
        :disabled="busy"
        type="button"
        @click="runAdaptive"
      >
        {{ busy ? "Running..." : "Run Adaptive Kernel" }}
      </button>

      <p
        v-if="errorMsg"
        class="text-sm text-red-600"
      >
        {{ errorMsg }}
      </p>
    </section>

    <!-- Loops JSON editor + preview -->
    <section class="border rounded p-4 bg-white space-y-4">
      <h2 class="font-semibold text-lg">
        Loops & Overlays
      </h2>
      <div class="grid gap-4 md:grid-cols-2">
        <div class="flex flex-col gap-2 text-sm">
          <label class="font-semibold">Loops JSON</label>
          <p class="text-[11px] text-gray-500">
            Array of <code>{ pts: [[x,y], ...] }</code>. Demo button above
            fills in a rectangular pocket with an island.
          </p>
          <textarea
            v-model="loopsText"
            class="border rounded px-2 py-1 text-xs font-mono min-h-[220px]"
          />
        </div>

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label class="font-semibold text-sm">2D Preview</label>
            <div class="flex items-center gap-3 text-[11px] text-gray-600">
              <label class="inline-flex items-center gap-1">
                <input
                  v-model="showToolpathPreview"
                  type="checkbox"
                >
                <span>Show toolpath preview</span>
              </label>
            </div>
          </div>
          <div
            class="border rounded bg-gray-50 flex items-center justify-center min-h-[220px]"
          >
            <LoopsPreviewSvg
              v-if="previewLoops.length"
              :preview-loops="previewLoops"
              :view-box="viewBox"
              :show-toolpath-preview="showToolpathPreview"
              :toolpath-segments="previewToolpathSegments"
              :overlays="previewOverlays"
            />
            <div
              v-else
              class="text-xs text-gray-500"
            >
              No loops to display. Load demo or paste JSON.
            </div>
          </div>

          <div class="flex gap-3 text-[11px] text-gray-500">
            <div class="inline-flex items-center gap-1">
              <span class="inline-block w-4 h-[2px] bg-[#0f766e]" />
              <span>Boundary loops</span>
            </div>
            <div class="inline-flex items-center gap-1">
              <span class="inline-block w-4 h-[2px] bg-[#1d4ed8]" />
              <span>Cut moves</span>
            </div>
            <div class="inline-flex items-center gap-1">
              <span
                class="inline-block w-4 h-[2px]"
                style="border-bottom:1px dashed #9ca3af"
              />
              <span>Rapid moves</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats + raw JSON -->
    <KernelOutputPanel
      v-if="result"
      :result="result"
      :last-request="lastRequest"
    />

    <!-- Pipeline op export -->
    <section class="border rounded p-4 bg-white space-y-2">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold text-lg">
          Export as Pipeline Op
        </h2>
        <label class="flex items-center gap-2 text-sm">
          <input
            v-model="showPipelineSnippet"
            type="checkbox"
          >
          <span>Show pipeline snippet</span>
        </label>
      </div>

      <p class="text-xs text-gray-600">
        When enabled, this shows a ready-to-paste JSON skeleton for
        <code>/api/pipeline/run</code> using an
        <code>AdaptivePocket</code> op. Update
        <code>dxf_path</code>, <code>machine_profile_id</code>, and
        <code>workspace_id</code> per job.
      </p>

      <div
        v-if="showPipelineSnippet"
        class="space-y-2"
      >
        <textarea
          readonly
          class="border rounded px-2 py-1 text-xs font-mono w-full min-h-[180px] bg-gray-50"
        >{{ pipelineSnippet }}</textarea>

        <div class="flex items-center justify-between mt-1">
          <button
            type="button"
            class="border rounded px-3 py-1 text-xs font-semibold hover:bg-gray-50"
            @click="sendToPipelineLab"
          >
            Send to PipelineLab
          </button>
          <span
            v-if="sentToPipeline"
            class="text-[11px] text-green-600"
          >
            Preset sent. Open <code>/lab/pipeline</code> to use it.
          </span>
        </div>
      </div>
    </section>
  </div>
</template>
