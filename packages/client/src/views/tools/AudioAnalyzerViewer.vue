<template>
  <div :class="shared.page">
    <header :class="styles.header">
      <div :class="shared.headerRow">
        <h1>🎛️ Audio Analyzer Evidence Viewer</h1>
        <div
          v-if="cursorFreqHz !== null"
          :class="styles.cursorPill"
          :title="`Linked cursor @ ${cursorFreqHz.toFixed(2)} Hz`"
        >
          <span :class="styles.cursorPillLabel">Cursor</span>
          <code :class="styles.cursorPillVal">{{ cursorFreqHz.toFixed(2) }} Hz</code>
          <button
            :class="styles.cursorPillClear"
            aria-label="Clear cursor"
            @click="clearCursorOnly"
          >
            ✕
          </button>
        </div>
      </div>
      <p :class="shared.sub">
        Evidence-pack viewer (ZIP). Supports both
        <code>viewer_pack_v1</code> and <code>toolbox_evidence_manifest_v1</code> schemas.
      </p>
    </header>

    <section
      :class="shared.dropZone"
      @dragover.prevent
      @drop.prevent="onDrop"
    >
      <div :class="shared.dropZoneInner">
        <div :class="shared.dropZoneTitle">
          Drop an evidence ZIP here
        </div>
        <div :class="shared.dropZoneSub">
          or
        </div>
        <input
          type="file"
          accept=".zip"
          @change="onPick"
        >
      </div>
    </section>

    <section
      v-if="err"
      :class="styles.err"
    >
      <strong>Error:</strong> {{ err }}
    </section>

    <section
      v-if="pack"
      :class="styles.grid"
    >
      <!-- Pack Metadata -->
      <div :class="shared.cardTransparent">
        <h2>Pack Summary</h2>
        <div :class="shared.kv">
          <div><span>schema</span><code>{{ pack.schema_id }}</code></div>
          <div><span>created_at_utc</span><code>{{ pack.created_at_utc || "-" }}</code></div>
          <div v-if="pack.source_capdir">
            <span>source_capdir</span><code>{{ pack.source_capdir }}</code>
          </div>
          <div v-if="pack.detected_phase">
            <span>detected_phase</span><code>{{ pack.detected_phase }}</code>
          </div>
          <div><span>measurement_only</span><code>{{ pack.measurement_only ? "Yes" : "No" }}</code></div>
          <div v-if="pack.interpretation">
            <span>interpretation</span><code>{{ pack.interpretation }}</code>
          </div>
          <div><span>files</span><code>{{ pack.files.length }}</code></div>
        </div>
      </div>

      <!-- Validation Report -->
      <div :class="[styles.validationCard, validationStatusClass]">
        <h2>
          <span :class="styles.validationIcon">{{ validationIcon }}</span>
          Validation Report
        </h2>
        <div
          v-if="!pack.validation"
          :class="styles.validationUnknown"
        >
          <p>No validation_report.json found in pack.</p>
          <p :class="shared.muted">
            Legacy packs may not include validation data.
          </p>
        </div>
        <div
          v-else
          :class="styles.validationContent"
        >
          <div :class="styles.validationStatus">
            <span :class="pack.validation.passed ? styles.validationBadgePass : styles.validationBadgeFail">
              {{ pack.validation.passed ? "PASS" : "FAIL" }}
            </span>
          </div>
          <div :class="shared.kv">
            <div><span>errors</span><code>{{ pack.validation.errors.length }}</code></div>
            <div><span>warnings</span><code>{{ pack.validation.warnings.length }}</code></div>
            <div v-if="pack.validation.schema_id">
              <span>schema_id</span><code>{{ pack.validation.schema_id }}</code>
            </div>
            <div v-if="pack.validation.validated_at">
              <span>validated_at</span><code>{{ pack.validation.validated_at }}</code>
            </div>
          </div>
          <details
            v-if="pack.validation.errors.length > 0"
            :class="styles.validationDetails"
          >
            <summary>Errors ({{ pack.validation.errors.length }})</summary>
            <ul :class="styles.validationList">
              <li
                v-for="(e, i) in pack.validation.errors"
                :key="'err-' + i"
              >
                <code>{{ e.path }}</code>: {{ e.message }}
              </li>
            </ul>
          </details>
          <details
            v-if="pack.validation.warnings.length > 0"
            :class="styles.validationDetails"
          >
            <summary>Warnings ({{ pack.validation.warnings.length }})</summary>
            <ul :class="styles.validationList">
              <li
                v-for="(w, i) in pack.validation.warnings"
                :key="'warn-' + i"
              >
                <code>{{ w.path }}</code>: {{ w.message }}
              </li>
            </ul>
          </details>
        </div>
      </div>

      <!-- File List -->
      <div :class="shared.cardTransparent">
        <h2>Files</h2>
        <div :class="shared.filterBar">
          <select
            v-model="kindFilter"
            :class="shared.filterSelect"
          >
            <option value="">
              All kinds
            </option>
            <option
              v-for="k in uniqueKinds"
              :key="k"
              :value="k"
            >
              {{ k }}
            </option>
          </select>
          <span :class="shared.filterCount">{{ filteredFiles.length }} file(s)</span>
        </div>
        <table :class="shared.tbl">
          <thead>
            <tr>
              <th>kind</th>
              <th>path</th>
              <th>bytes</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="f in filteredFiles"
              :key="f.relpath"
              :class="{ [shared.rowActive]: activePath === f.relpath }"
            >
              <td>
                <code
                  :class="styles.kindBadge"
                  :data-category="getCategory(f.kind)"
                >{{ f.kind }}</code>
              </td>
              <td
                :class="styles.pathCell"
                :title="f.relpath"
              >
                {{ f.relpath }}
              </td>
              <td :class="shared.mono">
                {{ formatBytes(f.bytes) }}
              </td>
              <td>
                <button
                  :class="shared.btnSmall"
                  @click="selectFile(f.relpath)"
                >
                  View
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Preview Panel -->
      <div :class="shared.cardTransparentWide">
        <h2>Preview</h2>
        <div
          v-if="activePath && activeEntry"
          :class="shared.previewContainer"
        >
          <div :class="shared.previewSplit">
            <div :class="shared.previewMain">
              <component
                :is="currentRenderer"
                :entry="activeEntry"
                :bytes="activeBytes"
                :peaks-bytes="peaksBytes"
                :selected-freq-hz="Number.isFinite(selectedPeak?.freq_hz) ? selectedPeak!.freq_hz : null"
                @peak-selected="onPeakSelected"
              />
            </div>

            <aside :class="shared.previewSide">
              <div :class="shared.sideHeader">
                <div :class="shared.sideTitle">
                  Selection Details
                </div>
                <button
                  :class="shared.btnSmall"
                  :disabled="!selectedPeak"
                  @click="clearSelectedPeak"
                >
                  Clear
                </button>
              </div>

              <div
                v-if="!selectedPeak"
                :class="styles.sideEmpty"
              >
                <p :class="shared.muted">
                  Click a peak marker in the spectrum chart to inspect it here.
                </p>
              </div>

              <div
                v-else
                :class="shared.sideBody"
              >
                <div :class="shared.kvCompact">
                  <div><span>source</span><code>{{ selectionSource }}</code></div>
                  <div><span>point</span><code>{{ selectedPeak.pointId || "—" }}</code></div>
                  <div>
                    <span>freq_hz</span>
                    <code>{{ Number.isFinite(selectedPeak.freq_hz) ? selectedPeak.freq_hz.toFixed(2) : "—" }}</code>
                  </div>
                  <div v-if="selectedPeak.label">
                    <span>label</span><code>{{ selectedPeak.label }}</code>
                  </div>
                  <div><span>file</span><code :class="shared.mono">{{ selectedPeak.spectrumRelpath }}</code></div>
                  <div v-if="selectedPeak.peaksRelpath">
                    <span>analysis</span><code :class="shared.mono">{{ selectedPeak.peaksRelpath }}</code>
                  </div>
                </div>

                <details
                  v-if="selectionSource === 'wsi'"
                  :class="styles.sideRaw"
                  open
                >
                  <summary :class="styles.sideSummary">
                    WSI row fields
                  </summary>
                  <div :class="shared.kvCompact">
                    <div><span>wsi</span><code>{{ fmtNum(selectedWsiRow?.wsi) }}</code></div>
                    <div><span>coh_mean</span><code>{{ fmtNum(selectedWsiRow?.coh_mean) }}</code></div>
                    <div><span>phase_disorder</span><code>{{ fmtNum(selectedWsiRow?.phase_disorder) }}</code></div>
                    <div><span>loc</span><code>{{ fmtNum(selectedWsiRow?.loc) }}</code></div>
                    <div><span>grad</span><code>{{ fmtNum(selectedWsiRow?.grad) }}</code></div>
                    <div><span>admissible</span><code>{{ fmtBool(selectedWsiRow?.admissible) }}</code></div>
                  </div>
                </details>

                <div :class="shared.sideActions">
                  <button
                    :class="shared.btnSmall"
                    :disabled="!selectedPeak.pointId"
                    @click="jumpToPointAudio"
                  >
                    ▶ Open point audio
                  </button>
                  <div
                    v-if="audioJumpError"
                    :class="styles.sideWarn"
                  >
                    {{ audioJumpError }}
                  </div>
                </div>

                <details
                  :class="styles.sideRaw"
                  open
                >
                  <summary :class="styles.sideSummary">
                    Raw selection JSON
                  </summary>
                  <pre :class="shared.codePre">{{ selectedPeak.rawPretty }}</pre>
                </details>
              </div>
            </aside>
          </div>
        </div>
        <div
          v-else
          :class="shared.placeholder"
        >
          <p>Select a file from the list above to preview.</p>
        </div>
      </div>

      <!-- Pack Debug Panel -->
      <details :class="shared.debugPanel">
        <summary :class="shared.debugSummary">
          🔍 Pack Debug Info
        </summary>
        <div :class="shared.debugContent">
          <div :class="shared.debugGrid">
            <div :class="styles.debugSection">
              <h3>Schema</h3>
              <div :class="styles.debugKv">
                <span>schema_id</span>
                <code>{{ pack.schema_id }}</code>
              </div>
              <div :class="styles.debugKv">
                <span>bundle_sha256</span>
                <code :class="shared.hash">{{ pack.bundle_sha256 || "—" }}</code>
              </div>
            </div>
            <div :class="styles.debugSection">
              <h3>Kinds Present ({{ uniqueKinds.length }})</h3>
              <div :class="shared.chips">
                <code
                  v-for="k in uniqueKinds"
                  :key="k"
                  :class="shared.chip"
                  :data-category="getCategory(k)"
                >
                  {{ k }} ({{ kindCounts[k] }})
                </code>
              </div>
            </div>
          </div>
          <div :class="styles.debugSection">
            <h3>All Files ({{ pack.files.length }})</h3>
            <table :class="styles.debugTbl">
              <thead>
                <tr>
                  <th>kind</th>
                  <th>relpath</th>
                  <th>bytes</th>
                  <th>sha256</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="f in pack.files"
                  :key="f.relpath"
                >
                  <td>
                    <code
                      :class="styles.kindBadge"
                      :data-category="getCategory(f.kind)"
                    >{{ f.kind }}</code>
                  </td>
                  <td :class="shared.mono">
                    {{ f.relpath }}
                  </td>
                  <td :class="shared.mono">
                    {{ f.bytes }}
                  </td>
                  <td :class="[shared.mono, shared.hash]">
                    {{ f.sha256?.slice(0, 12) || "—" }}…
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </details>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, shallowRef, type Component, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { loadNormalizedPack, type NormalizedPack, type NormalizedFileEntry } from "@/evidence";
import { pickRenderer, getRendererCategory } from "@/tools/audio_analyzer/renderers";
import { findSiblingPeaksRelpath } from "@/tools/audio_analyzer/packHelpers";
import { getDownloadUrl } from "@/sdk/endpoints/rmosAcoustics";
import styles from "./AudioAnalyzerViewer.module.css";
import shared from "@/styles/dark-theme-shared.module.css";

