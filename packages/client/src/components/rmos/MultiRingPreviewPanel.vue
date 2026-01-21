<!-- Patch N12.2 - MultiRingPreviewPanel scaffolding -->

<template>
  <div class="multi-ring-preview">
    <h2>Multi-Ring Preview (Summary)</h2>

    <button
      :disabled="loading"
      @click="onRefresh"
    >
      Refresh Preview
    </button>

    <p v-if="loading">
      Building preview...
    </p>

    <div
      v-if="preview && preview.rings.length"
      class="summary-table"
    >
      <table>
        <thead>
          <tr>
            <th>Ring ID</th>
            <th>Radius (mm)</th>
            <th>Width (mm)</th>
            <th>Tile Count</th>
            <th>Slice Count</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="ring in preview.rings"
            :key="ring.ring_id"
          >
            <td>{{ ring.ring_id }}</td>
            <td>{{ ring.radius_mm.toFixed(2) }}</td>
            <td>{{ ring.width_mm.toFixed(2) }}</td>
            <td>{{ ring.tile_count }}</td>
            <td>{{ ring.slice_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading">
      No preview yet. Add one or more rings, then click "Refresh Preview".
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

const loading = computed(() => store.loading)
const preview = computed(() => store.preview)

function onRefresh() {
  // patternId is optional for now
  store.fetchPreview(null)
}
</script>
