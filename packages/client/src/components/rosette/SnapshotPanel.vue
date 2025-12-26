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
      <div class="snap" v-for="s in store.snapshots" :key="s.snapshot_id">
        <div class="left">
          <div class="nm">{{ s.name }}</div>
          <div class="meta">{{ s.snapshot_id }} - {{ new Date(s.updated_at).toLocaleString() }}</div>
        </div>
        <div class="actions">
          <button class="btn" @click="store.loadSnapshot(s.snapshot_id)">Load</button>
          <button class="btn" @click="store.exportSnapshot(s.snapshot_id)">Export</button>
        </div>
      </div>
    </div>
    <div v-else class="empty">No snapshots yet.</div>
  </div>

  <div id="snapshot-compare" style="margin-top: 12px;">
    <SnapshotComparePanel />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";
import SnapshotComparePanel from "@/components/art/SnapshotComparePanel.vue";

const store = useRosetteStore();
const toast = useToastStore();
const name = ref("");
const notes = ref("");
const tags = ref("");

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
</style>
