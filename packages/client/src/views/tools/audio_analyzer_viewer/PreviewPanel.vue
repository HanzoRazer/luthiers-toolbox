<template>
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
            :selected-freq-hz="Number.isFinite(selectedFreqHz) ? selectedFreqHz : null"
            @peak-selected="$emit('peak-selected', $event)"
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
              @click="$emit('clear-peak')"
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
                <code>{{ Number.isFinite(selectedPeak.freq_hz) ? selectedPeak.freq_hz?.toFixed(2) : "—" }}</code>
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
                @click="$emit('jump-audio')"
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
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import styles from '../AudioAnalyzerViewer.module.css'
import shared from '@/styles/dark-theme-shared.module.css'

export interface SelectedPeak {
  freq_hz?: number
  label?: string
  pointId?: string | null
  spectrumRelpath?: string
  peaksRelpath?: string
  rawPretty?: string
}

export interface WsiRow {
  wsi?: number
  coh_mean?: number
  phase_disorder?: number
  loc?: number
  grad?: number
  admissible?: boolean
}

defineProps<{
  activePath: string | null
  activeEntry: any
  activeBytes: Uint8Array | null
  peaksBytes: Uint8Array | null
  currentRenderer: Component | null
  selectedPeak: SelectedPeak | null
  selectedFreqHz: number | null
  selectionSource: string
  selectedWsiRow: WsiRow | null
  audioJumpError: string
  fmtNum: (n?: number) => string
  fmtBool: (b?: boolean) => string
}>()

defineEmits<{
  'peak-selected': [event: any]
  'clear-peak': []
  'jump-audio': []
}>()
</script>
