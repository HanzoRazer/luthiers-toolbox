<template>
  <div
    :class="[styles.presetCard, styles[`presetCardKind${preset.kind.charAt(0).toUpperCase()}${preset.kind.slice(1)}`]]"
  >
    <!-- Card Header -->
    <div :class="styles.cardHeader">
      <div :class="styles.cardTitleRow">
        <h3 :class="styles.cardTitle">
          {{ preset.name }}
        </h3>
        <span
          :class="[styles.kindBadge, styles[`kindBadgeKind${preset.kind.charAt(0).toUpperCase()}${preset.kind.slice(1)}`]]"
        >
          {{ preset.kind.toUpperCase() }}
        </span>
      </div>
      <p
        v-if="preset.description"
        :class="styles.cardDescription"
      >
        {{ preset.description }}
      </p>
    </div>

    <!-- Card Metadata -->
    <div :class="styles.cardMetadata">
      <div
        v-if="preset.machine_id"
        :class="styles.metadataItem"
      >
        <span :class="styles.icon">machine</span>
        <span>{{ preset.machine_id }}</span>
      </div>
      <div
        v-if="preset.post_id"
        :class="styles.metadataItem"
      >
        <span :class="styles.icon">post</span>
        <span>{{ preset.post_id }}</span>
      </div>
      <div
        v-if="preset.units"
        :class="styles.metadataItem"
      >
        <span :class="styles.icon">units</span>
        <span>{{ preset.units }}</span>
      </div>
      <div
        v-if="preset.tags && preset.tags.length > 0"
        :class="styles.metadataItem"
      >
        <span :class="styles.icon">tags</span>
        <div :class="styles.tagList">
          <span
            v-for="tag in preset.tags"
            :key="tag"
            :class="styles.tag"
          >{{ tag }}</span>
        </div>
      </div>
    </div>

    <!-- Lineage Info -->
    <div
      v-if="preset.job_source_id"
      :class="styles.lineageInfo"
      @mouseenter="$emit('showTooltip', preset, $event)"
      @mouseleave="$emit('hideTooltip')"
    >
      <span :class="styles.icon">link</span>
      <span :class="styles.lineageText">Cloned from job {{ preset.job_source_id.slice(0, 8) }}...</span>
      <span
        :class="styles.tooltipHint"
        title="Hover to see job details"
      >info</span>
    </div>

    <!-- Card Actions -->
    <div :class="styles.cardActions">
      <button
        :class="styles.actionBtn"
        title="Use in PipelineLab"
        @click="$emit('usePipeline', preset)"
      >
        pipeline
      </button>
      <button
        :class="styles.actionBtn"
        title="Use in CompareLab"
        @click="$emit('useCompare', preset)"
      >
        compare
      </button>
      <button
        v-if="preset.kind === 'neck' || preset.kind === 'combo'"
        :class="styles.actionBtn"
        title="Use in NeckLab"
        @click="$emit('useNeck', preset)"
      >
        neck
      </button>
      <button
        :class="styles.actionBtn"
        title="Clone"
        @click="$emit('clone', preset)"
      >
        clone
      </button>
      <button
        :class="styles.actionBtn"
        title="Edit"
        @click="$emit('edit', preset)"
      >
        edit
      </button>
      <button
        :class="styles.actionBtnDanger"
        title="Delete"
        @click="$emit('delete', preset)"
      >
        delete
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Preset } from '../composables/usePresetFilters'
import styles from '../PresetHubView.module.css'

defineProps<{
  preset: Preset
}>()

defineEmits<{
  showTooltip: [preset: Preset, event: MouseEvent]
  hideTooltip: []
  usePipeline: [preset: Preset]
  useCompare: [preset: Preset]
  useNeck: [preset: Preset]
  clone: [preset: Preset]
  edit: [preset: Preset]
  delete: [preset: Preset]
}>()
</script>