// Agentic M1 events
import { useAgenticEvents } from "@/composables/useAgenticEvents";

const {
  emitViewRendered,
  emitArtifactCreated,
  emitAnalysisFailed,
  emitUserAction,
  emitToolRendered,
} = useAgenticEvents();

const route = useRoute();

const pack = shallowRef<NormalizedPack | null>(null);
const err = ref<string>("");
const activePath = ref<string>("");
const kindFilter = ref<string>("");

// Validation display computed properties
const validationStatusClass = computed(() => {
  if (!pack.value?.validation) return styles.validationUnknownBorder;
  return pack.value.validation.passed ? styles.validationPass : styles.validationFail;
});

const validationIcon = computed(() => {
  if (!pack.value?.validation) return "❓";
  return pack.value.validation.passed ? "✅" : "❌";
});

/**
 * GOVERNANCE NOTE — READ BEFORE MODIFYING
 *
 * SelectedPeak represents a user-controlled navigation cursor only.
 * It exists to coordinate highlighting and view alignment across renderers
 * without performing analysis, inference, ranking, filtering, or scoring.
 *
 * This object MUST NOT contain derived values, interpretations, risk scores,
 * recommendations, or cross-evidence aggregation. All fields must originate
 * directly from user actions or exported evidence artifacts.
 *
 * Any change that causes selection to imply meaning rather than display it
 * constitutes interpretation and is OUT OF SCOPE for Wave 6A / 6B.1.
 */
