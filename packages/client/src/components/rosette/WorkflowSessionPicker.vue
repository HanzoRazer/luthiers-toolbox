<template>
  <div class="picker">
    <div class="hdr">
      <div class="t">
        Recent workflow sessions
      </div>
      <button
        class="ghost"
        :disabled="loading"
        title="Refresh list"
        @click="refresh"
      >
        Refresh
      </button>
    </div>

    <div
      v-if="err"
      class="err"
    >
      {{ err }}
    </div>

    <div class="list">
      <button
        v-for="it in items"
        :key="it.session_id"
        class="row"
        :data-s="it.state"
        :data-active="it.session_id === currentId"
        :title="it.session_id"
        @click="open(it.session_id)"
      >
        <div class="a">
          <span class="id">{{ it.session_id.slice(0, 8) }}</span>
          <span class="st">{{ it.state }}</span>
          <span
            v-if="it.risk_bucket"
            class="risk"
          >• {{ it.risk_bucket }}</span>
        </div>
        <div class="b">
          <span class="ts">{{ fmtAge(it.updated_at) }}</span>
          <button
            class="del"
            title="Delete session"
            @click.stop="del(it.session_id)"
          >
            ×
          </button>
        </div>
      </button>
    </div>

    <div class="more">
      <button
        v-if="nextCursor"
        class="ghost"
        :disabled="loading"
        @click="loadMore"
      >
        Load more
      </button>
      <span
        v-else
        class="end"
      >End</span>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * WorkflowSessionPicker.vue (Bundle 32.7.7)
 *
 * Panel to list recent design-first workflow sessions.
 * Allows jumping between sessions and deleting stale ones.
 */
import { computed, onMounted, ref } from "vue";
import { useToastStore } from "@/stores/toastStore";
import { useArtDesignFirstWorkflowStore } from "@/stores/artDesignFirstWorkflowStore";
import {
  deleteWorkflowSession,
  listRecentWorkflowSessions,
  type WorkflowSessionSummary,
} from "@/sdk/endpoints/artDesignFirstWorkflowSessions";

const toast = useToastStore();
const wf = useArtDesignFirstWorkflowStore();

const items = ref<WorkflowSessionSummary[]>([]);
const nextCursor = ref<string | null>(null);
const loading = ref(false);
const err = ref<string | null>(null);

const currentId = computed(() => wf.session?.session_id ?? "");

function fmtAge(iso: string) {
  const t = new Date(iso).getTime();
  const s = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

async function refresh() {
  loading.value = true;
  err.value = null;
  try {
    const res = await listRecentWorkflowSessions(30);
    items.value = res.items;
    nextCursor.value = res.next_cursor ?? null;
  } catch (e: unknown) {
    err.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

async function loadMore() {
  if (!nextCursor.value) return;
  loading.value = true;
  err.value = null;
  try {
    const res = await listRecentWorkflowSessions(30, nextCursor.value);
    items.value = items.value.concat(res.items);
    nextCursor.value = res.next_cursor ?? null;
  } catch (e: unknown) {
    err.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

async function open(id: string) {
  await wf.loadSessionById(id);
  toast.info(`Loaded session ${id.slice(0, 8)}…`);
}

async function del(id: string) {
  const ok = await deleteWorkflowSession(id)
    .then(() => true)
    .catch(() => false);
  if (ok) {
    items.value = items.value.filter((x) => x.session_id !== id);
    toast.warning("Deleted workflow session.");
    // If deleting currently loaded session, clear store
    if (wf.session?.session_id === id) wf.clearSession();
  } else {
    toast.error("Delete failed.");
  }
}

onMounted(refresh);
</script>

<style scoped>
.picker {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 10px;
  margin: 10px 0;
}

.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.t {
  font-weight: 800;
  font-size: 13px;
}

.err {
  color: #b00020;
  font-size: 12px;
  margin-top: 6px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.row {
  width: 100%;
  text-align: left;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 8px 10px;
  background: white;
  cursor: pointer;
}

.row[data-active="true"] {
  outline: 2px solid rgba(0, 0, 0, 0.18);
}

.a {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
}

.st {
  font-size: 12px;
  padding: 2px 7px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.12);
}

.row[data-s="approved"] .st {
  background: rgba(0, 200, 0, 0.1);
}

.row[data-s="rejected"] .st {
  background: rgba(200, 0, 0, 0.1);
}

.row[data-s="in_review"] .st {
  background: rgba(200, 160, 0, 0.1);
}

.risk {
  font-size: 12px;
  opacity: 0.75;
}

.b {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ts {
  font-size: 12px;
  opacity: 0.7;
}

.del {
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 10px;
  padding: 2px 8px;
  background: transparent;
  cursor: pointer;
  opacity: 0.7;
}

.more {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.end {
  font-size: 12px;
  opacity: 0.6;
}

button.ghost {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  padding: 5px 9px;
  background: transparent;
}
</style>
