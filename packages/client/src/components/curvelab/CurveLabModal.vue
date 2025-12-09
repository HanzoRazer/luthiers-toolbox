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
            <p class="text-xs uppercase tracking-wide text-emerald-600">CurveLab</p>
            <h2 class="text-xl font-semibold">DXF Preflight + Auto-Fix</h2>
            <p class="text-sm text-slate-500">
              Validate inline CurveLab geometry or uploaded DXF files before CAM export.
            </p>
          </div>
          <button
            class="rounded-full border border-slate-200 p-2 text-slate-500 hover:bg-slate-50"
            type="button"
            @click="close"
            aria-label="Close CurveLab modal"
          >
            ✕
          </button>
        </header>

        <div class="grid gap-6 lg:grid-cols-2">
          <!-- Inline CurveLab Geometry Preflight -->
          <section class="rounded-xl border bg-slate-50/70 p-4">
            <div class="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 class="text-base font-semibold">Inline Geometry Report</h3>
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
                  v-model.number="tolerance"
                  type="number"
                  min="0.001"
                  step="0.01"
                  class="w-24 rounded border px-2 py-1"
                />
              </label>
              <label class="flex items-center gap-2">
                Layer
                <input v-model="layer" type="text" class="w-32 rounded border px-2 py-1" />
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
                @click="runInlineReport"
              >
                <span v-if="inlineBusy">Running…</span>
                <span v-else>Run Curve Report</span>
              </button>
              <button
                v-if="inlineResponse"
                class="rounded border px-3 py-1.5 text-sm"
                type="button"
                @click="downloadInlineJson"
              >
                Download JSON
              </button>
            </div>

            <p v-if="inlineError" class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {{ inlineError }}
            </p>

            <div v-else-if="inlineResponse" class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-3 rounded border bg-white p-3 text-xs">
                <div>
                  <p class="text-slate-500">Polyline Length</p>
                  <p class="font-mono text-slate-900">
                    {{ formatNumber(inlineResponse.polyline.length) }} {{ inlineResponse.polyline.length_units }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500">Bounding Box</p>
                  <p class="font-mono text-slate-900">
                    {{ formatNumber(inlineResponse.polyline.bounding_box.width) }} ×
                    {{ formatNumber(inlineResponse.polyline.bounding_box.height) }}
                    {{ inlineResponse.polyline.length_units }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500">Closed</p>
                  <p class="font-semibold" :class="inlineResponse.polyline.closed ? 'text-emerald-600' : 'text-amber-600'">
                    {{ inlineResponse.polyline.closed ? 'Yes' : 'No' }}
                  </p>
                </div>
                <div>
                  <p class="text-slate-500">Closure Gap</p>
                  <p class="font-mono text-slate-900">
                    {{ formatNumber(inlineResponse.polyline.closure_gap) }} {{ inlineResponse.polyline.closure_units }}
                  </p>
                </div>
              </div>

              <div v-if="inlineResponse.biarc" class="rounded border bg-white p-3">
                <p class="mb-2 text-xs font-semibold uppercase text-slate-500">Bi-arc Metrics</p>
                <dl class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <dt class="text-slate-500">Entities</dt>
                    <dd class="font-mono text-slate-900">{{ inlineResponse.biarc.entity_count }}</dd>
                  </div>
                  <div>
                    <dt class="text-slate-500">Arcs / Lines</dt>
                    <dd class="font-mono text-slate-900">
                      {{ inlineResponse.biarc.arcs }} / {{ inlineResponse.biarc.lines }}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-slate-500">Min Radius</dt>
                    <dd class="font-mono text-slate-900">
                      {{ inlineResponse.biarc.min_radius ? formatNumber(inlineResponse.biarc.min_radius) : '—' }}
                      {{ inlineResponse.biarc.radius_units }}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-slate-500">Max Radius</dt>
                    <dd class="font-mono text-slate-900">
                      {{ inlineResponse.biarc.max_radius ? formatNumber(inlineResponse.biarc.max_radius) : '—' }}
                      {{ inlineResponse.biarc.radius_units }}
                    </dd>
                  </div>
                </dl>
              </div>

              <div>
                <p class="text-xs font-semibold uppercase text-slate-500">Issues</p>
                <p v-if="!inlineResponse.issues.length" class="text-sm text-emerald-600">No issues detected 🎉</p>
                <ul v-else class="mt-2 space-y-2">
                  <li
                    v-for="(issue, idx) in inlineResponse.issues"
                    :key="idx"
                    class="rounded border bg-white p-2"
                  >
                    <div class="flex items-center justify-between text-xs">
                      <span :class="severityClass(issue.severity)">
                        {{ issue.severity.toUpperCase() }} · {{ issue.category }}
                      </span>
                      <span v-if="issue.fix_available" class="text-[11px] text-slate-500">Fix suggested</span>
                    </div>
                    <p class="font-medium text-slate-800">{{ issue.message }}</p>
                    <p v-if="issue.details" class="text-xs text-slate-500">{{ issue.details }}</p>
                    <p v-if="issue.fix_description" class="text-xs text-emerald-600">
                      {{ issue.fix_description }}
                    </p>
                  </li>
                </ul>
              </div>

              <div>
                <p class="text-xs font-semibold uppercase text-slate-500">Recommended Actions</p>
                <ul class="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  <li v-for="(rec, idx) in inlineResponse.recommended_actions" :key="idx">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>

            <p v-else class="text-sm text-slate-500">
              Provide at least two points to generate a CurveLab report. Use the Adaptive Kernel or Blueprint tools to feed geometry
              into this modal.
            </p>
          </section>

          <!-- DXF Validation + Auto Fix -->
          <section class="rounded-xl border bg-white p-4">
            <div class="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 class="text-base font-semibold">DXF Validation</h3>
                <p class="text-xs text-slate-500">
                  Uses <code class="rounded bg-slate-50 px-1 py-0.5">/dxf/preflight/validate</code> and <code>/auto_fix</code> for uploaded files.
                </p>
              </div>
              <span v-if="fileCamReadyLabel" class="rounded-full px-3 py-1 text-xs font-semibold" :class="fileCamReadyClass">
                {{ fileCamReadyLabel }}
              </span>
            </div>

            <div class="mb-4 space-y-2 text-sm">
              <p class="text-slate-600">
                File: <span class="font-mono text-slate-800">{{ filename }}</span>
              </p>
              <p v-if="!hasDxf" class="text-xs text-amber-600">
                Provide a DXF file in Blueprint Lab to enable validation + auto-fix tools.
              </p>
            </div>

            <div class="mb-4 flex flex-wrap gap-2">
              <button
                class="rounded border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50"
                type="button"
                :disabled="!hasDxf || fileBusy"
                @click="runFileValidation"
              >
                <span v-if="fileBusy">Validating…</span>
                <span v-else>Run DXF Validation</span>
              </button>
              <button
                class="rounded border border-emerald-400 px-3 py-1.5 text-sm font-medium text-emerald-600 hover:bg-emerald-50"
                type="button"
                :disabled="!hasDxf || autoFixBusy || !selectedFixes.length"
                @click="runAutoFix"
              >
                <span v-if="autoFixBusy">Applying Fixes…</span>
                <span v-else>Auto-Fix Selected</span>
              </button>
              <button
                v-if="fixedDownload"
                class="rounded border px-3 py-1.5 text-sm"
                type="button"
                @click="downloadFixedDxf"
              >
                Download Fixed DXF
              </button>
              <button
                v-if="fileResponse"
                class="rounded border px-3 py-1.5 text-sm"
                type="button"
                @click="downloadFileJson"
              >
                Download JSON
              </button>
            </div>

            <div class="mb-4 rounded border bg-slate-50 p-3 text-xs">
              <p class="mb-2 font-semibold uppercase text-slate-500">Auto-Fix Options</p>
              <div class="grid gap-2">
                <label
                  v-for="opt in fixOptions"
                  :key="opt.id"
                  class="flex items-start gap-2"
                >
                  <input
                    v-model="selectedFixes"
                    type="checkbox"
                    class="mt-1"
                    :value="opt.id"
                    :disabled="!hasDxf"
                  />
                  <span>
                    <span class="block text-sm font-semibold">{{ opt.label }}</span>
                    <span class="text-[11px] text-slate-500">{{ opt.helper }}</span>
                  </span>
                </label>
              </div>
            </div>

            <p v-if="fileError" class="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {{ fileError }}
            </p>

            <div v-else-if="fileResponse" class="space-y-3 text-sm">
              <div class="grid grid-cols-2 gap-3 rounded border bg-slate-50 p-3 text-xs">
                <div>
                  <p class="text-slate-500">Version</p>
                  <p class="font-mono text-slate-900">{{ fileResponse.dxf_version }}</p>
                </div>
                <div>
                  <p class="text-slate-500">Units</p>
                  <p class="font-mono text-slate-900">{{ fileResponse.units ?? 'unknown' }}</p>
                </div>
                <div>
                  <p class="text-slate-500">Geometry Total</p>
                  <p class="font-mono text-slate-900">{{ fileResponse.geometry.total }}</p>
                </div>
                <div>
                  <p class="text-slate-500">Layers</p>
                  <p class="font-mono text-slate-900">{{ fileResponse.layers.length }}</p>
                </div>
              </div>

              <div>
                <p class="text-xs font-semibold uppercase text-slate-500">Issues</p>
                <p v-if="!fileResponse.issues.length" class="text-sm text-emerald-600">No issues detected.</p>
                <ul v-else class="mt-2 space-y-2">
                  <li v-for="(issue, idx) in fileResponse.issues" :key="idx" class="rounded border p-2">
                    <div class="flex items-center justify-between text-xs">
                      <span :class="severityClass(issue.severity)">
                        {{ issue.severity.toUpperCase() }} · {{ issue.category }}
                      </span>
                      <span v-if="issue.fix_available" class="text-[11px] text-slate-500">Fix available</span>
                    </div>
                    <p class="font-medium text-slate-800">{{ issue.message }}</p>
                    <p v-if="issue.details" class="text-xs text-slate-500">{{ issue.details }}</p>
                    <p v-if="issue.fix_description" class="text-xs text-emerald-600">
                      {{ issue.fix_description }}
                    </p>
                  </li>
                </ul>
              </div>

              <div>
                <p class="text-xs font-semibold uppercase text-slate-500">Recommended Actions</p>
                <ul class="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
                  <li v-for="(rec, idx) in fileResponse.recommended_actions" :key="idx">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>

            <p v-else class="text-sm text-slate-500">
              Select a DXF in Blueprint Lab to enable validation. CurveLab will remember previous reports so you can quickly review before exporting CAM assets.
            </p>
          </section>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  autoFixDxf,
  fetchCurveReport,
  validateDxf,
} from "@/api/curvelab";
import type {
  AutoFixOption,
  CurveBiarcEntity,
  CurvePoint,
  CurvePreflightResponse,
  CurveUnits,
  ValidationIssue,
  ValidationReport,
} from "@/types/curvelab";

const props = defineProps({
  open: { type: Boolean, default: false },
  points: {
    type: Array as () => Array<[number, number]>,
    default: () => [],
  },
  units: {
    type: String as () => CurveUnits,
    default: "mm",
  },
  layer: {
    type: String,
    default: "CURVE",
  },
  biarcEntities: {
    type: Array as () => CurveBiarcEntity[] | null,
    default: () => [],
  },
  dxfBase64: {
    type: String,
    default: null,
  },
  filename: {
    type: String,
    default: "curve_preview.dxf",
  },
});

const emit = defineEmits(["close", "update:open", "auto-fix"]);

const tolerance = ref(0.1);
const layer = ref(props.layer);

const inlineBusy = ref(false);
const inlineResponse = ref<CurvePreflightResponse | null>(null);
const inlineError = ref<string | null>(null);

const fileBusy = ref(false);
const fileResponse = ref<ValidationReport | null>(null);
const fileError = ref<string | null>(null);

const autoFixBusy = ref(false);
const fixedDownload = ref<string | null>(null);
const selectedFixes = ref<AutoFixOption[]>([]);
const workingDxf = ref<string | null>(props.dxfBase64);

const fixOptions: { id: AutoFixOption; label: string; helper: string }[] = [
  {
    id: "convert_to_r12",
    label: "Convert to R12",
    helper: "Ensures exports target AC1009 for maximum CAM compatibility",
  },
  {
    id: "set_units_mm",
    label: "Set units to millimeters",
    helper: "Writes $INSUNITS=mm when file omits unit metadata",
  },
  {
    id: "close_open_polylines",
    label: "Close open polylines",
    helper: "Closes paths with <0.1 mm gap so pocketing works",
  },
  {
    id: "merge_duplicate_layers",
    label: "Merge duplicate layers",
    helper: "Consolidates inconsistently cased layer names",
  },
  {
    id: "explode_splines",
    label: "Explode splines",
    helper: "Converts splines to polylines (experimental)",
  },
];

const inlinePoints = computed<CurvePoint[]>(() =>
  (props.points || []).map(([x, y]) => ({ x, y })),
);

watch(
  () => props.layer,
  (next) => {
    layer.value = next || "CURVE";
  },
);

const hasInlineGeometry = computed(() => inlinePoints.value.length >= 2);
const inlinePointCount = computed(() => inlinePoints.value.length);

const hasDxf = computed(() => !!workingDxf.value);

watch(
  () => props.dxfBase64,
  (next) => {
    workingDxf.value = next;
    fixedDownload.value = null;
  },
);

const inlineCamReadyLabel = computed(() => {
  if (!inlineResponse.value) return "";
  return inlineResponse.value.cam_ready ? "CAM Ready" : "Needs Attention";
});

const inlineCamReadyClass = computed(() =>
  inlineResponse.value?.cam_ready
    ? "bg-emerald-100 text-emerald-700"
    : "bg-amber-100 text-amber-700",
);

const fileCamReadyLabel = computed(() => {
  if (!fileResponse.value) return "";
  return fileResponse.value.cam_ready ? "CAM Ready" : "Needs Review";
});

const fileCamReadyClass = computed(() =>
  fileResponse.value?.cam_ready
    ? "bg-emerald-100 text-emerald-700"
    : "bg-amber-100 text-amber-700",
);

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return Number(value).toFixed(3).replace(/\.000$/, ".0");
}

