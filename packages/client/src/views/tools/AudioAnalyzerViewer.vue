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
      <ValidationReportCard
        :validation="pack.validation"
        :validation-status-class="validationStatusClass"
        :validation-icon="validationIcon"
      />

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
      <PreviewPanel
        :active-path="activePath"
        :active-entry="activeEntry"
        :active-bytes="activeBytes"
        :peaks-bytes="peaksBytes"
        :current-renderer="currentRenderer"
        :selected-peak="selectedPeak"
        :selected-freq-hz="Number.isFinite(selectedPeak?.freq_hz) ? selectedPeak!.freq_hz : null"
        :selection-source="selectionSource"
        :selected-wsi-row="selectedWsiRow"
        :audio-jump-error="audioJumpError"
        :fmt-num="fmtNum"
        :fmt-bool="fmtBool"
        @peak-selected="onPeakSelected"
        @clear-peak="clearSelectedPeak"
        @jump-audio="jumpToPointAudio"
      />

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
import { watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getDownloadUrl } from '@/sdk/endpoints/rmosAcoustics'
import { useAgenticEvents } from '@/composables/useAgenticEvents'
import styles from './AudioAnalyzerViewer.module.css'
import shared from '@/styles/dark-theme-shared.module.css'

import {
  useAudioAnalyzerState,
  useAudioAnalyzerValidation,
  useAudioAnalyzerSelection,
  useAudioAnalyzerFiles,
  useAudioAnalyzerPack,
  useAudioAnalyzerNavigation
} from './audio_analyzer/composables'

import PreviewPanel from './audio_analyzer_viewer/PreviewPanel.vue'
import ValidationReportCard from './audio_analyzer_viewer/ValidationReportCard.vue'

// Agentic M1 events
const {
  emitViewRendered,
  emitArtifactCreated,
  emitAnalysisFailed,
  emitUserAction,
  emitToolRendered
} = useAgenticEvents()

const route = useRoute()

// State
const {
  pack,
  err,
  activePath,
  kindFilter,
  selectedPeak,
  audioJumpError,
  resetError
} = useAudioAnalyzerState()

// Validation
const { validationStatusClass, validationIcon } = useAudioAnalyzerValidation(pack, styles)

// Selection
const {
  cursorFreqHz,
  selectionSource,
  selectedWsiRow,
  clearSelectedPeak,
  clearCursorOnly,
  onPeakSelected,
  fmtNum,
  fmtBool
} = useAudioAnalyzerSelection(selectedPeak, activePath, audioJumpError, emitUserAction)

// Files
const {
  activeEntry,
  activeBytes,
  peaksBytes,
  currentRenderer,
  uniqueKinds,
  kindCounts,
  filteredFiles,
  getCategory,
  formatBytes,
  selectFile
} = useAudioAnalyzerFiles(pack, activePath, kindFilter)

// Pack loading
const { loadZip, onPick, onDrop } = useAudioAnalyzerPack(
  pack,
  err,
  activePath,
  kindFilter,
  selectedPeak,
  audioJumpError,
  resetError,
  emitArtifactCreated,
  emitViewRendered,
  emitAnalysisFailed
)

// Navigation
const { jumpToPointAudio } = useAudioAnalyzerNavigation(
  pack,
  selectedPeak,
  activePath,
  audioJumpError
)

// Clear audio jump error when navigating files
watch(activePath, () => {
  audioJumpError.value = ''
})

// Deep-link support: load from sha256 query param (from Acoustics Library)
onMounted(async () => {
  emitToolRendered('audio_analyzer')

  const sha256 = route.query.sha256
  if (typeof sha256 === 'string' && sha256.length > 0) {
    resetError()
    try {
      const url = getDownloadUrl(sha256)
      const resp = await fetch(url)
      if (!resp.ok) {
        throw new Error(`Failed to fetch attachment: ${resp.status}`)
      }
      const blob = await resp.blob()
      const file = new File([blob], `viewer_pack_${sha256.slice(0, 8)}.zip`, {
        type: 'application/zip'
      })
      await loadZip(file)
    } catch (e) {
      err.value = e instanceof Error ? e.message : String(e)
    }
  }
})
</script>
