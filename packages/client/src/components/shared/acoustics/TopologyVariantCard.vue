<script setup lang="ts">
/**
 * TopologyVariantCard — Display a topology variant descriptor
 *
 * Dev Order 66: Experimental topology variant framework
 * Dev Order 67: QA hardening for sparse/missing metadata
 *
 * Observational only — no calibration authority.
 * Handles sparse variants without layout collapse.
 */
import { computed } from 'vue'
import { GateBadge, SectionLabel } from '@/components/shared/workflow'
import type { TopologyVariant } from '@/types/acoustics/topologyVariant'
import {
  getCategoryDisplayLabel,
  getTopologyVariantStrategySummary,
  formatVariantTimestamp,
} from '@/utils/acoustics/topologyVariant'

const props = defineProps<{
  variant: TopologyVariant
  selected?: boolean
}>()

const emit = defineEmits<{
  select: [variant: TopologyVariant]
}>()

const strategySummary = computed(() => getTopologyVariantStrategySummary(props.variant))
const categoryLabel = computed(() => getCategoryDisplayLabel(props.variant.category))
const formattedDate = computed(() => formatVariantTimestamp(props.variant.createdAtIso))
// Dev Order 67: Safe title fallback for edge cases
const displayTitle = computed(() => props.variant.title?.trim() || props.variant.variantId || 'Unnamed Variant')

function handleSelect() {
  emit('select', props.variant)
}
</script>

<template>
  <div
    :class="[$style.card, selected && $style.selected]"
    @click="handleSelect"
  >
    <div :class="$style.header">
      <SectionLabel :text="displayTitle" />
      <GateBadge gate="yellow" :label="categoryLabel" />
    </div>

    <div :class="$style.summary">
      {{ strategySummary }}
    </div>

    <!-- Strategy details -->
    <div v-if="variant.bodyFamily || variant.apertureStrategy || variant.bracingStrategy" :class="$style.strategies">
      <div v-if="variant.bodyFamily" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Body</span>
        <span :class="$style.strategyValue">{{ variant.bodyFamily }}</span>
      </div>
      <div v-if="variant.apertureStrategy" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Aperture</span>
        <span :class="$style.strategyValue">{{ variant.apertureStrategy }}</span>
      </div>
      <div v-if="variant.bracingStrategy" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Bracing</span>
        <span :class="$style.strategyValue">{{ variant.bracingStrategy }}</span>
      </div>
      <div v-if="variant.shellFamily" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Shell</span>
        <span :class="$style.strategyValue">{{ variant.shellFamily }}</span>
      </div>
      <div v-if="variant.bridgeStrategy" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Bridge</span>
        <span :class="$style.strategyValue">{{ variant.bridgeStrategy }}</span>
      </div>
      <div v-if="variant.tornavozStrategy" :class="$style.strategyItem">
        <span :class="$style.strategyLabel">Tornavoz</span>
        <span :class="$style.strategyValue">{{ variant.tornavozStrategy }}</span>
      </div>
    </div>

    <!-- Tags -->
    <div v-if="variant.experimentTags?.length" :class="$style.tags">
      <span
        v-for="tag in variant.experimentTags"
        :key="tag"
        :class="$style.tag"
      >
        {{ tag }}
      </span>
    </div>

    <!-- Description -->
    <div v-if="variant.description" :class="$style.description">
      {{ variant.description }}
    </div>

    <!-- Footer -->
    <div :class="$style.footer">
      <span :class="$style.timestamp">{{ formattedDate }}</span>
      <span :class="$style.variantId">{{ variant.variantId }}</span>
    </div>
  </div>
</template>

<style module>
.card {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 0.5rem;
  padding: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s ease;
}

.card:hover {
  border-color: #6366f1;
}

.card.selected {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.summary {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
}

.strategies {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.strategyItem {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0.25rem 0.5rem;
  background: #1f2937;
  border-radius: 0.25rem;
}

.strategyLabel {
  font-size: 0.5625rem;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.strategyValue {
  font-size: 0.6875rem;
  color: #d1d5db;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.tag {
  padding: 0.125rem 0.375rem;
  background: rgba(99, 102, 241, 0.15);
  border-radius: 0.25rem;
  font-size: 0.625rem;
  color: #818cf8;
}

.description {
  font-size: 0.6875rem;
  color: #8b949e;
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.5rem;
  border-top: 1px solid #30363d;
}

.timestamp {
  font-size: 0.625rem;
  color: #6b7280;
}

.variantId {
  font-size: 0.5625rem;
  color: #4b5563;
  font-family: monospace;
}
</style>
