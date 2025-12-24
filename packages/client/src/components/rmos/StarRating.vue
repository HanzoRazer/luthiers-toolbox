<script setup lang="ts">
/**
 * StarRating.vue
 *
 * Interactive 1-5 star rating widget with hover preview.
 * Emits rating changes on click.
 */
import { ref, computed } from "vue";

const props = defineProps<{
  /** Current rating value (1-5, or null for unrated) */
  modelValue: number | null;
  /** Disable interaction (read-only mode) */
  disabled?: boolean;
  /** Star size in pixels */
  size?: number;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: number): void;
}>();

const hoverRating = ref<number | null>(null);

const displayRating = computed(() => {
  if (hoverRating.value !== null) return hoverRating.value;
  return props.modelValue || 0;
});

const starSize = computed(() => `${props.size || 24}px`);

function handleClick(star: number) {
  if (props.disabled) return;
  emit("update:modelValue", star);
}

function handleMouseEnter(star: number) {
  if (props.disabled) return;
  hoverRating.value = star;
}

function handleMouseLeave() {
  hoverRating.value = null;
}
</script>

<template>
  <div
    class="star-rating"
    :class="{ disabled }"
    @mouseleave="handleMouseLeave"
  >
    <button
      v-for="star in 5"
      :key="star"
      type="button"
      class="star-btn"
      :class="{ filled: star <= displayRating, hover: hoverRating !== null }"
      :disabled="disabled"
      :aria-label="`Rate ${star} star${star > 1 ? 's' : ''}`"
      @click="handleClick(star)"
      @mouseenter="handleMouseEnter(star)"
    >
      <svg
        :width="starSize"
        :height="starSize"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path
          d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
        />
      </svg>
    </button>
    <span v-if="modelValue" class="rating-text">
      {{ modelValue }}/5
    </span>
  </div>
</template>

<style scoped>
.star-rating {
  display: inline-flex;
  align-items: center;
  gap: 0.125rem;
}

.star-rating.disabled {
  opacity: 0.7;
}

.star-btn {
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #dee2e6;
  transition: color 0.15s, transform 0.1s;
}

.star-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.star-btn:disabled {
  cursor: default;
}

.star-btn.filled {
  color: #ffc107;
}

.star-btn.hover:not(.filled) {
  color: #ffe680;
}

.rating-text {
  margin-left: 0.5rem;
  font-size: 0.85rem;
  color: #6c757d;
}
</style>
