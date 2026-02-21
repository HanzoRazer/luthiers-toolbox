<template>
  <div
    :class="styles.modalOverlay"
    @click.self="emit('close')"
  >
    <div :class="styles.exportDialog">
      <header :class="styles.dialogHeader">
        <h2>Save Comparison as Preset</h2>
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
            Preset Name:
            <input
              :value="presetForm.name"
              type="text"
              placeholder="e.g., Les Paul Neck Comparison Template"
              :class="styles.textInput"
              required
              @input="emit('update:presetForm', { ...presetForm, name: ($event.target as HTMLInputElement).value })"
            >
          </label>

          <label :class="styles.fieldLabel">
            Description (optional):
            <textarea
              :value="presetForm.description"
              placeholder="Describe this comparison preset..."
              :class="styles.textInput"
              rows="3"
              @input="emit('update:presetForm', { ...presetForm, description: ($event.target as HTMLTextAreaElement).value })"
            />
          </label>

          <label :class="styles.fieldLabel">
            Tags (comma-separated):
            <input
              :value="presetForm.tagsInput"
              type="text"
              placeholder="comparison, neck, les-paul"
              :class="styles.textInput"
              @input="emit('update:presetForm', { ...presetForm, tagsInput: ($event.target as HTMLInputElement).value })"
            >
          </label>

          <label :class="styles.fieldLabel">
            Preset Kind:
            <select
              :value="presetForm.kind"
              :class="styles.textInput"
              @change="emit('update:presetForm', { ...presetForm, kind: ($event.target as HTMLSelectElement).value as 'export' | 'combo' })"
            >
              <option value="export">Export Only (template + format)</option>
              <option value="combo">Combo (comparison mode + export)</option>
            </select>
          </label>
          <p :class="styles.fieldHint">
            Export: Saves only export settings (template, format)<br>
            Combo: Saves comparison mode + export settings
          </p>
        </div>

        <div :class="styles.presetSummary">
          <h3>Preset Will Include:</h3>
          <ul>
            <li>✓ Filename Template: <code>{{ filenameTemplate }}</code></li>
            <li>✓ Export Format: <code>{{ exportFormat }}</code></li>
            <li v-if="neckProfileContext">
              ✓ Neck Profile Context: <code>{{ neckProfileContext }}</code>
            </li>
            <li v-if="neckSectionContext">
              ✓ Neck Section Context: <code>{{ neckSectionContext }}</code>
            </li>
            <li v-if="presetForm.kind === 'combo'">
              ✓ Compare Mode: <code>{{ diffResultMode }}</code>
            </li>
          </ul>
        </div>

        <div
          v-if="presetSaveMessage"
          :class="presetSaveMessage.type === 'success' ? styles.statusSuccess : styles.statusError"
        >
          {{ presetSaveMessage.text }}
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
          :disabled="!presetForm.name || presetSaveInProgress"
          @click="emit('save')"
        >
          {{ presetSaveInProgress ? 'Saving...' : 'Save Preset' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PresetForm {
  name: string
  description: string
  tagsInput: string
  kind: 'export' | 'combo'
}

interface PresetSaveMessage {
  type: 'success' | 'error'
  text: string
}

defineProps<{
  styles: Record<string, string>
  presetForm: PresetForm
  filenameTemplate: string
  exportFormat: 'svg' | 'png' | 'csv'
  neckProfileContext: string | null
  neckSectionContext: string | null
  diffResultMode: string
  presetSaveMessage: PresetSaveMessage | null
  presetSaveInProgress: boolean
}>()

const emit = defineEmits<{
  'close': []
  'update:presetForm': [value: PresetForm]
  'save': []
}>()
</script>
