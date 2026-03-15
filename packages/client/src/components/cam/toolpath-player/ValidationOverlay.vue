<script setup lang="ts">
/**
 * ValidationOverlay — G-code validation error display for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows validation errors with option to load anyway.
 */

import type { ValidationIssue } from '@/util/gcodeValidator';

interface Props {
  errors: ValidationIssue[];
}

defineProps<Props>();

const emit = defineEmits<{
  loadAnyway: [];
}>();
</script>

<template>
  <div class="error-overlay">
    <div class="error-box">
      <span class="error-icon">
        ⚠️
      </span>
      <div class="error-info">
        <strong>G-code has errors</strong>
        <ul class="error-list">
          <li
            v-for="iss in errors.slice(0, 3)"
            :key="iss.code + iss.line"
          >
            Line {{ iss.line }}: {{ iss.message }}
          </li>
        </ul>
      </div>
      <button
        class="btn-retry"
        @click="emit('loadAnyway')"
      >
        Load anyway
      </button>
    </div>
  </div>
</template>

<style scoped>
.error-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
  color: #e74c3c;
  background: rgba(30, 30, 46, 0.85);
  z-index: 5;
}

.error-box {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  background: #2a1a1a;
  border: 1px solid #e74c3c;
  border-radius: 8px;
  max-width: 460px;
}

.error-icon {
  font-size: 28px;
}

.error-info {
  flex: 1;
}

.error-list {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 11px;
  color: #e74c3c;
}

.btn-retry {
  padding: 5px 14px;
  background: #e74c3c;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  align-self: center;
}

.btn-retry:hover {
  background: #c0392b;
}
</style>
