<script setup lang="ts">
/**
 * SkeletonLoader - Content placeholder during loading
 *
 * Usage:
 *   <SkeletonLoader />
 *   <SkeletonLoader variant="text" :lines="3" />
 *   <SkeletonLoader variant="card" />
 *   <SkeletonLoader variant="avatar" />
 */
defineProps<{
  variant?: 'text' | 'card' | 'avatar' | 'button' | 'custom'
  lines?: number
  width?: string
  height?: string
}>()
</script>

<template>
  <div class="skeleton-container" :class="`skeleton--${variant || 'text'}`">
    <!-- Text lines -->
    <template v-if="variant === 'text' || !variant">
      <div
        v-for="i in (lines || 1)"
        :key="i"
        class="skeleton skeleton-line"
        :style="{
          width: i === lines ? '60%' : '100%',
        }"
      />
    </template>

    <!-- Card -->
    <template v-else-if="variant === 'card'">
      <div class="skeleton skeleton-card">
        <div class="skeleton-card-image" />
        <div class="skeleton-card-content">
          <div class="skeleton skeleton-line" style="width: 70%" />
          <div class="skeleton skeleton-line" style="width: 100%" />
          <div class="skeleton skeleton-line" style="width: 50%" />
        </div>
      </div>
    </template>

    <!-- Avatar -->
    <template v-else-if="variant === 'avatar'">
      <div class="skeleton skeleton-avatar" />
    </template>

    <!-- Button -->
    <template v-else-if="variant === 'button'">
      <div class="skeleton skeleton-button" />
    </template>

    <!-- Custom -->
    <template v-else-if="variant === 'custom'">
      <div
        class="skeleton"
        :style="{
          width: width || '100%',
          height: height || '1rem',
        }"
      />
    </template>
  </div>
</template>

<style scoped>
.skeleton-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 0.5rem);
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-elevated, #f3f4f6) 25%,
    var(--color-surface-hover, #e5e7eb) 50%,
    var(--color-surface-elevated, #f3f4f6) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm, 0.25rem);
}

.skeleton-line {
  height: 1rem;
}

.skeleton-avatar {
  width: 3rem;
  height: 3rem;
  border-radius: var(--radius-full, 9999px);
}

.skeleton-button {
  width: 6rem;
  height: 2.5rem;
  border-radius: var(--radius-md, 0.375rem);
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg, 0.5rem);
  overflow: hidden;
  background: none;
  animation: none;
}

.skeleton-card-image {
  width: 100%;
  height: 10rem;
  background: linear-gradient(
    90deg,
    var(--color-surface-elevated, #f3f4f6) 25%,
    var(--color-surface-hover, #e5e7eb) 50%,
    var(--color-surface-elevated, #f3f4f6) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.skeleton-card-content {
  padding: var(--space-4, 1rem);
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 0.5rem);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-top: none;
  border-radius: 0 0 var(--radius-lg, 0.5rem) var(--radius-lg, 0.5rem);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton,
  .skeleton-card-image {
    animation: none;
    background: var(--color-surface-elevated, #f3f4f6);
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .skeleton,
  .skeleton-card-image {
    background: linear-gradient(
      90deg,
      var(--color-surface-elevated, #1f2937) 25%,
      var(--color-surface-hover, #374151) 50%,
      var(--color-surface-elevated, #1f2937) 75%
    );
    background-size: 200% 100%;
  }

  .skeleton-card-content {
    background: var(--color-surface, #111827);
    border-color: var(--color-border, #374151);
  }
}
</style>
