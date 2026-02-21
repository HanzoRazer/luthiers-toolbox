<template>
  <div
    :class="styles.modalOverlay"
    @click.self="emit('close')"
  >
    <div :class="styles.exportDialog">
      <header :class="styles.dialogHeader">
        <h2>Export Comparison</h2>
        <button
          :class="styles.closeBtn"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div :class="styles.dialogContent">
        <div :class="styles.namingSection">
          <label :class="styles.fieldLabel">
            Export Preset (optional):
            <select
              :value="selectedPresetId"
              :class="styles.textInput"
              @change="emit('update:selectedPresetId', ($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Use custom template --</option>
              <option
                v-for="preset in exportPresets"
                :key="preset.id"
                :value="preset.id"
              >
                {{ preset.name }}
              </option>
            </select>
          </label>

          <label :class="styles.fieldLabel">
            Filename Template:
            <input
              :value="filenameTemplate"
              type="text"
              placeholder="{preset}__{compare_mode}__{date}"
              :class="styles.textInput"
              @input="emit('update:filenameTemplate', ($event.target as HTMLInputElement).value)"
              @blur="emit('validateTemplate')"
            >
          </label>

          <!-- Extension Mismatch Warning -->
          <div
            v-if="extensionMismatch"
            :class="styles.extensionWarning"
          >
            <div :class="styles.warningBanner">
              <span :class="styles.warningIcon">⚠️</span>
              <div :class="styles.warningContent">
                <strong>Extension Mismatch Detected</strong>
                <p>
                  Template has <code>.{{ extensionMismatch.templateExt }}</code> extension
                  but export format is <strong>{{ extensionMismatch.expectedExt.toUpperCase() }}</strong>
                </p>
              </div>
            </div>
            <div :class="styles.warningActions">
              <button
                type="button"
                :class="styles.fixButton"
                title="Change template extension to match format"
                @click="emit('fixTemplateExtension')"
              >
                Fix Template → .{{ extensionMismatch.expectedExt }}
              </button>
              <button
                type="button"
                :class="styles.fixButtonSecondary"
                title="Change format to match template extension"
                @click="emit('fixExportFormat')"
              >
                Fix Format → {{ extensionMismatch.templateExt.toUpperCase() }}
              </button>
            </div>
          </div>

          <p
            v-if="templateValidation"
            :class="styles.fieldHint"
          >
            <span v-if="templateValidation.valid">✓ Valid template</span>
            <span v-else>⚠ {{ templateValidation.warnings?.join(', ') }}</span>
          </p>
          <p :class="styles.fieldHint">
            Tokens: {preset}, {compare_mode}, {neck_profile}, {neck_section}, {date}, {timestamp}
          </p>
          <p
            v-if="neckProfileContext || neckSectionContext"
            :class="styles.fieldHint"
          >
            ℹ Neck context:
            <span v-if="neckProfileContext">Profile: <code>{{ neckProfileContext }}</code></span>
            <span v-if="neckSectionContext">Section: <code>{{ neckSectionContext }}</code></span>
          </p>
          <p
            v-else
            :class="styles.fieldHint"
          >
            ⚠ No neck context detected. Tokens {neck_profile} and {neck_section} will be empty.
          </p>
        </div>

        <div :class="styles.exportOptions">
          <label :class="styles.exportOption">
            <input
              :checked="exportFormat === 'svg'"
              type="radio"
              value="svg"
              name="exportFormat"
              @change="emit('update:exportFormat', 'svg')"
            >
            <span :class="styles.optionLabel">
              <strong>SVG</strong>
              <span :class="styles.optionDesc">Dual-pane layout with delta annotations (vector)</span>
            </span>
          </label>

          <label :class="styles.exportOption">
            <input
              :checked="exportFormat === 'png'"
              type="radio"
              value="png"
              name="exportFormat"
              @change="emit('update:exportFormat', 'png')"
            >
            <span :class="styles.optionLabel">
              <strong>PNG</strong>
              <span :class="styles.optionDesc">Rasterized screenshot at 300 DPI</span>
            </span>
          </label>

          <label :class="styles.exportOption">
            <input
              :checked="exportFormat === 'csv'"
              type="radio"
              value="csv"
              name="exportFormat"
              @change="emit('update:exportFormat', 'csv')"
            >
            <span :class="styles.optionLabel">
              <strong>CSV</strong>
              <span :class="styles.optionDesc">Delta metrics table (Excel compatible)</span>
            </span>
          </label>
        </div>

        <div :class="styles.filenamePreview">
          <label>Filename Preview:</label>
          <code>{{ exportFilename }}</code>
        </div>
      </div>

      <div :class="styles.dialogActions">
        <button
          :class="styles.ghost"
          @click="emit('close')"
        >
          Cancel
        </button>
        <button
          :class="styles.primary"
          :disabled="exportInProgress"
          @click="emit('export')"
        >
          {{ exportInProgress ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ExtensionMismatch {
  templateExt: string
  expectedExt: string
  hasConflict: boolean
}

interface TemplateValidation {
  valid: boolean
  warnings?: string[]
}

interface ExportPreset {
  id: string
  name: string
}

defineProps<{
  styles: Record<string, string>
  exportPresets: ExportPreset[]
  selectedPresetId: string
  filenameTemplate: string
  extensionMismatch: ExtensionMismatch | null
  templateValidation: TemplateValidation | null
  neckProfileContext: string | null
  neckSectionContext: string | null
  exportFormat: 'svg' | 'png' | 'csv'
  exportFilename: string
  exportInProgress: boolean
}>()

const emit = defineEmits<{
  'close': []
  'update:selectedPresetId': [value: string]
  'update:filenameTemplate': [value: string]
  'update:exportFormat': [value: 'svg' | 'png' | 'csv']
  'validateTemplate': []
  'fixTemplateExtension': []
  'fixExportFormat': []
  'export': []
}>()
</script>