function severityClass(level: ValidationIssue["severity"]): string {
  if (level === "error") return "text-rose-700";
  if (level === "warning") return "text-amber-700";
  return "text-slate-500";
}

async function runInlineReport() {
  if (!hasInlineGeometry.value) return;
  inlineBusy.value = true;
  inlineError.value = null;
  try {
    const res = await fetchCurveReport({
      points: inlinePoints.value,
      units: props.units,
      tolerance_mm: tolerance.value,
      layer: layer.value,
      biarc_entities: props.biarcEntities?.length
        ? (props.biarcEntities as any)
        : undefined,
    });
    inlineResponse.value = res;
  } catch (err: any) {
    inlineError.value = err?.message || "Failed to run curve report";
  } finally {
    inlineBusy.value = false;
  }
}

async function runFileValidation() {
  if (!hasDxf.value || !workingDxf.value) return;
  fileBusy.value = true;
  fileError.value = null;
  try {
    const res = await validateDxf(workingDxf.value, props.filename);
    fileResponse.value = res;
  } catch (err: any) {
    fileError.value = err?.message || "Failed to validate DXF";
  } finally {
    fileBusy.value = false;
  }
}

async function runAutoFix() {
  if (!hasDxf.value || !workingDxf.value || !selectedFixes.value.length) return;
  autoFixBusy.value = true;
  fileError.value = null;
  try {
    const res = await autoFixDxf({
      dxf_base64: workingDxf.value,
      filename: props.filename,
      fixes: selectedFixes.value,
    });
    fixedDownload.value = res.fixed_dxf_base64;
    fileResponse.value = res.validation_report;
    workingDxf.value = res.fixed_dxf_base64;
    emit("auto-fix", res);
  } catch (err: any) {
    fileError.value = err?.message || "Auto-fix failed";
  } finally {
    autoFixBusy.value = false;
  }
}

function downloadInlineJson() {
  if (!inlineResponse.value) return;
  const blob = new Blob([JSON.stringify(inlineResponse.value, null, 2)], {
    type: "application/json",
  });
  triggerDownload(blob, "curvelab_curve_report.json");
}

function downloadFileJson() {
  if (!fileResponse.value) return;
  const blob = new Blob([JSON.stringify(fileResponse.value, null, 2)], {
    type: "application/json",
  });
  triggerDownload(blob, "curvelab_dxf_report.json");
}

function downloadFixedDxf() {
  if (!fixedDownload.value) return;
  const blob = base64ToBlob(fixedDownload.value, "application/dxf");
  triggerDownload(blob, `curvelab_fixed_${props.filename}`);
}

function base64ToBlob(base64: string, mime: string): Blob {
  const byteCharacters = atob(base64);
  const bytes = new Uint8Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i += 1) {
    bytes[i] = byteCharacters.charCodeAt(i);
  }
  return new Blob([bytes], { type: mime });
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function close() {
  emit("update:open", false);
  emit("close");
}
</script>
