<template>
  <div class="card">
    <div class="row">
      <h3>Snapshots</h3>
      <button class="btn" @click="store.loadRecentSnapshots()" :disabled="store.snapshotsLoading">
        Refresh
      </button>
    </div>
    <div class="row">
      <input class="input" v-model="name" placeholder="Snapshot name" />
      <button class="btn primary" @click="save" :disabled="store.isRedBlocked">Save Snapshot</button>
    </div>
    <div v-if="store.isRedBlocked" class="hint-red">Saving disabled because feasibility is RED.</div>
    <textarea class="input" v-model="notes" rows="2" placeholder="notes (optional)"></textarea>
    <input class="input" v-model="tags" placeholder="tags (comma separated)" />
    <div class="row">
      <input class="input" type="file" accept="application/json" @change="onFile" />
      <button class="btn" @click="exportLast" :disabled="!store.lastSavedSnapshot">Export Last Saved</button>
      <button class="btn" @click="scrollToCompare">Compare…</button>
    </div>
    <div v-if="store.snapshotsError" class="err">{{ store.snapshotsError }}</div>
    <div class="list" v-if="store.snapshots?.length">
      <div
        class="snap"
        :class="{ selected: store.selectedSnapshotId === s.snapshot_id }"
        v-for="s in store.snapshots"
        :key="s.snapshot_id"
        @click="store.selectSnapshot(s.snapshot_id)"
      >
        <div class="left">
          <div class="nm">{{ s.name }}</div>
          <div class="meta">{{ s.snapshot_id }} - {{ new Date(s.updated_at).toLocaleString() }}</div>
        </div>
        <div class="actions" @click.stop>
          <button class="btn" @click="store.loadSnapshot(s.snapshot_id)">Load</button>
          <button class="btn" @click="store.exportSnapshot(s.snapshot_id)">Export</button>
        </div>
      </div>
    </div>

    <ConfidenceDetails
      v-if="selectedSnapshot"
      :current="selectedSnapshot"
      :previous="previousSnapshot"
      :onFocusWorstRing="focusWorstRing"
    />
    <div v-if="!store.snapshots?.length" class="empty">No snapshots yet.</div>
  </div>

  <div id="snapshot-compare" style="margin-top: 12px;">
    <SnapshotComparePanel />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";
import SnapshotComparePanel from "@/components/art/SnapshotComparePanel.vue";
import ConfidenceDetails from "@/components/art/ConfidenceDetails.vue";
import { getRingIndex } from "@/utils/ringFocus";

const store = useRosetteStore();
const toast = useToastStore();
const name = ref("");
const notes = ref("");
const tags = ref("");

// Per Bundle 32.3.0 spec S2.3: use store.selectedSnapshotId
const selectedSnapshot = computed(() => {
  const id = store.selectedSnapshotId;
  return (store.snapshots || []).find((s: any) => s.snapshot_id === id) || null;
});

const previousSnapshot = computed(() => {
  if (!selectedSnapshot.value) return null;
  const snaps = store.snapshots || [];
  const idx = snaps.findIndex((s: any) => s.snapshot_id === selectedSnapshot.value!.snapshot_id);
  // previous in time = next index (because newest-first)
  if (idx < 0) return null;
  return snaps[idx + 1] || null;
});

function parseTags(s: string) {
  return (s || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

async function save() {
  if (!name.value.trim()) {
    toast.push("warning", "Enter a snapshot name.");
    return;
  }
  await store.saveSnapshot({ name: name.value.trim(), notes: notes.value, tags: parseTags(tags.value) });
}

async function exportLast() {
  const sid = store.lastSavedSnapshot?.snapshot_id;
  if (!sid) return;
  await store.exportSnapshot(sid);
}

function onFile(evt: Event) {
  const input = evt.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async () => {
    const txt = String(reader.result || "");
    await store.importSnapshotFromJsonText(txt);
    input.value = "";
  };
  reader.readAsText(file);
}

function scrollToCompare() {
  document.getElementById("snapshot-compare")?.scrollIntoView({ behavior: "smooth" });
}

// -------------------------
// Ring Focus (Bundle 32.3.1)
// -------------------------
function focusWorstRing(diag: any) {
  const idx = getRingIndex(diag);
  if (idx == null) return;
  store.focusRing(idx);
}

// Scroll + highlight ring when focusedRingIndex changes
watch(
  () => store.focusedRingIndex,
  async (idx) => {
    if (idx == null) return;

    await nextTick();

    const el = document.querySelector(
      `[data-ring-index="${idx}"]`
    ) as HTMLElement | null;

    if (!el) {
      // If no DOM element yet, just log for debugging; future ring editor will have this
      console.debug(`[ringFocus] No element found for data-ring-index="${idx}"`);
      return;
    }

    el.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });

    el.classList.add("ring-focus");
    setTimeout(() => el.classList.remove("ring-focus"), 1200);
  }
);
</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0;
  flex-wrap: wrap;
}
.input {
  flex: 1;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 8px;
  min-width: 160px;
}
.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
.btn.primary {
  background: #111;
  color: #fff;
  border-color: #111;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
  max-height: 280px;
  overflow: auto;
}
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
.err {
  color: #a00;
  margin: 8px 0;
}
.empty {
  color: #666;
  font-size: 13px;
  padding: 10px;
}
.hint-red {
  font-size: 12px;
  color: #a00;
  margin: 4px 0;
}
.snap {
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.snap:hover {
  border-color: #ccc;
}
.snap.selected {
  border-color: #111;
  background: #f0f0f0;
}

/* Ring focus highlight (Bundle 32.3.1) */
:global(.ring-focus) {
  outline: 2px solid #ff9800;
  outline-offset: 2px;
  background: rgba(255, 152, 0, 0.08);
  transition: background 0.3s ease;
}
</style>