type SelectedPeak = {
  pointId: string | null;
  spectrumRelpath: string;
  peaksRelpath: string;
  peakIndex: number;
  freq_hz: number;
  label?: string;
  raw: unknown;
  rawPretty: string;
};
const selectedPeak = ref<SelectedPeak | null>(null);
const audioJumpError = ref<string>("");

// Wave 6A "linked cursor" pill should persist across file changes
const cursorFreqHz = computed<number | null>(() => {
  const f = selectedPeak.value?.freq_hz;
  return Number.isFinite(f) ? f! : null;
});

const selectionSource = computed<"spectrum" | "wsi" | "unknown">(() => {
  const rp = selectedPeak.value?.spectrumRelpath ?? "";
  if (rp.endsWith("/spectrum.csv")) return "spectrum";
  if (rp === "wolf/wsi_curve.csv") return "wsi";
  return "unknown";
});

type WsiRow = {
  freq_hz?: number;
  wsi?: number;
  loc?: number;
  grad?: number;
  phase_disorder?: number;
  coh_mean?: number;
  admissible?: boolean;
};

const selectedWsiRow = computed<WsiRow | null>(() => {
  if (!selectedPeak.value) return null;
  if (selectionSource.value !== "wsi") return null;
  const raw = selectedPeak.value.raw;
  if (!raw || typeof raw !== "object") return null;
  return raw as WsiRow;
});

