<script setup lang="ts">
/**
 * AssetQuickOpsPanel - Quick reject/promote/undo operations for an asset
 * Extracted from AiImageGallery.vue
 */
import type { RejectReasonCode } from '@/sdk/rmos/runs'

const props = defineProps<{
  advisoryId: string
  variant: {
    rejected?: boolean | null
    promoted?: boolean | null
    status?: string | null
  } | null
  promoteDisabledReason: string | null
  canUndoRejectReason: string | null
  busy: string | null
}>()

const emit = defineEmits<{
  'quick-promote': [advisoryId: string]
  'undo-reject': [advisoryId: string]
  'quick-reject': [advisoryId: string, reason: RejectReasonCode]
}>()

function handleRejectChange(ev: Event) {
  const target = ev.target as HTMLSelectElement
  const v = target.value as RejectReasonCode
  if (v) {
    emit('quick-reject', props.advisoryId, v)
    target.value = ''
  }
}
</script>

<template>
  <div class="assetOps">
    <div class="row">
      <button
        class="btn small primary"
        type="button"
        :disabled="Boolean(promoteDisabledReason) || !!busy"
        :title="promoteDisabledReason || 'Promote to manufacturing candidate'"
        @click="emit('quick-promote', advisoryId)"
      >
        {{ busy === 'promote' ? 'Promoting…' : 'Quick Promote' }}
      </button>

      <button
        v-if="variant?.rejected"
        class="btn small"
        type="button"
        :disabled="!!canUndoRejectReason || !!busy"
        :title="canUndoRejectReason || 'Clear rejection (Undo Reject)'"
        @click="emit('undo-reject', advisoryId)"
      >
        {{ busy === 'review' ? 'Clearing…' : 'Undo Reject' }}
      </button>

      <select
        class="select small"
        :disabled="!!busy"
        title="Reject this variant (records reason code)"
        @change="handleRejectChange"
      >
        <option value="">
          Quick Reject…
        </option>
        <option value="GEOMETRY_UNSAFE">
          GEOMETRY_UNSAFE
        </option>
        <option value="TEXT_REQUIRES_OUTLINE">
          TEXT_REQUIRES_OUTLINE
        </option>
        <option value="AESTHETIC">
          AESTHETIC
        </option>
        <option value="DUPLICATE">
          DUPLICATE
        </option>
        <option value="OTHER">
          OTHER
        </option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.assetOps {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.assetOps .row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.btn {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}
.btn.primary { background: rgba(0,0,0,0.08); font-weight: 600; }
.btn.small { padding: 6px 10px; font-size: 12px; border-radius: 10px; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.select {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
}
.select.small {
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 10px;
}
</style>
