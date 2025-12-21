<template>
  <div class="wrap">
    <PatternLibraryPanel />
    <div class="mid">
      <GeneratorPicker />
      <FeasibilityBanner />
      <SnapshotPanel />
    </div>
    <RosettePreviewPanel />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
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
});

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
@media (max-width: 1100px) {
  .wrap {
    grid-template-columns: 1fr;
  }
}
</style>