function fmtNum(v: unknown): string {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(3) : "—";
}
function fmtBool(v: unknown): string {
  if (typeof v === "boolean") return v ? "true" : "false";
  return "—";
}

// Current active file entry
const activeEntry = computed<NormalizedFileEntry | null>(() => {
  if (!pack.value || !activePath.value) return null;
  return pack.value.files.find((f) => f.relpath === activePath.value) ?? null;
});

// Current active file bytes
const activeBytes = computed<Uint8Array>(() => {
  if (!pack.value || !activePath.value) return new Uint8Array(0);
  return pack.value.resolveFile(activePath.value) ?? new Uint8Array(0);
});

// Sibling peaks bytes for spectrum CSV files (analysis.json)
const peaksBytes = computed<Uint8Array | null>(() => {
  if (!pack.value || !activePath.value) return null;
  const siblingPath = findSiblingPeaksRelpath(activePath.value);
  if (!siblingPath) return null;
  return pack.value.resolveFile(siblingPath) ?? null;
});

// Dynamically pick renderer based on file kind
const currentRenderer = computed<Component | null>(() => {
  if (!activeEntry.value) return null;
  return pickRenderer(activeEntry.value.kind);
});

// Unique kinds for filter dropdown
const uniqueKinds = computed<string[]>(() => {
  if (!pack.value) return [];
  const kinds = new Set(pack.value.files.map((f) => f.kind));
  return Array.from(kinds).sort();
});

// Kind counts for debug panel
const kindCounts = computed<Record<string, number>>(() => {
  if (!pack.value) return {};
  const counts: Record<string, number> = {};
  for (const f of pack.value.files) {
    counts[f.kind] = (counts[f.kind] || 0) + 1;
  }
  return counts;
});

// Filtered file list
const filteredFiles = computed<NormalizedFileEntry[]>(() => {
  if (!pack.value) return [];
  if (!kindFilter.value) return pack.value.files;
  return pack.value.files.filter((f) => f.kind === kindFilter.value);
});

