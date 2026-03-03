<script setup lang="ts">
/**
 * ReliefCarvingView - 3D Relief Carving Designer
 * Design and machine stunning 3D relief carvings for soundhole rosettes,
 * headstock logos, and decorative elements.
 */
import { ref } from 'vue'

const reliefDepth = ref(3)
const toolDiameter = ref(3.175)
const stepover = ref(0.4)
const feedRate = ref(1000)
</script>

<template>
  <div class="relief-carving-view">
    <header class="view-header">
      <h1>3D Relief Carving</h1>
      <p class="subtitle">Design and machine stunning relief carvings for rosettes, logos, and decorative elements</p>
    </header>

    <div class="content-grid">
      <section class="panel upload-panel">
        <h2>Import Design</h2>
        <div class="upload-zone">
          <div class="upload-placeholder">
            <span class="icon">🎨</span>
            <p>Drop grayscale heightmap or SVG</p>
            <p class="hint">PNG, JPG, or SVG files</p>
          </div>
        </div>
      </section>

      <section class="panel params-panel">
        <h2>Carving Parameters</h2>
        <div class="param-group">
          <label>
            Relief Depth (mm)
            <input v-model.number="reliefDepth" type="number" step="0.5" min="0.5" max="25" />
          </label>
          <label>
            Tool Diameter (mm)
            <input v-model.number="toolDiameter" type="number" step="0.125" min="0.5" max="12 " />
          </label>
          <label>
            Stepover (%)
            <input v-model.number="stepover" type="number" step="0.05" min="0.1" max="0.9" />
          </label>
          <label>
            Feed Rate (mm/min)
            <input v-model.number="feedRate" type="number" step="100" min="100" max="5000" />
          </label>
        </div>
        <button class="btn-primary">Generate Toolpath</button>
      </section>

      <section class="panel preview-panel">
        <h2>3D Preview</h2>
        <div class="preview-container">
          <div class="preview-placeholder">
            <span>3D relief preview will appear here</span>
          </div>
        </div>
      </section>

      <section class="panel risk-panel">
        <h2>Risk Analysis</h2>
        <div class="risk-indicators">
          <div class="risk-item safe">
            <span class="indicator"></span>
            <span>Tool engagement: OK</span>
          </div>
          <div class="risk-item safe">
            <span class="indicator"></span>
            <span>Depth of cut: OK</span>
          </div>
          <div class="risk-item safe">
            <span class="indicator"></span>
            <span>Surface finish: Good</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.relief-carving-view {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.panel h2 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1e293b;
}

.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 0.5rem;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}

.upload-zone:hover {
  border-color: #2563eb;
}

.upload-placeholder .icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.upload-placeholder .hint {
  font-size: 0.875rem;
  color: #94a3b8;
}

.param-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.param-group label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.param-group input {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.preview-container {
  aspect-ratio: 4/3;
  background: #f8fafc;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-placeholder {
  color: #94a3b8;
}

.risk-indicators {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.risk-item .indicator {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
}

.risk-item.safe .indicator {
  background: #10b981;
}

.risk-item.warning .indicator {
  background: #f59e0b;
}

.risk-item.danger .indicator {
  background: #ef4444;
}
</style>
