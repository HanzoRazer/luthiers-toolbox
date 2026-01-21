<!-- Patch N11.2 - TilePreviewCanvas scaffolding -->

<template>
  <div class="tile-preview">
    <h2>Tile Preview (Stub)</h2>

    <div v-if="!segmentation">
      <p>No segmentation yet. Click "Segment Ring" to compute a stub layout.</p>
    </div>

    <div v-else>
      <p>
        Stub segmentation:
        {{ segmentation.tile_count }} tiles
      </p>
      <ul>
        <li
          v-for="tile in segmentation.tiles"
          :key="tile.tile_index"
        >
          Tile {{ tile.tile_index }}:
          [{{ tile.theta_start_deg.toFixed(1) }}°
          → {{ tile.theta_end_deg.toFixed(1) }}°]
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()
const segmentation = computed(() => store.segmentation)
</script>

<style scoped>
.tile-preview {
  font-size: 0.9rem;
  max-height: 400px;
  overflow: auto;
}
</style>
