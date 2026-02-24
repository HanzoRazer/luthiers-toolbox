<script setup lang="ts">
/**
 * SnapshotCard - Unified left/right snapshot display card
 * Extracted from CompareOpenPanel.vue
 */

type AnySnap = any

defineProps<{
  snapshot: AnySnap
  label: 'Left' | 'Right'
}>()

const emit = defineEmits<{
  'load-snapshot': [snapshotId: string]
}>()

function fmtDate(s: any) {
  try {
    return new Date(String(s)).toLocaleString()
  } catch {
    return String(s || '')
  }
}
</script>

<template>
  <div class="snap">
    <div class="left">
      <div class="nm">
        {{ label }}: {{ snapshot.name || snapshot.snapshot_id }}
      </div>
      <div class="meta">
        {{ snapshot.snapshot_id }} - {{ fmtDate(snapshot.updated_at || snapshot.created_at) }}
        <span v-if="snapshot.baseline === true"> • BASELINE</span>
      </div>
      <div
        v-if="snapshot.notes"
        class="meta"
      >
        Notes: {{ snapshot.notes }}
      </div>
    </div>
    <div class="actions">
      <button
        class="btn"
        @click="emit('load-snapshot', snapshot.snapshot_id)"
      >
        Load
      </button>
    </div>
  </div>
</template>

<style scoped>
.snap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 12px;
  background: #fafafa;
}

.left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nm {
  font-weight: 600;
}

.meta {
  font-size: 12px;
  color: #444;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
</style>
