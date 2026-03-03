<script setup lang="ts">
/**
 * VCarveView - V-Carve Text and Decorative Lettering
 * Create V-carved text, logos, and decorative elements for
 * headstocks, labels, and body accents.
 */
import { ref } from 'vue'

const textContent = ref('Luthier')
const fontFamily = ref('serif')
const vbitAngle = ref(60)
const maxDepth = ref(3)
const flatDepth = ref(0)
</script>

<template>
  <div class="vcarve-view">
    <header class="view-header">
      <h1>V-Carve Designer</h1>
      <p class="subtitle">Create V-carved text, logos, and decorative elements for headstocks and labels</p>
    </header>

    <div class="content-grid">
      <section class="panel text-panel">
        <h2>Text Input</h2>
        <div class="text-input-group">
          <textarea
            v-model="textContent"
            placeholder="Enter text to carve..."
            rows="3"
          ></textarea>
          <div class="font-controls">
            <label>
              Font
              <select v-model="fontFamily">
                <option value="serif">Serif (Classic)</option>
                <option value="sans-serif">Sans-Serif (Modern)</option>
                <option value="script">Script (Elegant)</option>
                <option value="gothic">Gothic (Bold)</option>
                <option value="stencil">Stencil</option>
              </select>
            </label>
            <div class="style-buttons">
              <button class="style-btn" title="Bold">B</button>
              <button class="style-btn" title="Italic">I</button>
              <button class="style-btn" title="Outline">O</button>
            </div>
          </div>
        </div>
      </section>

      <section class="panel params-panel">
        <h2>V-Carve Parameters</h2>
        <div class="param-group">
          <label>
            V-Bit Angle (degrees)
            <select v-model.number="vbitAngle">
              <option :value="30">30°</option>
              <option :value="45">45°</option>
              <option :value="60">60°</option>
              <option :value="90">90°</option>
            </select>
          </label>
          <label>
            Max Depth (mm)
            <input v-model.number="maxDepth" type="number" step="0.5" min="0.5" max="10" />
          </label>
          <label>
            Flat Depth (mm)
            <input v-model.number="flatDepth" type="number" step="0.1" min="0" max="5" />
            <span class="hint">0 for pure V-carve, >0 for flat bottom</span>
          </label>
        </div>
        <button class="btn-primary">Generate Toolpath</button>
      </section>

      <section class="panel preview-panel">
        <h2>Preview</h2>
        <div class="preview-container">
          <div class="text-preview">
            <span :style="{ fontFamily: fontFamily }">{{ textContent || 'Preview' }}</span>
          </div>
        </div>
        <div class="preview-controls">
          <button class="control-btn">2D</button>
          <button class="control-btn active">3D</button>
          <button class="control-btn">Toolpath</button>
        </div>
      </section>

      <section class="panel templates-panel">
        <h2>Templates</h2>
        <div class="template-list">
          <div class="template-item">
            <span class="template-preview">Martin</span>
            <span class="template-name">Classic Headstock</span>
          </div>
          <div class="template-item">
            <span class="template-preview">Est. 2024</span>
            <span class="template-name">Date Stamp</span>
          </div>
          <div class="template-item">
            <span class="template-preview">Custom</span>
            <span class="template-name">Custom Logo</span>
          </div>
          <div class="template-item">
            <span class="template-preview">№ 001</span>
            <span class="template-name">Serial Number</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.vcarve-view {
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

.text-input-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 1rem;
  resize: vertical;
  margin-bottom: 1rem;
}

.font-controls {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
}

.font-controls label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

.font-controls select {
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
}

.style-buttons {
  display: flex;
  gap: 0.25rem;
}

.style-btn {
  width: 2rem;
  height: 2rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.style-btn:hover {
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

.param-group .hint {
  font-size: 0.75rem;
  color: #94a3b8;
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
  aspect-ratio: 16/9;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.text-preview {
  color: #f8fafc;
  font-size: 2rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

.preview-controls {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.control-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  background: #fff;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.control-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.template-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #2563eb;
  background: #f8fafc;
}

.template-preview {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
  min-width: 80px;
}

.template-name {
  font-size: 0.875rem;
  color: #64748b;
}
</style>