function getCategory(kind: string): string {
  return getRendererCategory(kind);
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function resetError() {
  err.value = "";
}

async function loadZip(f: File) {
  resetError();
  try {
    pack.value = await loadNormalizedPack(f);
    // Default preview: first CSV if present, else first file
    const firstCsv = pack.value.files.find((x) => x.kind.endsWith("_csv"));
    activePath.value = (firstCsv ?? pack.value.files[0])?.relpath ?? "";
    kindFilter.value = "";
    selectedPeak.value = null;
    audioJumpError.value = "";

    // --- Agentic M1: emit artifact created events ---
    const hasWolfData = pack.value.files.some((x) => x.kind.includes("wolf"));
    const hasOdsData = pack.value.files.some((x) => x.kind.includes("ods"));
    if (hasWolfData) {
      emitArtifactCreated("wolf_candidates_v1", 0.75);
    }
    if (hasOdsData) {
      emitArtifactCreated("ods_snapshot_v1", 0.8);
    }
    // Emit view rendered to trigger FIRST_SIGNAL
    emitViewRendered("audio_analyzer", pack.value.schema_id);
    // --- End Agentic ---
  } catch (e: unknown) {
    pack.value = null;
    activePath.value = "";
    err.value = e instanceof Error ? e.message : String(e);

    // --- Agentic M1: emit failure ---
    emitAnalysisFailed(err.value);
    // --- End Agentic ---
  }
}

async function onPick(ev: Event) {
  const input = ev.target as HTMLInputElement;
  const f = input.files?.[0];
  if (f) await loadZip(f);
}

async function onDrop(ev: DragEvent) {
  const f = ev.dataTransfer?.files?.[0];
  if (f) await loadZip(f);
}

function selectFile(relpath: string) {
  activePath.value = relpath;
}

function clearSelectedPeak() {
  selectedPeak.value = null;
  audioJumpError.value = "";
}

function clearCursorOnly() {
  // Keep details panel context but clear the linked cursor frequency.
  if (!selectedPeak.value) return;
  selectedPeak.value = { ...selectedPeak.value, freq_hz: NaN };
  // We treat NaN as "no cursor" in the renderer binding below by mapping to null.
}

function pointIdFromSpectrumRelpath(relpath: string): string | null {
  // spectra/points/{POINT_ID}/spectrum.csv
  const m = relpath.match(/^spectra\/points\/([^/]+)\/spectrum\.csv$/);
  return m?.[1] ?? null;
}

function audioRelpathForPoint(pointId: string): string {
  // Contracted path for point audio in viewer_pack_v1
  return `audio/points/${pointId}.wav`;
}

function onPeakSelected(payload: any) {
  audioJumpError.value = "";
  const spectrumRelpath = typeof payload?.spectrumRelpath === "string" ? payload.spectrumRelpath : activePath.value;
  const peaksRelpath = findSiblingPeaksRelpath(spectrumRelpath) ?? "";
  const pointId = pointIdFromSpectrumRelpath(spectrumRelpath);
  const freq_hz = Number(payload?.freq_hz);
  if (!Number.isFinite(freq_hz)) return;

  // --- Agentic M1: emit peak selection ---
  emitUserAction("peak_selected", { freq_hz, spectrum: activePath.value });
  // --- End Agentic ---

  const raw = payload?.raw ?? payload;
  let rawPretty = "";
  try {
    rawPretty = JSON.stringify(raw, null, 2);
  } catch {
    rawPretty = String(raw);
  }

  selectedPeak.value = {
    pointId,
    spectrumRelpath,
    peaksRelpath,
    peakIndex: Number(payload?.peakIndex ?? -1),
    freq_hz,
    label: typeof payload?.label === "string" ? payload.label : undefined,
    raw,
    rawPretty,
  };
}

function jumpToPointAudio() {
  audioJumpError.value = "";
  if (!pack.value || !selectedPeak.value?.pointId) return;
  const audioRel = audioRelpathForPoint(selectedPeak.value.pointId);
  const exists = pack.value.files.some((f) => f.relpath === audioRel);
  if (!exists) {
    audioJumpError.value = `Audio missing for point ${selectedPeak.value.pointId}: expected ${audioRel}`;
    return;
  }
  activePath.value = audioRel;
}

// If user navigates away from the source spectrum, keep selection but make sure
// details stay coherent: if activePath is not a spectrum.csv, we keep selectedPeak as-is.
// (This is Wave 3 behavior; Wave 6A persistence rules can extend later.)
watch(activePath, () => {
  audioJumpError.value = "";
});

// Deep-link support: load from sha256 query param (from Acoustics Library)
onMounted(async () => {
  // --- Agentic M1: emit tool rendered on mount ---
  emitToolRendered("audio_analyzer");
  // --- End Agentic ---

  const sha256 = route.query.sha256;
  if (typeof sha256 === "string" && sha256.length > 0) {
    resetError();
    try {
      const url = getDownloadUrl(sha256);
      const resp = await fetch(url);
      if (!resp.ok) {
        throw new Error(`Failed to fetch attachment: ${resp.status}`);
      }
      const blob = await resp.blob();
      const file = new File([blob], `viewer_pack_${sha256.slice(0, 8)}.zip`, {
        type: "application/zip",
      });
      await loadZip(file);
    } catch (e) {
      err.value = e instanceof Error ? e.message : String(e);
    }
  }
});
</script>
