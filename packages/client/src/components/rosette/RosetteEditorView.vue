<template>
  <div class="wrap">
    <PatternLibraryPanel />
    <div class="mid">
      <div class="toolbar" v-if="store.problematicRingIndices.length > 0">
        <button
          class="jump-btn"
          type="button"
          title="Jump to next problematic ring (])"
          @click="jumpNext"
        >
          Next problem ({{ store.problematicRingIndices.length }})
        </button>
      </div>
      <GeneratorPicker />
      <FeasibilityBanner />
      <SnapshotPanel />
    </div>
    <RosettePreviewPanel />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import PatternLibraryPanel from "./PatternLibraryPanel.vue";
import GeneratorPicker from "./GeneratorPicker.vue";
import RosettePreviewPanel from "./RosettePreviewPanel.vue";
import SnapshotPanel from "./SnapshotPanel.vue";
import FeasibilityBanner from "./FeasibilityBanner.vue";

const store = useRosetteStore();

onMounted(async () => {
  await store.loadPatterns();
  await store.loadGenerators();
  await store.loadRecentSnapshots();
  await store.refreshPreviewAndFeasibility();

  // Keyboard shortcut: ] = jump to next problematic ring (Bundle 32.3.3)
  window.addEventListener("keydown", onKeyDown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
});

function onKeyDown(e: KeyboardEvent) {
  // ] key -> jump to next problematic ring
  if (e.key === "]" && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    store.jumpToNextProblemRing();
  }
}

function jumpNext() {
  store.jumpToNextProblemRing();
}

// Auto refresh: debounce on any param change
watch(
  () => store.currentParams,
  () => {
    store.requestAutoRefresh();
  },
  { deep: true }
);
</script>

<style scoped>
.wrap {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  padding: 12px;
}
.mid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
}
.jump-btn {
  font-size: 11px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid #f3bcbc;
  background: #fdeaea;
  color: #a00;
  cursor: pointer;
}
.jump-btn:hover {
  background: #fbd5d5;
}
@media (max-width: 1100px) {
  .wrap {
    grid-template-columns: 1fr;
  }
}
</style>
