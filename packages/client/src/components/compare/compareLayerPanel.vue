<template>
  <aside
    v-if="hasLayers"
    class="layer-panel"
  >
    <header class="layer-panel__header">
      <span class="layer-panel__title">Layers</span>
      <label class="layer-panel__filter">
        <input
          v-model="showOnlyMismatched"
          type="checkbox"
          :disabled="disabled"
        >
        Only mismatched
      </label>
    </header>

    <ul class="layer-panel__list">
      <li
        v-for="layer in filteredLayers"
        :key="layer.id"
        class="layer-row"
        :class="{
          'layer-row--left-only': layer.inLeft && !layer.inRight,
          'layer-row--right-only': !layer.inLeft && layer.inRight,
        }"
      >
        <div class="layer-row__label">
          <span class="layer-row__name">
            {{ layer.label || layer.id }}
          </span>
          <span
            v-if="layer.inLeft !== layer.inRight"
            class="layer-row__badge"
          >
            {{ layer.inLeft && !layer.inRight ? "Left only" : "Right only" }}
          </span>
        </div>

        <div class="layer-row__toggles">
          <label class="layer-row__toggle">
            <input
              v-model="layer.visibleLeft"
              type="checkbox"
              :disabled="!layer.inLeft || disabled"
              :title="layer.inLeft ? 'Toggle left visibility' : 'Not in left'"
            >
            L
          </label>
          <label class="layer-row__toggle">
            <input
              v-model="layer.visibleRight"
              type="checkbox"
              :disabled="!layer.inRight || disabled"
              :title="
                layer.inRight ? 'Toggle right visibility' : 'Not in right'
              "
            >
            R
          </label>
        </div>
      </li>
    </ul>

    <footer
      v-if="summary"
      class="layer-panel__footer"
    >
      <div class="layer-summary">
        <span class="layer-summary__stat">
          {{ summary.common.length }} common
        </span>
        <span
          v-if="summary.addedLeftOnly.length > 0"
          class="layer-summary__stat layer-summary__stat--left"
        >
          {{ summary.addedLeftOnly.length }} left only
        </span>
        <span
          v-if="summary.addedRightOnly.length > 0"
          class="layer-summary__stat layer-summary__stat--right"
        >
          {{ summary.addedRightOnly.length }} right only
        </span>
      </div>
    </footer>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import {
  isLayerMismatched,
  buildLayerDiffSummary,
  type LayerInfo,
} from "./compareLayers";

// Props
interface Props {
  layers: LayerInfo[];
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
});

// State
const showOnlyMismatched = ref(false);

// Computed
const hasLayers = computed(() => props.layers.length > 0);

const filteredLayers = computed(() => {
  if (!showOnlyMismatched.value) return props.layers;
  return props.layers.filter(isLayerMismatched);
});

const summary = computed(() => {
  if (!hasLayers.value) return null;
  return buildLayerDiffSummary(props.layers);
});
</script>

<style scoped>
.layer-panel {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  padding: 0.5rem;
  background: #111;
  font-size: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.layer-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.layer-panel__title {
  font-weight: 600;
  font-size: 0.85rem;
}

.layer-panel__filter {
  font-size: 0.7rem;
  opacity: 0.8;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
}

.layer-panel__list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
}

.layer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.3rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  gap: 0.5rem;
}

.layer-row:last-child {
  border-bottom: none;
}

.layer-row--left-only {
  background: rgba(59, 130, 246, 0.08);
  padding-left: 0.25rem;
  padding-right: 0.25rem;
  border-radius: 3px;
}

.layer-row--right-only {
  background: rgba(168, 85, 247, 0.08);
  padding-left: 0.25rem;
  padding-right: 0.25rem;
  border-radius: 3px;
}

.layer-row__label {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.layer-row__name {
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layer-row__badge {
  margin-top: 0.15rem;
  font-size: 0.65rem;
  padding: 0.05rem 0.35rem;
  border-radius: 999px;
  background: rgba(234, 179, 8, 0.25);
  color: #fde68a;
  width: fit-content;
}

.layer-row__toggles {
  display: flex;
  gap: 0.4rem;
  flex-shrink: 0;
}

.layer-row__toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.7rem;
  cursor: pointer;
  user-select: none;
}

.layer-row__toggle input[type="checkbox"] {
  cursor: pointer;
}

.layer-row__toggle input[type="checkbox"]:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.layer-panel__footer {
  padding-top: 0.35rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.layer-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.7rem;
  opacity: 0.8;
}

.layer-summary__stat {
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
}

.layer-summary__stat--left {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
}

.layer-summary__stat--right {
  background: rgba(168, 85, 247, 0.15);
  color: #d8b4fe;
}
</style>
