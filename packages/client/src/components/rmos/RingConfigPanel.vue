<!-- Patch N11.2 - RingConfigPanel scaffolding -->

<template>
  <div class="ring-config-panel">
    <h2>Ring Configuration (Stub)</h2>

    <div v-if="!currentRing">
      <p>No ring selected. Click "Add Ring" above.</p>
    </div>

    <div v-else class="form">
      <label>
        Radius (mm)
        <input type="number" v-model.number="currentRing.radius_mm" />
      </label>

      <label>
        Width (mm)
        <input type="number" v-model.number="currentRing.width_mm" />
      </label>

      <label>
        Tile length (mm)
        <input type="number" v-model.number="currentRing.tile_length_mm" />
      </label>

      <label>
        Kerf (mm)
        <input type="number" v-model.number="currentRing.kerf_mm" />
      </label>

      <label>
        Herringbone angle (deg)
        <input type="number" v-model.number="currentRing.herringbone_angle_deg" />
      </label>

      <label>
        Twist angle (deg)
        <input type="number" v-model.number="currentRing.twist_angle_deg" />
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRosetteDesignerStore } from '@/stores/useRosetteDesignerStore'

const store = useRosetteDesignerStore()

const currentRing = computed(() => {
  if (store.selectedRingId === null) return null
  return store.rings.find(r => r.ring_id === store.selectedRingId) || null
})
</script>

<style scoped>
.ring-config-panel {
  font-size: 0.9rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.form input {
  padding: 0.25rem 0.4rem;
  font-size: 0.9rem;
}
</style>
