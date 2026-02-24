<script setup lang="ts">
/**
 * DxfValidationPanel - DXF file validation and auto-fix
 * Extracted from CurveLabModal.vue
 *
 * Uses /dxf/preflight/validate and /auto_fix for uploaded files.
 */
import type { ValidationReport, AutoFixOption } from './composables/curveLabTypes'
import type { FixOptionDef } from './composables/curveLabTypes'

defineProps<{
  filename: string
  hasDxf: boolean
  fileBusy: boolean
  fileResponse: ValidationReport | null
  fileError: string | null
  autoFixBusy: boolean
  fixedDownload: string | null
  selectedFixes: AutoFixOption[]
  fileCamReadyLabel: string | null
  fileCamReadyClass: string
  fixOptions: FixOptionDef[]
}>()

const emit = defineEmits<{
  'update:selectedFixes': [value: AutoFixOption[]]
  'run-validation': []
  'run-autofix': []
  'download-fixed': []
  'download-json': []
}>()

// Helpers
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

function toggleFix(fixId: AutoFixOption, currentFixes: AutoFixOption[]) {
  const idx = currentFixes.indexOf(fixId)
  if (idx >= 0) {
    emit('update:selectedFixes', currentFixes.filter((f) => f !== fixId))
  } else {
    emit('update:selectedFixes', [...currentFixes, fixId])
  }
}
</script>

<template>
  <section class="rounded-xl border bg-white p-4">
    <div class="mb-3 flex items-center justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold">
          DXF Validation
        </h3>
        <p class="text-xs text-slate-500">
          Uses <code class="rounded bg-slate-50 px-1 py-0.5">/dxf/preflight/validate</code> and <code>/auto_fix</code> for uploaded files.
        </p>
      </div>
      <span
        v-if="fileCamReadyLabel"
        class="rounded-full px-3 py-1 text-xs font-semibold"
        :class="fileCamReadyClass"
      >
        {{ fileCamReadyLabel }}
      </span>
    </div>

    <div class="mb-4 space-y-2 text-sm">
      <p class="text-slate-600">
        File: <span class="font-mono text-slate-800">{{ filename }}</span>
      </p>
      <p
        v-if="!hasDxf"
        class="text-xs text-amber-600"
      >
        Provide a DXF file in Blueprint Lab to enable validation + auto-fix tools.
      </p>
    </div>

    <div class="mb-4 flex flex-wrap gap-2">
      <button
        class="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50"
        type="button"
        :disabled="!hasDxf || fileBusy"
        @click="emit('run-validation')"
      >
        <span v-if="fileBusy">Validating…</span>
        <span v-else>Run DXF Validation</span>
      </button>
      <button
        class="rounded border border-emerald-400 px-3 py-1.5 text-sm font-medium text-emerald-600 hover:bg-emerald-50"
        type="button"
        :disabled="!hasDxf || autoFixBusy || !selectedFixes.length"
        @click="emit('run-autofix')"
      >
        <span v-if="autoFixBusy">Applying Fixes…</span>
        <span v-else>Auto-Fix Selected</span>
      </button>
      <button
        v-if="fixedDownload"
        class="rounded border px-3 py-1.5 text-sm"
        type="button"
        @click="emit('download-fixed')"
      >
        Download Fixed DXF
      </button>
      <button
        v-if="fileResponse"
        class="rounded border px-3 py-1.5 text-sm"
        type="button"
        @click="emit('download-json')"
      >
        Download JSON
      </button>
    </div>

    <div class="mb-4 rounded border bg-slate-50 p-3 text-xs">
      <p class="mb-2 font-semibold uppercase text-slate-500">
        Auto-Fix Options
      </p>
      <div class="grid gap-2">
        <label
          v-for="opt in fixOptions"
          :key="opt.id"
          class="flex items-start gap-2"
        >
          <input
            type="checkbox"
            class="mt-1"
            :checked="selectedFixes.includes(opt.id)"
            :value="opt.id"
            :disabled="!hasDxf"
            @change="toggleFix(opt.id, selectedFixes)"
          >
          <span>
            <span class="block text-sm font-semibold">{{ opt.label }}</span>
            <span class="text-[11px] text-slate-500">{{ opt.helper }}</span>
          </span>
        </label>
      </div>
    </div>

    <p
      v-if="fileError"
      class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
    >
      {{ fileError }}
    </p>

    <div
      v-else-if="fileResponse"
      class="space-y-3 text-sm"
    >
      <div class="grid grid-cols-2 gap-3 rounded border bg-slate-50 p-3 text-xs">
        <div>
          <p class="text-slate-500">
            Version
          </p>
          <p class="font-mono text-slate-900">
            {{ fileResponse.dxf_version }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Units
          </p>
          <p class="font-mono text-slate-900">
            {{ fileResponse.units ?? 'unknown' }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Geometry Total
          </p>
          <p class="font-mono text-slate-900">
            {{ fileResponse.geometry.total }}
          </p>
        </div>
        <div>
          <p class="text-slate-500">
            Layers
          </p>
          <p class="font-mono text-slate-900">
            {{ fileResponse.layers.length }}
          </p>
        </div>
      </div>

      <div>
        <p class="text-xs font-semibold uppercase text-slate-500">
          Issues
        </p>
        <p
          v-if="!fileResponse.issues.length"
          class="text-sm text-emerald-600"
        >
          No issues detected.
        </p>
        <ul
          v-else
          class="mt-2 space-y-2"
        >
          <li
            v-for="(issue, idx) in fileResponse.issues"
            :key="idx"
            class="rounded border p-2"
          >
            <div class="flex items-center justify-between text-xs">
              <span :class="severityClass(issue.severity)">
                {{ issue.severity.toUpperCase() }} · {{ issue.category }}
              </span>
              <span
                v-if="issue.fix_available"
                class="text-[11px] text-slate-500"
              >Fix available</span>
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
            v-for="(rec, idx) in fileResponse.recommended_actions"
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
      Select a DXF in Blueprint Lab to enable validation. CurveLab will remember previous reports so you can quickly review before exporting CAM assets.
    </p>
  </section>
</template>
