<script setup lang="ts">
/**
 * RmosRunsView.vue
 *
 * Route wrapper for the Run Artifacts browser.
 * Combines RunArtifactPanel (list) and RunArtifactDetail (selected).
 */
import { useRmosRunsStore } from "@/stores/rmosRunsStore";
import RunArtifactPanel from "@/components/rmos/RunArtifactPanel.vue";
import RunArtifactDetail from "@/components/rmos/RunArtifactDetail.vue";

const store = useRmosRunsStore();
</script>

<template>
  <div class="rmos-runs-view">
    <header class="view-header">
      <div>
        <h1>Run Artifacts</h1>
        <p class="subtitle">
          Browse and inspect RMOS manufacturing run artifacts.
          <router-link to="/rmos/runs/diff">Open Diff Viewer →</router-link>
        </p>
      </div>
    </header>

    <div class="main-content">
      <!-- Master: Run List -->
      <div class="panel-list">
        <RunArtifactPanel />
      </div>

      <!-- Detail: Selected Run -->
      <div class="panel-detail">
        <template v-if="store.selected">
          <RunArtifactDetail :artifact="store.selected" />
        </template>
        <template v-else>
          <div class="no-selection">
            <p>Select a run from the list to view details.</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rmos-runs-view {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.view-header {
  margin-bottom: 1.5rem;
}

.view-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.subtitle {
  margin: 0.5rem 0 0 0;
  color: #6c757d;
}

.subtitle a {
  color: #0066cc;
  margin-left: 0.5rem;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

.panel-list {
  min-height: 400px;
}

.panel-detail {
  position: sticky;
  top: 1rem;
}

.no-selection {
  padding: 3rem;
  text-align: center;
  color: #6c757d;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}
</style>
