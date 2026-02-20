<template>
  <section
    v-if="camResults"
    class="form-section cam-results"
  >
    <h3>CAM Toolpath Statistics</h3>

    <!-- Statistics Grid -->
    <div class="stats-grid">
      <div class="stat-item">
        <span class="stat-label">Total Length:</span>
        <span class="stat-value">{{ camResults.stats.length_mm.toFixed(2) }} mm</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Pocket Area:</span>
        <span class="stat-value">{{ camResults.stats.area_mm2.toFixed(2) }} mm²</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Machining Time:</span>
        <span class="stat-value">
          {{ camResults.stats.time_min.toFixed(2) }} min ({{ camResults.stats.time_s.toFixed(1) }}s)
        </span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Material Volume:</span>
        <span class="stat-value">{{ camResults.stats.volume_mm3.toFixed(2) }} mm³</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Move Count:</span>
        <span class="stat-value">{{ camResults.stats.move_count }}</span>
      </div>
    </div>

    <!-- CAM Parameters -->
    <div class="cam-params">
      <h4>CAM Parameters Used:</h4>
      <ul>
        <li>
          <strong>Tool Diameter:</strong> {{ camResults.cam_params.tool_d }} mm
        </li>
        <li>
          <strong>Stepover:</strong> {{ (camResults.cam_params.stepover * 100).toFixed(0) }}%
          ({{ (camResults.cam_params.tool_d * camResults.cam_params.stepover).toFixed(2) }} mm)
        </li>
        <li>
          <strong>Strategy:</strong> {{ camResults.cam_params.strategy }}
        </li>
      </ul>
    </div>

    <!-- Download Actions -->
    <div class="cam-actions">
      <button
        class="btn-primary"
        @click="emit('download')"
      >
        Download G-code ({{ selectedPost }})
      </button>
      <select
        :value="selectedPost"
        class="post-selector"
        @change="emit('update:selectedPost', ($event.target as HTMLSelectElement).value)"
      >
        <option value="GRBL">
          GRBL
        </option>
        <option value="Mach3">
          Mach3
        </option>
        <option value="Mach4">
          Mach4
        </option>
        <option value="LinuxCNC">
          LinuxCNC
        </option>
        <option value="PathPilot">
          PathPilot
        </option>
      </select>
    </div>

    <!-- Move Preview -->
    <details class="move-preview">
      <summary>Preview First 20 Moves</summary>
      <pre class="gcode-preview">{{ movesPreview }}</pre>
    </details>
  </section>
</template>

<script setup lang="ts">
import type { CamResults } from '../composables/useGuitarCAM'

defineProps<{
  camResults: CamResults | null
  selectedPost: string
  movesPreview: string
}>()

const emit = defineEmits<{
  download: []
  'update:selectedPost': [value: string]
}>()
</script>

<style scoped>
.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
}

.cam-results {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1.5rem;
  border-bottom: none;
}

.cam-results h3 {
  margin-top: 0;
  font-size: 1.4rem;
  margin-bottom: 1rem;
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-item {
  background: rgba(255, 255, 255, 0.15);
  padding: 1rem;
  border-radius: 6px;
  backdrop-filter: blur(10px);
}

.stat-label {
  display: block;
  font-size: 0.85rem;
  opacity: 0.9;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.stat-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
}

.cam-params {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.cam-params h4 {
  margin-top: 0;
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
}

.cam-params ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.cam-params li {
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.cam-params li:last-child {
  border-bottom: none;
}

.cam-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.post-selector {
  padding: 0.6rem 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.post-selector:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.post-selector option {
  background: #764ba2;
  color: white;
}

.move-preview {
  background: rgba(0, 0, 0, 0.2);
  padding: 0.75rem;
  border-radius: 6px;
  margin-top: 1rem;
}

.move-preview summary {
  cursor: pointer;
  font-weight: 600;
  padding: 0.5rem;
  user-select: none;
}

.move-preview summary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.gcode-preview {
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  overflow-x: auto;
  margin-top: 0.75rem;
  white-space: pre;
}
</style>
