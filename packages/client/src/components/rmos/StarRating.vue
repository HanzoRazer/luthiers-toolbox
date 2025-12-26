<script setup lang="ts">
/**
 * StarRating.vue
 *
 * Interactive 1-5 star rating widget.
 * Click to set, double-click to clear.
 */
const props = defineProps<{
  modelValue: number | null | undefined;
}>();
const emit = defineEmits<{
  (e: "update:modelValue", v: number | null): void;
}>();

function set(v: number) {
  emit("update:modelValue", v);
}
function clear() {
  emit("update:modelValue", null);
}
</script>

<template>
  <div class="stars" title="Rate 1-5 (click to set, double-click to clear)">
    <button
      v-for="i in 5"
      :key="i"
      class="star"
      :class="{ on: (modelValue ?? 0) >= i }"
      @click="set(i)"
      @dblclick.prevent="clear"
      type="button"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    </button>
    <span class="val" v-if="modelValue">{{ modelValue }}/5</span>
    <span class="val subtle" v-else>-</span>
  </div>
</template>

<style scoped>
.stars {
  display: flex;
  gap: 4px;
  align-items: center;
}

.star {
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  color: #dee2e6;
  transition: color 0.15s, transform 0.1s;
}

.star:hover {
  transform: scale(1.1);
}

.star.on {
  color: #ffc107;
}

.val {
  margin-left: 6px;
  font-size: 12px;
}

.subtle {
  opacity: 0.6;
}
</style>
