<script setup lang="ts">
/**
 * DiffSkeletonLoader - Loading skeleton for diff computation
 * Extracted from DualSvgDisplay.vue
 */
</script>

<template>
  <div class="skeleton-container">
    <div class="skeleton-pane left">
      <div class="skeleton-shimmer" />
      <p class="skeleton-label">
        Computing diff...
      </p>
    </div>
    <div class="skeleton-pane right">
      <div class="skeleton-shimmer" />
      <p class="skeleton-label">
        Computing diff...
      </p>
    </div>
  </div>
</template>

<style scoped>
.skeleton-container {
  display: flex;
  gap: 2rem;
}

.skeleton-pane {
  flex: 1;
  background: #f5f5f5;
  border: 1px solid #ddd;
  padding: 1rem;
  border-radius: 8px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.skeleton-shimmer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.6) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.skeleton-label {
  position: relative;
  z-index: 1;
  color: #999;
  font-size: 0.9rem;
  font-style: italic;
}
</style>
