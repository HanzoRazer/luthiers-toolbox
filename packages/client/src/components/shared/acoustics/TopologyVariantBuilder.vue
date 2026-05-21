<script setup lang="ts">
/**
 * TopologyVariantBuilder — Create new topology variant descriptors
 *
 * Dev Order 66: Experimental topology variant framework
 * Dev Order 67: QA hardening for input validation
 *
 * Lightweight structured inputs, no numeric dimensions.
 * Observational only — no calibration authority.
 * Empty title is rejected (canCreate guard).
 */
import { ref, computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { TopologyVariant, TopologyVariantCategory } from '@/types/acoustics/topologyVariant'
import { createTopologyVariant } from '@/utils/acoustics/topologyVariant'

const emit = defineEmits<{
  created: [variant: TopologyVariant]
  cancel: []
}>()

// Form state
const title = ref('')
const description = ref('')
const category = ref<TopologyVariantCategory | ''>('')
const bodyFamily = ref('')
const shellFamily = ref('')
const apertureStrategy = ref('')
const bracingStrategy = ref('')
const bridgeStrategy = ref('')
const localContourStrategy = ref('')
const tornavozStrategy = ref('')
const experimentTagsInput = ref('')
const notes = ref('')

const categories: { value: TopologyVariantCategory | ''; label: string }[] = [
  { value: '', label: 'Select category...' },
  { value: 'body', label: 'Body' },
  { value: 'shell', label: 'Shell/Radius' },
  { value: 'aperture', label: 'Aperture' },
  { value: 'bracing', label: 'Bracing' },
  { value: 'bridge', label: 'Bridge/Plate' },
  { value: 'tornavoz', label: 'Tornavoz/Liner' },
  { value: 'combined', label: 'Combined' },
]

const canCreate = computed(() => title.value.trim().length > 0)

const experimentTags = computed(() =>
  experimentTagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t.length > 0)
)

function handleCreate() {
  if (!canCreate.value) return

  const variant = createTopologyVariant(title.value.trim(), {
    description: description.value.trim() || undefined,
    category: category.value || undefined,
    bodyFamily: bodyFamily.value.trim() || undefined,
    shellFamily: shellFamily.value.trim() || undefined,
    apertureStrategy: apertureStrategy.value.trim() || undefined,
    bracingStrategy: bracingStrategy.value.trim() || undefined,
    bridgeStrategy: bridgeStrategy.value.trim() || undefined,
    localContourStrategy: localContourStrategy.value.trim() || undefined,
    tornavozStrategy: tornavozStrategy.value.trim() || undefined,
    experimentTags: experimentTags.value.length > 0 ? experimentTags.value : undefined,
    notes: notes.value.trim() || undefined,
  })

  emit('created', variant)
  resetForm()
}

function handleCancel() {
  resetForm()
  emit('cancel')
}

function resetForm() {
  title.value = ''
  description.value = ''
  category.value = ''
  bodyFamily.value = ''
  shellFamily.value = ''
  apertureStrategy.value = ''
  bracingStrategy.value = ''
  bridgeStrategy.value = ''
  localContourStrategy.value = ''
  tornavozStrategy.value = ''
  experimentTagsInput.value = ''
  notes.value = ''
}
</script>

