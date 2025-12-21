<template>
  <div class="card">
    <div class="row">
      <h3>Preview</h3>
      <button class="btn" @click="store.refreshPreview()" :disabled="store.previewLoading">
        Refresh
      </button>
    </div>
    <div v-if="store.previewError" class="err">{{ store.previewError }}</div>
    <div v-if="store.preview?.warnings?.length" class="warn">
      <div><strong>Preview warnings:</strong></div>
      <ul>
        <li v-for="(w, i) in store.preview.warnings" :key="i">{{ w }}</li>
      </ul>
    </div>
    <div class="svgWrap" v-if="store.preview?.svg" v-html="store.preview.svg"></div>
    <div v-else class="empty">No preview yet.</div>
  </div>
</template>

<script setup lang="ts">
import { useRosetteStore } from "@/stores/rosetteStore";
const store = useRosetteStore();
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
  margin-bottom: 8px;
}
.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
.svgWrap {
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 10px;
  background: #fff;
  overflow: auto;
}
.empty {
  color: #666;
  font-size: 13px;
  padding: 10px;
}
.err {
  color: #a00;
  margin: 8px 0;
}
.warn {
  margin: 8px 0;
  padding: 10px;
  border-radius: 10px;
  background: #fff7e6;
  border: 1px solid #f1d199;
}
</style>
