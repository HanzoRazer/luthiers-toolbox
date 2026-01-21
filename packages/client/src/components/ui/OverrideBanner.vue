<script setup lang="ts">
/**
 * OverrideBanner.vue - Always-visible banner when an override is applied
 *
 * Rule: If a run has decision.override_reason OR an override artifact,
 * this banner MUST be visible without clicking anything.
 */

const props = defineProps<{
  reason?: string | null
  overrideArtifact?: { sha256?: string; created_at?: string } | null
}>()

const hasOverride = computed(() => {
  return Boolean(props.reason) || Boolean(props.overrideArtifact)
})

const displayReason = computed(() => {
  return props.reason || 'Override recorded (see artifact for details)'
})

import { computed } from 'vue'
</script>

<template>
  <div
    v-if="hasOverride"
    class="override-banner"
    role="alert"
  >
    <span
      class="override-icon"
      aria-hidden="true"
    >⚡</span>
    <div class="override-content">
      <strong class="override-title">Override Applied</strong>
      <p class="override-reason">
        {{ displayReason }}
      </p>
      <span
        v-if="overrideArtifact?.sha256"
        class="override-meta"
      >
        SHA: <code>{{ overrideArtifact.sha256.slice(0, 12) }}…</code>
      </span>
    </div>
  </div>
</template>

<style scoped>
.override-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #fef9c3;
  border: 1px solid #eab308;
  border-left: 4px solid #ca8a04;
  border-radius: 0.375rem;
  margin: 0.5rem 0;
}

.override-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.override-content {
  flex: 1;
  min-width: 0;
}

.override-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #854d0e;
  margin-bottom: 0.25rem;
}

.override-reason {
  font-size: 0.8125rem;
  color: #713f12;
  margin: 0;
  word-break: break-word;
}

.override-meta {
  display: block;
  font-size: 0.75rem;
  color: #a16207;
  margin-top: 0.25rem;
}

.override-meta code {
  font-family: ui-monospace, monospace;
  background: rgba(255, 255, 255, 0.5);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}
</style>