<template>
  <div :class="$style.builder">
    <div :class="$style.header">
      <SectionLabel text="New Topology Variant" />
      <GateBadge gate="yellow" label="Experimental" />
    </div>

    <div :class="$style.form">
      <!-- Title (required) -->
      <div :class="$style.field">
        <label :class="$style.label">Title *</label>
        <input
          v-model="title"
          type="text"
          :class="$style.input"
          placeholder="e.g., Carlos Jumbo dual-spiral"
        />
      </div>

      <!-- Category -->
      <div :class="$style.field">
        <label :class="$style.label">Category</label>
        <select v-model="category" :class="$style.select">
          <option
            v-for="cat in categories"
            :key="cat.value"
            :value="cat.value"
          >
            {{ cat.label }}
          </option>
        </select>
      </div>

      <!-- Description -->
      <div :class="$style.field">
        <label :class="$style.label">Description</label>
        <textarea
          v-model="description"
          :class="$style.textarea"
          rows="2"
          placeholder="Brief description of this experimental configuration"
        />
      </div>

      <!-- Strategy fields -->
      <div :class="$style.fieldGroup">
        <div :class="$style.fieldGroupLabel">Strategy Descriptors</div>

        <div :class="$style.fieldRow">
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Body Family</label>
            <input
              v-model="bodyFamily"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., Carlos Jumbo, J-45"
            />
          </div>
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Shell/Radius</label>
            <input
              v-model="shellFamily"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., 32/8 reflective shell"
            />
          </div>
        </div>

        <div :class="$style.fieldRow">
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Aperture Strategy</label>
            <input
              v-model="apertureStrategy"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., triple treble spiral"
            />
          </div>
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Bracing Strategy</label>
            <input
              v-model="bracingStrategy"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., minimal A-frame"
            />
          </div>
        </div>

        <div :class="$style.fieldRow">
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Bridge/Plate Strategy</label>
            <input
              v-model="bridgeStrategy"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., floating bridge"
            />
          </div>
          <div :class="$style.fieldHalf">
            <label :class="$style.labelSmall">Tornavoz/Liner</label>
            <input
              v-model="tornavozStrategy"
              type="text"
              :class="$style.inputSmall"
              placeholder="e.g., Selmer-hybrid tornavoz"
            />
          </div>
        </div>

        <div :class="$style.field">
          <label :class="$style.labelSmall">Local Contouring</label>
          <input
            v-model="localContourStrategy"
            type="text"
            :class="$style.inputSmall"
            placeholder="e.g., domed island"
          />
        </div>
      </div>

      <!-- Experiment Tags -->
      <div :class="$style.field">
        <label :class="$style.label">Experiment Tags</label>
        <input
          v-model="experimentTagsInput"
          type="text"
          :class="$style.input"
          placeholder="Comma-separated tags"
        />
        <div v-if="experimentTags.length > 0" :class="$style.tagPreview">
          <span v-for="tag in experimentTags" :key="tag" :class="$style.tag">
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Notes -->
      <div :class="$style.field">
        <label :class="$style.label">Notes</label>
        <textarea
          v-model="notes"
          :class="$style.textarea"
          rows="2"
          placeholder="Additional notes"
        />
      </div>
    </div>

    <div :class="$style.actions">
      <button :class="$style.cancelButton" @click="handleCancel">
        Cancel
      </button>
      <button
        :class="$style.createButton"
        :disabled="!canCreate"
        @click="handleCreate"
      >
        Create Variant
      </button>
    </div>

    <div :class="$style.notice">
      Topology variants are local descriptors. No persistence backend in this session.
    </div>
  </div>
</template>

<style module>
.builder {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 1rem;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #30363d;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.fieldGroup {
  padding: 0.75rem;
  background: #1f2937;
  border-radius: 0.375rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fieldGroupLabel {
  font-size: 0.6875rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.25rem;
}

.fieldRow {
  display: flex;
  gap: 0.75rem;
}

.fieldHalf {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.label {
  font-size: 0.75rem;
  color: #9ca3af;
}

.labelSmall {
  font-size: 0.625rem;
  color: #6b7280;
}

.input,
.select,
.textarea {
  padding: 0.5rem;
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.8125rem;
}

.inputSmall {
  padding: 0.375rem;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.75rem;
}

.input:focus,
.inputSmall:focus,
.select:focus,
.textarea:focus {
  outline: none;
  border-color: #6366f1;
}

.select {
  cursor: pointer;
}

.textarea {
  resize: vertical;
  min-height: 3rem;
}

.tagPreview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
}

.tag {
  padding: 0.125rem 0.375rem;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #818cf8;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid #30363d;
}

.cancelButton {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid #374151;
  border-radius: 0.25rem;
  color: #9ca3af;
  font-size: 0.8125rem;
  cursor: pointer;
}

.cancelButton:hover {
  background: #374151;
  color: #f9fafb;
}

.createButton {
  padding: 0.5rem 1rem;
  background: #6366f1;
  border: none;
  border-radius: 0.25rem;
  color: #f9fafb;
  font-size: 0.8125rem;
  cursor: pointer;
}

.createButton:disabled {
  background: #4b5563;
  cursor: not-allowed;
  opacity: 0.6;
}

.createButton:not(:disabled):hover {
  background: #4f46e5;
}

.notice {
  margin-top: 0.75rem;
  padding: 0.375rem 0.5rem;
  background: rgba(107, 114, 128, 0.08);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #6b7280;
  text-align: center;
}
</style>
