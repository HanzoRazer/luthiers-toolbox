<template>
  <div class="wf-actions">
    <button :disabled="busy" class="btn" @click="$emit('ensure')">
      {{ hasSession ? 'Restart' : 'Start' }}
    </button>
    <button :disabled="busy || !hasSession" class="btn" @click="$emit('toReview')">
      Review
    </button>
    <button :disabled="busy || !hasSession" class="btn" @click="$emit('approve')">
      Approve
    </button>
    <button :disabled="busy || !hasSession" class="btn ghost" @click="$emit('reject')">
      Reject
    </button>
    <button :disabled="busy || !hasSession" class="btn ghost" @click="$emit('reopen')">
      Reopen
    </button>
    <button :disabled="busy || !canIntent" class="btn primary" @click="$emit('intent')">
      Get CAM Handoff Intent
    </button>
    <button
      :disabled="busy || !canIntent"
      class="btn"
      title="Phase 33.0: Promote to downstream CAM request (does NOT execute)"
      @click="$emit('promoteToCam')"
    >
      Promote to CAM Request
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  busy: boolean
  hasSession: boolean
  canIntent: boolean
}>()

defineEmits<{
  ensure: []
  toReview: []
  approve: []
  reject: []
  reopen: []
  intent: []
  promoteToCam: []
}>()
</script>

<style scoped>
.wf-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn.primary {
  background: rgba(0, 0, 0, 0.06);
  font-weight: 600;
}

.btn.ghost {
  background: transparent;
}
</style>
