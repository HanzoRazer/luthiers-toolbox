<script setup lang="ts">
/**
 * InlineGeometryReport - Inline CurveLab geometry preflight report
 * Extracted from CurveLabModal.vue
 *
 * Runs /dxf/preflight/curve_report using current CurveLab points.
 */
import type { CurvePreflightResponse } from './composables/curveLabTypes'

defineProps<{
  tolerance: number
  layer: string
  inlinePointCount: number
  hasInlineGeometry: boolean
  inlineBusy: boolean
  inlineResponse: CurvePreflightResponse | null
  inlineError: string | null
  inlineCamReadyLabel: string | null
  inlineCamReadyClass: string
}>()

const emit = defineEmits<{
  'update:tolerance': [value: number]
  'update:layer': [value: string]
  'run-report': []
  'download-json': []
}>()

// Helpers
function formatNumber(num: number | null | undefined): string {
  if (num == null) return '—'
  return Number(num).toLocaleString(undefined, { maximumFractionDigits: 3 })
}

function severityClass(severity: string): string {
  switch (severity) {
    case 'error':
      return 'text-rose-600 font-semibold'
    case 'warning':
      return 'text-amber-600'
    default:
      return 'text-slate-600'
  }
}
</script>

<template>
  <section class="rounded-xl border bg-slate-50/70 p-4">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold">
          Inline Geometry Report
        </h3>
        <p class="text-xs text-slate-500">
          Runs <code class="rounded bg-white px-1 py-0.5">/dxf/preflight/curve_report</code> using current CurveLab points.
        </p>
      </div>
      <span
        v-if="inlineCamReadyLabel"
        class="rounded-full px-3 py-1 text-xs font-semibold"
        :class="inlineCamReadyClass"
      >
        {{ inlineCamReadyLabel }}
      </span>
    </div>

    <div class="mb-4 flex flex-wrap gap-3 text-sm">
      <label class="flex items-center gap-2">
        Tolerance (mm)
        <input
          :value="tolerance"
          type="number"
          min="0.001"
          step="0.01"
          class="w-24 rounded border px-2 py-1"
          @input="emit('update:tolerance', parseFloat(($event.target as HTMLInputElement).value))"
        >
      </label>
      <label class="flex items-center gap-2">
        Layer
        <input
          :value="layer"
          type="text"
          class="w-32 rounded border px-2 py-1"
          @input="emit('update:layer', ($event.target as HTMLInputElement).value)"
        >
      </label>
      <span class="flex items-center gap-2 text-xs text-slate-500">
        Points: <span class="font-mono text-slate-700">{{ inlinePointCount }}</span>
      </span>
    </div>

    <div class="mb-4 flex flex-wrap gap-2">
      <button
        class="rounded border border-emerald-500 px-3 py-1.5 text-sm font-medium text-emerald-600 transition hover:bg-emerald-50"
        type="button"
        :disabled="!hasInlineGeometry || inlineBusy"
        @click="emit('run-report')"
      >
        <span v-if="inlineBusy">Running…</span>
        <span v-else>Run Curve Report</span>
      </button>
      <button
        v-if="inlineResponse"
        class="rounded border px-3 py-1.5 text-sm"
        type="button"
        @click="emit('download-json')"
      >
        Download JSON
      </button>
    </div>

    <p
      v-if="inlineError"
      class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
    >
      {{ inlineError }}
    </p>

    <div
      v-else-if="inlineResponse"
      class="space-y-3 text-sm"
    >
      <div class="grid grid-cols-2 gap-3 rounded border bg-white p-3 text-xs">
        <div>
          <p class="text-slate-500">
            Polyline Length
          </p>
          <p class="font-mono text-slate-900">
            {{ formatNumber(inlineResponse.polyline.length) }} {{ inlineResponse.polyline.length_units }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Bounding Box
          </p>
          <p class="font-mono text-slate-900">
            {{ formatNumber(inlineResponse.polyline.bounding_box.width) }} ×
            {{ formatNumber(inlineResponse.polyline.bounding_box.height) }}
            {{ inlineResponse.polyline.length_units }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Closed
          </p>
          <p
            class="font-semibold"
            :class="inlineResponse.polyline.closed ? 'text-emerald-600' : 'text-amber-600'"
          >
            {{ inlineResponse.polyline.closed ? 'Yes' : 'No' }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Closure Gap
          </p>
          <p class="font-mono text-slate-900">
            {{ formatNumber(inlineResponse.polyline.closure_gap) }} {{ inlineResponse.polyline.closure_units }}
          </p>
        </div>
      </div>

      <div
        v-if="inlineResponse.biarc"
        class="rounded border bg-white p-3"
      >
        <p class="mb-2 text-xs font-semibold uppercase text-slate-500">
          Bi-arc Metrics
        </p>
        <dl class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <dt class="text-slate-500">
              Entities
            </dt>
            <dd class="font-mono text-slate-900">
              {{ inlineResponse.biarc.entity_count }}
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">
              Arcs / Lines
            </dt>
            <dd class="font-mono text-slate-900">
              {{ inlineResponse.biarc.arcs }} / {{ inlineResponse.biarc.lines }}
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">
              Min Radius
            </dt>
            <dd class="font-mono text-slate-900">
              {{ inlineResponse.biarc.min_radius ? formatNumber(inlineResponse.biarc.min_radius) : '—' }}
              {{ inlineResponse.biarc.radius_units }}
            </dd>
          </div>
          <div>
            <dt class="text-slate-500">
              Max Radius
            </dt>
            <dd class="font-mono text-slate-900">
              {{ inlineResponse.biarc.max_radius ? formatNumber(inlineResponse.biarc.max_radius) : '—' }}
              {{ inlineResponse.biarc.radius_units }}
            </dd>
          </div>
        </dl>
      </div>

      <div>
        <p class="text-xs font-semibold uppercase text-slate-500">
          Issues
        </p>
        <p
          v-if="!inlineResponse.issues.length"
          class="text-sm text-emerald-600"
        >
          No issues detected
        </p>
        <ul
          v-else
          class="mt-2 space-y-2"
        >
          <li
            v-for="(issue, idx) in inlineResponse.issues"
            :key="idx"
            class="rounded border bg-white p-2"
          >
            <div class="flex items-center justify-between text-xs">
              <span :class="severityClass(issue.severity)">
                {{ issue.severity.toUpperCase() }} · {{ issue.category }}
              </span>
              <span
                v-if="issue.fix_available"
                class="text-[11px] text-slate-500"
              >Fix suggested</span>
            </div>
            <p class="font-medium text-slate-800">
              {{ issue.message }}
            </p>
            <p
              v-if="issue.details"
              class="text-xs text-slate-500"
            >
              {{ issue.details }}
            </p>
            <p
              v-if="issue.fix_description"
              class="text-xs text-emerald-600"
            >
              {{ issue.fix_description }}
            </p>
          </li>
        </ul>
      </div>

      <div>
        <p class="text-xs font-semibold uppercase text-slate-500">
          Recommended Actions
        </p>
        <ul class="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
          <li
            v-for="(rec, idx) in inlineResponse.recommended_actions"
            :key="idx"
          >
            {{ rec }}
          </li>
        </ul>
      </div>
    </div>

    <p
      v-else
      class="text-sm text-slate-500"
    >
      Provide at least two points to generate a CurveLab report. Use the Adaptive Kernel or Blueprint tools to feed geometry
      into this modal.
    </p>
  </section>
</template>
