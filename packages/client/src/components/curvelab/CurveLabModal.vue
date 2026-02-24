<template>
  <teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      @click.self="close"
    >
      <div class="w-full max-w-5xl rounded-2xl bg-white p-6 shadow-2xl">
        <header class="mb-6 flex items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-wide text-emerald-600">
              CurveLab
            </p>
            <h2 class="text-xl font-semibold">
              DXF Preflight + Auto-Fix
            </h2>
            <p class="text-sm text-slate-500">
              Validate inline CurveLab geometry or uploaded DXF files before CAM export.
            </p>
          </div>
          <button
            class="rounded-full border border-slate-200 p-2 text-slate-500 hover:bg-slate-50"
            type="button"
            aria-label="Close CurveLab modal"
            @click="close"
          >
            ✕
          </button>
        </header>

        <div class="grid gap-6 lg:grid-cols-2">
          <!-- Inline CurveLab Geometry Preflight -->
          <InlineGeometryReport
            :tolerance="tolerance"
            :layer="layer"
            :inline-point-count="inlinePointCount"
            :has-inline-geometry="hasInlineGeometry"
            :inline-busy="inlineBusy"
            :inline-response="inlineResponse"
            :inline-error="inlineError"
            :inline-cam-ready-label="inlineCamReadyLabel"
            :inline-cam-ready-class="inlineCamReadyClass"
            @update:tolerance="tolerance = $event"
            @update:layer="layer = $event"
            @run-report="runInlineReport"
            @download-json="downloadInlineJson"
          />

          <!-- DXF Validation + Auto Fix -->
          <DxfValidationPanel
            :filename="filename"
            :has-dxf="hasDxf"
            :file-busy="fileBusy"
            :file-response="fileResponse"
            :file-error="fileError"
            :auto-fix-busy="autoFixBusy"
            :fixed-download="fixedDownload"
            :selected-fixes="selectedFixes"
            :file-cam-ready-label="fileCamReadyLabel"
            :file-cam-ready-class="fileCamReadyClass"
            :fix-options="fixOptions"
            @update:selected-fixes="selectedFixes = $event"
            @run-validation="runFileValidation"
            @run-autofix="runAutoFix"
            @download-fixed="downloadFixedDxf"
            @download-json="downloadFileJson"
          />
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import type { CurveBiarcEntity, CurveUnits } from '@/types/curvelab'
import InlineGeometryReport from './InlineGeometryReport.vue'
import DxfValidationPanel from './DxfValidationPanel.vue'
import {
  FIX_OPTIONS,
  useCurveLabState,
  useCurveLabInline,
  useCurveLabFile,
  useCurveLabDownload
} from './composables'

const props = defineProps({
  open: { type: Boolean, default: false },
  points: {
    type: Array as () => Array<[number, number]>,
    default: () => []
  },
  units: {
    type: String as () => CurveUnits,
    default: 'mm'
  },
  layer: {
    type: String,
    default: 'CURVE'
  },
  biarcEntities: {
    type: Array as () => CurveBiarcEntity[] | null,
    default: () => []
  },
  dxfBase64: {
    type: String,
    default: null
  },
  filename: {
    type: String,
    default: 'curve_preview.dxf'
  }
})

const emit = defineEmits(['close', 'update:open', 'auto-fix'])

// State
const {
  tolerance,
  layer,
  inlineBusy,
  inlineResponse,
  inlineError,
  fileBusy,
  fileResponse,
  fileError,
  autoFixBusy,
  fixedDownload,
  selectedFixes,
  workingDxf,
  inlinePoints,
  hasInlineGeometry,
  inlinePointCount,
  hasDxf,
  inlineCamReadyLabel,
  inlineCamReadyClass,
  fileCamReadyLabel,
  fileCamReadyClass
} = useCurveLabState(props)

// Constants
const fixOptions = FIX_OPTIONS

// Inline report
const { runInlineReport } = useCurveLabInline(
  inlinePoints,
  hasInlineGeometry,
  props.units,
  tolerance,
  layer,
  props.biarcEntities,
  inlineBusy,
  inlineResponse,
  inlineError
)

// File validation
const { runFileValidation, runAutoFix } = useCurveLabFile(
  props.filename,
  hasDxf,
  workingDxf,
  selectedFixes,
  fileBusy,
  fileResponse,
  fileError,
  autoFixBusy,
  fixedDownload,
  (event, payload) => emit(event, payload)
)

// Downloads
const { downloadInlineJson, downloadFileJson, downloadFixedDxf } = useCurveLabDownload(
  props.filename,
  inlineResponse,
  fileResponse,
  fixedDownload
)

// Modal actions
function close() {
  emit('update:open', false)
  emit('close')
}
</script>
