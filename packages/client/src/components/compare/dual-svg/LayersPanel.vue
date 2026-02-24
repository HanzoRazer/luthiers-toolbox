<script setup lang="ts">
/**
 * LayersPanel - Layer toggle controls for compare view
 * Extracted from DualSvgDisplay.vue
 */
interface Layer {
  id: string
  inLeft: boolean
  inRight: boolean
  hasDiff?: boolean
  enabled: boolean
}

defineProps<{
  layers: Layer[]
}>()

const emit = defineEmits<{
  'toggle-layer': [layerId: string, enabled: boolean]
}>()

function onLayerToggle(layer: Layer) {
  emit('toggle-layer', layer.id, !layer.enabled)
}
</script>

<template>
  <div class="compare-layers-panel">
    <h4 class="layers-title">
      Layers
    </h4>
    <ul class="layers-list">
      <li
        v-for="layer in layers"
        :key="layer.id"
        class="layer-item"
      >
        <label class="layer-label">
          <input
            type="checkbox"
            :checked="layer.enabled"
            class="layer-checkbox"
            @change="onLayerToggle(layer)"
          >
          <span class="layer-name">{{ layer.id }}</span>
          <span
            v-if="layer.hasDiff"
            class="layer-badge layer-badge-diff"
          >
            diff
          </span>
          <span
            v-if="!layer.inLeft"
            class="layer-badge layer-badge-missing"
          >
            not in left
          </span>
          <span
            v-if="!layer.inRight"
            class="layer-badge layer-badge-missing"
          >
            not in right
          </span>
        </label>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.compare-layers-panel {
  margin-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
}

.layers-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.layers-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.layer-item {
  padding: 0;
}

.layer-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  transition: background-color 0.15s ease;
}

.layer-label:hover {
  background-color: #f9fafb;
}

.layer-checkbox {
  cursor: pointer;
}

.layer-name {
  font-size: 0.9rem;
  color: #1f2937;
}

.layer-badge {
  margin-left: 0.5rem;
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 999px;
  font-weight: 500;
}

.layer-badge-diff {
  background: #fee2e2;
  color: #991b1b;
}

.layer-badge-missing {
  background: #fef3c7;
  color: #92400e;
}
</style>
