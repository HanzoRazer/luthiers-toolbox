<template>
  <Teleport to="body">
    <div
      v-if="show"
      :class="styles.modalOverlay"
      @click.self="$emit('close')"
    >
      <div :class="styles.modalContent">
        <div :class="styles.modalHeader">
          <h2>{{ editingPreset ? 'Edit Preset' : 'Create New Preset' }}</h2>
          <button
            :class="styles.closeBtn"
            @click="$emit('close')"
          >
            &times;
          </button>
        </div>
        <div :class="styles.modalBody">
          <form @submit.prevent="$emit('save')">
            <!-- Basic Info -->
            <div :class="styles.formGroup">
              <label>Name <span :class="styles.required">*</span></label>
              <input
                :value="formData.name"
                type="text"
                required
                :class="styles.formInput"
                @input="$emit('update:formData', { ...formData, name: ($event.target as HTMLInputElement).value })"
              >
            </div>

            <div :class="styles.formGroup">
              <label>Kind <span :class="styles.required">*</span></label>
              <select
                :value="formData.kind"
                required
                :class="styles.formInput"
                @change="$emit('update:formData', { ...formData, kind: ($event.target as HTMLSelectElement).value })"
              >
                <option value="cam">
                  CAM
                </option>
                <option value="export">
                  Export
                </option>
                <option value="neck">
                  Neck
                </option>
                <option value="combo">
                  Combo
                </option>
              </select>
            </div>

            <div :class="styles.formGroup">
              <label>Description</label>
              <textarea
                :value="formData.description"
                :class="styles.formInput"
                rows="3"
                @input="$emit('update:formData', { ...formData, description: ($event.target as HTMLTextAreaElement).value })"
              />
            </div>

            <div :class="styles.formGroup">
              <label>Tags (comma-separated)</label>
              <input
                :value="tagsInput"
                type="text"
                placeholder="roughing, adaptive, baseline"
                :class="styles.formInput"
                @input="$emit('update:tagsInput', ($event.target as HTMLInputElement).value)"
              >
            </div>

            <!-- Machine/Post (for CAM presets) -->
            <div
              v-if="formData.kind === 'cam' || formData.kind === 'combo'"
              :class="styles.formSection"
            >
              <h3>Machine & Post</h3>
              <div :class="styles.formRow">
                <div :class="styles.formGroup">
                  <label>Machine ID</label>
                  <input
                    :value="formData.machine_id"
                    type="text"
                    :class="styles.formInput"
                    @input="$emit('update:formData', { ...formData, machine_id: ($event.target as HTMLInputElement).value })"
                  >
                </div>
                <div :class="styles.formGroup">
                  <label>Post ID</label>
                  <input
                    :value="formData.post_id"
                    type="text"
                    :class="styles.formInput"
                    @input="$emit('update:formData', { ...formData, post_id: ($event.target as HTMLInputElement).value })"
                  >
                </div>
              </div>
            </div>

            <!-- Export Template (for export presets) -->
            <div
              v-if="formData.kind === 'export' || formData.kind === 'combo'"
              :class="styles.formSection"
            >
              <h3>Export Settings</h3>
              <div :class="styles.formGroup">
                <label>Filename Template</label>
                <input
                  :value="exportTemplate"
                  type="text"
                  placeholder="{preset}__{post}__{date}.nc"
                  :class="styles.formInput"
                  @input="$emit('update:exportTemplate', ($event.target as HTMLInputElement).value)"
                >
                <small :class="styles.helpText">
                  Tokens: {preset}, {machine}, {post}, {neck_profile}, {neck_section}, {date}
                </small>
              </div>
            </div>

            <!-- Action Buttons -->
            <div :class="styles.modalActions">
              <button
                type="button"
                :class="styles.btnSecondary"
                @click="$emit('close')"
              >
                Cancel
              </button>
              <button
                type="submit"
                :class="styles.btnPrimary"
                :disabled="saving"
              >
                {{ saving ? 'Saving...' : (editingPreset ? 'Update' : 'Create') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import styles from '../PresetHubView.module.css'

interface FormData {
  name: string
  kind: string
  description: string
  machine_id: string
  post_id: string
}

defineProps<{
  show: boolean
  editingPreset: boolean
  saving: boolean
  formData: FormData
  tagsInput: string
  exportTemplate: string
}>()

defineEmits<{
  close: []
  save: []
  'update:formData': [data: FormData]
  'update:tagsInput': [value: string]
  'update:exportTemplate': [value: string]
}>()
</script>
