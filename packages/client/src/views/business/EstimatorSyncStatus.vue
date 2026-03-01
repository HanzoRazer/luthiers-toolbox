<script setup lang="ts">
import { ref, onMounted } from "vue";

interface SyncState { synced: boolean; lastSync: Date | null; pendingCount: number; error: string | null; }
const state = ref<SyncState>({ synced: true, lastSync: null, pendingCount: 0, error: null });
const syncing = ref(false);

function formatTime(d: Date | null): string {
  if (!d) return "Never";
  const now = new Date();
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000);
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return d.toLocaleDateString();
}

async function syncNow(): Promise<void> {
  syncing.value = true;
  state.value.error = null;
  try {
    // Simulate API sync - in production would call backend
    await new Promise((r) => setTimeout(r, 800));
    state.value.synced = true;
    state.value.lastSync = new Date();
    state.value.pendingCount = 0;
  } catch (e) {
    state.value.error = e instanceof Error ? e.message : "Sync failed";
  } finally {
    syncing.value = false;
  }
}

onMounted(() => {
  const saved = localStorage.getItem("ltb:estimator:sync:v1");
  if (saved) {
    try {
      const p = JSON.parse(saved);
      state.value.lastSync = p.lastSync ? new Date(p.lastSync) : null;
    } catch { /* ignore */ }
  }
});
</script>

<template>
  <div class="sync-status" :class="{ synced: state.synced, pending: state.pendingCount > 0 }">
    <div class="status-indicator">
      <span v-if="syncing" class="spinner"></span>
      <span v-else-if="state.synced" class="dot green"></span>
      <span v-else class="dot yellow"></span>
    </div>
    <div class="status-text">
      <span v-if="syncing">Syncing...</span>
      <span v-else-if="state.error" class="error">{{ state.error }}</span>
      <span v-else-if="state.pendingCount > 0">{{ state.pendingCount }} pending</span>
      <span v-else>Synced {{ formatTime(state.lastSync) }}</span>
    </div>
    <button v-if="!syncing" type="button" class="btn-sync" @click="syncNow" title="Sync now">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.sync-status { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: #14192a; border: 1px solid #1e2438; border-radius: 4px; font-size: 10px; }
.status-indicator { display: flex; align-items: center; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot.green { background: #30a050; box-shadow: 0 0 4px #30a050; }
.dot.yellow { background: #c0a030; box-shadow: 0 0 4px #c0a030; }
.spinner { width: 10px; height: 10px; border: 2px solid #2a3040; border-top-color: #4080f0; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.status-text { color: #8090b0; flex: 1; }
.status-text .error { color: #e05050; }
.btn-sync { width: 22px; height: 22px; padding: 0; display: flex; align-items: center; justify-content: center; background: transparent; border: 1px solid #2a3040; color: #6080b0; border-radius: 3px; cursor: pointer; }
.btn-sync:hover { background: #1a2030; color: #a0b0d0; }
</style>
