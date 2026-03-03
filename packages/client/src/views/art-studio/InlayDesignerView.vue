<script setup lang="ts">
/**
 * InlayDesignerView - Inlay Pattern Designer
 * Create and machine decorative inlays for fretboards, headstocks,
 * and body ornamentation.
 */
import { ref } from 'vue'

const inlayMaterial = ref('mother-of-pearl')
const pocketDepth = ref(1.5)
const toolDiameter = ref(1.0)
const clearanceOffset = ref(0.05)
</script>

<template>
  <div class="inlay-designer-view">
    <header class="view-header">
      <h1>Inlay Designer</h1>
      <p class="subtitle">Create and machine decorative inlays for fretboards, headstocks, and body ornamentation</p>
    </header>

    <div class="content-grid">
      <section class="panel design-panel">
        <h2>Design Canvas</h2>
        <div class="canvas-container">
          <div class="canvas-placeholder">
            <span class="icon">💎</span>
            <p>Draw or import inlay design</p>
            <p class="hint">SVG, DXF, or freehand drawing</p>
          </div>
        </div>
        <div class="canvas-tools">
          <button class="tool-btn" title="Select">◇</button>
          <button class="tool-btn" title="Draw">✎</button>
          <button class="tool-btn" title="Circle">○</button>
          <button class="tool-btn" title="Rectangle">□</button>
          <button class="tool-btn" title="Import">↓</button>
        </div>
      </section>

      <section class="panel params-panel">
        <h2>Inlay Parameters</h2>
        <div class="param-group">
          <label>
            Material
            <select v-model="inlayMaterial">
              <option value="mother-of-pearl">Mother of Pearl</option>
              <option value="abalone">Abalone</option>
              <option value="wood">Contrasting Wood</option>
              <option value="acrylic">Acrylic</option>
              <option value="metal">Metal</option>
            </select>
          </label>
          <label>
            Pocket Depth (mm)
            <input v-model.number="pocketDepth" type="number" step="0.1" min="0.5" max="5" />
          </label>
          <label>
            Tool Diameter (mm)
            <input v-model.number="toolDiameter" type="number" step="0.125" min="0.5" max="6" />
          </label>
          <label>
            Clearance Offset (mm)
            <input v-model.number="clearanceOffset" type="number" step="0.01" min="0" max="0.5" />
          </label>
        </div>
        <div class="button-group">
          <button class="btn-secondary">Generate Pocket</button>
          <button class="btn-primary">Generate Inlay Piece</button>
        </div>
      </section>

      <section class="panel preview-panel">
        <h2>Preview</h2>
        <div class="preview-tabs">
          <button class="tab active">Pocket</button>
          <button class="tab">Inlay</button>
          <button class="tab">Assembled</button>
        </div>
        <div class="preview-container">
          <div class="preview-placeholder">
            <span>Toolpath preview will appear here</span>
          </div>
        </div>
      </section>

      <section class="panel library-panel">
        <h2>Pattern Library</h2>
        <div class="pattern-grid">
          <div class="pattern-item">
            <div class="pattern-preview">◆</div>
            <span>Diamond</span>
          </div>
          <div class="pattern-item">
            <div class="pattern-preview">●</div>
            <span>Dot</span>
          </div>
          <div class="pattern-item">
            <div class="pattern-preview">★</div>
            <span>Star</span>
          </div>
          <div class="pattern-item">
            <div class="pattern-preview">♣</div>
            <span>Clover</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.inlay-designer-view {
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

.canvas-container {
  aspect-ratio: 4/3;
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.canvas-placeholder {
  text-align: center;
  color: #64748b;
}

.canvas-placeholder .icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.canvas-placeholder .hint {
  font-size: 0.875rem;
  color: #94a3b8;
}

.canvas-tools {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.tool-btn {
  width: 2.5rem;
  height: 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.tool-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
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

.param-group input,
.param-group select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-primary,
.btn-secondary {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.preview-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.tab.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
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

.pattern-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.pattern-item {
  text-align: center;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.pattern-item:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.pattern-preview {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.pattern-item span {
  font-size: 0.75rem;
  color: #64748b;
}
</style>
