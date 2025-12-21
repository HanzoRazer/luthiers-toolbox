<template>
  <div class="card">
    <div class="row">
      <h3>Pattern Library</h3>
      <button class="btn" @click="store.loadPatterns()" :disabled="store.patternsLoading">Refresh</button>
    </div>
    <div class="filters">
      <input class="input" v-model="q" placeholder="Search..." />
      <input class="input" v-model="tag" placeholder="Tag..." />
      <button class="btn" @click="applyFilters">Filter</button>
    </div>
    <div v-if="store.patternsError" class="err">{{ store.patternsError }}</div>
    <div class="list" v-if="store.patterns?.length">
      <button
        class="item"
        v-for="p in store.patterns"
        :key="p.pattern_id"
        @click="store.openPattern(p.pattern_id)"
      >
        <div class="name">{{ p.name }}</div>
        <div class="meta">{{ p.generator_key }}</div>
        <div class="tags">
          <span class="tag" v-for="t in p.tags" :key="t">{{ t }}</span>
        </div>
      </button>
    </div>
    <div v-else class="empty">No patterns yet.</div>
    <hr class="hr" />
    <h4>Save Current as Pattern</h4>
    <input class="input" v-model="newName" placeholder="Pattern name" />
    <input class="input" v-model="newTags" placeholder="tags (comma separated)" />
    <textarea class="input" v-model="newDesc" rows="3" placeholder="description (optional)"></textarea>
    <div class="row">
      <button class="btn primary" @click="savePattern">Save</button>
      <button class="btn danger" @click="store.deleteSelectedPattern()" :disabled="!store.selectedPattern">
        Delete Selected
      </button>
    </div>
    <div class="hint" v-if="store.selectedPattern">
      <div class="small"><strong>Selected:</strong> {{ store.selectedPattern.name }}</div>
      <div class="small">ID: {{ store.selectedPattern.pattern_id }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";

const store = useRosetteStore();
const q = ref("");
const tag = ref("");
const newName = ref("");
const newTags = ref("");
const newDesc = ref("");

function applyFilters() {
  store.loadPatterns({ q: q.value || undefined, tag: tag.value || undefined });
}

function parseTags(s: string) {
  return (s || "")
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

async function savePattern() {
  if (!newName.value.trim()) return;
  await store.saveCurrentAsPattern({
    name: newName.value.trim(),
    description: newDesc.value || undefined,
    tags: parseTags(newTags.value),
  });
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
.filters {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.input {
  flex: 1;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 8px;
  min-width: 120px;
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
.btn.danger {
  background: #fee;
  border-color: #f7b;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow: auto;
}
.item {
  text-align: left;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid #eee;
  background: #fafafa;
  cursor: pointer;
}
.item:hover {
  background: #f3f3f3;
}
.name {
  font-weight: 600;
}
.meta {
  font-size: 12px;
  color: #444;
  margin-top: 2px;
}
.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.tag {
  font-size: 11px;
  padding: 2px 8px;
  border: 1px solid #ddd;
  border-radius: 999px;
  background: #fff;
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
.hr {
  margin: 12px 0;
  border: none;
  border-top: 1px solid #eee;
}
.hint {
  margin-top: 10px;
  padding: 8px;
  border-radius: 10px;
  background: #fafafa;
  border: 1px solid #eee;
}
.small {
  font-size: 12px;
  color: #333;
}
h4 {
  margin: 10px 0 6px;
}
</style>
